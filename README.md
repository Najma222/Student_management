# CourseMAGE - Student Management System

A comprehensive Flask-based course management system with email verification, user authentication, and academic workflow management.

## Features

- 🎓 **User Management**: Student and instructor roles with secure authentication
- 📧 **Email Verification**: Professional email verification system using Resend
- 📚 **Course Management**: Create, enroll, and manage academic courses
- 📝 **Assignment System**: Submit assignments and track grades
- 🔐 **Security**: Password hashing, token-based verification, and secure sessions
- 🎨 **Modern UI**: Responsive design with Tailwind CSS and smooth animations

## Quick Start

### Prerequisites
- Python 3.9+
- MySQL/TiDB database
- Resend API key (for email functionality)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Najma222/Student_management.git
   cd Student_management
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Set up database**
   ```sql
   CREATE DATABASE course_mgmt;
   -- Run the provided SQL schema
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

## Environment Variables

Create a `.env` file with the following:

```env
# Database Configuration
DB_HOST=localhost
DB_USER=DBMS_Project
DB_PASS=2005
DB_NAME=course_mgmt
DB_PORT=3306

# Email Configuration
RESEND_API_KEY=your_resend_api_key
RESEND_FROM_EMAIL=your_verified_email@domain.com

# Flask Configuration
SECRET_KEY=your_secret_key_here
```

## Database Schema

The application uses the following main tables:
- `users` - User authentication and profiles
- `courses` - Course information and management
- `enrollments` - Student course enrollments
- `assignments` - Course assignments and submissions
- `grades` - Student grade tracking

## Deployment

### Render Deployment

1. **Push to GitHub** (already done)
2. **Create Render account** at [render.com](https://render.com)
3. **Connect GitHub repository**
4. **Create Web Service** with:
   - Runtime: Python 3
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
5. **Set environment variables** in Render dashboard
6. **Deploy and test**

## Features in Detail

### Authentication System
- Secure user registration with email verification
- Role-based access control (student/instructor)
- Password reset and login ID recovery
- Session management with security tokens

### Email System
- Professional HTML email templates
- Account verification emails
- Password reset notifications
- Login ID recovery emails

### Course Management
- Instructors can create and manage courses
- Students can browse and enroll in courses
- Assignment creation and submission
- Grade tracking and feedback

### Security Features
- Password hashing with Flask-Bcrypt
- CSRF protection
- Input validation and sanitization
- Secure session management

## Technology Stack

- **Backend**: Flask (Python)
- **Database**: MySQL/TiDB
- **Frontend**: HTML, Tailwind CSS, JavaScript
- **Email**: Resend API
- **Deployment**: Render, Gunicorn
- **Authentication**: Flask-Bcrypt, itsdangerous

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For support and questions, please open an issue on GitHub.

---

**CourseMAGE** - Empowering education through technology 🚀
