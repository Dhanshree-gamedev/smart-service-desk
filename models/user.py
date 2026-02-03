"""
User model with Flask-Login integration.
"""
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db_connection


class User(UserMixin):
    """User model for authentication and authorization."""
    
    def __init__(self, user_id, name, email, password, role, created_at=None):
        self.id = user_id  # Flask-Login requires 'id' attribute
        self.user_id = user_id
        self.name = name
        self.email = email
        self.password = password
        self.role = role
        self.created_at = created_at
    
    @property
    def is_admin(self):
        """Check if user has admin role."""
        return self.role == 'ADMIN'
    
    @property
    def is_user(self):
        """Check if user has regular user role."""
        return self.role == 'USER'
    
    def verify_password(self, password):
        """Verify password against stored hash."""
        return check_password_hash(self.password, password)
    
    @staticmethod
    def create(name, email, password, role='USER'):
        """Create a new user in the database."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        hashed_password = generate_password_hash(password)
        
        try:
            cursor.execute('''
                INSERT INTO users (name, email, password, role)
                VALUES (?, ?, ?, ?)
            ''', (name, email, hashed_password, role))
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()
            return User.get_by_id(user_id)
        except Exception as e:
            conn.close()
            raise e
    
    @staticmethod
    def get_by_id(user_id):
        """Retrieve user by ID."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_id, name, email, password, role, created_at
            FROM users WHERE user_id = ?
        ''', (user_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return User(
                user_id=row['user_id'],
                name=row['name'],
                email=row['email'],
                password=row['password'],
                role=row['role'],
                created_at=row['created_at']
            )
        return None
    
    @staticmethod
    def get_by_email(email):
        """Retrieve user by email."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_id, name, email, password, role, created_at
            FROM users WHERE email = ?
        ''', (email,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return User(
                user_id=row['user_id'],
                name=row['name'],
                email=row['email'],
                password=row['password'],
                role=row['role'],
                created_at=row['created_at']
            )
        return None
    
    @staticmethod
    def email_exists(email):
        """Check if email is already registered."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT 1 FROM users WHERE email = ?', (email,))
        exists = cursor.fetchone() is not None
        conn.close()
        
        return exists
    
    def to_dict(self):
        """Convert user to dictionary (excludes password)."""
        return {
            'user_id': self.user_id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at
        }
