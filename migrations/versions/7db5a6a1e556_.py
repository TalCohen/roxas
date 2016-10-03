"""empty message

Revision ID: 7db5a6a1e556
Revises: ee799286d836
Create Date: 2016-09-20 15:01:43.587435

"""

# revision identifiers, used by Alembic.
revision = '7db5a6a1e556'
down_revision = 'ee799286d836'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('nfcs', sa.Column('verified', sa.Boolean(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('nfcs', 'verified')
    ### end Alembic commands ###
