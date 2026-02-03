"""
User routes: dashboard, create request, track requests, submit feedback.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models.request import ServiceRequest, RequestStatusLog, PRIORITY_LEVELS, DEFAULT_PRIORITY
from models.category import Category
from models.feedback import Feedback
from routes import role_required
from config import config

user_bp = Blueprint('user', __name__, url_prefix='/user')


@user_bp.route('/dashboard')
@login_required
@role_required('USER')
def dashboard():
    """User dashboard with overview."""
    stats = ServiceRequest.get_user_stats(current_user.user_id)
    
    # Get recent requests (last 5)
    recent_requests = ServiceRequest.get_by_user(current_user.user_id)[:5]
    
    return render_template('user/dashboard.html', 
                           stats=stats, 
                           recent_requests=recent_requests)


@user_bp.route('/new-request', methods=['GET', 'POST'])
@login_required
@role_required('USER')
def new_request():
    """Create a new service request."""
    # Get active categories from database
    categories = Category.get_active()
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        category_id = request.form.get('category_id', '').strip()
        priority = request.form.get('priority', DEFAULT_PRIORITY).strip()
        
        # Validation
        errors = []
        
        if not title or len(title) < 5:
            errors.append('Title must be at least 5 characters.')
        
        if not description or len(description) < 10:
            errors.append('Description must be at least 10 characters.')
        
        if not category_id:
            errors.append('Please select a category.')
        
        try:
            category_id = int(category_id)
        except (ValueError, TypeError):
            errors.append('Please select a valid category.')
            category_id = None
        
        if priority not in PRIORITY_LEVELS:
            priority = DEFAULT_PRIORITY
        
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('user/new_request.html', 
                                   categories=categories,
                                   priority_levels=PRIORITY_LEVELS,
                                   title=title,
                                   description=description,
                                   category_id=category_id,
                                   priority=priority)
        
        # Create the request
        try:
            service_request = ServiceRequest.create(
                user_id=current_user.user_id,
                title=title,
                description=description,
                category_id=category_id,
                priority=priority
            )
            flash(f'Request #{service_request.request_id} created successfully!', 'success')
            return redirect(url_for('user.request_detail', request_id=service_request.request_id))
        except ValueError as e:
            flash(str(e), 'danger')
        except Exception as e:
            flash('An error occurred while creating your request.', 'danger')
    
    return render_template('user/new_request.html', 
                           categories=categories,
                           priority_levels=PRIORITY_LEVELS)


@user_bp.route('/my-requests')
@login_required
@role_required('USER')
def my_requests():
    """View all user's requests."""
    status_filter = request.args.get('status', None)
    
    valid_statuses = [config.STATUS_SUBMITTED, config.STATUS_IN_PROGRESS, config.STATUS_RESOLVED]
    if status_filter and status_filter not in valid_statuses:
        status_filter = None
    
    requests_list = ServiceRequest.get_by_user(current_user.user_id, status_filter)
    
    return render_template('user/my_requests.html', 
                           requests=requests_list,
                           status_filter=status_filter,
                           statuses=valid_statuses)


@user_bp.route('/request/<int:request_id>')
@login_required
@role_required('USER')
def request_detail(request_id):
    """View request details with timeline and feedback option."""
    service_request = ServiceRequest.get_by_id(request_id)
    
    if not service_request:
        flash('Request not found.', 'danger')
        return redirect(url_for('user.my_requests'))
    
    # Ensure user can only view their own requests
    if service_request.user_id != current_user.user_id:
        flash('You do not have permission to view this request.', 'danger')
        return redirect(url_for('user.my_requests'))
    
    # Get status history
    status_logs = RequestStatusLog.get_by_request(request_id)
    
    # Get existing feedback if any
    feedback = Feedback.get_by_request(request_id)
    
    # Determine if feedback can be submitted
    can_submit_feedback = (
        service_request.status == config.STATUS_RESOLVED and 
        feedback is None
    )
    
    return render_template('user/request_detail.html',
                           request=service_request,
                           status_logs=status_logs,
                           feedback=feedback,
                           can_submit_feedback=can_submit_feedback,
                           statuses=[config.STATUS_SUBMITTED,
                                    config.STATUS_IN_PROGRESS,
                                    config.STATUS_RESOLVED])


@user_bp.route('/request/<int:request_id>/feedback', methods=['POST'])
@login_required
@role_required('USER')
def submit_feedback(request_id):
    """Submit feedback for a resolved request."""
    service_request = ServiceRequest.get_by_id(request_id)
    
    if not service_request:
        flash('Request not found.', 'danger')
        return redirect(url_for('user.my_requests'))
    
    # Ensure user can only submit feedback for their own requests
    if service_request.user_id != current_user.user_id:
        flash('You do not have permission to submit feedback for this request.', 'danger')
        return redirect(url_for('user.my_requests'))
    
    rating = request.form.get('rating', '').strip()
    comment = request.form.get('comment', '').strip()
    
    # Validate rating
    try:
        rating = int(rating)
    except (ValueError, TypeError):
        flash('Please select a rating.', 'warning')
        return redirect(url_for('user.request_detail', request_id=request_id))
    
    try:
        Feedback.create(
            request_id=request_id,
            user_id=current_user.user_id,
            rating=rating,
            comment=comment
        )
        flash('Thank you for your feedback!', 'success')
    except ValueError as e:
        flash(str(e), 'danger')
    except Exception as e:
        flash('An error occurred while submitting feedback.', 'danger')
    
    return redirect(url_for('user.request_detail', request_id=request_id))
