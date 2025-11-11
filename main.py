from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, abort
from datetime import datetime
import json
import os 
from typing import Dict, List, Any
from feedback_manager import FeedbackManager


app = Flask(__name__)
app.secret_key= 'my-secret-key'

#memory management
guestbook_entries = []
user_history = []
feedback_entries = []

feedback_manager = FeedbackManager()

class GuestbookEntry:
    def __init__(self, name: str, message:str, email:str = None):
        self.id = len(guestbook_entries) + 1
        self.name = name.strip()
        self.message = message.strip()
        self.email = email.strip() if email else None 
        self.timestamp = datetime.now()
        self.ip_address = request.remote_addr
        self.user_agent = request.headers.get('User-Agent', 'Unknown')
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'message': self.message,
            'email': self.email,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'ip_address': self.ip_address,
            'user_agent': self.user_agent
        }

class UserHistory:
    def __init__(self, action:str, details:str):
        self.timestamp = datetime.now()
        self.action = action
        self.details = details
        self.ip_address = request.remote_addr
        self.user_agent = request.headers.get('User-Agent', 'Unknown')

    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'action': self.action,
            'details': self.details,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent
        }
    

def log_user_history(action: str, details: str):
    """ LOG user actions to history """
    history_entry = UserHistory(action, details)
    user_history.append(history_entry)
    #Keep only last 100 entries
    if len(user_history) > 100:
        user_history.pop(0)

class FeedbackEntry:
    def __init__(self, name: str, email:str, subject: str, message:str, feedback_type: str = 'general'):
        self.id = len(feedback_entries) +1
        self.name = name.strip()
        self.email = email.strip()
        self.subject = subject.strip()
        self.message = message.strip()
        self.feedback_type = feedback_type #general, bug etc.
        self.timestamp = datetime.now()
        self.ip_address = request.remote_addr
        self.user_agent = request.headers.get('User-Agent', 'Unknown')
        self.status = 'new' 
        self.priority = 'medium'
        self.admin_notes = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'subject': self.subject,
            'message': self.message,
            'feedback_type': self.feedback_type,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'status': self.status,
            'priority': self.priority,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'admin_notes': self.admin_notes 
        }

@app.route('/')
def index():
    """Home page"""
    log_user_history('PAGE_VISIT', 'Visited home page')
    return render_template('index.html', 
                         total_entries=len(guestbook_entries),
                         total_visits=len([h for h in user_history if h.action == 'PAGE_VISIT']),
                         feedback_count=len(feedback_entries))

@app.route('/guestbook', methods=['GET', 'POST'])
def guestbook():
    """Guestbook main page - view entries and add new ones"""
    if request.method == 'POST':
        return handle_post_entry()
    
    # GET request - show guestbook entries
    log_user_history('PAGE_VISIT', 'Viewed guestbook')
    return render_template('guestbook.html', entries=guestbook_entries)

def handle_post_entry():
    """Handle POST request for new guestbook entry"""
    try:
        # Validate required fields
        name = request.form.get('name', '').strip()
        message = request.form.get('message', '').strip()
        email = request.form.get('email', '').strip()
        
        # Validation
        if not name:
            flash('Name is required!', 'error')
            return redirect(url_for('guestbook'))
        
        if not message:
            flash('Message is required!', 'error')
            return redirect(url_for('guestbook'))
        
        if len(name) > 50:
            flash('Name must be less than 50 characters!', 'error')
            return redirect(url_for('guestbook'))
        
        if len(message) > 500:
            flash('Message must be less than 500 characters!', 'error')
            return redirect(url_for('guestbook'))
        
        if email and len(email) > 100:
            flash('Email must be less than 100 characters!', 'error')
            return redirect(url_for('guestbook'))
        
        # Create new entry
        new_entry = GuestbookEntry(name, message, email)
        guestbook_entries.append(new_entry)
        
        # Log the action
        log_user_history('NEW_ENTRY', f'Added guestbook entry: {name}')
        
        flash('Thank you for signing our guestbook!', 'success')
        return redirect(url_for('guestbook'))
        
    except Exception as e:
        app.logger.error(f"Error adding guestbook entry: {str(e)}")
        flash('An error occurred while adding your entry. Please try again.', 'error')
        return redirect(url_for('guestbook'))

@app.route('/guestbook/delete/<int:entry_id>', methods=['POST'])
def delete_entry(entry_id: int):
    """Delete a guestbook entry (admin function)"""
    try:
        # In a real app, you'd have proper authentication
        global guestbook_entries
        
        entry_to_delete = next((entry for entry in guestbook_entries if entry.id == entry_id), None)
        
        if not entry_to_delete:
            flash('Entry not found!', 'error')
            return redirect(url_for('guestbook'))
        
        guestbook_entries = [entry for entry in guestbook_entries if entry.id != entry_id]
        
        # Log the action
        log_user_history('DELETE_ENTRY', f'Deleted entry ID: {entry_id}')
        
        flash('Entry deleted successfully!', 'success')
        return redirect(url_for('guestbook'))
        
    except Exception as e:
        app.logger.error(f"Error deleting entry {entry_id}: {str(e)}")
        flash('An error occurred while deleting the entry.', 'error')
        return redirect(url_for('guestbook'))

@app.route('/history')
def view_history():
    """View user activity history"""
    log_user_history('PAGE_VISIT', 'Viewed user history')
    return render_template('history.html', history=user_history[-50:])  # Show last 50 entries

@app.route('/api/guestbook')
def api_guestbook():
    """JSON API endpoint for guestbook entries"""
    try:
        entries_data = [entry.to_dict() for entry in guestbook_entries]
        return jsonify({
            'status': 'success',
            'count': len(entries_data),
            'entries': entries_data
        })
    except Exception as e:
        app.logger.error(f"API error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Internal server error'
        }), 500

@app.route('/api/history')
def api_history():
    """JSON API endpoint for user history"""
    try:
        history_data = [history.to_dict() for history in user_history]
        return jsonify({
            'status': 'success',
            'count': len(history_data),
            'history': history_data
        })
    except Exception as e:
        app.logger.error(f"API error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Internal server error'
        }), 500

@app.route('/stats')
def stats():
    """Display statistics about the guestbook"""
    try:
        total_entries = len(guestbook_entries)
        total_history = len(user_history)
        page_visits = len([h for h in user_history if h.action == 'PAGE_VISIT'])
        new_entries = len([h for h in user_history if h.action == 'NEW_ENTRY'])
        
        # Get unique IP addresses
        unique_visitors = len(set(entry.ip_address for entry in guestbook_entries))
        
        stats_data = {
            'total_entries': total_entries,
            'total_history_events': total_history,
            'page_visits': page_visits,
            'guestbook_entries': new_entries,
            'unique_visitors': unique_visitors,
            'first_entry_date': guestbook_entries[0].timestamp.strftime('%Y-%m-%d') if guestbook_entries else 'No entries yet'
        }
        
        log_user_history('PAGE_VISIT', 'Viewed statistics')
        return render_template('stats.html', stats=stats_data)
        
    except Exception as e:
        app.logger.error(f"Stats error: {str(e)}")
        flash('Error loading statistics.', 'error')
        return redirect(url_for('index'))

# FEEDBACK SECTION | DETTA ÄR UPPGIFT 1 IMPLEMENTERING, TITTA REFERENS TILL UPPGIFT I CLASSROOM PÅ WEBBSERVERPROGRAMMERING 1

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    """ Main page for feedback - view & submit and/or delete """
    if request.method == 'POST':
        return handle_feedback_submission()

    #GET request 
    log_user_history('PAGE_VISIT', 'Viewed feedback page')
    return render_template('feedback.html')

@app.route('/feedback/submit', methods=['POST'])
def submit_feedback():
    """API ENDPOINT"""
    try:
        #Vi måste validera input fields 
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()
        feedback_type = request.form.get('type', 'general').strip()

        #Validering / bekräftning 
        validation_result = feedback_manager.validate_feedback(
            name, email, subject, message, feedback_type
        )
        if not validation_result['valid']:
            return jsonify({
                'status': 'error',
                'message': validation_result['message']
            }), 400
        
        can_proceed, wait_time = feedback_manager.check_rate_limit(request.remote_addr)
        if not can_proceed:
            return jsonify({
                'status': 'error',
                'message': f'Rate limit exceeded, wait {wait_time} seconds and try again. '
                }), 429
        
        new_feedback = FeedbackEntry(name, email, subject, message, feedback_type)

        #Analyze sentiments && decide priority order (check the feedback_manager.py)
        sentiment_result = feedback_manager.analyze_feedback_sentiment(message)
        new_feedback.priority = sentiment_result['suggested_priority']

        feedback_entries.append(new_feedback)

        #Send to the user log
        log_user_history('FEEDBACK_SUBMITTED', f'submitted feedback: {subject}')

        #Skicka en hypotetisk notis / pseudo notis 

        feedback_manager.notify_new_feedback(new_feedback)

        return jsonify({
            'status': 'success',
            'message': 'Thank you for your feedback. Felix will review it soon!',
            'feedback_id': new_feedback.id 
        })
    except Exception as e:
        app.logger.error(f"Error submitting feedback: {str(e)} ")
        return jsonify({
            'status': 'error',
            'message': 'Error occured! Try again' 
        }), 500

@app.route('/feedback/thank-you')
def feedback_thank_you():
    feedback_id = request.args.get('id')
    log_user_history('PAGE_VISIT', 'Viewed feedback thank-you section')
    return render_template('feedback_thank_you.html', feedback_id=feedback_id)

@app.route('/feedback/admin', methods=['GET'])
def feedback_admin():
    log_user_history('PAGE_VISIT', 'Accessed admin panel')

    #filters 
    status_filter = request.args.get('status', 'all')
    type_filter = request.args.get('type', 'all')
    priority_filter = request.args.get('priority', 'all')

    #filter 2
    filtered_feedback = feedback_manager.filter_feedback(
        feedback_entries, status_filter, type_filter, priority_filter
    )

    stats = feedback_manager.get_feedback_stats(feedback_entries)

    return render_template('feedback_admin.html', feedback_entries=filtered_feedback, stats=stats,
                           filters={
                               'status': status_filter,
                               'type': type_filter,
                               'priority': priority_filter
                           })

@app.route('/feedback/admin/update/<int:feedback_id>', methods=['POST'])
def update_feedback_status(feedback_id):
    try:
        feedback_entry = next((f for f in feedback_entries if f.id == feedback_id), None)

        if not feedback_entry:
            return jsonify({
                'status': 'error',
                'message': 'Feedback not found'
            }), 404
        
        new_status = request.form.get('status')
        new_priority = request.form.get('priority')
        admin_notes = request.form.get('admin_notes', '')

        #Validation åter igen 
        valid_statuses = ['new', 'reviewed', 'in_progress', 'resolved', 'closed']
        valid_priorities = ['low', 'medium', 'high', 'critical']

        if new_status and new_status in valid_statuses:
            feedback_entry.status = new_status
        
        if new_priority and new_priority in valid_priorities:
            feedback_entry.priority = new_priority
        
        if admin_notes:
            feedback_entry.admin_notes = admin_notes.strip()

        #log 
        log_user_history('FEEDBACK_UPDATED', f'updates feedback ID: {feedback_id}')

        return jsonify({
            'status': 'success',
            'message': 'Feedback updated' 
        })
    except Exception as e:
        app.logger.error(f"Error updating feedback {feedback_id} : {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'An error occured while updating the feedback'
        }), 500

@app.route('/api/feedback')
def api_feedback():
    try:
        feedback_data = [entry.to_dict() for entry in feedback_entries]

        return jsonify({
            'status': 'success',
            'count': len(feedback_data),
            'feedback': feedback_data
        })
    except Exception as e:
        app.logger.error(f"API error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Internal error'
        }), 500

@app.route('/api/feedback/stats')
def api_feedback_stats():
    """JSON API endpoint for feedback statistics"""
    try:
        stats = feedback_manager.get_feedback_stats(feedback_entries)
        
        return jsonify({
            'status': 'success',
            'stats': stats
        })
    except Exception as e:
        app.logger.error(f"API error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Internal server error'
        }), 500

def handle_feedback_submission():
    """Handle POST request for new feedback (form submission)"""
    try:
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()
        feedback_type = request.form.get('type', 'general').strip()
        
        # Validation
        validation_result = feedback_manager.validate_feedback(
            name, email, subject, message, feedback_type
        )
        
        if not validation_result['valid']:
            flash(validation_result['message'], 'error')
            return redirect(url_for('feedback'))
        
        # Check rate limiting
        can_proceed, wait_time = feedback_manager.check_rate_limit(request.remote_addr)
        if not can_proceed:
            flash(f'Rate limit exceeded. Please try again in {wait_time} seconds.', 'error')
            return redirect(url_for('feedback'))
        
        # Create new feedback entry
        new_feedback = FeedbackEntry(name, email, subject, message, feedback_type)
        
        # Analyze sentiment and set priority
        sentiment_result = feedback_manager.analyze_feedback_sentiment(message)
        new_feedback.priority = sentiment_result['suggested_priority']
        
        feedback_entries.append(new_feedback)
        
        # Log the action
        log_user_history('FEEDBACK_SUBMITTED', f'Submitted feedback: {subject}')
        
        # Send notification
        feedback_manager.notify_new_feedback(new_feedback)
        
        flash('Thank you for your feedback! We will review it soon.', 'success')
        return redirect(url_for('feedback_thank_you', id=new_feedback.id))
        
    except Exception as e:
        app.logger.error(f"Error submitting feedback: {str(e)}")
        flash('An error occurred while submitting your feedback. Please try again.', 'error')
        return redirect(url_for('feedback'))


# Error Handlers
@app.errorhandler(404)
def not_found_error(error):
    log_user_history('ERROR', '404 Page Not Found')
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    log_user_history('ERROR', '500 Internal Server Error')
    return render_template('500.html'), 500

@app.errorhandler(403)
def forbidden_error(error):
    log_user_history('ERROR', '403 Forbidden')
    return render_template('error.html', error_code=403, error_message="Forbidden"), 403

@app.errorhandler(400)
def bad_request_error(error):
    log_user_history('ERROR', '400 Bad Request')
    return render_template('error.html', error_code=400, error_message="Bad Request"), 400

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
