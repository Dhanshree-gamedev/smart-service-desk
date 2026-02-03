"""
Smart Service Desk - Main Application Entry Point
A production-ready web-based service request management system.
"""
from flask import Flask, render_template, redirect, url_for
from flask_login import LoginManager, current_user
from flask_wtf.csrf import CSRFProtect

from config import config
from database import init_db, create_default_admin
from models.user import User
from routes.auth import auth_bp
from routes.user import user_bp
from routes.admin import admin_bp


def create_app():
    """Application factory pattern."""
    app = Flask(__name__)
    
    # Load configuration
    app.config['SECRET_KEY'] = config.SECRET_KEY
    app.config['WTF_CSRF_ENABLED'] = config.WTF_CSRF_ENABLED
    app.config['WTF_CSRF_TIME_LIMIT'] = config.WTF_CSRF_TIME_LIMIT
    
    # Initialize CSRF protection
    csrf = CSRFProtect(app)
    
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.get_by_id(int(user_id))
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(admin_bp)
    
    # Main routes
    @app.route('/')
    def landing():
        if current_user.is_authenticated:
            if current_user.is_admin:
                return redirect(url_for('admin.dashboard'))
            return redirect(url_for('user.dashboard'))
        return render_template('landing.html')
    
    # Create a blueprint for main routes
    @app.context_processor
    def inject_config():
        """Inject config into all templates."""
        return {
            'STATUS_SUBMITTED': config.STATUS_SUBMITTED,
            'STATUS_IN_PROGRESS': config.STATUS_IN_PROGRESS,
            'STATUS_RESOLVED': config.STATUS_RESOLVED,
            'CATEGORIES': config.CATEGORIES
        }
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(500)
    def server_error(e):
        return render_template('errors/500.html'), 500
    
    return app


# Create the application instance
app = create_app()


if __name__ == '__main__':
    # Initialize database
    init_db()
    create_default_admin()
    
    # Run the application
    print("\n" + "="*50)
    print("Smart Service Desk")
    print("="*50)
    print("Server running at: http://127.0.0.1:5000")
    print("Default Admin: admin@servicedesk.com / admin123")
    print("="*50 + "\n")
    
    app.run(debug=True, host='127.0.0.1', port=5000)
