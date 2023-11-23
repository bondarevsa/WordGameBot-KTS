"""Update table

Revision ID: 1054f14fa453
Revises: ba2da0a775e4
Create Date: 2023-10-01 18:15:09.387789

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1054f14fa453'
down_revision: Union[str, None] = 'ba2da0a775e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('games', sa.Column('players_turn_time', sa.DateTime(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('games', 'players_turn_time')
    # ### end Alembic commands ###