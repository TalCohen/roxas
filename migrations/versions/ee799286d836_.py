"""empty message

Revision ID: ee799286d836
Revises: 059ac6bb84e1
Create Date: 2016-09-20 14:59:00.317841

"""

# revision identifiers, used by Alembic.
revision = 'ee799286d836'
down_revision = '059ac6bb84e1'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('nfcs', sa.Column('current_rolling_key', sa.String(length=64), nullable=False))
    op.add_column('nfcs', sa.Column('next_rolling_key', sa.String(length=64), nullable=True))
    op.alter_column('nfcs', 'old_rolling_key',
               existing_type=sa.VARCHAR(length=64),
               nullable=True)
    op.create_unique_constraint(None, 'nfcs', ['serial_number'])
    op.drop_column('nfcs', 'rolling_key')
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('nfcs', sa.Column('rolling_key', sa.VARCHAR(length=64), autoincrement=False, nullable=False))
    op.drop_constraint(None, 'nfcs', type_='unique')
    op.alter_column('nfcs', 'old_rolling_key',
               existing_type=sa.VARCHAR(length=64),
               nullable=False)
    op.drop_column('nfcs', 'next_rolling_key')
    op.drop_column('nfcs', 'current_rolling_key')
    ### end Alembic commands ###