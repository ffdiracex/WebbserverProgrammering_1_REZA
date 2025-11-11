// Advanced Feedback Management
class FeedbackManager {
    constructor() {
        this.form = document.getElementById('feedbackForm');
        this.messageTextarea = document.getElementById('message');
        this.charCount = document.getElementById('charCount');
        this.sentimentIndicator = document.getElementById('sentimentIndicator');
        this.submitBtn = document.getElementById('submitBtn');
        
        this.init();
    }

    init() {
        if (this.form) {
            this.setupEventListeners();
            this.setupRealTimeValidation();
            this.setupSentimentAnalysis();
        }
    }

    setupEventListeners() {
        // Character count
        if (this.messageTextarea && this.charCount) {
            this.messageTextarea.addEventListener('input', () => {
                this.updateCharCount();
                this.analyzeSentiment();
            });
        }

        // Form submission
        this.form.addEventListener('submit', (e) => {
            this.handleSubmit(e);
        });

        // Real-time validation
        const inputs = this.form.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            input.addEventListener('blur', () => {
                this.validateField(input);
            });
        });
    }

    setupRealTimeValidation() {
        // Add real-time validation indicators
        const fields = this.form.querySelectorAll('input[required], textarea[required], select[required]');
        fields.forEach(field => {
            field.addEventListener('input', () => {
                this.updateFieldStatus(field);
            });
        });
    }

    setupSentimentAnalysis() {
        // Initialize sentiment analysis on message field
        if (this.messageTextarea) {
            let analysisTimeout;
            this.messageTextarea.addEventListener('input', () => {
                clearTimeout(analysisTimeout);
                analysisTimeout = setTimeout(() => {
                    this.analyzeSentiment();
                }, 1000);
            });
        }
    }

    updateCharCount() {
        if (this.messageTextarea && this.charCount) {
            const length = this.messageTextarea.value.length;
            this.charCount.textContent = length;
            
            // Update color based on length
            if (length > 1800) {
                this.charCount.style.color = '#e74c3c';
            } else if (length > 1500) {
                this.charCount.style.color = '#f39c12';
            } else {
                this.charCount.style.color = '#666';
            }
        }
    }

    analyzeSentiment() {
        if (!this.messageTextarea || !this.sentimentIndicator) return;

        const text = this.messageTextarea.value;
        if (text.length < 10) {
            this.sentimentIndicator.textContent = '';
            this.sentimentIndicator.className = 'sentiment-indicator';
            return;
        }

        // Simple sentiment analysis (in real app, this would call an API)
        const sentiment = this.calculateSentiment(text);
        
        this.sentimentIndicator.textContent = sentiment.emoji + ' ' + sentiment.text;
        this.sentimentIndicator.className = `sentiment-indicator sentiment-${sentiment.type}`;
    }

    calculateSentiment(text) {
        const positiveWords = ['great', 'excellent', 'amazing', 'wonderful', 'awesome', 'love', 'good', 'nice', 'perfect', 'thanks'];
        const negativeWords = ['bad', 'terrible', 'awful', 'horrible', 'worst', 'hate', 'broken', 'slow', 'difficult', 'problem'];
        const urgentWords = ['urgent', 'emergency', 'critical', 'broken', 'not working', 'failed', 'error'];

        const words = text.toLowerCase().split(/\s+/);
        let positive = 0;
        let negative = 0;
        let urgent = 0;

        words.forEach(word => {
            if (positiveWords.includes(word)) positive++;
            if (negativeWords.includes(word)) negative++;
            if (urgentWords.includes(word)) urgent++;
        });

        if (urgent > 0) {
            return { type: 'urgent', emoji: '🚨', text: 'Urgent' };
        } else if (positive > negative) {
            return { type: 'positive', emoji: '😊', text: 'Positive' };
        } else if (negative > positive) {
            return { type: 'negative', emoji: '😟', text: 'Needs Attention' };
        } else {
            return { type: 'neutral', emoji: '😐', text: 'Neutral' };
        }
    }

    validateField(field) {
        const value = field.value.trim();
        let isValid = true;
        let message = '';

        switch (field.name) {
            case 'name':
                if (!value) {
                    isValid = false;
                    message = 'Name is required';
                } else if (value.length > 100) {
                    isValid = false;
                    message = 'Name must be less than 100 characters';
                }
                break;

            case 'email':
                if (value && !this.isValidEmail(value)) {
                    isValid = false;
                    message = 'Please enter a valid email address';
                } else if (value.length > 255) {
                    isValid = false;
                    message = 'Email must be less than 255 characters';
                }
                break;

            case 'subject':
                if (!value) {
                    isValid = false;
                    message = 'Subject is required';
                } else if (value.length > 200) {
                    isValid = false;
                    message = 'Subject must be less than 200 characters';
                }
                break;

            case 'message':
                if (!value) {
                    isValid = false;
                    message = 'Message is required';
                } else if (value.length < 10) {
                    isValid = false;
                    message = 'Message must be at least 10 characters';
                } else if (value.length > 2000) {
                    isValid = false;
                    message = 'Message must be less than 2000 characters';
                }
                break;

            case 'type':
                if (!value) {
                    isValid = false;
                    message = 'Please select a feedback type';
                }
                break;
        }

        this.setFieldStatus(field, isValid, message);
        return isValid;
    }

    isValidEmail(email) {
        const pattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
        return pattern.test(email);
    }

    setFieldStatus(field, isValid, message) {
        // Remove existing status
        field.classList.remove('is-valid', 'is-invalid');
        field.classList.add(isValid ? 'is-valid' : 'is-invalid');

        // Remove existing feedback
        const existingFeedback = field.parentNode.querySelector('.invalid-feedback, .valid-feedback');
        if (existingFeedback) {
            existingFeedback.remove();
        }

        // Add new feedback
        if (message) {
            const feedback = document.createElement('div');
            feedback.className = isValid ? 'valid-feedback' : 'invalid-feedback';
            feedback.textContent = message;
            field.parentNode.appendChild(feedback);
        }
    }

    updateFieldStatus(field) {
        const value = field.value.trim();
        if (value.length > 0) {
            field.classList.add('is-touched');
        } else {
            field.classList.remove('is-touched');
        }
    }

    async handleSubmit(e) {
        e.preventDefault();

        // Validate all fields
        const fields = this.form.querySelectorAll('input[required], textarea[required], select[required]');
        let allValid = true;

        fields.forEach(field => {
            if (!this.validateField(field)) {
                allValid = false;
            }
        });

        if (!allValid) {
            this.showMessage('Please fix the errors above.', 'error');
            return;
        }

        // Disable submit button
        this.submitBtn.disabled = true;
        this.submitBtn.textContent = 'Submitting...';

        try {
            const formData = new FormData(this.form);
            
            const response = await fetch('/feedback/submit', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.status === 'success') {
                window.location.href = `/feedback/thank-you?id=${data.feedback_id}`;
            } else {
                this.showMessage(data.message, 'error');
                this.submitBtn.disabled = false;
                this.submitBtn.textContent = 'Submit Feedback';
            }

        } catch (error) {
            console.error('Error submitting feedback:', error);
            this.showMessage('An error occurred while submitting your feedback. Please try again.', 'error');
            this.submitBtn.disabled = false;
            this.submitBtn.textContent = 'Submit Feedback';
        }
    }

    showMessage(message, type) {
        // Remove existing messages
        const existingMessages = document.querySelectorAll('.form-message');
        existingMessages.forEach(msg => msg.remove());

        // Create new message
        const messageDiv = document.createElement('div');
        messageDiv.className = `form-message form-message-${type}`;
        messageDiv.textContent = message;

        // Insert before form
        this.form.parentNode.insertBefore(messageDiv, this.form);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            messageDiv.remove();
        }, 5000);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new FeedbackManager();
});

// Export for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FeedbackManager;
}
