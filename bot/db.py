from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import DateTime, Integer, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    current_node: Mapped[str] = mapped_column(String, nullable=False)
    waiting_for: Mapped[str | None] = mapped_column(String, nullable=True)
    last_message_sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class FutureMessage(Base):
    __tablename__ = "future_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    chat_id: Mapped[int] = mapped_column(Integer, nullable=False)
    node_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    source_node_id: Mapped[str | None] = mapped_column(String, nullable=True)
    send_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


@dataclass(frozen=True)
class UserState:
    user_id: int
    current_node: str
    waiting_for: str | None = None
    last_message_sent_at: datetime | None = None


@dataclass(frozen=True)
class ScheduledFutureMessage:
    id: int
    user_id: int
    chat_id: int
    node_id: str
    source_node_id: str | None
    send_at: datetime


@dataclass(frozen=True)
class AdminStats:
    total_users: int
    registered_last_7_days: int
    completed_last_7_days: int
    registered_last_30_days: int
    completed_last_30_days: int


def database_url(path: Path) -> str:
    return f"sqlite:///{path}"


def aware_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


def alembic_config(database_path: Path) -> Config:
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url(database_path))
    config.attributes["database_path_set"] = True
    config.attributes["database_path"] = database_path
    return config


def init_database(database_path: Path) -> None:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    command.upgrade(alembic_config(database_path), "head")


class StateStorage:
    def __init__(self, path: Path, admin_user_ids: tuple[int, ...] = ()) -> None:
        self.path = path
        self.admin_user_ids = set(admin_user_ids)
        if not self.path.exists():
            raise RuntimeError(
                f"Database file does not exist: {self.path}. "
                f"Run `python -m bot.main --init-db` and add `DATABASE_PATH={self.path}` to .env."
            )
        self.engine = create_engine(database_url(self.path), future=True)
        self.session_factory = sessionmaker(self.engine, expire_on_commit=False, future=True)

    def get(self, user_id: int) -> UserState | None:
        with self.session_factory() as session:
            user = session.get(User, user_id)
            if user is None:
                return None
            return UserState(
                user_id=user.user_id,
                current_node=user.current_node,
                waiting_for=user.waiting_for,
                last_message_sent_at=user.last_message_sent_at,
            )

    def set(self, user_id: int, current_node: str, waiting_for: str | None = None) -> None:
        now = datetime.now(UTC)
        with self.session_factory() as session:
            self._upsert_user(session, user_id, current_node, waiting_for, now)
            session.commit()

    @staticmethod
    def _upsert_user(
        session: Session,
        user_id: int,
        current_node: str,
        waiting_for: str | None,
        now: datetime,
    ) -> None:
        user = session.scalar(select(User).where(User.user_id == user_id))
        if user is None:
            session.add(
                User(
                    user_id=user_id,
                    current_node=current_node,
                    waiting_for=waiting_for,
                    last_message_sent_at=now,
                    created_at=now,
                    updated_at=now,
                )
            )
            return

        user.current_node = current_node
        user.waiting_for = waiting_for
        user.last_message_sent_at = now
        user.updated_at = now

    def schedule_future_message(
        self,
        user_id: int,
        chat_id: int,
        node_id: str,
        send_at: datetime,
        source_node_id: str | None = None,
    ) -> None:
        now = datetime.now(UTC)
        with self.session_factory() as session:
            future_message = session.scalar(
                select(FutureMessage).where(
                    FutureMessage.user_id == user_id,
                    FutureMessage.node_id == node_id,
                    FutureMessage.source_node_id == source_node_id,
                    FutureMessage.status == "pending",
                )
            )
            if future_message is None:
                session.add(
                    FutureMessage(
                        user_id=user_id,
                        chat_id=chat_id,
                        node_id=node_id,
                        source_node_id=source_node_id,
                        send_at=send_at,
                        status="pending",
                        created_at=now,
                    )
                )
            else:
                future_message.chat_id = chat_id
                future_message.send_at = send_at
            session.commit()

    def due_future_messages(self, now: datetime, limit: int = 100) -> list[ScheduledFutureMessage]:
        with self.session_factory() as session:
            rows = session.scalars(
                select(FutureMessage)
                .where(
                    FutureMessage.status == "pending",
                    FutureMessage.send_at <= now,
                )
                .order_by(FutureMessage.send_at, FutureMessage.id)
                .limit(limit)
            ).all()
            return [
                ScheduledFutureMessage(
                    id=row.id,
                    user_id=row.user_id,
                    chat_id=row.chat_id,
                    node_id=row.node_id,
                    source_node_id=row.source_node_id,
                    send_at=row.send_at,
                )
                for row in rows
            ]

    def mark_future_message_sent(self, user_id: int, node_id: str) -> None:
        now = datetime.now(UTC)
        with self.session_factory() as session:
            rows = session.scalars(
                select(FutureMessage).where(
                    FutureMessage.user_id == user_id,
                    FutureMessage.node_id == node_id,
                    FutureMessage.status == "pending",
                )
            ).all()
            for row in rows:
                row.status = "sent"
                row.sent_at = now
            session.commit()

    def admin_stats(self, completed_node_ids: set[str], now: datetime | None = None) -> AdminStats:
        now = now or datetime.now(UTC)
        last_7_days = now - timedelta(days=7)
        last_30_days = now - timedelta(days=30)

        with self.session_factory() as session:
            base_query = select(User)
            if self.admin_user_ids:
                base_query = base_query.where(User.user_id.not_in(self.admin_user_ids))
            users = session.scalars(base_query).all()

        completed_users = [user for user in users if user.current_node in completed_node_ids]
        return AdminStats(
            total_users=len(users),
            registered_last_7_days=sum(
                aware_datetime(user.created_at) >= last_7_days for user in users
            ),
            completed_last_7_days=sum(
                aware_datetime(user.updated_at) >= last_7_days for user in completed_users
            ),
            registered_last_30_days=sum(
                aware_datetime(user.created_at) >= last_30_days for user in users
            ),
            completed_last_30_days=sum(
                aware_datetime(user.updated_at) >= last_30_days for user in completed_users
            ),
        )
