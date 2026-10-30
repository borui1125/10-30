"""
資料模型定義 (models.py)
依據組員 A 的規格實作：
- Event：活動資料模型
- Registration：報名資料模型
"""

from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # 關聯：一個活動可以有多筆報名紀錄
    # 刪除活動時透過 ORM cascade 與資料庫外鍵確保連帶刪除報名資料，避免孤兒紀錄
    registrations = relationship(
        "Registration",
        back_populates="event",
        cascade="all, delete-orphan",
    )


class Registration(Base):
    __tablename__ = "registrations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    event_id = Column(
        Integer,
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
    )
    name = Column(String(100), nullable=False)
    phone = Column(String(50), nullable=False)

    # 關聯：每筆報名紀錄對應一個活動
    event = relationship("Event", back_populates="registrations")
