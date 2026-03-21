from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
import json
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Article, Favorite
from app.core.config import get_settings
from app.schemas.article_schema import ArticleDetailOut
from app.services.config_service import load_rss_config
from app.services.scheduler_service import run_fetch_job

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


def _get_config_maps() -> tuple[dict[str, str], dict[str, str]]:
    try:
        cfg = load_rss_config(settings.rss_config_path)
    except Exception:
        return {}, {}
    category_map = {item.id: item.name for item in cfg.categories}
    source_icon_map: dict[str, str] = {}
    for category in cfg.categories:
        for source in category.sources:
            if source.name and source.icon and source.name not in source_icon_map:
                source_icon_map[source.name] = source.icon
    return category_map, source_icon_map


def _build_list_items(rows: list[Article]) -> list[dict]:
    category_map, source_icon_map = _get_config_maps()
    return [
        {
            'id': item.id,
            'title': item.title,
            'source_name': item.source_name,
            'source_icon': source_icon_map.get(item.source_name, ''),
            'category_name': category_map.get(item.category_id, item.category_id),
            'created_at': item.created_at,
        }
        for item in rows
    ]


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

    favorite = db.scalar(select(Favorite).where(Favorite.article_id == article_id))
    tpl = jinja.get_template('article_detail.html')
    html = tpl.render(article=article, is_favorited=bool(favorite))
    return HTMLResponse(content=html)


@router.post('/favorites/{article_id}')
def add_favorite(article_id: int, db: Session = Depends(get_db)) -> RedirectResponse:
    article = db.scalar(select(Article).where(Article.id == article_id))
    if not article:
        raise HTTPException(status_code=404, detail='article not found')

    existing = db.scalar(select(Favorite).where(Favorite.article_id == article_id))
    if not existing:
        db.add(Favorite(article_id=article_id))
        db.commit()
    return RedirectResponse(url=f'/go/{article_id}', status_code=303)


@router.post('/favorites/{article_id}/remove')
def remove_favorite(article_id: int, db: Session = Depends(get_db)) -> RedirectResponse:
    fav = db.scalar(select(Favorite).where(Favorite.article_id == article_id))
    if fav:
        db.delete(fav)
        db.commit()
    return RedirectResponse(url=f'/go/{article_id}', status_code=303)


@router.get('/articles', response_class=HTMLResponse)
def article_list_page(page: int = 1, db: Session = Depends(get_db)) -> HTMLResponse:
    page_size = 20
    current_page = max(page, 1)
    total = db.scalar(select(func.count(Article.id))) or 0
    total_pages = max((total + page_size - 1) // page_size, 1)
    if current_page > total_pages:
        current_page = total_pages

    offset = (current_page - 1) * page_size
    rows = db.scalars(
        select(Article).order_by(Article.created_at.desc(), Article.id.desc()).offset(offset).limit(page_size)
    ).all()

    tpl = jinja.get_template('article_list.html')
    html = tpl.render(
        articles=_build_list_items(rows),
        page=current_page,
        total_pages=total_pages,
        has_prev=current_page > 1,
        has_next=current_page < total_pages,
        prev_page=current_page - 1,
        next_page=current_page + 1,
        list_title='文章列表',
    )
    return HTMLResponse(content=html)


@router.get('/favorites', response_class=HTMLResponse)
def favorite_list_page(page: int = 1, db: Session = Depends(get_db)) -> HTMLResponse:
    page_size = 20
    current_page = max(page, 1)

    base_query = select(Article).join(Favorite, Favorite.article_id == Article.id)
    total = db.scalar(select(func.count()).select_from(base_query.subquery())) or 0
    total_pages = max((total + page_size - 1) // page_size, 1)
    if current_page > total_pages:
        current_page = total_pages

    offset = (current_page - 1) * page_size
    rows = db.scalars(
        base_query.order_by(Favorite.created_at.desc(), Favorite.id.desc()).offset(offset).limit(page_size)
    ).all()

    tpl = jinja.get_template('article_list.html')
    html = tpl.render(
        articles=_build_list_items(rows),
        page=current_page,
        total_pages=total_pages,
        has_prev=current_page > 1,
        has_next=current_page < total_pages,
        prev_page=current_page - 1,
        next_page=current_page + 1,
        list_title='收藏文章',
        page_base='/favorites',
    )
    return HTMLResponse(content=html)


@router.get('/', response_class=HTMLResponse)
def home(page: int = 1, db: Session = Depends(get_db)) -> HTMLResponse:
    return article_list_page(page=page, db=db)


@router.get('/digests/latest')
def get_latest_digest() -> RedirectResponse:
    out_dir = Path(settings.digest_output_dir)
    digest_files = sorted(out_dir.glob('*.json'))
    if not digest_files:
        raise HTTPException(status_code=404, detail='no digest found')
    latest = digest_files[-1].stem
    return RedirectResponse(url=f'/digests/{latest}', status_code=307)


@router.get('/digests/{date_str}', response_class=HTMLResponse)
def get_digest_html(date_str: str) -> HTMLResponse:
    out_path = Path(settings.digest_output_dir) / f'{date_str}.json'
    if not out_path.exists():
        raise HTTPException(status_code=404, detail='digest json not found')
    payload = json.loads(out_path.read_text(encoding='utf-8'))
    tpl = jinja.get_template('daily_digest.html')
    html = tpl.render(payload=payload, base_url=settings.server_base_url, digest_date=date_str)
    return HTMLResponse(content=html)


@router.get('/fetch/manual', response_class=HTMLResponse)
def trigger_fetch_manually() -> HTMLResponse:
    try:
        run_fetch_job()
        content = '<h3>手动触发抓取成功</h3><p><a href="/">返回首页</a></p>'
        return HTMLResponse(content=content)
    except Exception as exc:
        content = f'<h3>手动触发抓取失败</h3><pre>{exc}</pre><p><a href="/">返回首页</a></p>'
        return HTMLResponse(content=content, status_code=500)
