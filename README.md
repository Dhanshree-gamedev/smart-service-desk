# Smart Service Desk

A production-ready web-based service request management system built with Flask and SQLite.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0-green.svg)
![SQLite](https://img.shields.io/badge/SQLite-3-lightgrey.svg)

## Features

- **Role-Based Access Control**: Separate interfaces for Users and Administrators
- **Request Lifecycle Management**: Strict forward-only status transitions (Submitted → In Progress → Resolved)
- **Complete Audit Trail**: Every status change is logged with timestamps and remarks
- **Modern UI**: Glassmorphism design with smooth animations
- **CSRF Protection**: All forms protected against cross-site request forgery
- **Production-Ready**: Indexed database, secure password hashing, session management

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the Application

```bash
python app.py
```

The server will start at `http://127.0.0.1:5000`

### 3. Default Credentials

**Admin Account:**
- Email: `admin@servicedesk.com`
- Password: `admin123`

## Project Structure

```
auth/
├── app.py                    # Main Flask application
├── config.py                 # Configuration settings
├── database.py               # Database initialization
├── requirements.txt          # Python dependencies
├── models/
│   ├── user.py               # User model with Flask-Login
│   └── request.py            # Service request & audit log
├── routes/
│   ├── __init__.py           # Role decorators
│   ├── auth.py               # Login/Register/Logout
│   ├── user.py               # User dashboard & requests
│   └── admin.py              # Admin management
├── static/
│   ├── css/style.css         # Modern CSS design system
│   └── js/main.js            # Client-side interactions
├── templates/
│   ├── base.html             # Base template
│   ├── landing.html          # Public landing page
│   ├── auth/                 # Login & Register
│   ├── user/                 # User dashboard & views
│   ├── admin/                # Admin dashboard & views
│   └── errors/               # Error pages
└── instance/
    └── service_desk.db       # SQLite database (auto-created)
```

## User Roles

### User (Student/Citizen)
- Register and login
- Submit new service requests
- Track request status and history
- View audit trail for their requests

### Admin (Service Authority)
- View all system requests
- Filter by status and category
- Update request status with remarks
- Monitor complete audit logs

## Request Lifecycle

```
Submitted → In Progress → Resolved
```

- **Submitted**: Initial state when user creates a request
- **In Progress**: Admin has started working on the request
- **Resolved**: Request has been completed (final state, locked)

> **Note**: Reverse transitions are blocked. Once resolved, requests cannot be modified.

## Database Schema

### Users Table
- `user_id` - Primary key
- `name` - User's full name
- `email` - Unique email address
- `password` - Hashed password (PBKDF2)
- `role` - USER or ADMIN
- `created_at` - Registration timestamp

### Service Requests Table
- `request_id` - Primary key (auto-generated)
- `user_id` - Foreign key to users
- `title` - Request title
- `description` - Detailed description
- `category` - Service category
- `status` - Current status
- `created_at` / `updated_at` - Timestamps

### Request Status Log (Audit Trail)
- `log_id` - Primary key
- `request_id` - Foreign key to requests
- `old_status` / `new_status` - Status transition
- `remark` - Admin comment
- `updated_by` - Admin who made the change
- `updated_at` - Timestamp

## Security Features

- **Password Hashing**: PBKDF2 with SHA-256 via Werkzeug
- **CSRF Protection**: Flask-WTF token validation
- **Session Security**: Secure cookie settings
- **Role Guards**: Decorator-based route protection
- **SQL Injection Prevention**: Parameterized queries

## API Endpoints

| Route | Method | Description |
|-------|--------|-------------|
| `/` | GET | Landing page |
| `/auth/login` | GET/POST | User login |
| `/auth/register` | GET/POST | User registration |
| `/auth/logout` | GET | Session logout |
| `/user/dashboard` | GET | User dashboard |
| `/user/new-request` | GET/POST | Create request |
| `/user/my-requests` | GET | List user requests |
| `/user/request/<id>` | GET | Request detail |
| `/admin/dashboard` | GET | Admin dashboard |
| `/admin/requests` | GET | All requests |
| `/admin/request/<id>` | GET | Request management |
| `/admin/request/<id>/update` | POST | Update status |

## Categories

- IT Support
- Facilities
- Academic
- Administrative
- Financial
- Other

## Scaling

The SQLite database is suitable for small to medium deployments. For larger scale:

1. Migrate to PostgreSQL by updating the connection string
2. Add connection pooling
3. Consider adding Redis for session management
4. Deploy with Gunicorn/uWSGI behind Nginx

## License

MIT License - Free for institutional and commercial use.
