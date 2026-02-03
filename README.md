<div align="center">

# 🎫 Smart Service Desk

### A Modern, Production-Ready Service Request Management System

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![SQLite](https://img.shields.io/badge/SQLite-Database-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

[Features](#-features) • [Installation](#-installation) • [Usage](#-usage) • [API](#-api-routes) • [Contributing](#-contributing)

---

</div>

## 📋 Overview

**Smart Service Desk** is a full-featured service request management system built with Flask. It provides a streamlined workflow for submitting, tracking, and resolving service requests with role-based access control, real-time status tracking, and a modern glassmorphism UI design.

Perfect for organizations that need:
- 📝 Internal ticketing systems
- 🏢 Facilities management
- 💻 IT helpdesk solutions
- 🎓 Academic support portals

---

## ✨ Features

<table>
<tr>
<td width="50%">

### 👤 User Features
- ✅ Submit service requests with priority levels
- ✅ Track request status in real-time
- ✅ View complete activity timeline
- ✅ Submit satisfaction ratings for resolved requests
- ✅ Secure authentication with password hashing

</td>
<td width="50%">

### 🔧 Admin Features
- ✅ Manage all service requests
- ✅ Update request status with audit logging
- ✅ Dynamic category management (CRUD)
- ✅ Priority level management
- ✅ View user feedback & satisfaction metrics
- ✅ Filter requests by status/category/priority

</td>
</tr>
</table>

### 🎨 Design Highlights

| Feature | Description |
|---------|-------------|
| 🌈 **Modern UI** | Glassmorphism design with smooth animations |
| 📱 **Responsive** | Mobile-first design, works on all devices |
| 🎯 **Priority Badges** | Color-coded (Low/Medium/High/Critical) |
| ⭐ **Star Rating** | Interactive 5-star feedback system |
| 📊 **Dashboard** | Real-time statistics and quick actions |

---

## 🚀 Installation

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)

### Quick Start

```bash
# Clone the repository
git clone https://github.com/Dhanshree-gamedev/smart-service-desk.git
cd smart-service-desk

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

The application will be available at **http://127.0.0.1:5000**

### Default Credentials

| Role | Email | Password |
|------|-------|----------|
| Admin | `admin@servicedesk.com` | `admin123` |

> ⚠️ **Important**: Change default credentials before deploying to production!

---

## 💻 Usage

### Request Lifecycle

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  📝 SUBMITTED │ ──► │  🔄 IN PROGRESS │ ──► │  ✅ RESOLVED  │
└──────────────┘     └──────────────┘     └──────────────┘
     User                Admin                 Admin
   submits             picks up              resolves
   request              request               request
```

### Priority Levels

| Priority | Badge | Use Case |
|----------|-------|----------|
| 🟢 **Low** | Gray | Non-urgent requests |
| 🔵 **Medium** | Blue | Standard requests (default) |
| 🟠 **High** | Orange | Urgent issues |
| 🔴 **Critical** | Red (pulsing) | Emergency situations |

---

## 📁 Project Structure

```
smart-service-desk/
├── 📄 app.py                 # Application entry point
├── 📄 config.py              # Configuration settings
├── 📄 database.py            # Database initialization & migrations
├── 📄 requirements.txt       # Python dependencies
│
├── 📁 models/                # Data models
│   ├── user.py               # User model with authentication
│   ├── request.py            # Service request model
│   ├── category.py           # Dynamic category model
│   └── feedback.py           # User feedback model
│
├── 📁 routes/                # Route handlers
│   ├── auth.py               # Login/Register/Logout
│   ├── user.py               # User dashboard & requests
│   └── admin.py              # Admin management
│
├── 📁 templates/             # Jinja2 templates
│   ├── base.html             # Base layout
│   ├── 📁 auth/              # Authentication pages
│   ├── 📁 user/              # User interface
│   ├── 📁 admin/             # Admin interface
│   └── 📁 errors/            # Error pages
│
└── 📁 static/                # Static assets
    ├── 📁 css/               # Stylesheets
    └── 📁 js/                # JavaScript
```

---

## 🛣️ API Routes

### Authentication
| Method | Route | Description |
|--------|-------|-------------|
| GET/POST | `/auth/login` | User login |
| GET/POST | `/auth/register` | User registration |
| GET | `/auth/logout` | User logout |

### User Routes
| Method | Route | Description |
|--------|-------|-------------|
| GET | `/user/dashboard` | User dashboard |
| GET/POST | `/user/new-request` | Create new request |
| GET | `/user/my-requests` | View all user requests |
| GET | `/user/request/<id>` | Request details |
| POST | `/user/request/<id>/feedback` | Submit feedback |

### Admin Routes
| Method | Route | Description |
|--------|-------|-------------|
| GET | `/admin/dashboard` | Admin dashboard |
| GET | `/admin/requests` | All requests (with filters) |
| GET | `/admin/request/<id>` | Request details |
| POST | `/admin/request/<id>/update` | Update status |
| POST | `/admin/request/<id>/priority` | Update priority |
| GET/POST | `/admin/categories` | Manage categories |
| GET | `/admin/feedback` | View all feedback |

---

## 🔒 Security Features

- ✅ Password hashing with Werkzeug
- ✅ CSRF protection on all forms
- ✅ Session management with secure cookies
- ✅ Role-based access control (RBAC)
- ✅ Input validation and sanitization
- ✅ SQL injection prevention (parameterized queries)

---

## 🛠️ Tech Stack

<div align="center">

| Category | Technology |
|----------|------------|
| **Backend** | Flask 3.0, Python 3.9+ |
| **Database** | SQLite with migrations |
| **Auth** | Flask-Login, Werkzeug |
| **Security** | Flask-WTF (CSRF) |
| **Frontend** | HTML5, CSS3, JavaScript |
| **Design** | Custom CSS with Glassmorphism |

</div>

---

## 📈 Future Enhancements

- [ ] Email notifications for status updates
- [ ] File attachments for requests
- [ ] Request assignment to specific admins
- [ ] SLA tracking and escalation
- [ ] Export reports (PDF/CSV)
- [ ] Dark mode toggle
- [ ] API authentication (JWT)
- [ ] Docker containerization

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">

### ⭐ Star this repository if you found it helpful!

Made with ❤️ by [Dhanshree](https://github.com/Dhanshree-gamedev)

</div>
