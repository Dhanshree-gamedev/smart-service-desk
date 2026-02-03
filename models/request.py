"""
Service Request and Status Log models with lifecycle enforcement.
Includes priority levels and dynamic category support.
"""
from datetime import datetime
from database import get_db_connection
from config import config


# Priority levels for display
PRIORITY_LEVELS = ['Low', 'Medium', 'High', 'Critical']
DEFAULT_PRIORITY = 'Medium'


class ServiceRequest:
    """Service Request model with lifecycle management."""
    
    def __init__(self, request_id, user_id, title, description, category,
                 status, created_at, updated_at, user_name=None, user_email=None,
                 priority=None, category_id=None, category_name=None):
        self.request_id = request_id
        self.user_id = user_id
        self.title = title
        self.description = description
        self.category = category  # Legacy text field
        self.category_id = category_id
        self.category_name = category_name or category
        self.status = status
        self.priority = priority or DEFAULT_PRIORITY
        self.created_at = created_at
        self.updated_at = updated_at
        self.user_name = user_name
        self.user_email = user_email
    
    @property
    def is_resolved(self):
        """Check if request is in final resolved state."""
        return self.status == config.STATUS_RESOLVED
    
    @property
    def can_transition_to(self):
        """Get list of valid next statuses."""
        return config.VALID_TRANSITIONS.get(self.status, [])
    
    def can_update_to(self, new_status):
        """Check if transition to new_status is valid."""
        return new_status in self.can_transition_to
    
    @staticmethod
    def create(user_id, title, description, category_id, priority=None):
        """Create a new service request with category_id and priority."""
        from models.category import Category
        
        # Get category info
        category = Category.get_by_id(category_id)
        if not category:
            raise ValueError("Invalid category selected.")
        if not category.is_active:
            raise ValueError("Selected category is no longer available.")
        
        # Validate priority
        if priority and priority not in PRIORITY_LEVELS:
            priority = DEFAULT_PRIORITY
        elif not priority:
            priority = DEFAULT_PRIORITY
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute('''
            INSERT INTO service_requests 
            (user_id, title, description, category, category_id, priority, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, title, description, category.name, category_id, priority, 
              config.STATUS_SUBMITTED, now, now))
        
        request_id = cursor.lastrowid
        
        # Log the initial creation
        cursor.execute('''
            INSERT INTO request_status_log 
            (request_id, old_status, new_status, remark, updated_by, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (request_id, None, config.STATUS_SUBMITTED, 'Request created', user_id, now))
        
        conn.commit()
        conn.close()
        
        return ServiceRequest.get_by_id(request_id)
    
    @staticmethod
    def _from_row(row):
        """Create ServiceRequest from database row."""
        if row is None:
            return None
        
        # Helper to safely get optional columns from sqlite3.Row
        def safe_get(row, key, default=None):
            try:
                return row[key]
            except (IndexError, KeyError):
                return default
        
        return ServiceRequest(
            request_id=row['request_id'],
            user_id=row['user_id'],
            title=row['title'],
            description=row['description'],
            category=row['category'],
            status=row['status'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            user_name=safe_get(row, 'user_name'),
            user_email=safe_get(row, 'user_email'),
            priority=safe_get(row, 'priority'),
            category_id=safe_get(row, 'category_id'),
            category_name=safe_get(row, 'category_name') or row['category']
        )
    
    @staticmethod
    def get_by_id(request_id):
        """Get request by ID with user and category info."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT r.*, u.name as user_name, u.email as user_email,
                   c.name as category_name
            FROM service_requests r
            JOIN users u ON r.user_id = u.user_id
            LEFT JOIN request_categories c ON r.category_id = c.category_id
            WHERE r.request_id = ?
        ''', (request_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        return ServiceRequest._from_row(row)
    
    @staticmethod
    def get_by_user(user_id, status_filter=None):
        """Get all requests for a user."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT r.*, u.name as user_name, u.email as user_email,
                   c.name as category_name
            FROM service_requests r
            JOIN users u ON r.user_id = u.user_id
            LEFT JOIN request_categories c ON r.category_id = c.category_id
            WHERE r.user_id = ?
        '''
        params = [user_id]
        
        if status_filter:
            query += ' AND r.status = ?'
            params.append(status_filter)
        
        query += ' ORDER BY r.created_at DESC'
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [ServiceRequest._from_row(row) for row in rows]
    
    @staticmethod
    def get_all(status_filter=None, category_filter=None, priority_filter=None):
        """Get all requests (for admin) with optional filters."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT r.*, u.name as user_name, u.email as user_email,
                   c.name as category_name
            FROM service_requests r
            JOIN users u ON r.user_id = u.user_id
            LEFT JOIN request_categories c ON r.category_id = c.category_id
            WHERE 1=1
        '''
        params = []
        
        if status_filter:
            query += ' AND r.status = ?'
            params.append(status_filter)
        
        if category_filter:
            query += ' AND (r.category = ? OR c.name = ?)'
            params.extend([category_filter, category_filter])
        
        if priority_filter:
            query += ' AND r.priority = ?'
            params.append(priority_filter)
        
        query += ' ORDER BY r.created_at DESC'
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [ServiceRequest._from_row(row) for row in rows]
    
    @staticmethod
    def get_stats():
        """Get request statistics for dashboard."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        stats = {
            'total': 0,
            'submitted': 0,
            'in_progress': 0,
            'resolved': 0,
            'by_category': {},
            'by_priority': {}
        }
        
        # Count by status
        cursor.execute('''
            SELECT status, COUNT(*) as count
            FROM service_requests
            GROUP BY status
        ''')
        
        for row in cursor.fetchall():
            status = row['status']
            count = row['count']
            stats['total'] += count
            
            if status == config.STATUS_SUBMITTED:
                stats['submitted'] = count
            elif status == config.STATUS_IN_PROGRESS:
                stats['in_progress'] = count
            elif status == config.STATUS_RESOLVED:
                stats['resolved'] = count
        
        # Count by category
        cursor.execute('''
            SELECT COALESCE(c.name, r.category) as cat_name, COUNT(*) as count
            FROM service_requests r
            LEFT JOIN request_categories c ON r.category_id = c.category_id
            GROUP BY cat_name
        ''')
        
        for row in cursor.fetchall():
            stats['by_category'][row['cat_name']] = row['count']
        
        # Count by priority
        cursor.execute('''
            SELECT priority, COUNT(*) as count
            FROM service_requests
            GROUP BY priority
        ''')
        
        for row in cursor.fetchall():
            if row['priority']:
                stats['by_priority'][row['priority']] = row['count']
        
        conn.close()
        return stats
    
    @staticmethod
    def get_user_stats(user_id):
        """Get request statistics for a specific user."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        stats = {
            'total': 0,
            'submitted': 0,
            'in_progress': 0,
            'resolved': 0
        }
        
        cursor.execute('''
            SELECT status, COUNT(*) as count
            FROM service_requests
            WHERE user_id = ?
            GROUP BY status
        ''', (user_id,))
        
        for row in cursor.fetchall():
            status = row['status']
            count = row['count']
            stats['total'] += count
            
            if status == config.STATUS_SUBMITTED:
                stats['submitted'] = count
            elif status == config.STATUS_IN_PROGRESS:
                stats['in_progress'] = count
            elif status == config.STATUS_RESOLVED:
                stats['resolved'] = count
        
        conn.close()
        return stats
    
    def update_status(self, new_status, remark, updated_by):
        """Update request status with audit logging."""
        if not self.can_update_to(new_status):
            raise ValueError(
                f"Invalid status transition: {self.status} -> {new_status}"
            )
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        old_status = self.status
        
        # Update the request
        cursor.execute('''
            UPDATE service_requests
            SET status = ?, updated_at = ?
            WHERE request_id = ?
        ''', (new_status, now, self.request_id))
        
        # Log the status change
        cursor.execute('''
            INSERT INTO request_status_log 
            (request_id, old_status, new_status, remark, updated_by, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (self.request_id, old_status, new_status, remark, updated_by, now))
        
        conn.commit()
        conn.close()
        
        # Update instance
        self.status = new_status
        self.updated_at = now
        
        return True
    
    def update_priority(self, new_priority, updated_by):
        """Update request priority (admin only, not allowed if resolved)."""
        if self.is_resolved:
            raise ValueError("Cannot change priority of a resolved request.")
        
        if new_priority not in PRIORITY_LEVELS:
            raise ValueError(f"Invalid priority. Must be one of: {PRIORITY_LEVELS}")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        old_priority = self.priority
        
        cursor.execute('''
            UPDATE service_requests
            SET priority = ?, updated_at = ?
            WHERE request_id = ?
        ''', (new_priority, now, self.request_id))
        
        # Log the priority change
        cursor.execute('''
            INSERT INTO request_status_log 
            (request_id, old_status, new_status, remark, updated_by, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (self.request_id, self.status, self.status, 
              f'Priority changed from {old_priority} to {new_priority}', updated_by, now))
        
        conn.commit()
        conn.close()
        
        self.priority = new_priority
        self.updated_at = now
        
        return True
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'request_id': self.request_id,
            'user_id': self.user_id,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'category_id': self.category_id,
            'category_name': self.category_name,
            'priority': self.priority,
            'status': self.status,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'user_name': self.user_name,
            'user_email': self.user_email
        }


class RequestStatusLog:
    """Request Status Log model for audit trail."""
    
    def __init__(self, log_id, request_id, old_status, new_status, 
                 remark, updated_by, updated_at, admin_name=None):
        self.log_id = log_id
        self.request_id = request_id
        self.old_status = old_status
        self.new_status = new_status
        self.remark = remark
        self.updated_by = updated_by
        self.updated_at = updated_at
        self.admin_name = admin_name
    
    @staticmethod
    def get_by_request(request_id):
        """Get all status logs for a request."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT l.*, u.name as admin_name
            FROM request_status_log l
            JOIN users u ON l.updated_by = u.user_id
            WHERE l.request_id = ?
            ORDER BY l.updated_at ASC
        ''', (request_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [RequestStatusLog(
            log_id=row['log_id'],
            request_id=row['request_id'],
            old_status=row['old_status'],
            new_status=row['new_status'],
            remark=row['remark'],
            updated_by=row['updated_by'],
            updated_at=row['updated_at'],
            admin_name=row['admin_name']
        ) for row in rows]
    
    @staticmethod
    def get_recent(limit=10):
        """Get recent status updates (for admin dashboard)."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT l.*, u.name as admin_name, r.title as request_title
            FROM request_status_log l
            JOIN users u ON l.updated_by = u.user_id
            JOIN service_requests r ON l.request_id = r.request_id
            ORDER BY l.updated_at DESC
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        logs = []
        for row in rows:
            log = RequestStatusLog(
                log_id=row['log_id'],
                request_id=row['request_id'],
                old_status=row['old_status'],
                new_status=row['new_status'],
                remark=row['remark'],
                updated_by=row['updated_by'],
                updated_at=row['updated_at'],
                admin_name=row['admin_name']
            )
            log.request_title = row['request_title']
            logs.append(log)
        return logs
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'log_id': self.log_id,
            'request_id': self.request_id,
            'old_status': self.old_status,
            'new_status': self.new_status,
            'remark': self.remark,
            'updated_by': self.updated_by,
            'updated_at': self.updated_at,
            'admin_name': self.admin_name
        }
