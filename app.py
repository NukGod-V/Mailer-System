# app.py
from flask import Flask, request, jsonify
from celery import Celery
from flask_cors import CORS
from models import db, User, GmailAccount, EmailLog, EmailStatus
from routes.email import email_bp
from routes.tracking import track_bp
from dotenv import load_dotenv
from scheduler import start_scheduler
from utils.logger import logger
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
import os

load_dotenv()
# --- CELERY FACTORY ---
def make_celery(app):
    celery = Celery(
        app.import_name, 
        broker=os.getenv('REDIS_URL', 'redis://redis:6379/0')
    )
    celery.conf.update(app.config, broker_connection_retry_on_startup=True)
    
    # This binds Celery to Flask so it can read/write to MySQL
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
                
    celery.Task = ContextTask
    return celery

sentry_sdk.init(
    dsn=os.environ.get("SENTRY_DSN"),
    integrations=[
        FlaskIntegration(),
        CeleryIntegration()
    ],
    # Set traces_sample_rate to 1.0 to capture 100% of transactions for performance monitoring.
    traces_sample_rate=1.0,
    # Set to 'production' so your dashboard organizes errors properly
    environment="production" 
)

app = Flask(__name__)
CORS(app)
# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize Celery
celery = make_celery(app)

# IMPORTANT: Import tasks here AFTER celery is initialized so it registers them
import tasks 

# Register database and blueprint routes
db.init_app(app)

# Define root route
@app.route('/')
def home():
    logger.info("Home endpoint accessed")
    return "Welcome to the mailer system!"

# Register blueprint routes
app.register_blueprint(email_bp)
app.register_blueprint(track_bp)

#fetch from the database
@app.route('/api/emails', methods=['GET'])
def get_emails():
    # Fetch the 50 most recent emails
    logs = EmailLog.query.order_by(EmailLog.sent_at.desc()).limit(50).all()
    
    log_data = []
    for log in logs:
        # Check if there is tracking data in the EmailStatus table
        status_record = log.statuses[0] if log.statuses else None
        
        # Determine what to show on the UI
        display_status = "Sent"
        opened_time = None
        
        if status_record:
            if status_record.opened:
                display_status = "Opened"
                opened_time = status_record.opened_at.strftime("%b %d, %I:%M %p") if status_record.opened_at else None
            elif status_record.sent:
                display_status = "Delivered"

        log_data.append({
            "id": f"e{log.log_id:03d}",
            "to": log.to_email,
            "subject": log.subject,
            "status": display_status,
            "sentAt": log.sent_at.strftime("%b %d, %I:%M %p") if log.sent_at else "Unknown",
            "openedAt": opened_time,
            "role": "admin"
        })
        
    return jsonify(log_data), 200

@app.route('/api/admin/purge', methods=['POST'])
def purge_database():
    # 1. SECURITY CHECK: Read the Authorization header
    auth_header = request.headers.get('Authorization')
    
    # 2. If the header is missing or doesn't match our secret password, kick them out!
    if auth_header != "NukeGod":
        return jsonify({"error": "Unauthorized: Nice try, hacker."}), 401

    # 3. If the password matches, execute the purge
    try:
        # Delete all statuses first (because of foreign key constraints)
        EmailStatus.query.delete()
        # Then delete the core logs
        EmailLog.query.delete()
        db.session.commit()
        return jsonify({"message": "Database completely purged."}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/api/debug-sentry')
def trigger_error():
    # This will intentionally crash Python by dividing by zero
    division_by_zero = 1 / 0
    return "This will never render"

if __name__ == '__main__':
    logger.info("Starting mailer application")
    
    # Initialize database tables
    with app.app_context():
        logger.info("Creating database tables if they don't exist")
        db.create_all()
        
        # Start scheduled tasks
        logger.info("Starting scheduler")
        start_scheduler(app)
    
    logger.info("Running Flask application")
    # app.run(debug=True)
    # Production configuration
    # app.run(host='0.0.0.0', port=10000)
    app.run(host='0.0.0.0', port=5000, debug=True)
