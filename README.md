# 🌈 TherapyTrack - Autism Therapy Management System

A comprehensive web-based therapy management system designed to help doctors track and monitor the developmental progress of children with autism spectrum disorder (ASD).

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)
![MongoDB](https://img.shields.io/badge/MongoDB-4.6+-brightgreen.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ Features

### 👨‍⚕️ For Doctors
- **Patient Management**: Register and manage child profiles with unique access codes
- **Therapy Session Logging**: Record daily therapy sessions with detailed evaluations across 8 developmental domains
- **Progress Tracking**: Monitor improvement trends with visual charts and analytics
- **Report Generation**: Generate comprehensive weekly and monthly progress reports
- **Parent Account Management**: Auto-create parent accounts with email notifications

### 👨‍👩‍👧 For Parents
- **Child Progress Monitoring**: View your child's therapy progress in real-time
- **Report Access**: Access weekly and monthly progress reports
- **Session History**: Review past therapy sessions and activities
- **Easy Onboarding**: Simple registration with child code provided by doctor

### 📊 8 Developmental Domains Tracked
1. **Communication Skills** - Verbal/non-verbal communication, language comprehension
2. **Emotional Development** - Emotion recognition, regulation, expression
3. **Social Skills** - Eye contact, turn-taking, peer interaction
4. **Behavior** - Compliance, tantrum management, self-stimulatory behaviors
5. **Cognitive Skills** - Problem-solving, memory, attention span
6. **Sensory Processing** - Sensory responses, integration, tolerance
7. **Daily Living Skills** - Self-care, eating, toileting, dressing
8. **Therapy Participation** - Engagement, instruction following, motivation

## 🛠️ Tech Stack

- **Backend**: Python 3.10+, FastAPI
- **Database**: MongoDB
- **Authentication**: JWT (JSON Web Tokens)
- **Frontend**: HTML5, CSS3, JavaScript
- **Charts**: Chart.js
- **Email**: SMTP (aiosmtplib)
- **Templating**: Jinja2

## 📁 Project Structure

```
autism_therapy_system/
├── .env.example              # Environment variables template
├── requirements.txt          # Python dependencies
├── README.md                 # This file
└── app/
    ├── main.py              # FastAPI application entry point
    ├── config.py            # Configuration settings
    ├── database.py          # MongoDB connection
    ├── models.py            # Pydantic data models
    ├── auth.py              # Authentication & JWT
    ├── email_service.py     # Email functionality
    ├── routes.py            # API endpoints
    ├── static/
    │   ├── css/
    │   │   └── styles.css   # Application styles
    │   └── js/
    │       └── app.js       # Frontend JavaScript
    └── templates/
        ├── index.html            # Landing page
        ├── login.html            # Login page
        ├── register.html         # Registration page
        ├── doctor_dashboard.html # Doctor dashboard
        ├── parent_dashboard.html # Parent dashboard
        ├── add_child.html        # Add child form
        ├── add_session.html      # Therapy session form
        ├── view_child.html       # Child details
        ├── weekly_report.html    # Weekly report
        └── monthly_report.html   # Monthly report
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- MongoDB (local or Atlas)
- SMTP email account (for sending emails)

### Installation

1. **Clone or navigate to the project directory**
   ```bash
   cd autism_therapy_system
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   # Copy the example file
   copy .env.example .env    # Windows
   cp .env.example .env      # macOS/Linux
   
   # Edit .env with your settings
   ```

5. **Start MongoDB**
   - Make sure MongoDB is running on `localhost:27017`
   - Or update `MONGODB_URL` in `.env` for MongoDB Atlas

6. **Run the application**
   ```bash
   python -m uvicorn app.main:app --reload
   ```

7. **Open in browser**
   ```
   http://localhost:8000
   ```

## ⚙️ Configuration

Create a `.env` file in the project root with the following variables:

```env
# MongoDB
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=autism_therapy_db

# JWT Authentication
SECRET_KEY=your-super-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# SMTP Email (Gmail example)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com

# App Settings
APP_NAME=Autism Therapy Management System
DEBUG=True
```

### Gmail App Password Setup
1. Enable 2-Factor Authentication on your Google account
2. Go to Google Account → Security → App Passwords
3. Generate a new app password for "Mail"
4. Use this password in `SMTP_PASSWORD`

## 📡 API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/login` | User login |
| POST | `/api/auth/register/doctor` | Register doctor |
| POST | `/api/auth/register/parent` | Register parent |

### Doctor Routes
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/doctor/create-child` | Create child profile |
| GET | `/api/doctor/children` | Get all assigned children |
| GET | `/api/doctor/dashboard-stats` | Get dashboard statistics |

### Therapy Routes
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/therapy/add-log` | Add therapy session |
| GET | `/api/therapy/logs/{child_id}` | Get session history |

### Report Routes
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/reports/weekly/{child_id}` | Weekly progress report |
| GET | `/api/reports/monthly/{child_id}` | Monthly progress report |

## 🎨 UI Features

- **Modern Design**: Beautiful gradients, glassmorphism effects, and smooth animations
- **Responsive Layout**: Works on desktop, tablet, and mobile devices
- **Interactive Charts**: Visual progress tracking with Chart.js
- **Dark/Light Themes**: Easy on the eyes color schemes
- **Accessibility**: Designed with accessibility in mind

## 📈 Rating System

Each developmental area is rated on a 3-point scale:
- 🟢 **Good** - Showing positive progress
- 🟡 **Average** - Maintaining current level
- 🔴 **No Improvement** - Needs more focus

## 🔐 Security Features

- JWT-based authentication
- Password hashing with bcrypt
- Role-based access control (Doctor/Parent)
- Secure session management
- CORS protection

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👥 Support

For support, please open an issue in the repository or contact the development team.

---

**Made with ❤️ for children with autism and the dedicated professionals who help them thrive.**
