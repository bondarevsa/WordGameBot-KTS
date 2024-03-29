"""Update table

Revision ID: 6a357e808656
Revises: 8c25de61456a
Create Date: 2023-10-02 04:20:45.711531

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6a357e808656'
down_revision: Union[str, None] = '8c25de61456a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('gamescores', sa.Column('vote_status', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('gamescores', 'vote_status')
    # ### end Alembic commands ###
