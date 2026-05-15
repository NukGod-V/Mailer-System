# Roborosx Internal Mailer Pro

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Framework-Flask-green.svg)
![MySQL](https://img.shields.io/badge/Database-MySQL-blue.svg)
![License](https://img.shields.io/badge/License-Internal-red.svg)

## 📧 Project Overview

The **Internal Mailer System** is a robust, production-grade backend service designed to centralize and automate organizational communication. It handles bulk email dispatch, multi-threaded processing, and precise tracking of email engagement.

The system is built for scalability and security, supporting features like role-based access control, dynamic Jinja2 templating, and asynchronous scheduling via APScheduler.

---

## 🚀 Key Features

- **Intelligent Routing:** Supports Unicast (individual USN), Multicast (group wildcards like `puc1*`), and Broadcast (`*`) recipient resolution.
- **Scheduling Engine:** Built-in APScheduler to queue emails for future delivery with full **IST (Asia/Kolkata)** timezone support.
- **Engagement Analytics:** Tracks email opens via a 1×1 transparent tracking pixel (served at `/track/<id>.png`) and logs client IP and User-Agent data into the `email_status` table.
- **Dynamic Templating:** Integrates Jinja2 to render personalized HTML emails using database-driven variables.
- **Security First:**
  - API Token-based authentication for all endpoints.
  - Strict file-type whitelisting (PDF, JPEG, PNG, etc.) to block malicious uploads.
  - SQLAlchemy ORM to prevent SQL injection.

---

## 🏗️ Technical Architecture

The system follows a modular, service-oriented architecture:

- **API Layer:** Flask blueprints handling `/api/send_email` and `/track/` routes.
- **Service Layer:** Multi-threaded SMTP dispatcher using Python's `smtplib` with automated retry logic.
- **Data Layer:** Managed by MySQL (or PostgreSQL via SQLAlchemy) containing tables for Users, Email Logs, Status Tracking, and Scheduled Jobs.
- **Scheduler:** A background worker that polls the database every 30 seconds for pending deliveries.

---

## 🛠️ Installation & Setup

### Prerequisites

- **Python 3.8+**
- **MySQL** or **PostgreSQL** database server
- A valid **Gmail account** with an [App Password](https://support.google.com/accounts/answer/185833) generated for SMTP

### 1. Clone & Install

```bash
git clone https://github.com/your-username/internal-mailer.git
cd internal-mailer
pip install -r requirements.txt
```

### 2. Environment Configuration

Create a `.env` file in the root directory:

```env
DATABASE_URL=mysql+mysqlconnector://user:password@localhost:3306/mailer_db
TRACKING_BASE_URL=https://your-production-domain.com
```

### 3. Initialize Database

```python
from app import app
from models import db

with app.app_context():
    db.create_all()
```

---

## 📖 API Usage

### Send an Immediate Email

**Endpoint:** `POST /api/send_email`

**Request Payload:**

```json
{
  "token": "your_secure_api_token",
  "from_role": "hr_admin",
  "to": ["1BY23MC001", "puc_2024*"],
  "subject": "Monthly Performance Update",
  "template": "monthly_report_v1",
  "body": "Optional fallback text if no template is used."
}
```

**Success Response `(200 OK)`:**

```json
{
  "message": "Emails sent successfully."
}
```

**Error Response `(400 Bad Request)`:**

```json
{
  "message": "Some emails failed to send.",
  "failed_recipients": ["invalid@email.com"]
}
```

---

## 📈 Database Schema

| Table | Purpose |
|---|---|
| `users` | Stores service names and encrypted API tokens |
| `email_logs` | Permanent history of every dispatch attempt and error messages |
| `email_status` | Real-time tracking of views, `opened_at` timestamps, and view counts |
| `scheduled_emails` | Queue for the APScheduler background worker |

---

## 📝 Maintenance & Troubleshooting

- **Logs:** All system activity is recorded in `logs/mailer.log`.
- **Retries:** The system attempts up to 3 SMTP connections before marking an email as `failed` and notifying the admin.
- **Timezone:** Ensure your server system time is synchronized; the application strictly uses `Asia/Kolkata` for all scheduling.
- **SMTP Authentication Errors:** If you see `SMTPAuthenticationError` in the logs, verify that your Gmail App Password stored in the database is correct and has not expired.
- **App Context Errors:** If background threads fail with `Working outside of application context`, ensure `app.app_context()` is pushed inside your threaded wrapper functions.

---

**Author:** Vaibhav Karbhantnal  
*Developed as part of the Roborosx Omni Tech Solutions Backend Internship 2025.*
