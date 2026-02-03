"""
Feedback model for user satisfaction ratings on resolved requests.
"""
from database import get_db_connection


class Feedback:
    """Represents user feedback for a resolved service request."""
    
    def __init__(self, feedback_id, request_id, user_id, rating, comment, submitted_at):
        self.feedback_id = feedback_id
        self.request_id = request_id
        self.user_id = user_id
        self.rating = rating
        self.comment = comment
        self.submitted_at = submitted_at
    
    @staticmethod
    def from_row(row):
        """Create a Feedback instance from a database row."""
        if row is None:
            return None
        return Feedback(
            feedback_id=row['feedback_id'],
            request_id=row['request_id'],
            user_id=row['user_id'],
            rating=row['rating'],
            comment=row['comment'],
            submitted_at=row['submitted_at']
        )
    
    @staticmethod
    def get_by_request(request_id):
        """Get feedback for a specific request."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM request_feedback WHERE request_id = ?', (request_id,))
        row = cursor.fetchone()
        conn.close()
        return Feedback.from_row(row)
    
    @staticmethod
    def exists_for_request(request_id):
        """Check if feedback already exists for a request."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT feedback_id FROM request_feedback WHERE request_id = ?', (request_id,))
        exists = cursor.fetchone() is not None
        conn.close()
        return exists
    
    @staticmethod
    def create(request_id, user_id, rating, comment=None):
        """
        Create feedback for a resolved request.
        Enforces one-feedback-per-request rule.
        """
        # Import here to avoid circular import
        from models.request import ServiceRequest
        from config import config
        
        # Verify request exists and is resolved
        request = ServiceRequest.get_by_id(request_id)
        if not request:
            raise ValueError("Request not found.")
        
        if request.status != config.STATUS_RESOLVED:
            raise ValueError("Feedback can only be submitted for resolved requests.")
        
        # Verify user owns the request
        if request.user_id != user_id:
            raise ValueError("You can only provide feedback for your own requests.")
        
        # Check if feedback already exists
        if Feedback.exists_for_request(request_id):
            raise ValueError("Feedback has already been submitted for this request.")
        
        # Validate rating
        if not isinstance(rating, int) or rating < 1 or rating > 5:
            raise ValueError("Rating must be between 1 and 5.")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO request_feedback (request_id, user_id, rating, comment)
            VALUES (?, ?, ?, ?)
        ''', (request_id, user_id, rating, comment.strip() if comment else None))
        conn.commit()
        feedback_id = cursor.lastrowid
        conn.close()
        
        return Feedback.get_by_id(feedback_id)
    
    @staticmethod
    def get_by_id(feedback_id):
        """Get feedback by ID."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM request_feedback WHERE feedback_id = ?', (feedback_id,))
        row = cursor.fetchone()
        conn.close()
        return Feedback.from_row(row)
    
    @staticmethod
    def get_all():
        """Get all feedback with request and user details (for admin view)."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT f.*, 
                   r.title as request_title, 
                   r.request_id,
                   u.name as user_name,
                   u.email as user_email
            FROM request_feedback f
            JOIN service_requests r ON f.request_id = r.request_id
            JOIN users u ON f.user_id = u.user_id
            ORDER BY f.submitted_at DESC
        ''')
        rows = cursor.fetchall()
        conn.close()
        
        feedbacks = []
        for row in rows:
            fb = Feedback.from_row(row)
            fb.request_title = row['request_title']
            fb.user_name = row['user_name']
            fb.user_email = row['user_email']
            feedbacks.append(fb)
        return feedbacks
    
    @staticmethod
    def get_stats():
        """Get feedback statistics."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) as total FROM request_feedback')
        total = cursor.fetchone()['total']
        
        cursor.execute('SELECT AVG(rating) as avg_rating FROM request_feedback')
        avg_row = cursor.fetchone()
        avg_rating = round(avg_row['avg_rating'], 2) if avg_row['avg_rating'] else 0
        
        cursor.execute('''
            SELECT rating, COUNT(*) as count 
            FROM request_feedback 
            GROUP BY rating 
            ORDER BY rating DESC
        ''')
        by_rating = {row['rating']: row['count'] for row in cursor.fetchall()}
        
        conn.close()
        
        return {
            'total': total,
            'average_rating': avg_rating,
            'by_rating': by_rating
        }
