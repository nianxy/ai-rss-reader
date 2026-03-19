from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Article
from app.core.config import get_settings
from app.schemas.article_schema import ArticleDetailOut
from app.services.config_service import load_rss_config

router = APIRouter()
jinja = Environment(loader=FileSystemLoader('app/templates'), autoescape=True)
settings = get_settings()


def _get_category_name(category_id: str) -> str:
    try:
        cfg = load_rss_config(settings.rss_config_path)
        mapping = {item.id: item.name for item in cfg.categories}
        return mapping.get(category_id, category_id)
    except Exception:
        return category_id


@router.get('/healthz')
def healthz() -> dict:
    return {'ok': True}


@router.get('/articles/{article_id}', response_model=ArticleDetailOut)
def get_article(article_id: int, db: Session = Depends(get_db)) -> ArticleDetailOut:
    article = db.scalar(select(Article).where(Article.id == article_id))
    if not article:
        raise HTTPException(status_code=404, detail='article not found')

    return ArticleDetailOut(
        id=article.id,
        category_id=article.category_id,
        category_name=_get_category_name(article.category_id),
        source_name=article.source_name,
        link=article.link,
        title=article.title,
        summary_short=article.summary_short,
        summary_keypoints=article.summary_keypoints,
        created_at=article.created_at,
    )


@router.get('/go/{article_id}', response_class=HTMLResponse)
def article_page(article_id: int, db: Session = Depends(get_db)) -> HTMLResponse:
    article = db.scalar(select(Article).where(Article.id == article_id))
    if not article:
        raise HTTPException(status_code=404, detail='article not found')
    tpl = jinja.get_template('article_detail.html')
    html = tpl.render(article=article)
    return HTMLResponse(content=html)
