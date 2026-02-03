"""
Authentication routes: login, register, logout.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models.user import User

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if current_user.is_authenticated:
        return redirect_by_role()
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)
        
        if not email or not password:
            flash('Please fill in all fields.', 'warning')
            return render_template('auth/login.html')
        
        user = User.get_by_email(email)
        
        if user and user.verify_password(password):
            login_user(user, remember=bool(remember))
            flash(f'Welcome back, {user.name}!', 'success')
            
            # Redirect to intended page or dashboard
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            
            return redirect_by_role()
        else:
            flash('Invalid email or password.', 'danger')
    
    return render_template('auth/login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration."""
    if current_user.is_authenticated:
        return redirect_by_role()
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        errors = []
        
        if not name or len(name) < 2:
            errors.append('Name must be at least 2 characters.')
        
        if not email or '@' not in email:
            errors.append('Please enter a valid email address.')
        
        if len(password) < 6:
            errors.append('Password must be at least 6 characters.')
        
        if password != confirm_password:
            errors.append('Passwords do not match.')
        
        if User.email_exists(email):
            errors.append('Email is already registered.')
        
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('auth/register.html', name=name, email=email)
        
        # Create user
        try:
            user = User.create(name=name, email=email, password=password, role='USER')
            login_user(user)
            flash('Registration successful! Welcome to Smart Service Desk.', 'success')
            return redirect(url_for('user.dashboard'))
        except Exception as e:
            flash('An error occurred during registration. Please try again.', 'danger')
            return render_template('auth/register.html', name=name, email=email)
    
    return render_template('auth/register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """Handle user logout."""
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('landing'))


def redirect_by_role():
    """Redirect user based on their role."""
    if current_user.is_admin:
        return redirect(url_for('admin.dashboard'))
    else:
        return redirect(url_for('user.dashboard'))
