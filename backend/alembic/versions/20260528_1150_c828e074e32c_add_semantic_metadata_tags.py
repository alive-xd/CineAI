"""add semantic metadata tags

Revision ID: c828e074e32c
Revises: b4cea0f35e0a
Create Date: 2026-05-28
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers
revision: str = "c828e074e32c"
down_revision: Union[str, None] = "b4cea0f35e0a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    op.add_column(
        "movies",
        sa.Column(
            "tone_tags",
            postgresql.JSONB(
                astext_type=sa.Text()
            ),
            nullable=False,
            server_default="[]",
        ),
    )

    op.add_column(
        "movies",
        sa.Column(
            "theme_tags",
            postgresql.JSONB(
                astext_type=sa.Text()
            ),
            nullable=False,
            server_default="[]",
        ),
    )

    op.add_column(
        "movies",
        sa.Column(
            "pacing_tags",
            postgresql.JSONB(
                astext_type=sa.Text()
            ),
            nullable=False,
            server_default="[]",
        ),
    )

    op.add_column(
        "movies",
        sa.Column(
            "emotion_tags",
            postgresql.JSONB(
                astext_type=sa.Text()
            ),
            nullable=False,
            server_default="[]",
        ),
    )

    op.add_column(
        "movies",
        sa.Column(
            "embedding_updated_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )


def downgrade() -> None:

    op.drop_column(
        "movies",
        "embedding_updated_at",
    )

    op.drop_column(
        "movies",
        "emotion_tags",
    )

    op.drop_column(
        "movies",
        "pacing_tags",
    )

    op.drop_column(
        "movies",
        "theme_tags",
    )

    op.drop_column(
        "movies",
        "tone_tags",
    )