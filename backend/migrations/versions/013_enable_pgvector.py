"""Enable pgvector extension for semantic search

Revision ID: 013
Revises: 012
Create Date: 2025-11-04 00:00:00
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '013'
down_revision = '012'
branch_labels = None
depends_on = None


def upgrade():
    """Enable pgvector extension for vector similarity search."""
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')

    # Verify installation
    connection = op.get_bind()
    result = connection.execute(
        sa.text("SELECT * FROM pg_extension WHERE extname = 'vector'")
    )
    if not result.fetchone():
        raise Exception("Failed to install pgvector extension. Please install it manually:\n"
                       "PostgreSQL: CREATE EXTENSION vector;\n"
                       "Or install via package manager:\n"
                       "Ubuntu/Debian: apt install postgresql-15-pgvector\n"
                       "Mac: brew install pgvector")


def downgrade():
    """Disable pgvector extension."""
    # Drop extension (CASCADE will drop dependent columns)
    op.execute('DROP EXTENSION IF EXISTS vector CASCADE')
