# scripts/seed_ci_db.py
import os
import sys

# Add the parent directory to the Python path so we can import 'app' and 'models'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import db, User, GmailAccount
from utils.logger import logger

def seed_database():
    with app.app_context():
        logger.info("Initializing CI/CD Database Seeding...")
        
        # 1. Create tables if they don't exist
        db.create_all()
        
        # 2. Pull secure secrets from the CI/CD environment
        smtp_email = os.environ.get("CI_SMTP_EMAIL")
        smtp_password = os.environ.get("CI_SMTP_PASSWORD")
        api_token = os.environ.get("CI_API_TOKEN", "pipeline-test-token-123")
        
        if not smtp_email or not smtp_password:
            logger.error("CRITICAL: CI_SMTP_EMAIL or CI_SMTP_PASSWORD environment variables are missing.")
            print("❌ Seeding failed: Missing SMTP environment variables.")
            sys.exit(1)

        # 3. Inject the Gmail Account
        existing_account = GmailAccount.query.filter_by(role="admin").first()
        if not existing_account:
            admin_account = GmailAccount(
                role="admin",
                email=smtp_email,
                token=smtp_password,
                is_admin=True
            )
            db.session.add(admin_account)
            logger.info(f"Seeded GmailAccount for role: admin ({smtp_email})")
            
        # 4. Inject the API User Token
        existing_user = User.query.filter_by(api_token=api_token).first()
        if not existing_user:
            test_user = User(
                user_id="ci-pipeline-user",
                service_name="admin",
                api_token=api_token,
                is_active=True
            )
            db.session.add(test_user)
            logger.info("Seeded User API Token for role: admin")

        db.session.commit()
        print("✅ Database successfully seeded for CI/CD pipeline.")

if __name__ == "__main__":
    seed_database()