"""
Configuration settings for Smart Service Desk application.
"""
import os
from datetime import timedelta

# Base directory
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Instance folder for database (Flask best practice)
INSTANCE_DIR = os.path.join(BASE_DIR, 'instance')


class Config:
    """Base configuration class."""
    
    # Secret key for session management and CSRF protection
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # SQLite database path (in instance folder)
    DATABASE_PATH = os.path.join(INSTANCE_DIR, 'service_desk.db')
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    SESSION_COOKIE_SECURE = False  # Set True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # CSRF protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour
    
    # Request status constants (consistent naming)
    STATUS_SUBMITTED = 'Submitted'
    STATUS_IN_PROGRESS = 'In Progress'
    STATUS_RESOLVED = 'Resolved'
    
    # Valid status transitions
    VALID_TRANSITIONS = {
        'Submitted': ['In Progress'],
        'In Progress': ['Resolved'],
        'Resolved': []  # Final state - no transitions allowed
    }
    
    # Request categories
    CATEGORIES = [
        'IT Support',
        'Facilities',
        'Academic',
        'Administrative',
        'Financial',
        'Other'
    ]


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    SESSION_COOKIE_SECURE = True


# Active configuration
config = DevelopmentConfig()
