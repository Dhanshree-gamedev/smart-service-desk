"""
Routes package initialization with role decorators.
"""
from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user


def role_required(role):
    """
    Decorator to require a specific role for route access.
    Usage: @role_required('ADMIN')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login'))
            
            if current_user.role != role:
                flash('You do not have permission to access this page.', 'danger')
                if current_user.is_admin:
                    return redirect(url_for('admin.dashboard'))
                else:
                    return redirect(url_for('user.dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    """Decorator shortcut for admin-only routes."""
    return role_required('ADMIN')(f)


def user_required(f):
    """Decorator shortcut for user-only routes."""
    return role_required('USER')(f)
