"""
Admin routes: dashboard, request management, status updates, category management, feedback view.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models.request import ServiceRequest, RequestStatusLog, PRIORITY_LEVELS
from models.category import Category
from models.feedback import Feedback
from routes import admin_required
from config import config

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Admin dashboard with statistics."""
    stats = ServiceRequest.get_stats()
    feedback_stats = Feedback.get_stats()
    
    # Get recent requests (last 10)
    recent_requests = ServiceRequest.get_all()[:10]
    
    # Get categories for display
    categories = Category.get_all()
    
    return render_template('admin/dashboard.html',
                           stats=stats,
                           feedback_stats=feedback_stats,
                           recent_requests=recent_requests,
                           categories=categories,
                           priority_levels=PRIORITY_LEVELS)


@admin_bp.route('/requests')
@login_required
@admin_required
def all_requests():
    """View all requests with filters."""
    status_filter = request.args.get('status', None)
    category_filter = request.args.get('category', None)
    priority_filter = request.args.get('priority', None)
    
    # Validate status filter
    valid_statuses = [config.STATUS_SUBMITTED, config.STATUS_IN_PROGRESS, config.STATUS_RESOLVED]
    if status_filter and status_filter not in valid_statuses:
        status_filter = None
    
    # Validate priority filter
    if priority_filter and priority_filter not in PRIORITY_LEVELS:
        priority_filter = None
    
    requests_list = ServiceRequest.get_all(status_filter, category_filter, priority_filter)
    
    # Get categories from database
    categories = Category.get_all()
    category_names = [c.name for c in categories]
    
    return render_template('admin/all_requests.html',
                           requests=requests_list,
                           status_filter=status_filter,
                           category_filter=category_filter,
                           priority_filter=priority_filter,
                           statuses=valid_statuses,
                           categories=category_names,
                           priority_levels=PRIORITY_LEVELS)


@admin_bp.route('/request/<int:request_id>')
@login_required
@admin_required
def request_detail(request_id):
    """View request details with update option."""
    service_request = ServiceRequest.get_by_id(request_id)
    
    if not service_request:
        flash('Request not found.', 'danger')
        return redirect(url_for('admin.all_requests'))
    
    # Get status history
    status_logs = RequestStatusLog.get_by_request(request_id)
    
    # Get valid next statuses
    valid_transitions = service_request.can_transition_to
    
    # Get feedback if exists
    feedback = Feedback.get_by_request(request_id)
    
    return render_template('admin/request_detail.html',
                           request=service_request,
                           status_logs=status_logs,
                           valid_transitions=valid_transitions,
                           feedback=feedback,
                           priority_levels=PRIORITY_LEVELS,
                           statuses=[config.STATUS_SUBMITTED,
                                    config.STATUS_IN_PROGRESS,
                                    config.STATUS_RESOLVED])


@admin_bp.route('/request/<int:request_id>/update', methods=['POST'])
@login_required
@admin_required
def update_request(request_id):
    """Update request status."""
    service_request = ServiceRequest.get_by_id(request_id)
    
    if not service_request:
        flash('Request not found.', 'danger')
        return redirect(url_for('admin.all_requests'))
    
    new_status = request.form.get('status', '').strip()
    remark = request.form.get('remark', '').strip()
    
    # Validation
    if not new_status:
        flash('Please select a status.', 'warning')
        return redirect(url_for('admin.request_detail', request_id=request_id))
    
    if not remark:
        flash('Please add a remark explaining the status change.', 'warning')
        return redirect(url_for('admin.request_detail', request_id=request_id))
    
    # Check if transition is valid
    if not service_request.can_update_to(new_status):
        flash(f'Invalid status transition: {service_request.status} -> {new_status}', 'danger')
        return redirect(url_for('admin.request_detail', request_id=request_id))
    
    # Update the request
    try:
        service_request.update_status(new_status, remark, current_user.user_id)
        flash(f'Request #{request_id} updated to "{new_status}" successfully!', 'success')
    except Exception as e:
        flash(f'Error updating request: {str(e)}', 'danger')
    
    return redirect(url_for('admin.request_detail', request_id=request_id))


@admin_bp.route('/request/<int:request_id>/priority', methods=['POST'])
@login_required
@admin_required
def update_priority(request_id):
    """Update request priority."""
    service_request = ServiceRequest.get_by_id(request_id)
    
    if not service_request:
        flash('Request not found.', 'danger')
        return redirect(url_for('admin.all_requests'))
    
    new_priority = request.form.get('priority', '').strip()
    
    if not new_priority or new_priority not in PRIORITY_LEVELS:
        flash('Please select a valid priority level.', 'warning')
        return redirect(url_for('admin.request_detail', request_id=request_id))
    
    try:
        service_request.update_priority(new_priority, current_user.user_id)
        flash(f'Priority updated to "{new_priority}" successfully!', 'success')
    except ValueError as e:
        flash(str(e), 'danger')
    except Exception as e:
        flash(f'Error updating priority: {str(e)}', 'danger')
    
    return redirect(url_for('admin.request_detail', request_id=request_id))


# ============ CATEGORY MANAGEMENT ============

@admin_bp.route('/categories')
@login_required
@admin_required
def categories():
    """View and manage categories."""
    all_categories = Category.get_all()
    
    # Add usage count to each category
    for cat in all_categories:
        cat.usage_count = cat.get_usage_count()
    
    return render_template('admin/categories.html', categories=all_categories)


@admin_bp.route('/categories/add', methods=['POST'])
@login_required
@admin_required
def add_category():
    """Add a new category."""
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    
    if not name:
        flash('Category name is required.', 'warning')
        return redirect(url_for('admin.categories'))
    
    if len(name) < 2:
        flash('Category name must be at least 2 characters.', 'warning')
        return redirect(url_for('admin.categories'))
    
    try:
        Category.create(name, description, current_user.user_id)
        flash(f'Category "{name}" created successfully!', 'success')
    except ValueError as e:
        flash(str(e), 'danger')
    except Exception as e:
        flash(f'Error creating category: {str(e)}', 'danger')
    
    return redirect(url_for('admin.categories'))


@admin_bp.route('/categories/<int:category_id>/update', methods=['POST'])
@login_required
@admin_required
def update_category(category_id):
    """Update a category."""
    category = Category.get_by_id(category_id)
    
    if not category:
        flash('Category not found.', 'danger')
        return redirect(url_for('admin.categories'))
    
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    
    if not name:
        flash('Category name is required.', 'warning')
        return redirect(url_for('admin.categories'))
    
    try:
        category.update(name, description)
        flash(f'Category updated successfully!', 'success')
    except ValueError as e:
        flash(str(e), 'danger')
    except Exception as e:
        flash(f'Error updating category: {str(e)}', 'danger')
    
    return redirect(url_for('admin.categories'))


@admin_bp.route('/categories/<int:category_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_category(category_id):
    """Toggle category active status."""
    category = Category.get_by_id(category_id)
    
    if not category:
        flash('Category not found.', 'danger')
        return redirect(url_for('admin.categories'))
    
    try:
        category.toggle_active()
        status = 'activated' if category.is_active else 'deactivated'
        flash(f'Category "{category.name}" {status} successfully!', 'success')
    except Exception as e:
        flash(f'Error updating category: {str(e)}', 'danger')
    
    return redirect(url_for('admin.categories'))


# ============ FEEDBACK VIEW ============

@admin_bp.route('/feedback')
@login_required
@admin_required
def feedback():
    """View all user feedback."""
    all_feedback = Feedback.get_all()
    stats = Feedback.get_stats()
    
    return render_template('admin/feedback.html', 
                           feedbacks=all_feedback, 
                           stats=stats)
