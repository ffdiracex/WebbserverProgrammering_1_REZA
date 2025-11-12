#!/usr/bin/env python
import re
import time
from datetime import datetime, timedelta 
from collections import defaultdict, Counter 
from typing import Dict, List, Any, Tuple, Optional 
import smtplib
from email.mime.text import MIMEText 
from email.mime.multipart import MIMEMultipart
import json 

class FeedbackManager:
    def __init__(self):
        self.rate_limits = {}
        self.feedback_categories={
            'general': 'General Feedback',
            'bug': 'Bug Report',
            'feature': 'Feature Request',
            'suggestion': 'Suggestion',
            'complaint': 'Complaint',
            'praise': 'Praise'
        }

        self.positive_words = {
            'great', 'excellent', 'amazing', 'wonderful', 'awesome', 'fantastic',
            'love', 'like', 'good', 'nice', 'perfect', 'brilliant', 'outstanding',
            'impressive', 'helpful', 'useful', 'easy', 'smooth', 'fast', 'quick'
        }

        self.negative_words = {
            'bad', 'terrible', 'awful', 'horrible', 'worst', 'hate', 'dislike', 'broken', 'slow',
            'difficult', 'hard', 'complicated', 'frustrating', 'annoying', 'useless', 'poor',
            'disappointing', 'fails', 'crash', 'error', 'bug', 'issue', 'problem', 'doesn\'t work'
        }

        self.urgent_indicators = {
            'urgent', 'emergency', 'critical', 'asap', 'immidiately', 'now', 'broken', 'crash', 'error',
            'not working', 'failed', 'stop' 
                            }
        
        def validate_feedback(self, name: str, email:str, subject:str, message:str, feedback_type:str) -> Dict[str, Any]:
            """validate user feedback, like a complaint or if someone is very upset with my design """

            errors = []

            #Name validation
            if not name or len(name.strip()) == 0:
                errors.append("Name is required")
            elif len(name) > 100:
                errors.append("Name must be less than 100 characters !")
            
            #Email validation 
            if email and len(email) > 0:
                if not self.is_valid_email(email):
                    errors.append("Please enter a valid email")
                elif len(email) > 255:
                    errors.append("Email must be shorter than 255 characters!")
            
            #Subject validation 
            if not subject or len(subject.strip()) == 0:
                errors.append("Subject is required!")
            elif len(subject) > 200:
                errors.append("Subject can't exceed 200 characters!")
            
            #msg validation (msg = Message)
            if not message or len(message.strip()) == 0:
                errors.append("Message is required!")
            elif len(message) < 10:
                errors.append("Message must be at least 10 characters!")
            elif len(message) > 2000:
                errors.append("Wow too large! max 2000 characters, calm down bro!")
            
            #Feedback validation TYPE
            if feedback_type not in self.feedback_categories:
                errors.append("Invalid type of feedback!")
            
            #Spam control 
            if self.contains_spam_indicators(message):
                errors.append("Your message is likely spam!")
            
            return {
                'valid': len(errors) == 0,
                'message': ''.join(errors) if errors else 'Valid',
                'errors': errors
            }
        
        def is_valid_email(self, email:str) -> bool:
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$' #The author learns string parsing from perl (#!/usr/bin/env perl)
            return bool(re.match(pattern, email))
        
        def contains_spam_indicators(self, text:str) -> bool:
            spam_indicators = [
                r'http[s]?://', #URL , i.e. links, posts etc. 
                r'[0-9]{10,}', #Long number sequences such as phone numbers, addresses etc.
                r'[$\£][0-9]+', #money
                r'(?i)buy now|click here|limited time|offer|discount', #ads or sales 
                r'(?i)viagra|cialis|weed|meth|drugs', #Obvious 
                r'[!@#$%^&*()]{5,}', #wierd amount of symbols for a feedback
            ]

            for pattern in spam_indicators:
                if re.search(pattern, text, re.IGNORECASE):
                    return True #pattern MATCHED
            return False #no match
        
        def check_rate_limit(self, identifier: str, max_requests: int = 5, window_seconds: int = 3600) -> Tuple[bool, int]:
            now = time.time() 
            window_start = now - window_seconds

            if identifier not in self.rate_limits:
                self.rate_limits[identifier] = [] #empty array 
            
            self.rate_limits[identifier] = [
                timestamp for timestamp in self.rate_limits[identifier]
                if timestamp > window_start
            ]

            #check current / limit 
            if len(self.rate_limits[identifier]) >= max_requests:
                wait_time = int(window_seconds - (now - self.rate_limits[identifier][0]))
                return False, wait_time
            
            #add current request
            self.rate_limits[identifier].append(now)

            return True, max_requests - len(self.rate_limits[identifier])
        
        def analyze_feedback_sentiment(self, message:str) -> Dict[str, Any]:
            message_lower = message.lower()
            words = re.findall(r'\b\w+\b', message_lower)

            positive_count = sum(1 for word in words if word in self.positive_words)
            negative_count = sum(1 for word in words if word in self.negative_words)
            urgent_count = sum(1 for word in words if word in self.urgent_indicators)

            total_words = len(words)

            if total_words == 0:
                sentiment_score = 0
            else:
                sentiment_score = (positive_count - negative_count) / total_words

            #Determine sentiment
            if sentiment_score > 0.1:
                sentiment = 'positive'
            elif sentiment_score < -0.1:
                sentiment = 'negative'
            else:
                sentiment = 'neutral'
            
            if urgent_count > 0 or negative_count > total_words * 0.3:
                priority = 'high'
            elif negative_count > total_words * 0.1:
                priority = 'medium'
            else:
                priority = 'low'
            
            critical_phrases = [
                'not working', 'broken', 'crash', 'error', 'failed', 'urgent', 'emergency',
                'critical issue'
            ]

            for phrase in critical_phrases:
                if phrase in message_lower:
                    priority = 'critical'
                    break
            
            return {
                'sentiment': sentiment,
                'sentiment_score': sentiment_score,
                'positive_words': positive_count,
                'negative_words': negative_count,
                'urgent_indicators': urgent_count,
                'suggested_priority': priority,
                'word_count': total_words
            }
        

        def filter_feedback(self, feedback_entries: List, status: str = 'all', feedback_type: str = 'all', priority: str = 'all') -> List:
            filtered = feedback_entries.copy()
            if status != 'all':
                filtered = [f for f in filtered if f.status == status]
            
            if feedback_type != 'all':
                filtered = [f for f in filtered if f.feedback_type == feedback_type]

            if priority != 'all':
                filtered = [f for f in filtered if f.priority == priority]

            #sort after our will
            
            priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
            filtered.sort(key=lambda x: (priority_order.get(x.priority, 4), x.timestamp), reverse=True)
            return filtered
        
        def get_feedback_stats(self, feedback_entries: List) -> Dict[str, Any]:
            if not feedback_entries:
                return {
                    'total_feedback': 0,
                    'by_status': {},
                    'by_type': {},
                    'by_priority': {},
                    'response_rate': 0,
                    'average_response_time': 0
                }
            
            status_counts = Counter(entry.status for entry in feedback_entries)

            type_counts = Counter(entry.feedback_type for entry in feedback_entries)

            priority_counts = Counter(entry.priority for entry in feedback_entries)

            responded_count = sum(1 for entry in feedback_entries if entry.status in ['resolved', 'closed'])
            response_rate = (responded_count / len(feedback_entries)) * 100

            #history
            week_ago = datetime.now() - timedelta(days=7)
            recent_feedback = [f for f in feedback_entries if f.timestamp > week_ago]

            sentiments = []
            for entry in feedback_entries:
                sentiment_result = self.analyze_feedback_sentiment(entry.message)
                sentiments.append(sentiment_result['sentiment'])
            sentiments_count = Counter(sentiments)

            return {
                'total_feedback': len(feedback_entries),
                'recent_feedback': len(recent_feedback),
                'by_status': dict(status_counts),
                'by_type': dict(type_counts),
                'by_priority': dict(priority_counts),
                'by_sentiment': dict(sentiments_count),
                'response_rate': round(response_rate, 1),
                'unresolved_count': status_counts.get('new', 0) + status_counts.get('reviewed', 0),
                'critical_count': priority_counts.get('critical', 0)
            }
        
        def notify_new_feedback(self, feedback_entry) -> bool:
            """ Send a notification (hypothetical for the author but fun to imagine)"""
            try:
                print("====new feedback=====")
                print(f" ID: {feedback_entry.id}")
                print(f" FROM: {feedback_entry.name} ({feedback_entry.email})")
                print(f" TYPE: {feedback_entry.feedback_type}")
                print(f" SUBJECT: {feedback_entry.subject}")
                print(f" PRIORITY: {feedback_entry.priority}")
                print(f" MESSAGE: {feedback_entry.message[:100]}...")
                print(f" TIMESTAMP: {feedback_entry.timestamp}")

                return True
            except Exception as e:
                print(f"Error sending notification: {e}")
                return False
            
        def send_email_notification(self, feedback_entry) -> bool:
            try:
                """
                msg = MIMEMultipart()
                msg['From'] = 'noreply@felix.com'
                msg['To'] = 'admin@felix.com'
                msg['Subject'] = f'New Feedback: {feedback_entry.subject}
                
                body = f"""
                From: {feedback_entry.name}
                Email: {feedback_entry.email}
                Type: {feedback_entry.feedback_type}
                Priority: {feedback_entry.priority}

                Message: {feedback_entry.message}
                Timestamp: {feedback_entry.timestamp}

                """ 
                msg.attach(MIMEText(body, 'plain'))

                #SMTP server for email 
                server = smtplib.SMTP('smtp.felixserver.com', 587 #port 587)
                server.starttls()
                server.login('felix@coolguy.com', 'felix_isKing123')
                server.send_message(msg)
                server.quit()
                """

                return True
            
            except Exception as e:
                print(f"Error sending email: {e}")
                return False
        
        def export_feedback(self, feedback_entries: List, format:str = 'json') -> str:
            if format == 'json': #javascript object notation 
                data = [entry.to_dict() for entry in feedback_entries]
                return json.dumps(data, indent=2, default=str)
            
            elif format == 'csv': #comma seperated value file (db)
                csv_lines = ['ID,Name,Email,Type,Subject,Status,Priority,Timestamp']
                for entry in feedback_entries:
                    csv_line = [
                        str(entry.id),
                        f'"{entry.name}"',
                        f'"{entry.email}"',
                        entry.feedback_type,
                        f'"{entry.subject}"',
                        entry.status,
                        entry.priority,
                        entry.timestamp.isoformat()
                    ]
                    csv_lines.append(','.join(csv_line))
                
                return '\n'.join(csv_lines)
            else:
                raise ValueError(f"Unsupported format: {format}")
        
        def search_feedback(self, feedback_entries: List, query:str) -> List:
            if not query:
                return feedback_entries
            
            query_lower = query.lower()
            results = []

            for entry in feedback_entries:
                searchable_text = [
                    entry.name,
                    entry.email,
                    entry.subject,
                    entry.message,
                    entry.feedback_type,
                    entry.admin_notes
                ]

                if any(query_lower in str(field).lower() for field in searchable_text if field):
                    results.append(entry)

            return results
        
        def get_feedback_trends(self, feedback_entries: List, days: int = 30) -> Dict[str, Any]:
            if not feedback_entries: 
                return {}
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            #Filter entries
            period_entries = [
                entry for entry in feedback_entries if start_date <= entry.timestamp <= end_date]
            
            if not period_entries:
                return {}
            
            daily_counts = defaultdict(int)
            daily_sentiments = defaultdict(lambda: {'positive': 0, 'negative': 0, 'neutral': 0})

            for entry in period_entries:
                date_str = entry.timestamp.strftime('%Y-%m-%d')
                daily_counts[date_str] += 1

                sentiment_result = self.analyze_feedback_sentiment(entry.message)
                daily_sentiments[date_str][sentiment_result['sentiment']] += 1
            
            total_days = len(daily_counts)
            avg_daily = len(period_entries) / total_days if total_days > 0 else 0

            return {
                'period': {
                    'start': start_date.strftime('%Y-%m-%d'),
                    'end': end_date.strftime('%Y-%m-%d'),
                    'days': days
                },
                'total_feedback': len(period_entries),
                'daily_average': round(avg_daily, 2),
                'daily_counts': dict(daily_counts),
                'daily_sentiments': dict(daily_sentiments),
                'most_active_day': max(daily_counts, key=daily_counts.get) if daily_counts else None
            }

