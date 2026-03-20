from app.db.session import SessionLocal
from app.services.digest_service import DailyDigestService
from app.services.email_service import EmailService
from app.services.llm_service import LLMService


if __name__ == '__main__':
    with SessionLocal() as db:
        svc = DailyDigestService(db=db, llm=LLMService(), email=EmailService())
        payload = svc.build_digest_payload()
        print(f'categories={len(payload)}')
        if payload:
            html = svc.render_html(payload)
            print("Generated.")
