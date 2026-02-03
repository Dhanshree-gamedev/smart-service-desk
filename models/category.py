"""
Category model for admin-managed request categories.
"""
from database import get_db_connection


class Category:
    """Represents a service request category."""
    
    def __init__(self, category_id, name, description, is_active, created_by, created_at):
        self.category_id = category_id
        self.name = name
        self.description = description
        self.is_active = bool(is_active)
        self.created_by = created_by
        self.created_at = created_at
    
    @staticmethod
    def from_row(row):
        """Create a Category instance from a database row."""
        if row is None:
            return None
        return Category(
            category_id=row['category_id'],
            name=row['name'],
            description=row['description'],
            is_active=row['is_active'],
            created_by=row['created_by'],
            created_at=row['created_at']
        )
    
    @staticmethod
    def get_all():
        """Get all categories (for admin management)."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT c.*, u.name as creator_name
            FROM request_categories c
            LEFT JOIN users u ON c.created_by = u.user_id
            ORDER BY c.name
        ''')
        rows = cursor.fetchall()
        conn.close()
        
        categories = []
        for row in rows:
            cat = Category.from_row(row)
            cat.creator_name = row['creator_name']
            categories.append(cat)
        return categories
    
    @staticmethod
    def get_active():
        """Get only active categories (for user dropdown)."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM request_categories 
            WHERE is_active = 1 
            ORDER BY name
        ''')
        rows = cursor.fetchall()
        conn.close()
        return [Category.from_row(row) for row in rows]
    
    @staticmethod
    def get_by_id(category_id):
        """Get a category by ID."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM request_categories WHERE category_id = ?', (category_id,))
        row = cursor.fetchone()
        conn.close()
        return Category.from_row(row)
    
    @staticmethod
    def get_by_name(name):
        """Get a category by name (case-insensitive)."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM request_categories WHERE name = ? COLLATE NOCASE', (name,))
        row = cursor.fetchone()
        conn.close()
        return Category.from_row(row)
    
    @staticmethod
    def name_exists(name, exclude_id=None):
        """Check if a category name already exists."""
        conn = get_db_connection()
        cursor = conn.cursor()
        if exclude_id:
            cursor.execute('''
                SELECT category_id FROM request_categories 
                WHERE name = ? COLLATE NOCASE AND category_id != ?
            ''', (name, exclude_id))
        else:
            cursor.execute('''
                SELECT category_id FROM request_categories 
                WHERE name = ? COLLATE NOCASE
            ''', (name,))
        exists = cursor.fetchone() is not None
        conn.close()
        return exists
    
    @staticmethod
    def create(name, description, created_by):
        """Create a new category."""
        if Category.name_exists(name):
            raise ValueError(f"Category '{name}' already exists.")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO request_categories (name, description, is_active, created_by)
            VALUES (?, ?, 1, ?)
        ''', (name.strip(), description.strip() if description else None, created_by))
        conn.commit()
        category_id = cursor.lastrowid
        conn.close()
        
        return Category.get_by_id(category_id)
    
    def update(self, name, description):
        """Update category name and description."""
        if Category.name_exists(name, exclude_id=self.category_id):
            raise ValueError(f"Category '{name}' already exists.")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE request_categories 
            SET name = ?, description = ?
            WHERE category_id = ?
        ''', (name.strip(), description.strip() if description else None, self.category_id))
        conn.commit()
        conn.close()
        
        self.name = name.strip()
        self.description = description.strip() if description else None
    
    def toggle_active(self):
        """Toggle the active status of a category."""
        new_status = 0 if self.is_active else 1
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE request_categories SET is_active = ? WHERE category_id = ?
        ''', (new_status, self.category_id))
        conn.commit()
        conn.close()
        
        self.is_active = bool(new_status)
    
    def get_usage_count(self):
        """Get number of requests using this category."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) FROM service_requests WHERE category_id = ?
        ''', (self.category_id,))
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    def can_delete(self):
        """Check if category can be deleted (no requests using it)."""
        return self.get_usage_count() == 0
    
    def delete(self):
        """Delete the category if not in use."""
        if not self.can_delete():
            raise ValueError("Cannot delete category that is in use. Deactivate instead.")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM request_categories WHERE category_id = ?', (self.category_id,))
        conn.commit()
        conn.close()
