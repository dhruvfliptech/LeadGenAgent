"""
LinkedIn CSV Import Service

Handles importing contacts from LinkedIn CSV exports with:
- CSV parsing and validation
- Field mapping and transformation
- Deduplication logic
- Batch import processing
- Integration with leads system

Supports LinkedIn's standard Connections.csv export format.
"""

import csv
import io
import hashlib
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.models.linkedin_contacts import LinkedInContact
from app.models.leads import Lead
from app.schemas.linkedin_contacts import (
    CSVFieldMapping,
    CSVImportRequest,
    CSVImportPreview,
    CSVImportResponse,
    LinkedInContactResponse,
)

logger = logging.getLogger(__name__)


class LinkedInImportService:
    """
    Service for importing LinkedIn contacts from CSV files.

    Handles the complete import workflow:
    1. CSV file parsing and validation
    2. Field mapping and data transformation
    3. Deduplication against existing contacts
    4. Batch insertion with error handling
    5. Optional lead creation/linking
    """

    # Standard LinkedIn CSV columns
    LINKEDIN_STANDARD_COLUMNS = [
        'First Name',
        'Last Name',
        'Email Address',
        'Company',
        'Position',
        'Connected On',
        'URL',
    ]

    # Supported date formats in LinkedIn CSVs
    DATE_FORMATS = [
        '%d %b %Y',  # 01 Jan 2023
        '%d/%m/%Y',  # 01/01/2023
        '%Y-%m-%d',  # 2023-01-01
        '%m/%d/%Y',  # 01/01/2023
    ]

    def __init__(self, db: Session):
        """Initialize service with database session."""
        self.db = db

    async def preview_csv(
        self,
        file_content: str,
        field_mapping: Optional[CSVFieldMapping] = None,
    ) -> CSVImportPreview:
        """
        Preview CSV file before import.

        Args:
            file_content: CSV file content as string
            field_mapping: Optional custom field mapping

        Returns:
            CSVImportPreview with sample data and validation
        """
        if field_mapping is None:
            field_mapping = CSVFieldMapping()

        try:
            # Parse CSV
            reader = csv.DictReader(io.StringIO(file_content))
            rows = list(reader)

            if not rows:
                return CSVImportPreview(
                    total_rows=0,
                    sample_contacts=[],
                    field_mapping=field_mapping,
                    detected_columns=[],
                    validation_errors=['CSV file is empty'],
                )

            # Get detected columns
            detected_columns = list(rows[0].keys())

            # Validate required columns exist
            validation_errors = []
            required_fields = ['first_name', 'last_name']

            for field in required_fields:
                column_name = getattr(field_mapping, field)
                if column_name not in detected_columns:
                    validation_errors.append(
                        f"Required column '{column_name}' not found in CSV"
                    )

            # Parse sample contacts (first 5 rows)
            sample_contacts = []
            for row in rows[:5]:
                try:
                    contact = self._parse_csv_row(row, field_mapping)
                    sample_contacts.append(contact)
                except Exception as e:
                    validation_errors.append(f"Row parsing error: {str(e)}")

            return CSVImportPreview(
                total_rows=len(rows),
                sample_contacts=sample_contacts,
                field_mapping=field_mapping,
                detected_columns=detected_columns,
                validation_errors=validation_errors,
            )

        except csv.Error as e:
            logger.error(f"CSV parsing error: {str(e)}")
            return CSVImportPreview(
                total_rows=0,
                sample_contacts=[],
                field_mapping=field_mapping,
                detected_columns=[],
                validation_errors=[f"CSV parsing error: {str(e)}"],
            )

    async def import_csv(
        self,
        file_content: str,
        request: CSVImportRequest,
    ) -> CSVImportResponse:
        """
        Import contacts from CSV file.

        Args:
            file_content: CSV file content as string
            request: Import configuration

        Returns:
            CSVImportResponse with import statistics
        """
        # Generate batch ID if not provided
        import_batch_id = request.import_batch_id or self._generate_batch_id(
            request.filename
        )

        # Parse CSV
        reader = csv.DictReader(io.StringIO(file_content))
        rows = list(reader)

        imported_contacts = []
        skipped_count = 0
        failed_count = 0
        errors = []

        for idx, row in enumerate(rows, start=1):
            try:
                # Parse contact data
                contact_data = self._parse_csv_row(row, request.field_mapping)

                # Check for duplicates if enabled
                if request.skip_duplicates:
                    existing = self._find_duplicate(
                        contact_data,
                        request.deduplicate_by,
                    )
                    if existing:
                        skipped_count += 1
                        logger.debug(
                            f"Skipping duplicate contact: {contact_data.get('first_name')} "
                            f"{contact_data.get('last_name')}"
                        )
                        continue

                # Create contact
                contact = LinkedInContact(
                    **contact_data,
                    imported_from='csv',
                    import_batch_id=import_batch_id,
                    csv_filename=request.filename,
                    tags=request.tags,
                )

                self.db.add(contact)
                self.db.flush()  # Get contact ID

                # Optionally create/link lead
                if contact.email:
                    await self._create_or_link_lead(contact)

                imported_contacts.append(contact)

            except Exception as e:
                failed_count += 1
                error_msg = f"Row {idx}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)

        # Commit all imports
        try:
            self.db.commit()
            logger.info(
                f"Successfully imported {len(imported_contacts)} contacts "
                f"from batch {import_batch_id}"
            )
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to commit imports: {str(e)}")
            raise

        # Convert to response schemas
        contact_responses = [
            LinkedInContactResponse.from_orm(c) for c in imported_contacts
        ]

        return CSVImportResponse(
            import_batch_id=import_batch_id,
            total_rows=len(rows),
            imported=len(imported_contacts),
            skipped=skipped_count,
            failed=failed_count,
            errors=errors,
            contacts=contact_responses,
        )

    def _parse_csv_row(
        self,
        row: Dict[str, str],
        field_mapping: CSVFieldMapping,
    ) -> Dict[str, Any]:
        """
        Parse a single CSV row into contact data.

        Args:
            row: CSV row as dictionary
            field_mapping: Field mapping configuration

        Returns:
            Dictionary of contact data
        """
        contact_data = {}

        # Required fields
        contact_data['first_name'] = row.get(field_mapping.first_name, '').strip()
        contact_data['last_name'] = row.get(field_mapping.last_name, '').strip()

        if not contact_data['first_name'] or not contact_data['last_name']:
            raise ValueError("First name and last name are required")

        # Optional fields
        email = row.get(field_mapping.email, '').strip()
        if email and '@' in email:
            contact_data['email'] = email

        company = row.get(field_mapping.company, '').strip()
        if company:
            contact_data['company'] = company

        position = row.get(field_mapping.position, '').strip()
        if position:
            contact_data['position'] = position

        linkedin_url = row.get(field_mapping.linkedin_url, '').strip()
        if linkedin_url:
            contact_data['linkedin_url'] = linkedin_url

        # Parse connected on date
        connected_on_str = row.get(field_mapping.connected_on, '').strip()
        if connected_on_str:
            connected_on = self._parse_date(connected_on_str)
            if connected_on:
                contact_data['connected_on'] = connected_on

        return contact_data

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """
        Parse date string using multiple formats.

        Args:
            date_str: Date string to parse

        Returns:
            datetime object or None if parsing fails
        """
        for fmt in self.DATE_FORMATS:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        logger.warning(f"Could not parse date: {date_str}")
        return None

    def _find_duplicate(
        self,
        contact_data: Dict[str, Any],
        deduplicate_by: str,
    ) -> Optional[LinkedInContact]:
        """
        Find duplicate contact based on deduplication strategy.

        Args:
            contact_data: Contact data dictionary
            deduplicate_by: Deduplication field (linkedin_url, email, name)

        Returns:
            Existing contact or None
        """
        if deduplicate_by == 'linkedin_url':
            linkedin_url = contact_data.get('linkedin_url')
            if linkedin_url:
                return self.db.query(LinkedInContact).filter(
                    LinkedInContact.linkedin_url == linkedin_url
                ).first()

        elif deduplicate_by == 'email':
            email = contact_data.get('email')
            if email:
                return self.db.query(LinkedInContact).filter(
                    LinkedInContact.email == email
                ).first()

        elif deduplicate_by == 'name':
            return self.db.query(LinkedInContact).filter(
                and_(
                    LinkedInContact.first_name == contact_data.get('first_name'),
                    LinkedInContact.last_name == contact_data.get('last_name'),
                    LinkedInContact.company == contact_data.get('company'),
                )
            ).first()

        return None

    async def _create_or_link_lead(self, contact: LinkedInContact) -> Optional[Lead]:
        """
        Create or link contact to existing lead.

        Args:
            contact: LinkedIn contact

        Returns:
            Lead object or None
        """
        if not contact.email:
            return None

        try:
            # Check for existing lead by email
            lead = self.db.query(Lead).filter(
                Lead.email == contact.email
            ).first()

            if lead:
                # Link contact to existing lead
                contact.lead_id = lead.id
                logger.debug(f"Linked contact {contact.id} to existing lead {lead.id}")
            else:
                # Create new lead
                lead = Lead(
                    name=contact.full_name,
                    email=contact.email,
                    company=contact.company,
                    position=contact.position,
                    source='linkedin_contact',
                    status='new',
                    linkedin_url=contact.linkedin_url,
                )
                self.db.add(lead)
                self.db.flush()

                # Link contact to new lead
                contact.lead_id = lead.id
                logger.debug(f"Created new lead {lead.id} for contact {contact.id}")

            return lead

        except Exception as e:
            logger.error(f"Failed to create/link lead: {str(e)}")
            return None

    def _generate_batch_id(self, filename: str) -> str:
        """
        Generate unique batch ID for import.

        Args:
            filename: CSV filename

        Returns:
            Unique batch ID
        """
        timestamp = datetime.utcnow().isoformat()
        content = f"{filename}_{timestamp}"
        hash_value = hashlib.md5(content.encode()).hexdigest()[:8]
        return f"linkedin_import_{hash_value}"

    async def get_import_batches(
        self,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Get list of import batches with statistics.

        Args:
            limit: Maximum number of batches to return

        Returns:
            List of batch information
        """
        from sqlalchemy import func

        batches = (
            self.db.query(
                LinkedInContact.import_batch_id,
                LinkedInContact.csv_filename,
                func.count(LinkedInContact.id).label('contact_count'),
                func.min(LinkedInContact.created_at).label('imported_at'),
            )
            .filter(LinkedInContact.import_batch_id.isnot(None))
            .group_by(
                LinkedInContact.import_batch_id,
                LinkedInContact.csv_filename,
            )
            .order_by(func.min(LinkedInContact.created_at).desc())
            .limit(limit)
            .all()
        )

        return [
            {
                'import_batch_id': batch.import_batch_id,
                'csv_filename': batch.csv_filename,
                'contact_count': batch.contact_count,
                'imported_at': batch.imported_at.isoformat() if batch.imported_at else None,
            }
            for batch in batches
        ]

    async def delete_import_batch(
        self,
        import_batch_id: str,
    ) -> Tuple[int, int]:
        """
        Delete all contacts from an import batch.

        Args:
            import_batch_id: Batch ID to delete

        Returns:
            Tuple of (contacts_deleted, leads_deleted)
        """
        try:
            # Get contacts in batch
            contacts = self.db.query(LinkedInContact).filter(
                LinkedInContact.import_batch_id == import_batch_id
            ).all()

            contacts_deleted = len(contacts)
            leads_deleted = 0

            # Delete associated leads if they have no other contacts
            for contact in contacts:
                if contact.lead_id:
                    lead = self.db.query(Lead).get(contact.lead_id)
                    if lead and lead.source == 'linkedin_contact':
                        # Check if lead has other LinkedIn contacts
                        other_contacts = self.db.query(LinkedInContact).filter(
                            and_(
                                LinkedInContact.lead_id == lead.id,
                                LinkedInContact.id != contact.id,
                            )
                        ).first()

                        if not other_contacts:
                            self.db.delete(lead)
                            leads_deleted += 1

            # Delete contacts
            for contact in contacts:
                self.db.delete(contact)

            self.db.commit()
            logger.info(
                f"Deleted {contacts_deleted} contacts and {leads_deleted} leads "
                f"from batch {import_batch_id}"
            )

            return contacts_deleted, leads_deleted

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete import batch: {str(e)}")
            raise

    async def export_contacts_to_csv(
        self,
        filters: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Export contacts to CSV format.

        Args:
            filters: Optional filters to apply

        Returns:
            CSV content as string
        """
        # Build query
        query = self.db.query(LinkedInContact)

        if filters:
            if filters.get('status'):
                query = query.filter(LinkedInContact.status == filters['status'])
            if filters.get('import_batch_id'):
                query = query.filter(
                    LinkedInContact.import_batch_id == filters['import_batch_id']
                )
            if filters.get('company'):
                query = query.filter(
                    LinkedInContact.company.ilike(f"%{filters['company']}%")
                )

        contacts = query.all()

        # Generate CSV
        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=[
                'First Name',
                'Last Name',
                'Email Address',
                'Company',
                'Position',
                'LinkedIn URL',
                'Location',
                'Industry',
                'Connected On',
                'Status',
                'Tags',
            ],
        )

        writer.writeheader()

        for contact in contacts:
            writer.writerow({
                'First Name': contact.first_name,
                'Last Name': contact.last_name,
                'Email Address': contact.email or '',
                'Company': contact.company or '',
                'Position': contact.position or '',
                'LinkedIn URL': contact.linkedin_url or '',
                'Location': contact.location or '',
                'Industry': contact.industry or '',
                'Connected On': (
                    contact.connected_on.strftime('%d %b %Y')
                    if contact.connected_on else ''
                ),
                'Status': contact.status,
                'Tags': ', '.join(contact.tags) if contact.tags else '',
            })

        return output.getvalue()
