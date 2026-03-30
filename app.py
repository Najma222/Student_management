# app.py
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory, send_file
from flask_bcrypt import Bcrypt
from itsdangerous import URLSafeTimedSerializer
from functools import wraps
from datetime import datetime, timedelta
import mysql.connector
from mysql.connector import Error
import os
from werkzeug.utils import secure_filename
import pandas as pd
import io
import resend
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Professional email template
EMAIL_VERIFICATION_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verify Your Account</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f4f4; -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale;">
    
    <!-- Main Container -->
    <table width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #f4f4f4; padding: 20px 0;">
        <tr>
            <td align="center">
                <table width="100%" max-width="600" border="0" cellspacing="0" cellpadding="0" style="max-width: 600px; margin: 0 auto;">
                    
                    <!-- Header -->
                    <tr>
                        <td style="background-color: #ffffff; padding: 40px 30px 20px 30px; text-align: center; border-radius: 8px 8px 0 0;">
                            <div style="font-size: 32px; font-weight: bold; color: #1a73e8; margin-bottom: 10px;">
                                📚 CourseMAGE
                            </div>
                            <div style="font-size: 14px; color: #5f6368; font-weight: 500;">
                                Secure Student Portal
                            </div>
                        </td>
                    </tr>
                    
                    <!-- Main Content -->
                    <tr>
                        <td style="background-color: #ffffff; padding: 0 30px 30px 30px; border-radius: 0 0 8px 8px;">
                            
                            <!-- Welcome Message -->
                            <div style="text-align: center; margin-bottom: 30px;">
                                <h1 style="color: #202124; font-size: 24px; font-weight: 600; margin: 0 0 10px 0;">
                                    Welcome, {name}!
                                </h1>
                                <p style="color: #5f6368; font-size: 16px; line-height: 1.5; margin: 0;">
                                    Thank you for registering with CourseMAGE. Please verify your email address to activate your account.
                                </p>
                            </div>
                            
                            <!-- Verify Button -->
                            <table width="100%" border="0" cellspacing="0" cellpadding="0" style="margin: 30px 0;">
                                <tr>
                                    <td align="center">
                                        <a href="{verify_url}" 
                                           style="background-color: #1a73e8; color: #ffffff; font-size: 16px; font-weight: 600; text-decoration: none; padding: 15px 30px; border-radius: 6px; display: inline-block; -webkit-text-size-adjust: none;">
                                            Verify Your Account
                                        </a>
                                    </td>
                                </tr>
                            </table>
                            
                            <!-- Alternative Link -->
                            <div style="text-align: center; margin: 20px 0;">
                                <p style="color: #5f6368; font-size: 14px; line-height: 1.5; margin: 0;">
                                    If the button above doesn't work, copy and paste this link into your browser:
                                </p>
                                <p style="color: #1a73e8; font-size: 12px; word-break: break-all; margin: 5px 0; font-family: 'Courier New', monospace;">
                                    {verify_url}
                                </p>
                            </div>
                            
                            <!-- Security Info -->
                            <div style="background-color: #f8f9fa; border-left: 4px solid #1a73e8; padding: 15px; margin: 20px 0;">
                                <p style="color: #5f6368; font-size: 14px; line-height: 1.5; margin: 0;">
                                    <strong>🔒 Security Notice:</strong> This link expires in 1 hour for your protection. If you didn't request this verification, you can safely ignore this email.
                                </p>
                            </div>
                            
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 30px 0; text-align: center;">
                            <div style="color: #5f6368; font-size: 14px; line-height: 1.5;">
                                <p style="margin: 0 0 10px 0;">
                                    Thanks,<br>
                                    <strong>CourseMAGE Team</strong>
                                </p>
                                <div style="border-top: 1px solid #e0e0e0; padding-top: 15px; margin-top: 15px;">
                                    <p style="margin: 0; font-size: 12px; color: #9aa0a6;">
                                        This is an automated message. Please do not reply to this email.
                                    </p>
                                </div>
                            </div>
                        </td>
                    </tr>
                    
                </table>
            </td>
        </tr>
    </table>
    
</body>
</html>
"""

# Initialize Flask app
app = Flask(__name__)
# Set a strong secret key for session management from environment
app.secret_key = os.getenv('SECRET_KEY', 'key1234')  # Fallback to existing key

# Configuration for file uploads
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'docx', 'pptx', 'xlsx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Email configuration for Resend
app.config['RESEND_API_KEY'] = os.getenv('RESEND_API_KEY')
app.config['RESEND_FROM_EMAIL'] = os.getenv('RESEND_FROM_EMAIL')

# Initialize Resend
resend.api_key = app.config['RESEND_API_KEY']
s = URLSafeTimedSerializer(app.secret_key)

# Check if Resend API key is configured
print(f"[DEBUG] RESEND_API_KEY from env: {app.config['RESEND_API_KEY']}")
print(f"[DEBUG] RESEND_FROM_EMAIL from env: {app.config['RESEND_FROM_EMAIL']}")
if not app.config['RESEND_API_KEY'] or app.config['RESEND_API_KEY'] == 'your_resend_api_key_here':
    print("[WARNING] Resend API key not configured. Email functionality will show links in console.")
    REEND_CONFIGURED = False
else:
    print("[INFO] Resend API key configured. Email functionality enabled.")
    REEND_CONFIGURED = True

# Create the uploads folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
    print(f"Created UPLOAD_FOLDER: {os.path.abspath(UPLOAD_FOLDER)}")

# Initialize Bcrypt for password hashing
bcrypt = Bcrypt(app)

# Context processor to make 'now()' available in all templates for the current year
@app.context_processor
def inject_now():
    """Injects the datetime.now function into the Jinja2 context."""
    return {'now': datetime.now}

# ---- Utility Functions ----
def allowed_file(filename):
    """Checks if a file's extension is allowed for upload."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ---- Database Connection Function ----
def get_connection():
    """
    Establishes and returns a connection to the MySQL database.
    Prints an error message if the connection fails.
    """
    try:
        return mysql.connector.connect(
            host="localhost",
            user="DBMS_Project",
            password="2005",
            database="course_mgmt"
        )
    except Error as e:
        print(f"[DB Error] Could not connect to database: {e}")
        return None

# ---- Helper function to get all instructors ----
def get_all_instructors():
    """Fetches all users with the 'instructor' role from the database."""
    conn = None
    cursor = None
    instructors = []
    try:
        conn = get_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, full_name FROM users WHERE role = 'instructor' ORDER BY full_name")
            instructors = cursor.fetchall()
    except Exception as e:
        print(f"[DB Error] Error fetching instructors: {e}")
        flash("Could not load instructors list.", "danger")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    return instructors

# ---- Decorators for access control ----

def login_required(f):
    """
    Decorator to ensure a user is logged in before accessing a route.
    If not logged in, flashes a warning and redirects to the login page.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            flash("Please log in to access this page.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def instructor_required(f):
    """
    Decorator to ensure the logged-in user has the 'instructor' role.
    If not an instructor, flashes an error and redirects to the home page.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'instructor':
            flash("Access denied: instructors only.", "danger")
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

# ---- Routes ----

@app.route('/')
def home():
    """Renders the home page."""
    return render_template('home.html')

@app.route('/about')
def about():
    """Renders the about page."""
    return render_template('about.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Handles user registration. Supports GET for displaying form and POST for submission."""
    # Clear any existing flash messages on GET request
    if request.method == 'GET':
        session.pop('_flashes', None)
        
    if request.method == 'POST':
        login_id = request.form['login_id'].strip()
        full_name = request.form['full_name'].strip()
        email = request.form['email'].strip()
        password = request.form['password']
        role = request.form.get('role', 'student')

        if not login_id or not full_name or not email or not password:
            flash("Please fill out all fields.", "warning")
            return render_template('register.html')

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        conn = None
        cursor = None
        try:
            conn = get_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM users WHERE login_id=%s OR email=%s", (login_id, email))
                existing = cursor.fetchone()
                if existing:
                    flash("ID or email already taken.", "danger")
                    return render_template('register.html')

                # Generate email verification token
                token = s.dumps(email, salt='email-confirm')
                verification_url = url_for('verify_email', token=token, _external=True)
                expires_at = datetime.now() + timedelta(hours=1)

                # Insert user with verification fields
                cursor.execute(
                    "INSERT INTO users (login_id, password, full_name, email, role, is_verified, email_verification_token, email_verification_expires) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                    (login_id, hashed_password, full_name, email, role, False, token, expires_at)
                )
                conn.commit()

                # Send verification email
                if not REEND_CONFIGURED:
                    # Development mode - show link in console and flash message
                    print(f"[DEV MODE] Verification link: {verification_url}")
                    flash("Email service not configured. Please check console for verification link.", "warning")
                else:
                    try:
                        print(f"[DEBUG] Attempting to send email to: {email}")
                        print(f"[DEBUG] From: {app.config['RESEND_FROM_EMAIL']}")

                        # Use professional email template
                        html_content = EMAIL_VERIFICATION_TEMPLATE.format(
                            name=full_name,
                            verify_url=verification_url
                        )

                        params = {
                            "from": app.config['RESEND_FROM_EMAIL'],
                            "to": [email],
                            "subject": "Verify Your Student Account",
                            "html": html_content
                        }
                        result = resend.Emails.send(params)
                        print(f"[DEBUG] Resend API response: {result}")
                        flash("Registration successful! Please check your email to verify your account.", "info")
                    except Exception as e:
                        print(f"[Email Error] {e}")
                        print(f"[DEBUG] Error type: {type(e).__name__}")
                        # Fallback to showing the link
                        flash(f"Email service error. Please use this verification link: {verification_url}", "warning")

                return redirect(url_for('login'))
            else:
                flash("Database connection failed.", "danger")
        except Exception as e:
            print(f"[DB Error] {e}")
            flash("An error occurred during registration. Please try again.", "danger")
        finally:
            if cursor:
                cursor.close()
            if conn:
                    conn.close()

    return render_template('register.html')

@app.route('/verify_email/<token>')
def verify_email(token):
    """Handles email verification with token validation."""
    try:
        # Verify token and get email (expires in 1 hour)
        email = s.loads(token, salt='email-confirm', max_age=3600)
    except:
        flash("The verification link is invalid or expired. Please request a new one.", "danger")
        return redirect(url_for('register'))
    
    conn = None
    cursor = None
    try:
        conn = get_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, full_name, is_verified FROM users WHERE email=%s", (email,))
            user = cursor.fetchone()
            
            if not user:
                flash("Invalid verification link.", "danger")
                return redirect(url_for('register'))
            
            if user['is_verified']:
                flash("Your account is already verified. You can log in.", "info")
                return redirect(url_for('login'))
            
            # Mark user as verified
            cursor.execute("UPDATE users SET is_verified=TRUE, email_verification_token=NULL, email_verification_expires=NULL WHERE email=%s", (email,))
            conn.commit()
            
            flash(f"Success! Your account has been verified. You can now log in, {user['full_name']}!", "success")
            return redirect(url_for('login'))
        else:
            flash("Database connection failed.", "danger")
    except Exception as e:
        print(f"[DB Error] {e}")
        flash("An error occurred during verification. Please try again.", "danger")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    
    return redirect(url_for('register'))

@app.route('/resend_verification', methods=['GET', 'POST'])
def resend_verification():
    """Resend verification email to users."""
    # Clear any existing flash messages on GET request
    if request.method == 'GET':
        session.pop('_flashes', None)
        
    if request.method == 'POST':
        email = request.form['email'].strip()
        
        if not email:
            flash("Please enter your email address.", "warning")
            return render_template('resend_verification.html')
        
        conn = None
        cursor = None
        try:
            conn = get_connection()
            if conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT id, full_name, is_verified FROM users WHERE email=%s", (email,))
                user = cursor.fetchone()
                
                if user and not user['is_verified']:
                    # Generate new verification token
                    token = s.dumps(email, salt='email-confirm')
                    verification_url = url_for('verify_email', token=token, _external=True)
                    expires_at = datetime.now() + timedelta(hours=1)
                    
                    # Update user with new token
                    cursor.execute("UPDATE users SET email_verification_token=%s, email_verification_expires=%s WHERE email=%s", 
                                 (token, expires_at, email))
                    conn.commit()
                    
                    # Send verification email
                    if not REEND_CONFIGURED:
                        # Development mode - show link in console
                        print(f"[DEV MODE] Verification link: {verification_url}")
                        flash("Email service not configured. Please check console for verification link.", "warning")
                    else:
                        try:
                            # Use professional email template
                            html_content = EMAIL_VERIFICATION_TEMPLATE.format(
                                name=user['full_name'],
                                verify_url=verification_url
                            )
                            
                            params = {
                                "from": app.config['RESEND_FROM_EMAIL'],
                                "to": [email],
                                "subject": "Verify Your Student Account",
                                "html": html_content
                            }
                            resend.Emails.send(params)
                            flash("Verification email sent! Please check your inbox.", "success")
                        except Exception as e:
                            print(f"[Email Error] {e}")
                            flash(f"Email service error. Please use this verification link: {verification_url}", "warning")
                elif user and user['is_verified']:
                    flash("Your account is already verified. You can log in.", "info")
                else:
                    # Don't reveal if email exists or not
                    flash("If an account with that email exists and is not verified, a verification link has been sent.", "info")
                    
        except Exception as e:
            print(f"[DB Error] {e}")
            flash("An error occurred. Please try again.", "danger")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    return render_template('resend_verification.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handles user login. Supports GET for displaying form and POST for submission."""
    # Clear any existing flash messages on GET request
    if request.method == 'GET':
        session.pop('_flashes', None)
        
    if request.method == 'POST':
        login_id = request.form['login_id'].strip()
        password = request.form['password']

        conn = None
        cursor = None
        try:
            conn = get_connection()
            if conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT * FROM users WHERE login_id=%s", (login_id,))
                user = cursor.fetchone()
                
                if user and bcrypt.check_password_hash(user['password'], password):
                    # Check if user is verified
                    if not user['is_verified']:
                        flash("Please verify your email address before logging in. Check your inbox for the verification link.", "warning")
                        return render_template('login.html')
                    
                    session['user_id'] = user['id']
                    session['login_id'] = user['login_id']
                    session['role'] = user['role']
                    session['full_name'] = user['full_name']
                    flash(f"Welcome back, {user['full_name']}!", "success")
                    return redirect(url_for('home'))
                else:
                    flash("Invalid ID or password.", "danger")
            else:
                flash("Database connection failed.", "danger")
        except Exception as e:
            print(f"[DB Error] {e}")
            flash("An error occurred during login. Please try again.", "danger")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """Logs out the current user by clearing the session."""
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    """Handles password reset requests."""
    # Clear any existing flash messages on GET request
    if request.method == 'GET':
        session.pop('_flashes', None)
        
    if request.method == 'POST':
        email = request.form['email'].strip()
        
        if not email:
            flash("Please enter your email address.", "warning")
            return render_template('forgot_password.html')
        
        conn = None
        cursor = None
        try:
            conn = get_connection()
            if conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT id, full_name FROM users WHERE email=%s", (email,))
                user = cursor.fetchone()
                
                if user:
                    # Generate reset token
                    token = s.dumps(email, salt='password-reset-salt')
                    reset_url = url_for('reset_password', token=token, _external=True)
                    
                    # Send email with Resend
                    try:
                        params = {
                            "from": app.config['RESEND_FROM_EMAIL'],
                            "to": [email],
                            "subject": "Password Reset Request",
                            "html": f'''<p>Hello {user['full_name']},</p>
<p>You requested a password reset. Click the link below to reset your password:</p>
<p><a href="{reset_url}">Reset Password</a></p>
<p>This link will expire in 1 hour.</p>
<p>If you didn't request this, please ignore this email.</p>
<p>Thanks,<br>Course Management System</p>'''
                        }
                        resend.Emails.send(params)
                        flash("Password reset link sent to your email. Please check your inbox.", "success")
                    except Exception as e:
                        print(f"[Email Error] {e}")
                        # For development, show the reset link
                        flash(f"Email service unavailable. Reset link: {reset_url}", "info")
                else:
                    # Don't reveal if email exists or not
                    flash("If an account with that email exists, a password reset link has been sent.", "info")
                    
        except Exception as e:
            print(f"[DB Error] {e}")
            flash("An error occurred. Please try again.", "danger")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    return render_template('forgot_password.html')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Handles password reset with token validation."""
    try:
        # Verify token and get email (expires in 1 hour)
        email = s.loads(token, salt='password-reset-salt', max_age=3600)
    except:
        flash("Invalid or expired reset link. Please request a new one.", "danger")
        return redirect(url_for('forgot_password'))
    
    if request.method == 'POST':
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if not password or not confirm_password:
            flash("Please fill out all fields.", "warning")
            return render_template('reset_password.html', token=token)
        
        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template('reset_password.html', token=token)
        
        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "danger")
            return render_template('reset_password.html', token=token)
        
        conn = None
        cursor = None
        try:
            conn = get_connection()
            if conn:
                cursor = conn.cursor()
                hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
                cursor.execute("UPDATE users SET password=%s WHERE email=%s", (hashed_password, email))
                conn.commit()
                flash("Password reset successfully! Please log in with your new password.", "success")
                return redirect(url_for('login'))
            else:
                flash("Database connection failed.", "danger")
        except Exception as e:
            print(f"[DB Error] {e}")
            flash("An error occurred. Please try again.", "danger")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    return render_template('reset_password.html', token=token)

@app.route('/forgot_id', methods=['GET', 'POST'])
def forgot_id():
    """Help users recover their login ID using their email."""
    # Clear any existing flash messages on GET request
    if request.method == 'GET':
        session.pop('_flashes', None)
        
    if request.method == 'POST':
        email = request.form['email'].strip()
        
        if not email:
            flash("Please enter your email address.", "warning")
            return render_template('forgot_id.html')
        
        conn = None
        cursor = None
        try:
            conn = get_connection()
            if conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT login_id, full_name FROM users WHERE email=%s", (email,))
                user = cursor.fetchone()
                
                if user:
                    # Send email with login ID using Resend
                    try:
                        params = {
                            "from": app.config['RESEND_FROM_EMAIL'],
                            "to": [email],
                            "subject": "Your Login ID Information",
                            "html": f'''<p>Hello {user['full_name']},</p>
<p>Your login ID for Course Management System is: <strong>{user['login_id']}</strong></p>
<p>You can use this ID to log in to your account.</p>
<p>If you need to reset your password, visit: <a href="{url_for('forgot_password', _external=True)}">Forgot Password</a></p>
<p>Thanks,<br>Course Management System</p>'''
                        }
                        resend.Emails.send(params)
                        flash("Your login ID has been sent to your email. Please check your inbox.", "success")
                    except Exception as e:
                        print(f"[Email Error] {e}")
                        # For development, show login ID
                        flash(f"Email service unavailable. Your login ID is: {user['login_id']}", "info")
                else:
                    # Don't reveal if email exists or not
                    flash("If an account with that email exists, your login ID information has been sent.", "info")
                    
        except Exception as e:
            print(f"[DB Error] {e}")
            flash("An error occurred. Please try again.", "danger")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    return render_template('forgot_id.html')

@app.route('/add_course', methods=['GET', 'POST'])
@login_required
@instructor_required
def add_course():
    """Allows instructors to add new courses."""
    instructors = get_all_instructors()

    if request.method == 'POST':
        name = request.form['name'].strip()
        credits = request.form['credits']
        teacher_id = request.form['teacher_id']

        try:
            credits = int(credits)
            if credits not in [1, 2, 3, 4]:
                raise ValueError("Invalid credits")
        except ValueError:
            flash("Credits must be an integer between 1 and 4.", "danger")
            return render_template('add_course.html', instructors=instructors)

        if not name:
            flash("Course name cannot be empty.", "warning")
            return render_template('add_course.html', instructors=instructors)

        if not teacher_id:
            flash("Please select a teacher for the course.", "warning")
            return render_template('add_course.html', instructors=instructors)

        conn = None
        cursor = None
        try:
            conn = get_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO allcourses (name, credits, teacher_id) VALUES (%s, %s, %s)",
                    (name, credits, teacher_id)
                )
                conn.commit()
                flash(f"Course '{name}' added successfully!", "success")
                return redirect(url_for('courses'))
            else:
                flash("Database connection failed.", "danger")
        except Exception as e:
            print(f"[DB Error] {e}")
            flash("An error occurred while adding the course.", "danger")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    return render_template('add_course.html', instructors=instructors)

@app.route('/courses')
@login_required
def courses():
    """Displays courses based on the user's role (instructor sees all courses, student sees all)."""
    user_role = session.get('role')
    user_id = session.get('user_id')

    conn = None
    cursor = None
    try:
        conn = get_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT ac.*, u.full_name AS teacher_name
                FROM allcourses ac
                JOIN users u ON ac.teacher_id = u.id
            """)

            courses_data = cursor.fetchall()
            
            return render_template('courses.html', courses=courses_data, role=user_role)
        else:
            flash("Database connection failed.", "danger")
            return redirect(url_for('home'))
    except Exception as e:
        print(f"[DB Error] {e}")
        flash("An error occurred fetching courses.", "danger")
        return redirect(url_for('home'))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/enroll/<int:course_id>', methods=['POST'])
@login_required
def enroll_course(course_id):
    """Allows students to enroll in a specific course."""
    if session.get('role') != 'student':
        flash("Only students can enroll in courses.", "danger")
        return redirect(url_for('courses'))

    student_id = session.get('user_id')

    conn = None
    cursor = None
    try:
        conn = get_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM enrollments WHERE student_id=%s AND course_id=%s", (student_id, course_id))
            existing = cursor.fetchone()
            if existing:
                flash("You are already enrolled in this course.", "info")
            else:
                cursor.execute("INSERT INTO enrollments (student_id, course_id) VALUES (%s, %s)", (student_id, course_id))
                conn.commit()
                flash("Enrollment successful!", "success")
        else:
            flash("Database connection failed.", "danger")
    except Exception as e:
        print(f"[DB Error] {e}")
        flash("An error occurred during enrollment.", "danger")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return redirect(url_for('courses'))

@app.route('/my_enrollments')
@login_required
def my_enrollments():
    """Displays courses a student is currently enrolled in, along with their assignments."""
    if session.get('role') != 'student':
        flash("Access denied: Students only.", "danger")
        return redirect(url_for('home'))

    student_id = session.get('user_id')
    conn = None
    cursor = None
    enrolled_courses_with_assignments = []
    try:
        conn = get_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT ac.id AS course_id, ac.name AS course_name, ac.credits, u.full_name AS teacher_name
                FROM enrollments e
                JOIN allcourses ac ON e.course_id = ac.id
                JOIN users u ON ac.teacher_id = u.id
                WHERE e.student_id = %s
            """, (student_id,))
            enrolled_courses = cursor.fetchall()

            for course in enrolled_courses:
                cursor.execute("""
                    SELECT
                        a.id AS assignment_id,
                        a.title,
                        a.description,
                        a.due_date,
                        s.file_path AS submitted_file_path,
                        s.submission_date AS student_submission_date,
                        s.grade
                    FROM assignments a
                    LEFT JOIN submissions s ON a.id = s.assignment_id AND s.student_id = %s
                    WHERE a.course_id = %s
                    ORDER BY a.due_date
                """, (student_id, course['course_id']))
                assignments = cursor.fetchall()
                for assignment in assignments:
                    if assignment['submitted_file_path']:
                        assignment['submitted_file_path'] = assignment['submitted_file_path'].replace('\\', '/')
                course['assignments'] = assignments
                enrolled_courses_with_assignments.append(course)
            
            return render_template('enrollments.html', courses=enrolled_courses_with_assignments)
        else:
            flash("Database connection failed.", "danger")
            return redirect(url_for('home'))
    except Exception as e:
        print(f"[DB Error] {e}")
        flash("An error occurred fetching your enrollments and assignments.", "danger")
        return redirect(url_for('home'))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/my_grades')
@login_required
def my_grades():
    """
    Displays a consolidated gradebook for the logged-in student,
    showing all assignments and their grades across all enrolled courses.
    """
    if session.get('role') != 'student':
        flash("Access denied: Students only.", "danger")
        return redirect(url_for('home'))

    student_id = session.get('user_id')
    conn = None
    cursor = None
    all_student_grades = []

    print(f"DEBUG: Entering my_grades for student_id: {student_id}")
    try:
        conn = get_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)

            print("DEBUG: Fetching enrolled courses for student.")
            cursor.execute("""
                SELECT ac.id AS course_id, ac.name AS course_name, u.full_name AS teacher_name
                FROM enrollments e
                JOIN allcourses ac ON e.course_id = ac.id
                JOIN users u ON ac.teacher_id = u.id
                WHERE e.student_id = %s
                ORDER BY ac.name
            """, (student_id,))
            enrolled_courses = cursor.fetchall()
            print(f"DEBUG: Found {len(enrolled_courses)} enrolled courses.")

            for course in enrolled_courses:
                print(f"DEBUG: Processing course: {course['course_name']} (ID: {course['course_id']})")
                cursor.execute("""
                    SELECT
                        a.id AS assignment_id,
                        a.title,
                        a.description,
                        a.due_date,
                        s.grade,
                        s.submission_date,
                        s.file_path AS submitted_file_path,
                        s.id AS submission_id
                    FROM assignments a
                    LEFT JOIN submissions s ON a.id = s.assignment_id AND s.student_id = %s
                    WHERE a.course_id = %s
                    ORDER BY a.due_date
                """, (student_id, course['course_id']))
                assignments_with_grades = cursor.fetchall()
                print(f"DEBUG: Found {len(assignments_with_grades)} assignments for course {course['course_id']}.")

                course_data = {
                    'course_id': course['course_id'],
                    'course_name': course['course_name'],
                    'teacher_name': course['teacher_name'],
                    'assignments': []
                }

                for assignment in assignments_with_grades:
                    if assignment['submitted_file_path']:
                        assignment['submitted_file_path'] = assignment['submitted_file_path'].replace('\\', '/')
                    course_data['assignments'].append(assignment)
                
                all_student_grades.append(course_data)
            
            print("DEBUG: Successfully prepared all student grades data.")
            return render_template('my_grades.html', all_student_grades=all_student_grades)
        else:
            flash("Database connection failed.", "danger")
            print("DEBUG: Database connection failed in my_grades.")
            return redirect(url_for('home'))
    except Exception as e:
        error_message = f"An error occurred fetching your grades: {e}"
        print(f"[DB Error in my_grades] {error_message}")
        flash(error_message, "danger")
        return redirect(url_for('home'))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/edit_course/<int:course_id>', methods=['GET', 'POST'])
@login_required
@instructor_required
def edit_course(course_id):
    """Allows instructors to edit an existing course."""
    conn = None
    cursor = None
    course = None
    instructors = get_all_instructors()

    try:
        conn = get_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT ac.*, u.full_name AS teacher_name
                FROM allcourses ac
                LEFT JOIN users u ON ac.teacher_id = u.id
                WHERE ac.id = %s
            """, (course_id,))
            course = cursor.fetchone()

            if not course:
                flash("Course not found.", "danger")
                return redirect(url_for('courses'))

            if request.method == 'POST':
                name = request.form['name'].strip()
                credits = request.form['credits']
                teacher_id = request.form['teacher_id']

                try:
                    credits = int(credits)
                    if credits not in [1, 2, 3, 4]:
                        raise ValueError("Invalid credits")
                except ValueError:
                    flash("Credits must be an integer between 1 and 4.", "danger")
                    return render_template('edit_course.html', course=course, instructors=instructors)

                if not name:
                    flash("Course name cannot be empty.", "warning")
                    return render_template('edit_course.html', course=course, instructors=instructors)

                if not teacher_id:
                    flash("Please select a teacher for the course.", "warning")
                    return render_template('edit_course.html', course=course, instructors=instructors)

                cursor.execute(
                    "UPDATE allcourses SET name = %s, credits = %s, teacher_id = %s WHERE id = %s",
                    (name, credits, teacher_id, course_id)
                )
                conn.commit()
                flash(f"Course '{name}' updated successfully!", "success")
                return redirect(url_for('courses'))
            
        else:
            flash("Database connection failed.", "danger")
            return redirect(url_for('courses'))
    except Exception as e:
        print(f"[DB Error] {e}")
        flash("An error occurred while editing the course.", "danger")
        return redirect(url_for('courses'))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return render_template('edit_course.html', course=course, instructors=instructors)

@app.route('/add_assignment/<int:course_id>', methods=['GET', 'POST'])
@login_required
@instructor_required
def add_assignment(course_id):
    """
    Allows instructors to add assignments to a specific course.
    Handles both displaying the form (GET) and processing the submission (POST).
    """
    conn = None
    cursor = None
    course = None
    try:
        conn = get_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, name FROM allcourses WHERE id = %s AND teacher_id = %s", (course_id, session.get('user_id')))
            course = cursor.fetchone()

            if not course:
                flash("Course not found or you don't have permission to add assignments to it.", "danger")
                return redirect(url_for('courses'))

            if request.method == 'POST':
                title = request.form['title'].strip()
                description = request.form.get('description', '').strip()
                due_date_str = request.form['due_date']

                if not title or not due_date_str:
                    flash("Title and Due Date are required.", "warning")
                    return render_template('add_assignment.html', course=course)

                try:
                    due_date = datetime.strptime(due_date_str, '%Y-%m-%dT%H:%M')
                except ValueError:
                    flash("Invalid due date format. Please use %Y-%m-%dT%H:%M.", "danger")
                    return render_template('add_assignment.html', course=course)

                cursor.execute(
                    "INSERT INTO assignments (course_id, title, description, due_date) VALUES (%s, %s, %s, %s)",
                    (course_id, title, description, due_date)
                )
                conn.commit()
                flash(f"Assignment '{title}' added successfully to {course['name']}!", "success")
                return redirect(url_for('courses'))
            
            return render_template('add_assignment.html', course=course)
        else:
            flash("Database connection failed.", "danger")
            return redirect(url_for('courses'))
    except Exception as e:
        print(f"[DB Error] {e}")
        flash("An error occurred while adding the assignment.", "danger")
        return redirect(url_for('courses'))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route('/edit_assignment/<int:assignment_id>', methods=['GET', 'POST'])
@login_required
@instructor_required
def edit_assignment(assignment_id):
    """
    Allows instructors to edit an existing assignment.
    GET: Displays the edit form pre-populated with assignment data.
    POST: Processes the updated assignment data.
    """
    conn = None
    cursor = None
    assignment = None
    
    try:
        conn = get_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            
            # Fetch assignment details and verify instructor ownership of the course
            cursor.execute("""
                SELECT a.id, a.title, a.description, a.due_date, a.course_id, ac.name AS course_name
                FROM assignments a
                JOIN allcourses ac ON a.course_id = ac.id
                WHERE a.id = %s AND ac.teacher_id = %s
            """, (assignment_id, session.get('user_id')))
            assignment = cursor.fetchone()

            if not assignment:
                flash("Assignment not found or you don't have permission to edit it.", "danger")
                return redirect(url_for('courses')) # Redirect if not found or no permission

            # Format due_date for datetime-local input (YYYY-MM-DDTHH:MM)
            if assignment['due_date']:
                assignment['due_date_str'] = assignment['due_date'].strftime('%Y-%m-%dT%H:%M')
            else:
                assignment['due_date_str'] = ''

            if request.method == 'POST':
                title = request.form['title'].strip()
                description = request.form.get('description', '').strip()
                due_date_str = request.form['due_date']

                if not title or not due_date_str:
                    flash("Title and Due Date are required.", "warning")
                    return render_template('edit_assignment.html', assignment=assignment)

                try:
                    due_date = datetime.strptime(due_date_str, '%Y-%m-%dT%H:%M')
                except ValueError:
                    flash("Invalid due date format. Please use %Y-%m-%dT%H:%M.", "danger")
                    return render_template('edit_assignment.html', assignment=assignment)

                cursor.execute(
                    "UPDATE assignments SET title = %s, description = %s, due_date = %s WHERE id = %s",
                    (title, description, due_date, assignment_id)
                )
                conn.commit()
                flash(f"Assignment '{title}' updated successfully!", "success")
                # Redirect back to view_students for the course this assignment belongs to
                return redirect(url_for('view_students', course_id=assignment['course_id']))
            
            # For GET request, render the template with fetched assignment data
            return render_template('edit_assignment.html', assignment=assignment)
        else:
            flash("Database connection failed.", "danger")
            return redirect(url_for('courses'))
    except Exception as e:
        print(f"[DB Error] {e}")
        flash("An error occurred while editing the assignment.", "danger")
        return redirect(url_for('courses'))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route('/submit_assignment/<int:assignment_id>', methods=['GET', 'POST'])
@login_required
def submit_assignment(assignment_id):
    """
    Displays the form for a student to submit an assignment (GET).
    Handles the file upload and database insertion/update for assignment submission (POST).
    """
    if session.get('role') != 'student':
        flash("Only students can submit assignments.", "danger")
        return redirect(url_for('home'))

    student_id = session.get('user_id')
    conn = None
    cursor = None
    assignment = None
    submission = None

    try:
        conn = get_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, title, description, due_date FROM assignments WHERE id = %s", (assignment_id,))
            assignment = cursor.fetchone()

            if not assignment:
                flash("Assignment not found.", "danger")
                return redirect(url_for('my_enrollments'))

            cursor.execute("SELECT id, file_path, submission_date, grade FROM submissions WHERE assignment_id = %s AND student_id = %s",
                           (assignment_id, student_id))
            submission = cursor.fetchone()

            if submission and submission['file_path']:
                submission['file_path'] = submission['file_path'].replace('\\', '/')

            if request.method == 'POST':
                if 'submission_file' not in request.files:
                    flash('No file part', 'danger')
                    return redirect(url_for('submit_assignment', assignment_id=assignment_id))
                
                file = request.files['submission_file']

                if file.filename == '':
                    flash('No selected file', 'danger')
                    return redirect(url_for('submit_assignment', assignment_id=assignment_id))
                
                if file and allowed_file(file.filename):
                    filename = secure_filename(f"{student_id}_{assignment_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
                    file_path_os = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path_os)
                    print(f"File saved to: {os.path.abspath(file_path_os)}")

                    file_path_db = file_path_os.replace('\\', '/')

                    if submission:
                        cursor.execute("UPDATE submissions SET file_path = %s, submission_date = CURRENT_TIMESTAMP, grade = NULL WHERE id = %s",
                                       (file_path_db, submission['id']))
                        flash("Assignment resubmitted successfully!", "success")
                    else:
                        cursor.execute(
                            "INSERT INTO submissions (assignment_id, student_id, file_path) VALUES (%s, %s, %s)",
                            (assignment_id, student_id, file_path_db)
                        )
                        flash("Assignment submitted successfully!", "success")
                    
                    conn.commit()
                    return redirect(url_for('my_enrollments'))
                else:
                    flash('Allowed file types are txt, pdf, png, jpg, jpeg, gif, docx, pptx, xlsx', 'danger')
                    return redirect(url_for('submit_assignment', assignment_id=assignment_id))
            
            return render_template('submit_assignment.html', assignment=assignment, submission=submission)
        else:
            flash("Database connection failed.", "danger")
            return redirect(url_for('my_enrollments'))
    except Exception as e:
        print(f"[DB Error] {e}")
        flash("An error occurred during submission or fetching details.", "danger")
        return redirect(url_for('my_enrollments'))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/view_students/<int:course_id>')
@login_required
@instructor_required
def view_students(course_id):
    """
    Allows instructors to view students enrolled in a specific course,
    along with their submission status and grades for all assignments in that course.
    """
    conn = None
    cursor = None
    course = None
    students_data = []

    search_query = request.args.get('search_query', '').strip()
    search_param = f"%{search_query}%"

    try:
        conn = get_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            
            # --- DEBUG PRINTS FOR VIEW_STUDENTS ---
            user_id_in_session = session.get('user_id')
            print(f"DEBUG (view_students): Entering view_students for course_id={course_id}")
            print(f"DEBUG (view_students): User logged in (session.get('user_id')): {user_id_in_session}")
            print(f"DEBUG (view_students): User role (session.get('role')): {session.get('role')}")
            # --- END DEBUG PRINTS ---

            cursor.execute("SELECT id, name, teacher_id FROM allcourses WHERE id = %s", (course_id,))
            course = cursor.fetchone()

            # --- DEBUG PRINT FOR COURSE FETCH ---
            print(f"DEBUG (view_students): Course fetched: {course}")
            # --- END DEBUG PRINT ---

            if not course:
                flash("Course not found.", "danger")
                return redirect(url_for('courses'))
            
            # Verify instructor ownership of the course
            if course['teacher_id'] != user_id_in_session:
                flash("Access denied: You do not manage this course.", "danger")
                return redirect(url_for('courses'))

            cursor.execute("SELECT id AS assignment_id, title, description, due_date FROM assignments WHERE course_id = %s ORDER BY due_date", (course_id,))
            all_assignments = cursor.fetchall()

            # --- DEBUG PRINT FOR ALL_ASSIGNMENTS ---
            print(f"DEBUG (view_students): All assignments for course {course_id}: {all_assignments}")
            # --- END DEBUG PRINT ---

            student_query = """
                SELECT u.id AS student_id, u.full_name, u.login_id
                FROM enrollments e
                JOIN users u ON e.student_id = u.id
                WHERE e.course_id = %s
            """
            query_params = [course_id]

            if search_query:
                student_query += " AND (u.full_name LIKE %s OR u.login_id LIKE %s)"
                query_params.extend([search_param, search_param])

            student_query += " ORDER BY u.full_name"

            cursor.execute(student_query, tuple(query_params))
            enrolled_students = cursor.fetchall()

            # --- DEBUG PRINT FOR ENROLLED_STUDENTS ---
            print(f"DEBUG (view_students): Enrolled students for course {course_id}: {enrolled_students}")
            # --- END DEBUG PRINT ---

            for student in enrolled_students:
                student_assignments = []
                for assignment in all_assignments:
                    cursor.execute("""
                        SELECT s.id AS submission_id, s.file_path, s.submission_date, s.grade
                        FROM submissions s
                        WHERE s.assignment_id = %s AND s.student_id = %s
                    """, (assignment['assignment_id'], student['student_id']))
                    submission = cursor.fetchone()

                    if submission and submission['file_path']:
                        submission['file_path'] = submission['file_path'].replace('\\', '/')

                    student_assignments.append({
                        'assignment_id': assignment['assignment_id'],
                        'title': assignment['title'],
                        'due_date': assignment['due_date'],
                        'submission': submission
                    })
                student['assignments_data'] = student_assignments
                students_data.append(student)
            
            print(f"DEBUG (view_students): Final students_data prepared: {students_data}")
            return render_template('view_students.html', course=course, students_data=students_data, all_assignments=all_assignments, search_query=search_query)
        else:
            flash("Database connection failed.", "danger")
            return redirect(url_for('courses'))
    except Exception as e:
        error_message = f"An error occurred fetching student submissions: {e}"
        print(f"[DB Error in view_students] {error_message}")
        flash(error_message, "danger")
        return redirect(url_for('courses'))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/grade_submission/<int:submission_id>', methods=['GET', 'POST'])
@login_required
@instructor_required
def grade_submission(submission_id):
    """
    Handles grading an existing assignment submission.
    GET: Displays the grading form.
    POST: Updates the submission with the new grade.
    """
    conn = None
    cursor = None
    submission = None

    try:
        conn = get_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT
                    s.id AS submission_id,
                    s.file_path,
                    s.submission_date,
                    s.grade,
                    u.id AS student_id,
                    u.full_name AS student_name,
                    a.id AS assignment_id,
                    a.title AS assignment_title,
                    ac.name AS course_name,
                    ac.id AS course_id
                FROM submissions s
                JOIN users u ON s.student_id = u.id
                JOIN assignments a ON s.assignment_id = a.id
                JOIN allcourses ac ON a.course_id = ac.id
                WHERE s.id = %s AND ac.teacher_id = %s
            """, (submission_id, session.get('user_id')))
            submission = cursor.fetchone()

            if not submission:
                flash("Submission not found or you do not have permission to grade it.", "danger")
                return redirect(url_for('courses'))
            
            if submission['file_path']:
                submission['file_path'] = submission['file_path'].replace('\\', '/')

            if request.method == 'POST':
                grade_input = request.form.get('grade')
                
                if grade_input is None or grade_input == '':
                    grade = None
                else:
                    try:
                        grade = float(grade_input)
                        if not (0 <= grade <= 100):
                            flash("Grade must be between 0 and 100.", "danger")
                            return render_template('grade_submission.html', submission=submission)
                    except ValueError:
                        flash("Invalid grade format. Please enter a number.", "danger")
                        return render_template('grade_submission.html', submission=submission)
                
                cursor.execute(
                    "UPDATE submissions SET grade = %s WHERE id = %s",
                    (grade, submission_id)
                )
                conn.commit()
                flash("Grade saved successfully!", "success")
                return redirect(url_for('view_students', course_id=submission['course_id']))

            return render_template('grade_submission.html', submission=submission)
        else:
            flash("Database connection failed.", "danger")
            return redirect(url_for('home'))
    except Exception as e:
        print(f"[DB Error] {e}")
        flash("An error occurred while grading the submission.", "danger")
        return redirect(url_for('courses'))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/grade_submission_for_student_assignment/<int:student_id>/<int:assignment_id>', methods=['GET', 'POST'])
@login_required
@instructor_required
def grade_submission_for_student_assignment(student_id, assignment_id):
    """
    Allows an instructor to add a grade for a student for a specific assignment,
    even if no file has been submitted. This effectively creates a 'submission'
    entry if one doesn't exist, just with a grade and no file path.
    """
    conn = None
    cursor = None
    student = None
    assignment = None
    course = None
    submission = None

    try:
        conn = get_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)

            cursor.execute("SELECT id, full_name, login_id FROM users WHERE id = %s AND role = 'student'", (student_id,))
            student = cursor.fetchone()
            if not student:
                flash("Student not found.", "danger")
                return redirect(url_for('courses'))

            cursor.execute("SELECT id, title, description, course_id FROM assignments WHERE id = %s", (assignment_id,))
            assignment = cursor.fetchone()
            if not assignment:
                flash("Assignment not found.", "danger")
                return redirect(url_for('courses'))
            
            cursor.execute("SELECT id, name FROM allcourses WHERE id = %s AND teacher_id = %s", (assignment['course_id'], session.get('user_id')))
            course = cursor.fetchone()
            if not course:
                flash("Course not found or you do not have permission to grade assignments for this course.", "danger")
                return redirect(url_for('courses'))

            cursor.execute("SELECT id AS submission_id, file_path, submission_date, grade FROM submissions WHERE student_id = %s AND assignment_id = %s",
                           (student_id, assignment_id))
            submission = cursor.fetchone()

            if request.method == 'POST':
                grade_input = request.form.get('grade')
                
                if grade_input is None or grade_input == '':
                    grade = None
                else:
                    try:
                        grade = float(grade_input)
                        if not (0 <= grade <= 100):
                            flash("Grade must be between 0 and 100.", "danger")
                            return render_template('grade_submission.html', student=student, assignment=assignment, course=course, submission=submission)
                    except ValueError:
                        flash("Invalid grade format. Please enter a number.", "danger")
                        return render_template('grade_submission.html', student=student, assignment=assignment, course=course, submission=submission)

                if submission:
                    cursor.execute("UPDATE submissions SET grade = %s WHERE id = %s", (grade, submission['submission_id']))
                else:
                    cursor.execute(
                        "INSERT INTO submissions (assignment_id, student_id, grade) VALUES (%s, %s, %s)",
                        (assignment_id, student_id, grade)
                    )
                conn.commit()
                flash(f"Grade for {student['full_name']} on '{assignment['title']}' saved successfully!", "success")
                return redirect(url_for('view_students', course_id=course['id']))

            return render_template('grade_submission.html', student=student, assignment=assignment, course=course, submission=submission)
        else:
            flash("Database connection failed.", "danger")
            return redirect(url_for('home'))
    except Exception as e:
        print(f"[DB Error] {e}")
        flash("An error occurred while managing the grade.", "danger")
        return redirect(url_for('courses'))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """
    Serves uploaded files from the UPLOAD_FOLDER.
    Uses send_from_directory for secure serving.
    """
    # DEBUG: Print the filename being requested for download
    print(f"DEBUG: Attempting to serve file: {filename} from {app.config['UPLOAD_FOLDER']}")
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/assignments/<int:course_id>')
@login_required
@instructor_required
def view_assignments(course_id):
    conn = None
    cursor = None
    assignments = []
    course = None
    try:
        conn = get_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            # Check instructor ownership
            cursor.execute("SELECT * FROM allcourses WHERE id=%s AND teacher_id=%s", (course_id, session.get('user_id')))
            course = cursor.fetchone()
            if not course:
                flash("Access denied or course not found.", "danger")
                return redirect(url_for('courses'))
            cursor.execute("SELECT * FROM assignments WHERE course_id=%s ORDER BY due_date", (course_id,))
            assignments = cursor.fetchall()
        else:
            flash("Database connection failed.", "danger")
            return redirect(url_for('courses'))
    except Exception as e:
        flash(f"Error loading assignments: {e}", "danger")
        return redirect(url_for('courses'))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    return render_template('view_assignments.html', course=course, assignments=assignments)

@app.route('/instructor_courses')
@login_required
@instructor_required
def instructor_courses():
    instructor_id = session.get('user_id')
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT id, name, credits
        FROM allcourses
        WHERE teacher_id = %s
        ORDER BY name
    """, (instructor_id,))
    courses = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('instructor_courses.html', courses=courses)

@app.route('/track_students')
@login_required
@instructor_required
def track_students():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    # Get all students
    cursor.execute("SELECT id, full_name, login_id FROM users WHERE role = 'student' ORDER BY full_name")
    students = cursor.fetchall()
    student_data = []
    for student in students:
        cursor.execute('''
            SELECT ac.name AS course_name, ac.credits
            FROM enrollments e
            JOIN allcourses ac ON e.course_id = ac.id
            WHERE e.student_id = %s
        ''', (student['id'],))
        courses = cursor.fetchall()
        total_credits = sum(course['credits'] for course in courses)
        student_data.append({
            'full_name': student['full_name'],
            'login_id': student['login_id'],
            'courses': courses,
            'total_credits': total_credits
        })
    cursor.close()
    conn.close()
    return render_template('track_students.html', students=student_data)

@app.route('/export_grades/<int:course_id>')
@login_required
@instructor_required
def export_grades(course_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    # Get course info
    cursor.execute("SELECT name FROM allcourses WHERE id=%s", (course_id,))
    course = cursor.fetchone()
    # Get all students in the course
    cursor.execute("""
        SELECT u.full_name, u.login_id, a.title AS assignment, a.id AS assignment_id, \
               s.grade, s.submission_date, s.file_path
        FROM enrollments e
        JOIN users u ON e.student_id = u.id
        JOIN assignments a ON a.course_id = e.course_id
        LEFT JOIN submissions s ON s.assignment_id = a.id AND s.student_id = u.id
        WHERE e.course_id = %s
        ORDER BY u.full_name, a.title
    """, (course_id,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    # Prepare DataFrame
    df = pd.DataFrame(rows)
    if not df.empty:
        df['Submission Status'] = df['file_path'].apply(lambda x: 'Submitted' if pd.notnull(x) else 'Not Submitted')
        df['Grade'] = df['grade'].fillna('N/A')
        df['Submission Date'] = df['submission_date'].fillna('N/A')
        df = df[['full_name', 'login_id', 'assignment', 'Submission Status', 'Grade', 'Submission Date']]
        df.columns = ['Student Name', 'Student ID', 'Assignment', 'Submission Status', 'Grade', 'Submission Date']
    else:
        df = pd.DataFrame([{'Student Name': '', 'Student ID': '', 'Assignment': '', 'Submission Status': '', 'Grade': '', 'Submission Date': ''}])

    # Export to Excel in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Grades')
    output.seek(0)

    filename = f"{course['name']}_grades.xlsx"
    return send_file(output, as_attachment=True, download_name=filename, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

if __name__ == '__main__':
    app.run(debug=True)
