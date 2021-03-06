"""empty message

Revision ID: 8f587187dd61
Revises: None
Create Date: 2016-09-10 14:51:09.241839

"""

# revision identifiers, used by Alembic.
revision = '8f587187dd61'
down_revision = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('devices',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=64), nullable=False),
    sa.Column('description', sa.String(length=500), nullable=False),
    sa.Column('created_by', sa.String(length=64), nullable=False),
    sa.Column('api_key', sa.String(length=64), nullable=False),
    sa.Column('device_owners_users', postgresql.ARRAY(sa.String()), nullable=True),
    sa.Column('device_owners_groups', postgresql.ARRAY(sa.String()), nullable=True),
    sa.Column('accessible_by_users', postgresql.ARRAY(sa.String()), nullable=True),
    sa.Column('accessible_by_groups', postgresql.ARRAY(sa.String()), nullable=True),
    sa.Column('enabled', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('api_key')
    )
    op.create_table('test',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=64), nullable=True),
    sa.Column('datetime_created', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('test')
    op.drop_table('devices')
    ### end Alembic commands ###
