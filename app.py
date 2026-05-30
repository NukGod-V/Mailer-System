# app.py
from flask import Flask
from flask_cors import CORS
from celery import Celery
from models import db
from routes.email import email_bp
from routes.tracking import track_bp
from dotenv import load_dotenv
from scheduler import start_scheduler
from utils.logger import logger
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