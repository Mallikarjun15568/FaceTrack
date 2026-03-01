<div align="center">

# 🎯 FaceTrack Pro

### Enterprise AI-Powered Attendance Management System

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?style=for-the-badge&logo=mysql&logoColor=white)](https://www.mysql.com/)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.4-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](LICENSE)

**Production-ready facial recognition attendance system powered by InsightFace ArcFace with modern UI and advanced security features**

[Features](#-key-features) • [Installation](#-quick-start) • [Documentation](#-documentation) • [Demo](#-demo)

---

### 🌟 Latest Version: 2.6

✨ Modern Kiosk UI • 🔐 Enhanced Security • 🎨 Professional Design • 📱 Mobile-Optimized

</div>

---

## 🎥 Demo

<div align="center">

### Modern Kiosk Interface
Real-time face recognition with professional UI design and smooth animations

### Dashboard & Analytics
Comprehensive attendance tracking with real-time insights and visual reports

</div>

---

## 🚀 Key Features

<table>
<tr>
<td width="50%">

### 🎭 AI-Powered Recognition
- **InsightFace ArcFace** ResNet-100
- **98%+ Accuracy** in controlled environments
- **<150ms** recognition speed
- **512-dim embeddings** with cosine similarity
- **Anti-spoofing** liveness detection
- **Multi-face** detection support

</td>
<td width="50%">

### 🖥️ Modern Kiosk Mode
- **Touchless operation** with auto-detection
- **Mobile-optimized** with camera switching
- **Real-time feedback** visual + audio
- **Professional UI** with smooth animations
- **Snapshot storage** for audit trails
- **Fullscreen mode** for dedicated terminals

</td>
</tr>
<tr>
<td>

### 👥 Employee Management
- Complete CRUD operations
- Department organization
- Face enrollment system
- Profile photo management
- Self-service portal
- Request approval workflow

</td>
<td>

### 📊 Advanced Analytics
- Real-time attendance tracking
- Department-wise reports
- Custom date ranges
- CSV export capabilities
- Monthly trends analysis
- Visual charts & graphs

</td>
</tr>
<tr>
<td>

### 🔐 Enterprise Security
- Multi-factor authentication
- Role-based access control (RBAC)
- Session management with "Remember Me"
- CSRF protection
- Password encryption (PBKDF2 SHA-256)
- Complete audit logging

</td>
<td>

### 🏖️ Leave & Holiday Management
- Leave application system
- Admin approval workflow
- Balance tracking
- Holiday calendar integration
- Multiple leave types
- Comprehensive history

</td>
</tr>
</table>

---

## 🛠️ Technology Stack

### Backend
- **Framework**: Flask 3.1.3
- **Language**: Python 3.11+
- **Database**: MySQL 8.0
- **Security**: Werkzeug, Flask-CSRF

### AI/ML
- **Face Recognition**: InsightFace 0.7.3
- **Model**: buffalo_l (ArcFace ResNet-100)
- **Detection**: RetinaFace
- **Runtime**: ONNX Runtime 1.19+
- **Image Processing**: OpenCV 4.10+

### Frontend
- **Template Engine**: Jinja2
- **CSS Framework**: TailwindCSS 3.4
- **JavaScript**: Vanilla ES6+
- **Icons**: Font Awesome 6.5

---

## ⚡ Quick Start

### Prerequisites
```bash
✓ Python 3.11+
✓ MySQL 8.0
✓ Webcam (for enrollment and kiosk)
✓ 8GB RAM recommended
```

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/Mallikarjun15568/FaceTrack.git
cd FaceTrack
```

2. **Create virtual environment**
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure database**
```bash
# Create database
mysql -u root -p
CREATE DATABASE facetrack_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EXIT;
```

5. **Update configuration**
```python
# config.py
DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASSWORD = 'your_password'
DB_NAME = 'facetrack_db'
```

6. **Initialize database**
```bash
python db_utils.py
```

7. **Run the application**
```bash
python app.py
```

8. **Access the application**
```
🌐 Application: http://127.0.0.1:5000
👤 Default Admin: admin@facetrack.com / admin123
```

---

## 📖 Usage Guide

### 1. Admin Login
- Navigate to `http://127.0.0.1:5000`
- Login with default credentials (change immediately!)
- Access admin dashboard

### 2. Add Employees
1. Go to **Employees** → **Add Employee**
2. Fill in employee details (name, ID, email, department)
3. Upload profile photo (optional)
4. Save employee record

### 3. Enroll Faces
1. Navigate to **Enroll** page
2. Select employee from dropdown
3. Position face in camera view
4. Capture photo when prompted
5. System generates 512-dim embedding

**Best Practices:**
- ✅ Good lighting (avoid shadows)
- ✅ Front-facing, neutral expression  
- ✅ Remove glasses if possible
- ✅ Clear background

### 4. Mark Attendance (Kiosk)
1. Open `http://127.0.0.1:5000/kiosk`
2. System auto-detects and recognizes faces
3. First recognition = Check-in
4. Subsequent recognition = Check-out
5. View real-time confirmation

### 5. View & Export Reports
1. Go to **Reports** page
2. Select date range and filters
3. Generate attendance reports
4. Export to CSV for analysis

---

## 📁 Project Structure

```
FaceTrack/
├── app.py                     # Main Flask application
├── config.py                  # Configuration settings
├── db_utils.py                # Database utilities
├── requirements.txt           # Python dependencies
├── package.json               # Node.js dependencies
├── tailwind.config.js         # TailwindCSS config
│
├── blueprints/                # Flask blueprints
│   ├── admin/                 # Admin dashboard
│   ├── attendance/            # Attendance management
│   ├── auth/                  # Authentication
│   ├── employee/              # Employee portal
│   ├── enroll/                # Face enrollment
│   ├── kiosk/                 # Kiosk mode
│   └── leave/                 # Leave management
│
├── models/                    # Database models
│   └── users.py               # User model
│
├── static/                    # Static assets
│   ├── css/                   # Compiled CSS
│   ├── js/                    # JavaScript files
│   ├── images/                # Images & icons
│   ├── faces/                 # Face embeddings
│   └── snapshots/             # Attendance photos
│
├── templates/                 # Jinja2 templates
│   ├── base.html              # Base layout
│   ├── home.html              # Landing page
│   ├── kiosk.html             # Kiosk interface
│   ├── admin/                 # Admin templates
│   └── employee/              # Employee templates
│
├── utils/                     # Utility modules
│   ├── face_encoder.py        # Face recognition
│   ├── liveness_detector.py   # Liveness detection
│   ├── email_service.py       # Email notifications
│   └── validators.py          # Input validation
│
├── logs/                      # Application logs
├── scripts/                   # Utility scripts
└── docs/                      # Documentation
```

---

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the project root:

```env
# Database
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=facetrack_db

# Flask
SECRET_KEY=your-secret-key-here
FLASK_ENV=production

# Email (Optional)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
```

### System Settings
- **Recognition Threshold**: 0.4 (adjustable in admin settings)
- **Session Timeout**: 30 minutes (configurable)
- **Working Hours**: 8:00 AM - 6:00 PM (customizable)
- **Late Threshold**: 15 minutes after start time

---

## 🔍 Troubleshooting

### Common Issues

**Issue**: Camera not detected
```bash
✓ Check camera permissions in browser
✓ Try different browser (Chrome recommended)
✓ Restart application
```

**Issue**: Face not recognized
```bash
✓ Ensure good lighting
✓ Check if face is enrolled
✓ Verify recognition threshold in settings
✓ Re-enroll face if needed
```

**Issue**: Database connection error
```bash
✓ Verify MySQL is running
✓ Check credentials in config.py
✓ Ensure database exists
✓ Check firewall settings
```

**Issue**: InsightFace model not loading
```bash
✓ Download buffalo_l model manually
✓ Place in ~/.insightface/models/
✓ Restart application
```

---

## 🧪 Testing

### Run Tests
```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_camera.py

# Run with coverage
pytest --cov=app tests/
```

### Test Coverage
- Unit tests for face recognition
- Integration tests for API endpoints
- Performance tests for recognition speed
- Security tests for authentication

---

## 📚 Documentation

- 📖 [Full Documentation](docs/README.md)
- 🚀 [Deployment Guide](DEPLOYMENT.md)
- 📱 [Mobile Setup](docs/MOBILE_ACCESS_SETUP.md)
- ⚙️ [Scheduler Guide](docs/SCHEDULER_PRODUCTION_GUIDE.md)

---

## 🎯 Roadmap

### Version 2.7 (Coming Soon)
- [ ] Multi-language support
- [ ] Dark mode toggle
- [ ] Advanced analytics dashboard
- [ ] Mobile app integration
- [ ] Push notifications
- [ ] Geolocation tracking

### Version 3.0 (Future)
- [ ] Cloud deployment support
- [ ] Multi-tenant architecture
- [ ] Advanced AI models
- [ ] Biometric integration
- [ ] API for third-party apps

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 💬 Support

- 📧 Email: support@facetrack.com
- 🐛 Issues: [GitHub Issues](https://github.com/Mallikarjun15568/FaceTrack/issues)
- 📖 Wiki: [Project Wiki](https://github.com/Mallikarjun15568/FaceTrack/wiki)

---

## 🌟 Acknowledgments

- [InsightFace](https://github.com/deepinsight/insightface) - Face recognition model
- [Flask](https://flask.palletsprojects.com/) - Web framework
- [TailwindCSS](https://tailwindcss.com/) - CSS framework
- [OpenCV](https://opencv.org/) - Computer vision library

---

<div align="center">

### Made with ❤️ by FaceTrack Team

**⭐ Star this repo if you find it helpful!**

</div>
