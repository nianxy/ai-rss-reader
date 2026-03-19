from collections import defaultdict
from datetime import datetime, timedelta

from jinja2 import Environment, FileSystemLoader
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import Article
from app.services.config_service import load_rss_config
from app.services.email_service import EmailService
from app.services.llm_service import LLMService

settings = get_settings()


def _yesterday_range(now: datetime | None = None) -> tuple[datetime, datetime]:
    now = now or datetime.now()
    start = datetime(now.year, now.month, now.day) - timedelta(days=1)
    end = datetime(now.year, now.month, now.day)
    return start, end


class DailyDigestService:
    def __init__(self, db: Session, llm: LLMService, email: EmailService) -> None:
        self.db = db
        self.llm = llm
        self.email = email
        self.jinja = Environment(loader=FileSystemLoader('app/templates'), autoescape=True)
        try:
            cfg = load_rss_config(settings.rss_config_path)
            self.category_names = {item.id: item.name for item in cfg.categories}
        except Exception:
            self.category_names = {}

    def build_digest_payload(self) -> list[dict]:
        start, end = _yesterday_range()
        rows = self.db.scalars(
            select(Article).where(and_(Article.created_at >= start, Article.created_at < end)).order_by(Article.id.asc())
        ).all()

        by_category: dict[str, list[Article]] = defaultdict(list)
        for row in rows:
            by_category[row.category_id].append(row)

        output: list[dict] = []
        for _, articles in by_category.items():
            category_name = self.category_names.get(articles[0].category_id, articles[0].category_id)
            dedup_input = [
                {
                    'id': item.id,
                    'source': item.source_name,
                    'title': item.title,
                    'summary_short': item.summary_short,
                }
                for item in articles
            ]
            dedup_result = self.llm.deduplicate_by_llm(category_name=category_name, article_rows=dedup_input)
            keep_map = {int(item['id']): [int(x) for x in item.get('duplicate_ids', [])] for item in dedup_result}
            article_map = {a.id: a for a in articles}

            merged_articles = []
            for keep_id, dup_ids in keep_map.items():
                keep_article = article_map.get(keep_id)
                if not keep_article:
                    continue
                ids = [keep_id, *dup_ids]
                sources = []
                for aid in ids:
                    art = article_map.get(aid)
                    if not art:
                        continue
                    sources.append(art.source_name)
                merged_articles.append(
                    {
                        'id': keep_article.id,
                        'title': keep_article.title,
                        'summary_short': keep_article.summary_short,
                        'sources': sorted(set(sources)) or [keep_article.source_name],
                    }
                )

            output.append({'category_name': category_name, 'articles': merged_articles})
        return output

    def render_html(self, payload: list[dict]) -> str:
        tpl = self.jinja.get_template('daily_digest.html')
        return tpl.render(payload=payload, base_url=settings.server_base_url)

    def send_yesterday_digest(self) -> None:
        payload = self.build_digest_payload()
        if not payload:
            return
        html = self.render_html(payload)
        self.email.send_html(subject='昨日RSS汇总', html=html)
