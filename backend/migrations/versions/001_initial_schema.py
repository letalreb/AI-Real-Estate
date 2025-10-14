"""Initial database schema migration."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import geoalchemy2

# revision identifiers
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Enable PostGIS extension
    op.execute('CREATE EXTENSION IF NOT EXISTS postgis')
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('is_admin', sa.Boolean(), nullable=True, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    
    # Create auctions table
    op.create_table(
        'auctions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('external_id', sa.String(length=255), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('property_type', sa.Enum('APPARTAMENTO', 'VILLA', 'ATTICO', 'LOCALE_COMMERCIALE', 'UFFICIO', 'MAGAZZINO', 'TERRENO', 'BOX', 'RUSTICO', 'ALTRO', name='propertytype'), nullable=False),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('province', sa.String(length=100), nullable=True),
        sa.Column('address', sa.String(length=500), nullable=True),
        sa.Column('coordinates', geoalchemy2.types.Geometry(geometry_type='POINT', srid=4326), nullable=True),
        sa.Column('surface_sqm', sa.Float(), nullable=True),
        sa.Column('rooms', sa.Integer(), nullable=True),
        sa.Column('bathrooms', sa.Integer(), nullable=True),
        sa.Column('floor', sa.Integer(), nullable=True),
        sa.Column('base_price', sa.Float(), nullable=False),
        sa.Column('current_price', sa.Float(), nullable=True),
        sa.Column('estimated_value', sa.Float(), nullable=True),
        sa.Column('auction_date', sa.DateTime(), nullable=True),
        sa.Column('auction_round', sa.Integer(), nullable=True, default=1),
        sa.Column('court', sa.String(length=200), nullable=True),
        sa.Column('case_number', sa.String(length=100), nullable=True),
        sa.Column('status', sa.Enum('ACTIVE', 'ENDED', 'SUSPENDED', 'CANCELLED', name='auctionstatus'), nullable=True, default='ACTIVE'),
        sa.Column('is_occupied', sa.Boolean(), nullable=True, default=False),
        sa.Column('ai_score', sa.Float(), nullable=True),
        sa.Column('score_breakdown', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('source_url', sa.String(length=500), nullable=True),
        sa.Column('raw_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('scraped_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('embedding_id', sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_auctions_external_id'), 'auctions', ['external_id'], unique=True)
    op.create_index(op.f('ix_auctions_id'), 'auctions', ['id'], unique=False)
    op.create_index(op.f('ix_auctions_city'), 'auctions', ['city'], unique=False)
    op.create_index(op.f('ix_auctions_status'), 'auctions', ['status'], unique=False)
    op.create_index(op.f('ix_auctions_ai_score'), 'auctions', ['ai_score'], unique=False)
    op.create_index(op.f('ix_auctions_auction_date'), 'auctions', ['auction_date'], unique=False)
    
    # Create spatial index on coordinates (idempotent)
    op.execute('CREATE INDEX IF NOT EXISTS idx_auctions_coordinates ON auctions USING GIST (coordinates)')
    
    # Create search_preferences table
    op.create_table(
        'search_preferences',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('filters', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('notify', sa.Boolean(), nullable=True, default=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_search_preferences_id'), 'search_preferences', ['id'], unique=False)
    
    # Create notifications table
    op.create_table(
        'notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('auction_id', sa.Integer(), nullable=True),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=True, default=False),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['auction_id'], ['auctions.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notifications_id'), 'notifications', ['id'], unique=False)
    
    # Create scraping_logs table
    op.create_table(
        'scraping_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source', sa.String(length=100), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('auctions_found', sa.Integer(), nullable=True, default=0),
        sa.Column('auctions_new', sa.Integer(), nullable=True, default=0),
        sa.Column('auctions_updated', sa.Integer(), nullable=True, default=0),
        sa.Column('errors_count', sa.Integer(), nullable=True, default=0),
        sa.Column('status', sa.String(length=50), nullable=True, default='running'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_scraping_logs_id'), 'scraping_logs', ['id'], unique=False)


def downgrade():
    op.drop_table('scraping_logs')
    op.drop_table('notifications')
    op.drop_table('search_preferences')
    op.drop_table('auctions')
    op.drop_table('users')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS propertytype')
    op.execute('DROP TYPE IF EXISTS auctionstatus')
