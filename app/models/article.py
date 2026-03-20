from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Article(Base):
    __tablename__ = 'articles'
    __table_args__ = (UniqueConstraint('category_id', 'dedup_key', name='uq_category_dedup_key'),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category_id: Mapped[str] = mapped_column(String(100), index=True)

    source_name: Mapped[str] = mapped_column(String(255))

    entry_id: Mapped[str] = mapped_column(String(1000), default='')
    dedup_key: Mapped[str] = mapped_column(String(1000))
    title: Mapped[str] = mapped_column(String(1000))
    link: Mapped[str] = mapped_column(String(2000))

    summary_short: Mapped[str] = mapped_column(String(200), default='')
    summary_keypoints: Mapped[str] = mapped_column(Text, default='')

    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now())
