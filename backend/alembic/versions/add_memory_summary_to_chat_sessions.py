"""添加memory_summary字段到chat_sessions表

Revision ID: add_memory_summary
Revises: 1101db6a84b8
Create Date: 2025-01-XX XX:XX:XX.XXXXXX

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_memory_summary'
down_revision: Union[str, None] = '1101db6a84b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 添加 memory_summary 字段到 chat_sessions 表
    op.add_column('chat_sessions', sa.Column('memory_summary', sa.Text(), nullable=True))


def downgrade() -> None:
    # 删除 memory_summary 字段
    op.drop_column('chat_sessions', 'memory_summary')

