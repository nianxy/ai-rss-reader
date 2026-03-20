import hashlib
import re
from html import unescape
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from datetime import datetime
from email.utils import parsedate_to_datetime

import feedparser
import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Article
from app.schemas.config_schema import CategoryConfig, SourceConfig
from app.services.llm_service import LLMService


class RSSIngestService:
    def __init__(self, db: Session, llm: LLMService) -> None:
        self.db = db
        self.llm = llm

    def run_for_category(self, category: CategoryConfig) -> int:
        created = 0
        for source in category.sources:
            created += self._ingest_source(category, source)
        return created

    def _ingest_source(self, category: CategoryConfig, source: SourceConfig) -> int:
        parsed = feedparser.parse(source.url)
        inserted = 0
        for entry in parsed.entries[: source.fetch_limit]:
            entry_id = str(entry.get('id') or '')
            title = str(entry.get('title') or '').strip()
            link = str(entry.get('link') or '').strip()
            dedup_key = self._compute_dedup_key(entry_id, link)
            if not dedup_key:
                continue

            existing = self.db.scalar(
                select(Article).where(
                    Article.dedup_key == dedup_key,
                )
            )
            if existing:
                continue

            print(f"Processing article [SRC:{source.name}]: {title}")

            content = self._extract_content(entry)
            if len(content.strip()) < 300 and link:
                fallback = self._fetch_content_from_link(link)
                if len(fallback.strip()) > len(content.strip()):
                    content = fallback

            try:
                short_summary, keypoints = self.llm.summarize_article(title=title, content=content)
            except Exception as e:
                print(f"LLM summarization failed: Error: {e}")
                continue

            article = Article(
                category_id=category.id,
                source_name=source.name,
                entry_id=entry_id,
                dedup_key=dedup_key,
                title=title or '(Untitled)',
                link=link,
                summary_short=short_summary,
                summary_keypoints=keypoints,
                published_at=self._parse_published_at(entry),
            )
            self.db.add(article)
            self.db.commit()
            inserted += 1

        return inserted

    @staticmethod
    def _extract_content(entry: dict) -> str:
        if entry.get('content'):
            parts = [str(part.get('value', '')) for part in entry.get('content', [])]
            return '\n'.join(parts).strip()
        if entry.get('summary'):
            return str(entry.get('summary')).strip()
        return ''

    @staticmethod
    def _compute_dedup_key(entry_id: str, link: str) -> str:
        normalized_link = RSSIngestService._normalize_link(link)
        key = entry_id.strip() or normalized_link
        if not key:
            return ''
        return hashlib.md5(key.encode('utf-8')).hexdigest()

    @staticmethod
    def _normalize_link(link: str) -> str:
        raw = (link or '').strip()
        if not raw:
            return ''
        try:
            parsed = urlsplit(raw)
            query_items = [
                (k, v)
                for k, v in parse_qsl(parsed.query, keep_blank_values=True)
                if not k.lower().startswith('utm_')
            ]
            query = urlencode(query_items, doseq=True)
            return urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), parsed.path, query, ''))
        except Exception:
            return raw

    @staticmethod
    def _parse_published_at(entry: dict) -> datetime | None:
        published = entry.get('published') or entry.get('updated')
        if not published:
            return None
        try:
            return parsedate_to_datetime(str(published)).replace(tzinfo=None)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _fetch_content_from_link(link: str) -> str:
        try:
            with httpx.Client(timeout=10, follow_redirects=True) as client:
                resp = client.get(link, headers={'User-Agent': 'rss-reader/0.1'})
                resp.raise_for_status()
                html = resp.text
        except Exception:
            return ''
        return RSSIngestService._extract_focus_text_from_html(html)

    @staticmethod
    def _extract_focus_text_from_html(html: str) -> str:
        # Keep only headings and paragraphs to reduce prompt token usage.
        cleaned = re.sub(r'<(script|style)[^>]*>.*?</\1>', ' ', html, flags=re.IGNORECASE | re.DOTALL)
        blocks = list(
            re.finditer(r'<(?P<tag>h[1-6]|p|tr)\b[^>]*>(?P<inner>.*?)</(?P=tag)>', cleaned, flags=re.IGNORECASE | re.DOTALL)
        )
        if not blocks:
            return ''

        parts: list[str] = []
        for block in blocks:
            tag = block.group('tag').lower()
            inner = block.group('inner')

            if tag.startswith('h'):
                text = RSSIngestService._normalize_inline_text(inner)
                if text:
                    parts.append(f'<{tag}>{text}</{tag}>')
                continue

            if tag == 'p':
                text = RSSIngestService._normalize_inline_text(inner)
                if text:
                    parts.append(text)
                continue

            # Preserve table row shape: td/th -> tab, tr -> newline.
            if tag == 'tr':
                cells = re.findall(r'<(td|th)\b[^>]*>(.*?)</\1>', inner, flags=re.IGNORECASE | re.DOTALL)
                if not cells:
                    continue
                row_cells = []
                for _, cell in cells:
                    cell_text = RSSIngestService._normalize_inline_text(cell)
                    if cell_text:
                        row_cells.append(cell_text)
                if row_cells:
                    parts.append('\t'.join(row_cells))
                continue

        return '\n'.join(parts).strip()

    @staticmethod
    def _normalize_inline_text(raw: str) -> str:
        text = re.sub(r'<[^>]+>', '', raw)
        text = unescape(text).replace('\xa0', ' ')
        text = re.sub(r'\s+', ' ', text).strip()
        text = re.sub(r'\s+([,.;:!?])', r'\1', text)
        text = re.sub(r'\s+([，。；：！？、])', r'\1', text)
        return text
