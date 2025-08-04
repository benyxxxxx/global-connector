"""create_and_seed_service_categories

Revision ID: df478cd71cd9
Revises: e5fc093c2709
Create Date: 2025-08-04 18:00:46.237424

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel



# revision identifiers, used by Alembic.
revision = 'df478cd71cd9'
down_revision = 'e5fc093c2709'
branch_labels = None
depends_on = None


def upgrade():
    service_categories_table = op.create_table('service_categories',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False, unique=True),
        sa.Column('description', sqlmodel.sql.sqltypes.AutoString(), nullable=True)
    )

    op.add_column('services',
        sa.Column('category_id', sa.Integer(), sa.ForeignKey('service_categories.id'), nullable=True)
    )

    op.bulk_insert(service_categories_table,
        [
            {'id': 1, 'name': 'food', 'description': 'Restaurant info and delivery options'},
            {'id': 2, 'name': 'sim card', 'description': 'Buy and activate SIM cards or eSIMs'},
            {'id': 3, 'name': 'real estate', 'description': 'Apartment rentals and sales'},
            {'id': 4, 'name': 'surf', 'description': 'Surfing lessons and gear rentals'},
            {'id': 5, 'name': 'sport', 'description': 'Local sports activities and groups'},
            {'id': 6, 'name': 'tourism', 'description': 'Tours and exploration activities'},
            {'id': 7, 'name': 'tech', 'description': 'Phone and computer repair services'}
        ]
    )

def downgrade():
    op.drop_column('services', 'category_id')
    op.drop_table('service_categories')