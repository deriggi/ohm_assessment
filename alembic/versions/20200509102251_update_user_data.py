"""update user data

Revision ID: 5a47575e3ff6
Revises: 00000000
Create Date: 2020-05-09 10:22:51.822742

"""

# revision identifiers, used by Alembic.
revision = '5a47575e3ff6'
down_revision = '00000000'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.execute('''
        update  user set point_balance = 5000 where user_id = 1;
    ''')

    op.execute('''INSERT INTO rel_user (user_id, rel_lookup, attribute)
        VALUES
            (2, 'LOCATION', 'USA')
    ''')

    op.execute('''
        update  user set Tier = 'Silver' where user_id = 3
    ''')

    


def downgrade():
    pass
