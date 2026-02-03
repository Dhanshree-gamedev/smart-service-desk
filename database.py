"""
Database initialization and connection management for SQLite.
Includes migration support for schema updates.
"""
import os
import sqlite3
from config import config, INSTANCE_DIR


def get_db_connection():
    """Create and return a database connection."""
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    conn.execute("PRAGMA foreign_keys = ON")  # Enforce foreign key constraints
    return conn


def run_migrations():
    """Run database migrations for existing installations.
    This must be called BEFORE creating indexes on new columns.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check what columns exist in service_requests
    cursor.execute("PRAGMA table_info(service_requests)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if columns:  # Only migrate if table exists
        if 'priority' not in columns:
            print("Migration: Adding priority column to service_requests...")
            cursor.execute('''
                ALTER TABLE service_requests 
                ADD COLUMN priority TEXT DEFAULT 'Medium'
            ''')
            conn.commit()
            print("  Priority column added with default 'Medium'.")
        
        if 'category_id' not in columns:
            print("Migration: Adding category_id column to service_requests...")
            cursor.execute('''
                ALTER TABLE service_requests 
                ADD COLUMN category_id INTEGER
            ''')
            conn.commit()
            print("  category_id column added.")
    
    conn.close()


def init_db():
    """Initialize the database with schema."""
    # Ensure instance directory exists
    os.makedirs(INSTANCE_DIR, exist_ok=True)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT CHECK(role IN ('USER','ADMIN')) NOT NULL DEFAULT 'USER',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Request categories table (admin-managed)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS request_categories (
            category_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE COLLATE NOCASE,
            description TEXT,
            is_active INTEGER DEFAULT 1,
            created_by INTEGER NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(created_by) REFERENCES users(user_id)
        )
    ''')
    
    # Service requests table - base schema (migrations add new columns)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS service_requests (
            request_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            category TEXT NOT NULL,
            status TEXT CHECK(status IN ('Submitted','In Progress','Resolved')) DEFAULT 'Submitted',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME,
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
    ''')
    
    # Request status log (audit trail)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS request_status_log (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id INTEGER NOT NULL,
            old_status TEXT,
            new_status TEXT NOT NULL,
            remark TEXT,
            updated_by INTEGER NOT NULL,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(request_id) REFERENCES service_requests(request_id),
            FOREIGN KEY(updated_by) REFERENCES users(user_id)
        )
    ''')
    
    # Request feedback table (user satisfaction rating)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS request_feedback (
            feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id INTEGER NOT NULL UNIQUE,
            user_id INTEGER NOT NULL,
            rating INTEGER CHECK(rating BETWEEN 1 AND 5) NOT NULL,
            comment TEXT,
            submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(request_id) REFERENCES service_requests(request_id),
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
    ''')
    
    conn.commit()
    conn.close()
    
    # Run migrations to add new columns
    run_migrations()
    
    # Now create indexes (after migrations ensure columns exist)
    create_indexes()
    
    print(f"Database initialized at: {config.DATABASE_PATH}")


def create_indexes():
    """Create production indexes for performance."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Base indexes
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_requests_user_id 
        ON service_requests(user_id)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_requests_status 
        ON service_requests(status)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_logs_request_id 
        ON request_status_log(request_id)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_users_email 
        ON users(email)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_feedback_request_id 
        ON request_feedback(request_id)
    ''')
    
    # Indexes on migration columns (only if columns exist)
    try:
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_requests_priority 
            ON service_requests(priority)
        ''')
    except sqlite3.OperationalError:
        pass  # Column doesn't exist
    
    try:
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_requests_category_id 
            ON service_requests(category_id)
        ''')
    except sqlite3.OperationalError:
        pass  # Column doesn't exist
    
    conn.commit()
    conn.close()


def seed_default_categories(admin_id):
    """Seed default categories from the original hardcoded list."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if categories already exist
    cursor.execute("SELECT COUNT(*) FROM request_categories")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return
    
    default_categories = [
        ('IT Support', 'Technical issues, software, hardware, network problems'),
        ('Facilities', 'Building maintenance, cleaning, repairs'),
        ('Academic', 'Course-related issues, registration, scheduling'),
        ('Administrative', 'Documentation, certificates, general inquiries'),
        ('Financial', 'Fees, payments, refunds, financial aid'),
        ('Other', 'Requests that do not fit other categories')
    ]
    
    for name, description in default_categories:
        cursor.execute('''
            INSERT INTO request_categories (name, description, is_active, created_by)
            VALUES (?, ?, 1, ?)
        ''', (name, description, admin_id))
    
    conn.commit()
    conn.close()
    print("Default categories seeded.")


def migrate_existing_requests():
    """Migrate existing requests to use category_id."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if category_id column exists
    cursor.execute("PRAGMA table_info(service_requests)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'category_id' not in columns:
        conn.close()
        return
    
    # Get all categories
    cursor.execute("SELECT category_id, name FROM request_categories")
    categories = {row['name'].lower(): row['category_id'] for row in cursor.fetchall()}
    
    if not categories:
        conn.close()
        return
    
    # Update requests without category_id
    cursor.execute('''
        SELECT request_id, category FROM service_requests 
        WHERE category_id IS NULL
    ''')
    requests = cursor.fetchall()
    
    migrated = 0
    for req in requests:
        cat_name = req['category'].lower()
        cat_id = categories.get(cat_name)
        if cat_id:
            cursor.execute('''
                UPDATE service_requests SET category_id = ? WHERE request_id = ?
            ''', (cat_id, req['request_id']))
            migrated += 1
    
    conn.commit()
    conn.close()
    
    if migrated:
        print(f"Migrated {migrated} existing requests to use category_id.")


def create_default_admin():
    """
    Create a default admin user if none exists.
    NOTE: Default credentials are for development/demo only 
    and must be changed in production.
    """
    from werkzeug.security import generate_password_hash
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if admin exists
    cursor.execute("SELECT user_id FROM users WHERE role = 'ADMIN' LIMIT 1")
    admin = cursor.fetchone()
    
    if admin is None:
        # Create default admin
        hashed_password = generate_password_hash('admin123')
        cursor.execute('''
            INSERT INTO users (name, email, password, role)
            VALUES (?, ?, ?, ?)
        ''', ('System Admin', 'admin@servicedesk.com', hashed_password, 'ADMIN'))
        conn.commit()
        admin_id = cursor.lastrowid
        print("Default admin created: admin@servicedesk.com / admin123")
        print("  [!] Change default credentials in production!")
    else:
        admin_id = admin['user_id']
    
    conn.close()
    return admin_id


if __name__ == '__main__':
    init_db()
    admin_id = create_default_admin()
    seed_default_categories(admin_id)
    migrate_existing_requests()
