"""Initial schema

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum types
    user_role = postgresql.ENUM(
        "instructor", "student", name="userrole", create_type=False
    )
    user_role.create(op.get_bind(), checkfirst=True)

    theme_preference = postgresql.ENUM(
        "byu", "utah", name="themepreference", create_type=False
    )
    theme_preference.create(op.get_bind(), checkfirst=True)

    answer_option = postgresql.ENUM(
        "A", "B", "C", "D", name="answeroption", create_type=False
    )
    answer_option.create(op.get_bind(), checkfirst=True)

    attempt_status = postgresql.ENUM(
        "in_progress", "completed", name="attemptstatus", create_type=False
    )
    attempt_status.create(op.get_bind(), checkfirst=True)

    # Create users table
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", user_role, nullable=False),
        sa.Column("display_name", sa.String(255), nullable=True),
        sa.Column("theme_preference", theme_preference, server_default="byu"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )

    # Create quizzes table
    op.create_table(
        "quizzes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("topic", sa.String(255), nullable=False),
        sa.Column(
            "instructor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("is_published", sa.Boolean, server_default="true"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )

    # Create quiz_tags table
    op.create_table(
        "quiz_tags",
        sa.Column(
            "quiz_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("quizzes.id"),
            primary_key=True,
        ),
        sa.Column("tag", sa.String(100), primary_key=True),
    )

    # Create questions table
    op.create_table(
        "questions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "quiz_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("quizzes.id"),
            nullable=False,
        ),
        sa.Column("question_text", sa.Text, nullable=False),
        sa.Column("option_a", sa.Text, nullable=False),
        sa.Column("option_b", sa.Text, nullable=False),
        sa.Column("option_c", sa.Text, nullable=False),
        sa.Column("option_d", sa.Text, nullable=False),
        sa.Column("correct_answer", answer_option, nullable=False),
        sa.Column("explanation", sa.Text, nullable=True),
        sa.Column("order_index", sa.Integer, nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    # Create quiz_attempts table
    op.create_table(
        "quiz_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "quiz_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("quizzes.id"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column(
            "status", attempt_status, nullable=False, server_default="in_progress"
        ),
        sa.Column("score", sa.Integer, nullable=True),
        sa.Column("started_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime, nullable=True),
    )

    # Create attempt_answers table
    op.create_table(
        "attempt_answers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "attempt_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("quiz_attempts.id"),
            nullable=False,
        ),
        sa.Column(
            "question_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("questions.id"),
            nullable=False,
        ),
        sa.Column("selected_answer", answer_option, nullable=True),
        sa.Column("is_correct", sa.Boolean, nullable=True),
    )

    # Create refresh_tokens table
    op.create_table(
        "refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(255), nullable=False, index=True),
        sa.Column("expires_at", sa.DateTime, nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    # Create indexes
    op.create_index("ix_quizzes_topic", "quizzes", ["topic"])
    op.create_index("ix_quizzes_instructor_id", "quizzes", ["instructor_id"])
    op.create_index("ix_quiz_attempts_user_id", "quiz_attempts", ["user_id"])
    op.create_index("ix_quiz_attempts_quiz_id", "quiz_attempts", ["quiz_id"])


def downgrade() -> None:
    op.drop_index("ix_quiz_attempts_quiz_id")
    op.drop_index("ix_quiz_attempts_user_id")
    op.drop_index("ix_quizzes_instructor_id")
    op.drop_index("ix_quizzes_topic")

    op.drop_table("refresh_tokens")
    op.drop_table("attempt_answers")
    op.drop_table("quiz_attempts")
    op.drop_table("questions")
    op.drop_table("quiz_tags")
    op.drop_table("quizzes")
    op.drop_table("users")

    op.execute("DROP TYPE IF EXISTS attemptstatus")
    op.execute("DROP TYPE IF EXISTS answeroption")
    op.execute("DROP TYPE IF EXISTS themepreference")
    op.execute("DROP TYPE IF EXISTS userrole")
