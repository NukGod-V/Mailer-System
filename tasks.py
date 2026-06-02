# tasks.py
import os
from app import celery
from utils.email_sender import send_bulk_emails
from utils.logger import logger

@celery.task(name="dispatch_emails_background", acks_late=True)
def dispatch_emails_background(from_role, to_list, subject, body, content_type, attachments, template_name):
    logger.info(f"[CELERY] Picked up task to send {len(to_list)} emails from {from_role}")

    # 1. Send the email
    send_bulk_emails(from_role, to_list, subject, body, content_type, attachments, template_name)
    logger.info("[CELERY] Email successfully dispatched.")

    # 2. Auto-Delete the attachments to save AWS hard drive space!
    if attachments:
        for file_path in attachments:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"[CELERY] Auto-deleted attachment: {file_path}")
            except Exception as e:
                logger.error(f"[CELERY] Failed to delete file {file_path}: {str(e)}")
