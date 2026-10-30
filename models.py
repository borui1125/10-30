from datetime import date

from sqlalchemy import String, Integer, ForeignKey, Date, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    name: Mapped[str] = mapped_column(
        String,
        nullable=False
    )

    description: Mapped[str | None] = mapped_column(
        String,
        nullable=True
    )

    event_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True
    )

    registrations: Mapped[list["Registration"]] = relationship(
        "Registration",
        back_populates="event",
        cascade="all, delete-orphan",
    )


class Registration(Base):
    __tablename__ = "registrations"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    event_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "events.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    name: Mapped[str] = mapped_column(
        String,
        nullable=False
    )

    phone: Mapped[str] = mapped_column(
        String,
        nullable=False
    )

    event: Mapped["Event"] = relationship(
        "Event",
        back_populates="registrations"
    )


def init_db(engine):
    """建立所有資料表（若尚未存在）"""
    Base.metadata.create_all(engine)


if __name__ == "__main__":
    DATABASE_URL = (
        "postgresql+psycopg://postgres:950508@localhost:5432/event_db"
    )

    engine = create_engine(
        DATABASE_URL,
        echo=True
    )

    init_db(engine)

    print("資料表建立完成")