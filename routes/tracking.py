#routes/tracking.py
import io
import os
import base64
import pytz
from datetime import datetime, timezone
from flask import Blueprint, send_file, request
from models import db, EmailStatus

track_bp = Blueprint('track', __name__)

PIXEL_B64 = b'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII='

@track_bp.route('/api/track/<tracking_id>.png')
def track_open(tracking_id):
    print(f"\n--- PIXEL HIT ---", flush=True)
    print(f"Tracking ID: {tracking_id}", flush=True)

    log = EmailStatus.query.filter_by(tracking_id=tracking_id).first()

    if log:
        log.view_count = (log.view_count or 0) + 1
        is_bot = False
        
        # --- THE BULLETPROOF TIME SHIELD (ONLY) ---
        if hasattr(log, 'email_log') and log.email_log and log.email_log.sent_at:
            try:
                now_utc = datetime.now(timezone.utc)
                db_sent_time = log.email_log.sent_at
                
                # Parse the time safely
                if isinstance(db_sent_time, str):
                    clean_string = str(db_sent_time).split('.')[0]
                    parsed_time = datetime.strptime(clean_string, "%Y-%m-%d %H:%M:%S")
                    sent_time_utc = parsed_time.replace(tzinfo=timezone.utc)
                elif db_sent_time.tzinfo is None:
                    sent_time_utc = db_sent_time.replace(tzinfo=timezone.utc)
                else:
                    sent_time_utc = db_sent_time
                    
                seconds_elapsed = (now_utc - sent_time_utc).total_seconds()
                print(f"Time Elapsed: {seconds_elapsed:.1f} seconds", flush=True)
                
                # The 15-Second Rule
                if seconds_elapsed < 15:
                    if os.environ.get('FLASK_ENV') == 'testing':
                        print(">>> SHIELD BYPASS: Testing mode detected.", flush=True)
                        is_bot = False
                    else:
                        is_bot = True
                        print(">>> SHIELD: Blocked fast-scan bot via Time Math!", flush=True)
            except Exception as e:
                print(f"Time Shield Crashed: {str(e)}", flush=True)
        else:
            print("WARNING: Could not find 'sent_at' in parent EmailLog.", flush=True)
            
        # --- UPDATE DATABASE IF HUMAN (After 15s) ---
        if not is_bot and not log.opened:
            ist = pytz.timezone('Asia/Kolkata')
            log.opened = True
            log.opened_at = datetime.now(ist)
            print(f">>> REAL HUMAN: Marked as opened for {log.to_email}!", flush=True)

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"DB Error: {str(e)}", flush=True)
    else:
        print(">>> ERROR: Tracking ID not found.", flush=True)
        
    print("-----------------\n", flush=True)

    response = send_file(io.BytesIO(base64.b64decode(PIXEL_B64)), mimetype='image/png')
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response
