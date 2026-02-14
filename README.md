# 🎯 FaceTrack Pro - Enterprise AI Attendance System

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-3.1-green.svg)](https://flask.palletsprojects.com/)
[![InsightFace](https://img.shields.io/badge/InsightFace-buffalo__l-orange.svg)](https://github.com/deepinsight/insightface)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-blue.svg)](https://www.mysql.com/)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.4-38bdf8.svg)](https://tailwindcss.com/)
[![Production](https://img.shields.io/badge/Production-Ready-success.svg)](DEPLOYMENT.md)

> Production-grade facial recognition attendance system powered by InsightFace ArcFace. Features real-time kiosk mode with mobile camera support, smooth animations, liveness detection, and enterprise-level security.

> **🎉 Version 2.5** - Remember Me functionality, premium UI/UX enhancements, professional login pages, enhanced security messaging, and improved session management!

---

## 📱 Latest Updates (v2.5)

### 🔐 Remember Me Functionality
- **Persistent Sessions**: "Remember Me" checkbox on both admin and employee login pages
- **Configurable Duration**: Sessions persist for admin-configurable timeout period (default: 30 minutes)
- **Enhanced UX**: Users can stay logged in across browser sessions
- **Security Maintained**: All existing security features (CSRF, session regeneration) preserved

### 🎨 Premium UI/UX Enhancements
- **Modern Card Designs**: Premium cards with gradients, animations, and hover effects
- **Professional Login Pages**: Enterprise-grade login interfaces with security badges
- **Enhanced Flash Messages**: Improved error/success message styling and positioning
- **Smooth Animations**: Scroll-reveal animations and micro-interactions throughout
- **Consistent Branding**: Unified color scheme and professional styling

### 🛡️ Security & Session Management
- **Professional Error Messages**: Replaced harsh "access denied" with user-friendly language
- **Session Timeout Configuration**: Database-driven session timeout settings
- **CSRF Validation**: Enhanced error handling for CSRF token validation failures
- **Access Control**: Improved middleware with professional error responses

### 📊 Employee Interface Improvements
- **Face Request History**: Complete history table with image viewing modals
- **Settings Page**: Password change functionality with validation and strength indicators
- **Profile Management**: Enhanced employee profile with photo upload capabilities
- **Navigation**: Improved navigation with active state indicators and smooth transitions

### ⚡ Performance & Code Quality
- **Optimized Queries**: Improved database query performance
- **Clean Codebase**: Consistent error handling and code organization
- **Responsive Design**: Enhanced mobile and tablet compatibility
- **Animation Performance**: Hardware-accelerated animations for smooth UX

---

## � Screenshots

### Dashboard
![Dashboard View](docs/screenshots/dashboard.png)
*Admin dashboard with real-time attendance statistics and analytics*

### Kiosk Mode - Face Recognition
![Kiosk Mode](docs/screenshots/kiosk.png)
*Real-time face detection with guidance overlay, distance meter, and confidence scoring*

### Liveness Detection
![Liveness Detection](docs/screenshots/liveness.png)
*Real-time liveness verification with blink and movement prompts*

### Employee Management
![Employee List](docs/screenshots/employees.png)
*Complete employee directory with face enrollment status and management tools*

### Attendance Records
![Attendance View](docs/screenshots/attendance.png)
*Comprehensive attendance tracking with filters and export capabilities*

### Reports & Analytics
![Reports](docs/screenshots/reports.png)
*Department-wise analytics with monthly trends and custom date ranges*

### Settings Panel
![Settings](docs/screenshots/settings.png)
*System configuration for thresholds, working hours, and kiosk preferences*

> **Note**: Screenshots showcase the professional UI with consistent indigo theme, real-time feedback systems, and enterprise-grade design.

---

## 📋 Table of Contents

- [Screenshots](#-screenshots)
- [Features](#-features)
- [Technology Stack](#-technology-stack)
- [Installation](#-installation)
- [Usage](#-usage)
- [Project Structure](#-project-structure)
- [Database Schema](#-database-schema)
- [Configuration](#-configuration)
- [Troubleshooting](#-troubleshooting)
- [Testing](#-testing)
- [Roadmap](#-roadmap)

---

## ✨ Features

### 🔐 Authentication & Security
- **Face + Password Login**: Multi-factor authentication with live facial verification
- **Role-Based Access Control (RBAC)**: Admin, HR, and Employee roles
- **Remember Me Functionality**: Persistent sessions with configurable timeout
- **Centralized Security Middleware**: Unified access control across all blueprints
- **Custom Error Pages**: Professional 403/404 pages with consistent branding
- **Session Management**: Secure Flask sessions with encrypted cookies and permanent session support
- **Password Encryption**: Werkzeug PBKDF2 SHA-256 hashing
- **Anti-CSRF Protection**: Token-based request validation

### 👥 Employee Management
- **Complete CRUD**: Add, view, edit, and archive employees
- **Department Organization**: IT, HR, Sales, Marketing, Finance, Admin
- **Status Tracking**: Active, Inactive, On Leave
- **Profile Photos**: Upload and manage employee images
- **Face Enrollment**: Single high-quality capture with 512-dim embedding storage
- **Face Request Management**: Admin approval system for enrollment requests
- **Request Workflow**: Pending → Approved/Rejected with admin oversight
- **Employee Self-Service**: Profile management, face enrollment requests, password changes
- **Password Management**: Secure password change functionality with validation

### 📋 Leave Management System
- **Leave Types**: Annual, Sick, Personal, Maternity, Paternity, Emergency, Casual
- **Leave Application**: Employee self-service leave requests
- **Admin Approval**: HR/Admin approval workflow with status tracking
- **Leave Balance Tracking**: Automatic balance management per employee per year
- **Leave Calendar**: Integration with attendance system
- **Leave History**: Complete audit trail of leave applications

### 🏖️ Holiday Management
- **Company Holidays**: Configurable company holidays
- **Weekend Tracking**: Automatic weekend detection
- **Calendar Integration**: Attendance calculations exclude holidays/weekends
- **Holiday Types**: Distinguish between weekends and company holidays

### 🔍 Audit & Security
- **Audit Logging**: Complete system audit trail
- **Login Tracking**: Authentication attempt logging with IP addresses
- **Recognition Logging**: Face recognition event tracking with confidence scores
- **Password Reset**: Secure token-based password recovery
- **Session Security**: Encrypted sessions with configurable timeouts
- **Centralized Middleware**: Unified security checks across all blueprints
- **Face Request Management**: Admin approval system for enrollment requests
- **Request Workflow**: Pending → Approved/Rejected with admin oversight

### 🎭 Advanced Face Recognition
- **AI Engine**: InsightFace buffalo_l (ArcFace ResNet-100)
- **Accuracy**: 98%+ in controlled lighting
- **Speed**: <150ms per recognition
- **Embeddings**: 512-dimensional float32 vectors stored as MySQL BLOB
- **Similarity Metric**: Cosine distance (threshold: 0.4)
- **Multi-Face Support**: Detects up to 3 faces per frame
- **Live Detection**: RetinaFace (InsightFace built-in detector)

### �️ Liveness Detection
- **Anti-Spoofing**: Prevents photo/video attacks with real-time verification
- **Blink Detection**: Eye aspect ratio analysis for natural blink verification
- **Head Movement Tracking**: Directional movement detection (left/right)
- **Adaptive Texture Analysis**: Lighting-aware skin texture validation
- **Time-Window Voting**: Multi-frame analysis for robust detection
- **Performance Optimized**: Fast processing with caching and frame skipping

### �🖥️ Kiosk Mode (Production-Ready)
- **Touchless Operation**: Fully automated face-based attendance
- **Single-Row Per Day**: One record per employee per day (optimized)
- **Auto Check-in**: First recognition marks check-in
- **Auto Check-out**: Updates check-out on subsequent recognition
- **Real-time Feedback**: Visual + audio confirmation with smooth animations
- **Mobile Camera Support**: Front/back camera switching on mobile devices
- **Smooth UI**: Bouncing modals, fade transitions, hover effects
- **Flexible Settings**: Skip PIN for view-only access
- **Recent Logs**: Live display of last 10 attendance entries
- **Snapshot Storage**: Captures and stores attendance photos
- **Fullscreen Mode**: Dedicated kiosk interface
- **Responsive Design**: Works on desktop, tablet, and mobile

### 📊 Attendance System
- **Single-Row Architecture**: One record per employee/day
- **Working Hours**: Auto-calculates time between check-in/out
- **Status Management**: Present, Absent, Late, Half-Day
- **Date Filters**: Daily, weekly, monthly views
- **Department Filters**: Filter by department or all
- **Search**: Quick search by name or employee ID

### 📈 Reports & Analytics
- **Daily Reports**: Real-time attendance summary
- **Monthly Analytics**: Comprehensive statistics
- **Custom Date Ranges**: Flexible reporting
- **Department Reports**: Breakdown by departments
- **CSV Export**: Download for offline analysis

### ⚙️ Additional Features
- **Timeline View**: Chronological attendance feed
- **Settings Panel**: Configure thresholds, working hours
- **Department Management**: CRUD for departments
- **Profile Management**: Update personal information and password
- **Face Request Approval**: Admin dashboard for managing enrollment requests
- **Custom Error Handling**: Professional error pages with navigation
- **Charts & Analytics**: Visual data representation and insights
- **Email Notifications**: Automated email alerts for various events
- **Audit Trail**: Complete system activity logging
- **Password Recovery**: Secure password reset functionality
- **Holiday Calendar**: Company holiday and weekend management
- **Leave Management**: Complete leave application and approval system
- **Contact Form**: Database-backed contact form with message storage and admin management
- **Premium UI/UX**: Modern card designs, smooth animations, and professional styling
- **Remember Me**: Persistent login sessions with configurable timeout

---

## 🛠️ Technology Stack

### Backend
- **Framework**: Flask 3.1.3
- **Language**: Python 3.11+
- **Database**: MySQL 8.0 (Only database used)
- **ORM**: Flask-MySQLdb
- **Session**: Flask-Session
- **Security**: Werkzeug, Flask-CORS

### AI/ML Stack
- **Face Recognition**: InsightFace 0.7.3
- **Model**: buffalo_l (ArcFace ResNet-100)
- **Detection**: RetinaFace (built-in)
- **Runtime**: ONNX Runtime 1.19+
- **Image Processing**: OpenCV 4.10+
- **Embeddings**: NumPy 1.26+ (512-dim vectors)
- **Similarity**: Cosine Distance (scipy)

### Frontend
- **Template Engine**: Jinja2
- **CSS Framework**: TailwindCSS 3.4
- **JavaScript**: Vanilla ES6+
- **Icons**: Feather Icons
- **Webcam**: MediaDevices getUserMedia API

---

## 📥 Installation

### Prerequisites
- Python 3.11 or higher
- MySQL 8.0 Server
- Webcam (for enrollment and kiosk)
- Windows/Linux/macOS
- 8GB RAM recommended

### Step 1: Clone Repository

```bash
git clone https://github.com/Mallikarjun15568/FaceTrack.git
cd FaceTrack
```

### Step 2: Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Database

1. Create database:
```sql
CREATE DATABASE facetrack_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

2. Update `config.py`:
```python
DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASSWORD = 'your_password'
DB_NAME = 'facetrack_db'
```

3. Initialize tables:
```bash
python db_utils.py
```

### Step 5: Download InsightFace Model

```bash
# Model auto-downloads on first run
# Or manually download buffalo_l to models/ directory
```

### Step 6: Run Application

```bash
python app.py
```

Application starts at: **http://127.0.0.1:5000**

---

## 🚀 Usage

### 1. First Time Setup

#### Admin Login
Default credentials (change immediately):
- Email: `admin@facetrack.com`
- Password: `admin123`

### 2. Add Employees

1. Navigate to **Employees** → **Add Employee**
2. Fill in details:
   - Name, Employee ID, Email
   - Department, Role
   - Status (Active/Inactive)
3. Upload profile photo (optional)
4. Click **Save**

### 3. Enroll Faces

1. Go to **Enroll** page
2. Select employee from dropdown
3. Allow webcam access
4. Position face in frame (good lighting)
5. Click **Capture** when face is centered
6. System generates 512-dim embedding
7. Confirms enrollment success

**Best Practices:**
- ✅ Front-facing, neutral expression
- ✅ Good lighting (avoid shadows)
- ✅ Remove glasses if possible
- ✅ Clear background

### 4. Mark Attendance (Kiosk Mode)

1. Open: http://127.0.0.1:5000/kiosk
2. System auto-detects face
3. Recognizes employee
4. Marks check-in/check-out automatically
5. Displays confirmation with photo

**Kiosk Behavior:**
- **First recognition of day**: Check-in time recorded
- **Subsequent recognition**: Check-out time updated
- **Already marked**: Shows existing record
- **Unknown face**: Displays "Not Recognized" alert

### 5. View Attendance

1. Navigate to **Attendance** page
2. Filter by:
   - Date range (start/end)
   - Department
   - Employee
3. View check-in/out times
4. See total working hours
5. View attendance snapshots

### 6. Generate Reports

1. Go to **Reports** page
2. Select:
   - Report type (Daily/Monthly)
   - Date range
   - Department (optional)
3. Click **Generate**
4. Export to CSV if needed

---

## 📁 Project Structure

```
FaceTrack/
│
├── app.py                      # Main Flask application
├── config.py                   # Configuration settings
├── db_utils.py                 # Database initialization & helpers
├── requirements.txt            # Python dependencies
├── package.json                # Node.js dependencies (for TailwindCSS)
├── postcss.config.js           # PostCSS configuration
├── tailwind.config.js          # TailwindCSS configuration
├── README.md                   # Documentation
├── DEPLOYMENT.md               # Deployment guide
├── docker-compose.yml          # Docker Compose configuration
├── Dockerfile                  # Docker container setup
│
├── blueprints/                 # Feature modules
│   ├── auth/                   # Authentication (login/logout/signup)
│   │   ├── __init__.py
│   │   ├── routes.py           # Login, logout, password reset
│   │   └── __pycache__/
│   ├── admin/                  # Admin panel (/admin)
│   │   ├── __init__.py         # Admin middleware & sub-blueprints
│   │   ├── dashboard/          # Admin dashboard (/admin/dashboard)
│   │   │   └── ...
│   │   ├── employees/          # Employee management (/admin/employees)
│   │   ├── reports/            # Reports & analytics (/admin/reports)
│   │   ├── settings/           # System settings (/admin/settings)
│   │   └── __pycache__/
│   ├── attendance/             # Attendance records (/attendance)
│   │   ├── __init__.py
│   │   ├── attendance_utils.py # Attendance helper functions
│   │   ├── routes.py
│   │   └── __pycache__/
│   ├── enroll/                 # Face enrollment (/enroll)
│   ├── kiosk/                  # Kiosk mode (/kiosk)
│   ├── leave/                  # Leave management (/leave)
│   ├── charts/                 # Charts & analytics (/charts)
│   └── employee/               # Employee panel (/employee)
│
├── utils/                      # Helper utilities
│   ├── __init__.py
│   ├── face_encoder.py         # Face embedding generation + recognition
│   ├── liveness_detector.py    # Liveness detection module
│   ├── db.py                   # Database connection pool
│   ├── helpers.py              # Utility functions
│   ├── email_service.py        # Email notifications
│   ├── logger.py               # Logging utilities
│   ├── extensions.py           # Flask extensions
│   ├── input_validation.py     # Input validation utilities
│   ├── validators.py           # Data validators
│   ├── csrf_exemptions.py      # CSRF exemption handlers
│   ├── thread_safe_encoder.py  # Thread-safe face encoding
│   └── __pycache__/
│
├── models/                     # Data models
│   └── users.py                # User model
│
├── templates/                  # Jinja2 HTML templates
│   ├── base.html               # Base layout with sidebar
│   ├── base_kiosk.html         # Kiosk-specific base layout
│   ├── home.html               # Public homepage
│   ├── login.html              # Login page
│   ├── signup.html             # Signup page
│   ├── forgot_password.html    # Password reset request
│   ├── reset_password.html     # Password reset form
│   ├── 403.html                # Custom forbidden page
│   ├── 404.html                # Custom not found page
│   ├── 500.html                # Custom error page
│   ├── contact.html            # Contact form
│   ├── help.html               # Help page
│   ├── about.html              # About page
│   ├── admin/                  # Admin templates
│   │   ├── dashboard_admin.html
│   │   ├── employees.html
│   │   ├── employee_edit.html
│   │   ├── employee_view.html
│   │   ├── reports.html
│   │   ├── settings.html
│   │   ├── user_management.html
│   │   ├── backups/
│   │   └── face_requests.html
│   ├── employee/               # Employee panel templates
│   │   ├── dashboard.html
│   │   ├── attendance.html
│   │   ├── leave.html
│   │   ├── profile.html
│   │   └── face_request.html
│   ├── leave/                  # Leave management templates
│   │   ├── apply_leave.html
│   │   └── leave_list.html
│   ├── attendance.html         # Admin attendance view
│   ├── kiosk.html              # Kiosk interface
│   ├── kiosk_exit.html         # Kiosk exit confirmation
│   ├── enroll_face_list.html   # Enrollment management
│   ├── enrolled_list.html      # Enrolled faces list
│   ├── employees_face_enroll.html
│   ├── employees_face_enroll_update.html
│   ├── employees_add_modal.html
│   └── [other templates]
│
├── static/                     # Static assets
│   ├── css/                    # Compiled CSS
│   ├── js/                     # JavaScript files
│   ├── faces/                  # Enrolled face images
│   ├── snapshots/              # Attendance photos
│   ├── pending_faces/          # Pending face requests
│   ├── images/                 # UI assets
│   ├── uploads/                # Uploaded files
│   └── temp/                   # Temporary files
│
├── scripts/                    # Database scripts & utilities
│   ├── database_setup.sql      # Database setup script
│   ├── add_missing_columns.py  # Column addition script
│   ├── add_missing_columns.sql
│   ├── add_report_history.sql
│   ├── check_users.py          # User verification script
│   ├── checkout_reminder.py    # Checkout reminder script
│   ├── create_admin.py         # Admin creation script
│   ├── mark_absent.py          # Mark absent script
│   ├── test_email.py           # Email testing script
│   └── __pycache__/
│
├── logs/                       # Application logs
│   ├── attendance.csv
│   └── logout.csv
│
├── docs/                       # Documentation
│   ├── 00_TITLE_PAGE.md
│   ├── 01_CERTIFICATE.md
│   ├── CHAPTER_01.md
│   ├── CHAPTER_02.md
│   ├── CHAPTER_03.md
│   ├── CHAPTER_04.md
│   ├── CHAPTER_05.md
│   ├── CHAPTER_06_BIBLIOGRAPHY.md
│   ├── ANNEXURE_1.md
│   ├── ANNEXURE_2.md
│   ├── ANNEXURE_3.md
│   ├── MOBILE_ACCESS_SETUP.md
│   ├── README.md
│   ├── SCREENSHOT_CHECKLIST.md
│   ├── SCREENSHOT_GUIDE.md
│   └── diagrams/
│
├── tests/                      # Test suites
│   ├── test_camera.py          # Camera testing
│   ├── test_live_recognition.py # Live recognition testing
│   ├── integration/            # Integration tests
│   ├── performance/            # Performance tests
│   └── unit/                   # Unit tests
│
└── __pycache__/                # Python bytecode cache
```

---
│   ├── css/                    # Compiled CSS
│   ├── js/                     # JavaScript files
│   ├── faces/                  # Enrolled face images
│   ├── snapshots/              # Attendance photos
│   ├── pending_faces/          # Pending face requests
│   └── images/                 # UI assets
│
├── scripts/                    # Database scripts & utilities
│   ├── create_*.sql            # Table creation scripts
│   ├── add_*.sql               # Column addition scripts
│   ├── migrate_*.sql           # Migration scripts
│   └── *.py                    # Utility scripts
│
├── logs/                       # Application logs
│   ├── attendance.csv
│   └── logout.csv
│
└── instance/                   # Instance files
    └── facetrack.db            # SQLite database (dev)
```

---

## 🗄️ Database Schema

### Users Table (Authentication)

```sql
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role ENUM('admin', 'hr', 'employee') DEFAULT 'employee',
    email VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### Employees Table (Master Data)

```sql
CREATE TABLE employees (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNIQUE,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(150) UNIQUE,
    phone VARCHAR(20),
    gender VARCHAR(20),
    job_title VARCHAR(100),
    department_id INT,
    join_date DATE,
    status VARCHAR(20) DEFAULT 'Active',
    photo VARCHAR(255),                    -- Consolidated photo column (admin + employee photos)
    face_embedding LONGBLOB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE SET NULL,
    INDEX idx_email (email),
    INDEX idx_department (department_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

**Note**: The `photo` column consolidates both admin-uploaded photos and employee self-uploaded profile photos into a single, unified column. This simplifies the schema and eliminates confusion between `photo_path` and `profile_photo` columns that existed in earlier versions.

### Attendance Table (Single-Row Architecture)

```sql
CREATE TABLE attendance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id INT NOT NULL,
    date DATE NOT NULL,                    -- Legacy column (not used in queries)
    status ENUM('present','late','absent','check-in','check-out','already') DEFAULT 'present',
    captured_photo_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    timestamp DATETIME,                     -- Last action timestamp
    check_in_time DATETIME,                 -- Primary check-in datetime (used in all queries)
    check_out_time DATETIME,                -- Check-out datetime
    working_hours FLOAT,                    -- Calculated hours (check_out - check_in)
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
    INDEX idx_employee_date (employee_id, check_in_time),
    INDEX idx_date (date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- IMPORTANT: All queries use DATE(check_in_time) as primary date field
-- Legacy 'date' column exists for backward compatibility but is NOT used
```

### Face Encodings Table

```sql
CREATE TABLE face_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    emp_id INT NOT NULL,
    embedding LONGBLOB NOT NULL,     -- 512-dim float32 array (2048 bytes)
    image_path VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (emp_id) REFERENCES employees(id) ON DELETE CASCADE,
    INDEX idx_emp_id (emp_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### Settings Table (System Configuration)

```sql
CREATE TABLE IF NOT EXISTS settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    setting_key VARCHAR(100) NOT NULL UNIQUE,
    setting_value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_key (setting_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### Leaves Table (Leave Management)

```sql
CREATE TABLE IF NOT EXISTS leaves (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id INT NOT NULL,
    leave_type ENUM('annual', 'sick', 'personal', 'maternity', 'paternity', 'emergency', 'casual_leave') NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    reason TEXT,
    status ENUM('pending', 'approved', 'rejected', 'cancelled') DEFAULT 'pending',
    approved_by INT NULL,
    approved_at TIMESTAMP NULL,
    applied_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
    FOREIGN KEY (approved_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_employee_id (employee_id),
    INDEX idx_status (status),
    INDEX idx_dates (start_date, end_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### Holidays Table (Company Holidays & Weekends)

```sql
CREATE TABLE IF NOT EXISTS holidays (
    id INT AUTO_INCREMENT PRIMARY KEY,
    holiday_date DATE NOT NULL UNIQUE,
    holiday_name VARCHAR(255) NOT NULL,
    holiday_type ENUM('weekend', 'company_holiday') DEFAULT 'company_holiday',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_date (holiday_date),
    INDEX idx_type (holiday_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### Pending Face Requests Table (Face Enrollment Approval)

```sql
CREATE TABLE IF NOT EXISTS pending_face_requests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    emp_id INT NOT NULL,
    request_type ENUM('enroll', 'update') NOT NULL,
    image_path VARCHAR(255) NOT NULL,
    status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_at TIMESTAMP NULL,
    approved_by INT NULL,
    rejection_reason TEXT NULL,
    FOREIGN KEY (emp_id) REFERENCES employees(id) ON DELETE CASCADE,
    FOREIGN KEY (approved_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_status (status),
    INDEX idx_emp_id (emp_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### Audit Logs Table (System Audit Trail)

```sql
CREATE TABLE IF NOT EXISTS audit_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    action VARCHAR(100) NOT NULL,
    module VARCHAR(100) NULL,
    details TEXT NULL,
    ip_address VARCHAR(45) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user (user_id),
    INDEX idx_action (action),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### Password Reset Tokens Table (Password Recovery)

```sql
CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    token VARCHAR(255) NOT NULL UNIQUE,
    expires_at DATETIME NOT NULL,
    used TINYINT(1) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_token (token),
    INDEX idx_expires (expires_at),
    INDEX idx_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### Leave Balance Table (Leave Entitlements)

```sql
CREATE TABLE IF NOT EXISTS leave_balance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id INT NOT NULL,
    casual_leave INT DEFAULT 0,
    sick_leave INT DEFAULT 0,
    vacation_leave INT DEFAULT 0,
    emergency_leave INT DEFAULT 0,
    year INT NOT NULL,
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
    UNIQUE KEY unique_employee_year (employee_id, year)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### Login Logs Table (Authentication Audit)

```sql
CREATE TABLE IF NOT EXISTS login_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('success', 'failed') NOT NULL,
    ip_address VARCHAR(100),
    user_agent TEXT,
    INDEX idx_user (user_id),
    INDEX idx_timestamp (timestamp),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### Recognition Logs Table (Face Recognition Audit)

```sql
CREATE TABLE IF NOT EXISTS recognition_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id INT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    confidence FLOAT,
    action ENUM('enroll', 'recognize', 'unknown') DEFAULT 'unknown',
    image_path TEXT,
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE SET NULL,
    INDEX idx_employee (employee_id),
    INDEX idx_timestamp (timestamp),
    INDEX idx_action (action)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### Contact Messages Table (Contact Form Storage)

```sql
CREATE TABLE IF NOT EXISTS contact_messages (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('new', 'read', 'replied') DEFAULT 'new'
);
```

---

## ⚙️ Configuration

## ⚙️ Configuration

### Recognition Threshold

Edit `config.py`:

```python
RECOGNITION_THRESHOLD = 0.4  # Lower = stricter (0.3-0.5 recommended)
```

### Working Hours

```python
WORKING_HOURS = {
    'start': '09:00',
    'end': '18:00',
    'half_day_hours': 4.0
}
```

### Database Connection

```python
DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASSWORD = 'your_password'
DB_NAME = 'facetrack_db'
DB_POOL_SIZE = 10
```

---

## 🐛 Troubleshooting

### Camera Not Working

**Error**: `NotFoundError: Requested device not found`

**Solutions**:
1. Check browser permissions (Settings → Privacy → Camera)
2. Ensure no other app is using webcam
3. Try different browser (Chrome recommended)
4. Check camera drivers

### Face Not Recognized

**Problem**: Kiosk shows "Not Recognized"

**Solutions**:
1. Verify face enrollment (check `face_enrolled = TRUE`)
2. Improve lighting (avoid shadows)
3. Face camera directly
4. Clean camera lens
5. Lower `RECOGNITION_THRESHOLD` to 0.35

### Database Connection Error

**Error**: `OperationalError: (2003) Can't connect to MySQL server`

**Solutions**:
1. Start MySQL service: `net start MySQL80`
2. Check credentials in `config.py`
3. Verify database exists: `SHOW DATABASES;`
4. Check firewall settings

### InsightFace Model Not Loading

**Error**: `Model file not found`

**Solutions**:
1. Download model manually:
   ```bash
   python -c "import insightface; insightface.model_zoo.get_model('buffalo_l')"
   ```
2. Ensure `models/` directory exists
3. Check internet connection (first-time download)

---

## 🧪 Testing

### Manual Test Checklist

- [ ] Admin can login
- [ ] Add new employee
- [ ] Upload profile photo
- [ ] Enroll employee face
- [ ] Kiosk recognizes face
- [ ] Check-in recorded
- [ ] Check-out updates same record
- [ ] Reports generate correctly
- [ ] CSV export works
- [ ] Settings save properly

### Performance Benchmarks

| Operation | Time | Target |
|-----------|------|--------|
| Face Detection | 50-80ms | <100ms |
| Face Recognition | 100-150ms | <200ms |
| Embedding Generation | 80-120ms | <150ms |
| Database Query | 5-15ms | <50ms |
| Total Kiosk Cycle | 200-300ms | <500ms |

---

## 🔮 Roadmap

### Version 2.0 (Planned Q1 2026)

**Phase 1: Anti-Spoof Detection**
- [ ] Depth sensing (if hardware available)
- [ ] Challenge-response verification

**Phase 2: Advanced Features**
- [ ] Mobile app (React Native)
- [ ] Shift scheduling
- [ ] Geofencing for remote attendance
- [ ] Multi-camera support

**Phase 3: Analytics**
- [ ] Attendance prediction (ML)
- [ ] Behavioral analytics
- [ ] Department performance metrics
- [ ] Custom dashboards

**Phase 4: Integrations**
- [ ] Slack/Teams notifications
- [ ] Payroll integration
- [ ] HR management systems
- [ ] API for third-party apps

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Author

**Asapure Mallikarjun Siddharam**
- GitHub: [@Mallikarjun15568](https://github.com/Mallikarjun15568)
- Email: asapuremallikarjun23@gmail.com
- LinkedIn: [Mallikarjun Asapure](#)

---

## 🙏 Acknowledgments

- **InsightFace** - State-of-the-art face recognition models
- **Flask** - Lightweight and powerful web framework
- **TailwindCSS** - Utility-first CSS framework
- **MySQL** - Robust database management system
- **ONNX Runtime** - High-performance inference engine

---

## 📊 Project Stats

- **Lines of Code**: ~12,000+
- **Python Files**: 55+
- **HTML Templates**: 25+
- **JavaScript Files**: 20+
- **Database Tables**: 14
- **API Endpoints**: 50+
- **Blueprints**: 8
- **Recognition Accuracy**: 98%+
- **Avg Response Time**: <300ms

---

<div align="center">
  
**⭐ If you find this project useful, please give it a star! ⭐**

**Made with ❤️ using Flask, InsightFace & TailwindCSS**

</div>
