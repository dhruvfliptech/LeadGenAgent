"""
LinkedIn Integration Test Suite

Comprehensive tests for:
- CSV import functionality
- Contact management
- OAuth flow simulation
- Message sending
- Rate limiting
- API endpoints

Run with: pytest test_linkedin_integration.py -v
"""

import pytest
import io
import csv
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.models import Base
from app.models.linkedin_contacts import LinkedInContact, LinkedInMessage, LinkedInConnection
from app.models.leads import Lead
from app.models.campaigns import Campaign
from app.services.linkedin_import_service import LinkedInImportService
from app.services.linkedin_messaging_service import LinkedInMessagingService
from app.schemas.linkedin_contacts import (
    CSVImportRequest,
    CSVFieldMapping,
    LinkedInMessageCreate,
    LinkedInBulkMessageCreate,
)


# Test database setup
TEST_DATABASE_URL = "sqlite:///./test_linkedin.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a test database session."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session):
    """Create a test client."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    from app.api.deps import get_db
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def sample_csv_content():
    """Generate sample LinkedIn CSV content."""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=[
        'First Name', 'Last Name', 'Email Address',
        'Company', 'Position', 'Connected On', 'URL'
    ])

    writer.writeheader()
    writer.writerow({
        'First Name': 'John',
        'Last Name': 'Doe',
        'Email Address': 'john.doe@example.com',
        'Company': 'Acme Corp',
        'Position': 'Software Engineer',
        'Connected On': '01 Jan 2023',
        'URL': 'https://www.linkedin.com/in/johndoe',
    })
    writer.writerow({
        'First Name': 'Jane',
        'Last Name': 'Smith',
        'Email Address': 'jane.smith@example.com',
        'Company': 'Tech Inc',
        'Position': 'Product Manager',
        'Connected On': '15 Feb 2023',
        'URL': 'https://www.linkedin.com/in/janesmith',
    })

    return output.getvalue()


@pytest.fixture
def sample_contact(db_session):
    """Create a sample LinkedIn contact."""
    contact = LinkedInContact(
        first_name='Test',
        last_name='User',
        email='test@example.com',
        linkedin_url='https://www.linkedin.com/in/testuser',
        company='Test Company',
        position='Test Position',
        status='active',
        can_message=True,
    )
    db_session.add(contact)
    db_session.commit()
    db_session.refresh(contact)
    return contact


@pytest.fixture
def sample_connection(db_session):
    """Create a sample LinkedIn connection."""
    connection = LinkedInConnection(
        linkedin_user_id='test-user-123',
        account_name='Test Account',
        profile_email='test@example.com',
        profile_name='Test User',
        access_token='test-access-token',
        refresh_token='test-refresh-token',
        expires_at=datetime.utcnow() + timedelta(days=60),
        is_active=True,
        is_valid=True,
    )
    db_session.add(connection)
    db_session.commit()
    db_session.refresh(connection)
    return connection


# ============================================================================
# CSV Import Tests
# ============================================================================

class TestCSVImport:
    """Tests for CSV import functionality."""

    @pytest.mark.asyncio
    async def test_preview_csv(self, db_session, sample_csv_content):
        """Test CSV preview before import."""
        service = LinkedInImportService(db_session)

        preview = await service.preview_csv(sample_csv_content)

        assert preview.total_rows == 2
        assert len(preview.sample_contacts) == 2
        assert len(preview.detected_columns) == 7
        assert len(preview.validation_errors) == 0
        assert preview.sample_contacts[0]['first_name'] == 'John'

    @pytest.mark.asyncio
    async def test_import_csv_success(self, db_session, sample_csv_content):
        """Test successful CSV import."""
        service = LinkedInImportService(db_session)

        request = CSVImportRequest(
            filename='test_connections.csv',
            field_mapping=CSVFieldMapping(),
            skip_duplicates=True,
            deduplicate_by='linkedin_url',
        )

        result = await service.import_csv(sample_csv_content, request)

        assert result.imported == 2
        assert result.skipped == 0
        assert result.failed == 0
        assert len(result.errors) == 0

        # Verify contacts in database
        contacts = db_session.query(LinkedInContact).all()
        assert len(contacts) == 2
        assert contacts[0].first_name == 'John'
        assert contacts[0].company == 'Acme Corp'

    @pytest.mark.asyncio
    async def test_import_csv_skip_duplicates(self, db_session, sample_csv_content):
        """Test CSV import with duplicate skipping."""
        service = LinkedInImportService(db_session)

        # First import
        request = CSVImportRequest(
            filename='test_connections.csv',
            field_mapping=CSVFieldMapping(),
            skip_duplicates=True,
            deduplicate_by='linkedin_url',
        )

        result1 = await service.import_csv(sample_csv_content, request)
        assert result1.imported == 2

        # Second import (should skip duplicates)
        result2 = await service.import_csv(sample_csv_content, request)
        assert result2.imported == 0
        assert result2.skipped == 2

    @pytest.mark.asyncio
    async def test_import_csv_with_tags(self, db_session, sample_csv_content):
        """Test CSV import with tags."""
        service = LinkedInImportService(db_session)

        request = CSVImportRequest(
            filename='test_connections.csv',
            tags=['engineering', 'prospects'],
            skip_duplicates=True,
        )

        result = await service.import_csv(sample_csv_content, request)

        contacts = db_session.query(LinkedInContact).all()
        assert 'engineering' in contacts[0].tags
        assert 'prospects' in contacts[0].tags

    @pytest.mark.asyncio
    async def test_export_contacts_to_csv(self, db_session, sample_contact):
        """Test exporting contacts to CSV."""
        service = LinkedInImportService(db_session)

        csv_content = await service.export_contacts_to_csv()

        assert 'First Name' in csv_content
        assert 'Test' in csv_content
        assert 'User' in csv_content
        assert 'Test Company' in csv_content


# ============================================================================
# Contact Management Tests
# ============================================================================

class TestContactManagement:
    """Tests for contact CRUD operations."""

    def test_create_contact(self, db_session):
        """Test creating a new contact."""
        contact = LinkedInContact(
            first_name='New',
            last_name='Contact',
            email='new@example.com',
            company='New Company',
        )

        db_session.add(contact)
        db_session.commit()
        db_session.refresh(contact)

        assert contact.id is not None
        assert contact.full_name == 'New Contact'
        assert contact.status == 'active'

    def test_contact_properties(self, sample_contact):
        """Test contact computed properties."""
        assert sample_contact.full_name == 'Test User'
        assert sample_contact.can_send_message == True

        # Disable messaging
        sample_contact.can_message = False
        assert sample_contact.can_send_message == False

    def test_contact_to_dict(self, sample_contact):
        """Test contact serialization."""
        data = sample_contact.to_dict()

        assert data['id'] == sample_contact.id
        assert data['first_name'] == 'Test'
        assert data['full_name'] == 'Test User'
        assert data['company'] == 'Test Company'


# ============================================================================
# Messaging Tests
# ============================================================================

class TestMessaging:
    """Tests for LinkedIn messaging functionality."""

    @pytest.mark.asyncio
    @patch('app.services.linkedin_messaging_service.httpx.AsyncClient')
    async def test_send_message(self, mock_client, db_session, sample_contact, sample_connection):
        """Test sending a message."""
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {'id': 'message-123'}
        mock_response.raise_for_status = Mock()

        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        service = LinkedInMessagingService(db_session)

        message_create = LinkedInMessageCreate(
            contact_id=sample_contact.id,
            message_content='Hello {{first_name}}, this is a test message.',
            message_type='direct',
        )

        message = await service.send_message(
            contact_id=sample_contact.id,
            message_create=message_create,
            connection=sample_connection,
        )

        assert message.id is not None
        assert message.status == 'sent'
        assert message.contact_id == sample_contact.id

        # Verify contact updated
        db_session.refresh(sample_contact)
        assert sample_contact.total_messages_sent == 1

    def test_message_personalization(self, db_session, sample_contact):
        """Test message personalization."""
        service = LinkedInMessagingService(db_session)

        template = 'Hi {{first_name}} from {{company}}, interested in {{position}}?'

        personalized = service._personalize_message(template, sample_contact)

        assert personalized == 'Hi Test from Test Company, interested in Test Position?'

    @pytest.mark.asyncio
    async def test_rate_limiting(self, db_session, sample_connection):
        """Test rate limiting checks."""
        service = LinkedInMessagingService(db_session)
        service.daily_message_limit = 5

        # Should pass initially
        can_send = await service._check_rate_limits(sample_connection)
        assert can_send == True

        # Exceed limit
        sample_connection.daily_messages_sent = 5
        db_session.commit()

        can_send = await service._check_rate_limits(sample_connection)
        assert can_send == False
        assert sample_connection.rate_limit_exceeded == True


# ============================================================================
# OAuth Tests
# ============================================================================

class TestOAuth:
    """Tests for OAuth authentication flow."""

    def test_get_authorization_url(self, db_session):
        """Test generating authorization URL."""
        service = LinkedInMessagingService(db_session)
        service.client_id = 'test-client-id'

        url = service.get_authorization_url(state='test-state')

        assert 'linkedin.com/oauth/v2/authorization' in url
        assert 'client_id=test-client-id' in url
        assert 'state=test-state' in url

    @pytest.mark.asyncio
    @patch('app.services.linkedin_messaging_service.httpx.AsyncClient')
    async def test_exchange_code_for_token(self, mock_client, db_session):
        """Test exchanging authorization code for token."""
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            'access_token': 'test-token',
            'expires_in': 5184000,
            'refresh_token': 'refresh-token',
        }
        mock_response.raise_for_status = Mock()

        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        service = LinkedInMessagingService(db_session)
        service.client_id = 'test-client-id'
        service.client_secret = 'test-client-secret'

        result = await service.exchange_code_for_token('test-code')

        assert result['access_token'] == 'test-token'
        assert result['refresh_token'] == 'refresh-token'

    def test_connection_properties(self, sample_connection):
        """Test connection computed properties."""
        assert sample_connection.is_token_expired == False
        assert sample_connection.can_send_messages == True
        assert sample_connection.messages_remaining_today > 0


# ============================================================================
# API Endpoint Tests
# ============================================================================

class TestAPIEndpoints:
    """Tests for LinkedIn API endpoints."""

    def test_list_contacts_endpoint(self, client, sample_contact):
        """Test listing contacts via API."""
        response = client.get('/api/v1/linkedin/contacts')

        assert response.status_code == 200
        data = response.json()
        assert data['total'] == 1
        assert len(data['contacts']) == 1
        assert data['contacts'][0]['first_name'] == 'Test'

    def test_get_contact_endpoint(self, client, sample_contact):
        """Test getting single contact via API."""
        response = client.get(f'/api/v1/linkedin/contacts/{sample_contact.id}')

        assert response.status_code == 200
        data = response.json()
        assert data['id'] == sample_contact.id
        assert data['full_name'] == 'Test User'

    def test_create_contact_endpoint(self, client):
        """Test creating contact via API."""
        contact_data = {
            'first_name': 'API',
            'last_name': 'Test',
            'email': 'api@example.com',
            'company': 'API Company',
        }

        response = client.post('/api/v1/linkedin/contacts', json=contact_data)

        assert response.status_code == 201
        data = response.json()
        assert data['first_name'] == 'API'
        assert data['full_name'] == 'API Test'

    def test_update_contact_endpoint(self, client, sample_contact):
        """Test updating contact via API."""
        update_data = {
            'company': 'Updated Company',
            'position': 'Updated Position',
        }

        response = client.put(
            f'/api/v1/linkedin/contacts/{sample_contact.id}',
            json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data['company'] == 'Updated Company'
        assert data['position'] == 'Updated Position'

    def test_delete_contact_endpoint(self, client, sample_contact):
        """Test deleting contact via API."""
        response = client.delete(f'/api/v1/linkedin/contacts/{sample_contact.id}')

        assert response.status_code == 204

    def test_contact_stats_endpoint(self, client, sample_contact):
        """Test contact statistics endpoint."""
        response = client.get('/api/v1/linkedin/stats/contacts')

        assert response.status_code == 200
        data = response.json()
        assert data['total_contacts'] >= 1
        assert data['active_contacts'] >= 1


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """End-to-end integration tests."""

    @pytest.mark.asyncio
    async def test_full_import_and_message_flow(
        self,
        db_session,
        sample_csv_content,
        sample_connection,
    ):
        """Test complete flow from import to messaging."""
        # Import contacts
        import_service = LinkedInImportService(db_session)

        request = CSVImportRequest(
            filename='test.csv',
            skip_duplicates=True,
        )

        import_result = await import_service.import_csv(sample_csv_content, request)
        assert import_result.imported == 2

        # Get imported contacts
        contacts = db_session.query(LinkedInContact).all()
        assert len(contacts) == 2

        # Send message to first contact
        messaging_service = LinkedInMessagingService(db_session)

        with patch('app.services.linkedin_messaging_service.httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = {'id': 'msg-123'}
            mock_response.raise_for_status = Mock()

            mock_client_instance = AsyncMock()
            mock_client_instance.post.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_client_instance

            message_create = LinkedInMessageCreate(
                contact_id=contacts[0].id,
                message_content='Test message',
            )

            message = await messaging_service.send_message(
                contact_id=contacts[0].id,
                message_create=message_create,
                connection=sample_connection,
            )

            assert message.status == 'sent'

            # Verify stats
            db_session.refresh(contacts[0])
            assert contacts[0].total_messages_sent == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
