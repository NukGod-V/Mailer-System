# tasks.py
from app import celery
from utils.email_sender import send_bulk_emails
from utils.logger import logger

@celery.task(name="dispatch_emails_background", acks_late=True)
def dispatch_emails_background(from_role, to_list, subject, body, content_type, attachments, template_name):
    """
    This function runs completely isolated in the Celery Worker container.
    """
    logger.info(f"[CELERY] Picked up task to send {len(to_list)} emails from {from_role}")
    
    # We just call your existing robust logic!
    send_bulk_emails(from_role, to_list, subject, body, content_type, attachments, template_name)
    
    logger.info("[CELERY] Background task completed.")
    return True