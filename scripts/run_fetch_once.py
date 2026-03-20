from app.core.config import get_settings
from app.db.session import SessionLocal
from app.services.config_service import load_rss_config
from app.services.llm_service import LLMService
from app.services.rss_service import RSSIngestService


if __name__ == '__main__':
    settings = get_settings()
    cfg = load_rss_config(settings.rss_config_path)
    llm = LLMService()
    with SessionLocal() as db:
        svc = RSSIngestService(db=db, llm=llm)
        for cat in cfg.categories:
            count = svc.run_for_category(cat)
            print(f'category={cat.id} inserted={count}')
