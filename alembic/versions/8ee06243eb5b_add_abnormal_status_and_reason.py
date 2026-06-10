"""add_abnormal_status_and_reason

Revision ID: 8ee06243eb5b
Revises: 
Create Date: 2026-05-05 22:05:09.014729

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8ee06243eb5b'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 添加 abnormal_reason 列
    op.add_column('orders', sa.Column('abnormal_reason', sa.Text(), nullable=True))

    # 修改 status 列的 ENUM，添加 'abnormal' 选项
    op.execute("""
        ALTER TABLE orders 
        MODIFY COLUMN status ENUM(
            'pending', 'pending_review', 'accepted', 'in_progress', 
            'review', 'completed', 'cancelled', 'disputed', 'abnormal'
        ) NOT NULL DEFAULT 'pending_review'
    """)


def downgrade() -> None:
    # 删除 abnormal_reason 列
    op.drop_column('orders', 'abnormal_reason')

    # 恢复旧的 ENUM（移除 'abnormal'）
    op.execute("""
        ALTER TABLE orders 
        MODIFY COLUMN status ENUM(
            'pending', 'pending_review', 'accepted', 'in_progress', 
            'review', 'completed', 'cancelled', 'disputed'
        ) NOT NULL DEFAULT 'pending_review'
    """)
