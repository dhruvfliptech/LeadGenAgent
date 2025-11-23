"""Create knowledge base tables with pgvector embeddings

Revision ID: 020
Revises: 019
Create Date: 2025-11-05
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision = '020'
down_revision = '019'
branch_labels = None
depends_on = None


def upgrade():
    """Create knowledge base tables"""

    # Create knowledge_base_entries table
    op.create_table(
        'knowledge_base_entries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('entry_type', sa.String(length=50), nullable=False, index=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('metadata_json', JSONB(), nullable=True),
        sa.Column('tags', ARRAY(sa.String(100)), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=True, index=True),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='0', index=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true', index=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for common queries
    op.create_index('idx_kb_entry_type_active', 'knowledge_base_entries', ['entry_type', 'is_active'])
    op.create_index('idx_kb_category_active', 'knowledge_base_entries', ['category', 'is_active'])
    op.create_index('idx_kb_priority_desc', 'knowledge_base_entries', [sa.text('priority DESC')])
    op.create_index('idx_kb_tags_gin', 'knowledge_base_entries', ['tags'], postgresql_using='gin')

    # Create knowledge_base_embeddings table with pgvector
    op.create_table(
        'knowledge_base_embeddings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('entry_id', sa.Integer(), nullable=False),
        sa.Column('embedding', Vector(1536), nullable=False),
        sa.Column('model', sa.String(length=100), nullable=False, server_default='text-embedding-ada-002'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['entry_id'], ['knowledge_base_entries.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create index for foreign key
    op.create_index('idx_kb_embedding_entry_id', 'knowledge_base_embeddings', ['entry_id'])

    # Create vector similarity search index using IVFFlat
    # Note: This index will be created after inserting some vectors (needs training data)
    # We'll use a placeholder that can be activated later
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_kb_embedding_vector
        ON knowledge_base_embeddings
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100);
    """)

    # Create trigger for updated_at timestamp
    op.execute("""
        CREATE OR REPLACE FUNCTION update_knowledge_base_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER trigger_knowledge_base_updated_at
        BEFORE UPDATE ON knowledge_base_entries
        FOR EACH ROW
        EXECUTE FUNCTION update_knowledge_base_updated_at();
    """)


def downgrade():
    """Drop knowledge base tables"""

    # Drop triggers and functions
    op.execute('DROP TRIGGER IF EXISTS trigger_knowledge_base_updated_at ON knowledge_base_entries;')
    op.execute('DROP FUNCTION IF EXISTS update_knowledge_base_updated_at();')

    # Drop tables (CASCADE will handle foreign keys)
    op.drop_table('knowledge_base_embeddings')
    op.drop_table('knowledge_base_entries')
