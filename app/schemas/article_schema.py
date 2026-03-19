from datetime import datetime

from pydantic import BaseModel


class ArticleDetailOut(BaseModel):
    id: int
    category_id: str
    category_name: str
    source_name: str
    link: str
    title: str
    summary_short: str
    summary_keypoints: str
    created_at: datetime
