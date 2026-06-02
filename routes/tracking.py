#routes/tracking.py
from flask import Blueprint, send_file, request
from models import db, EmailStatus
from datetime import datetime
from utils.logger import logger
import pytz
import io
import base64

track_bp = Blueprint('track', __name__)

# The raw binary math for a 1x1 transparent PNG!
PIXEL_B64 = b'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII='

@track_bp.route('/api/track/<tracking_id>.png')
def track_open(tracking_id):
    client_ip = request.remote_addr
    user_agent = request.headers.get('User-Agent', 'Unknown')

    logger.info(f"Tracking pixel accessed for ID: {tracking_id}")
    log = EmailStatus.query.filter_by(tracking_id=tracking_id).first()

    if log:
        log.view_count = (log.view_count or 0) + 1
        if not log.opened and log.view_count >= 1:
            ist = pytz.timezone('Asia/Kolkata')
            log.opened = True
            log.opened_at = datetime.now(ist)
            logger.info(f"Confirmed real open for email to {log.to_email}")

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to update tracking: {str(e)}")

    # Generate the image directly from RAM (No physical file needed!)
    pixel_data = base64.b64decode(PIXEL_B64)
    response = send_file(io.BytesIO(pixel_data), mimetype='image/png')
    
    # Anti-Caching Headers so Google fetches it every time
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response
