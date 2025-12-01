from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import json
import re
import os
import secrets
from datetime import datetime, timedelta, timezone
from chat import FNNModel
from dotenv import load_dotenv
load_dotenv()


app = Flask(__name__)

secret_key = os.environ.get('SECRET_KEY')
if not secret_key:
    # 🚨 Production Safety Check
    if app.env == 'production':
        raise ValueError("FATAL ERROR: SECRET_KEY environment variable must be set in production.")
    else:
        # Fallback for development if you absolutely must
        print("Warning: SECRET_KEY not set. Using a temporary key for development.")
        secret_key = secrets.token_hex(16)

app.secret_key = secret_key
# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///estin_chatbot.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

chatbot_engine = FNNModel()

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    is_estin_student = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_login = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    login_count = db.Column(db.Integer, default=0)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Chat Message Model
class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_user = db.Column(db.Boolean, nullable=False)  # True for user, False for bot
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    user = db.relationship('User', backref=db.backref('chat_messages', lazy=True))

# Create database tables
with app.app_context():
    db.create_all()
    print("Database tables created!")



# Test route to check database
@app.route('/test-db')
def test_db():
    try:
        # Test database connection
        user_count = User.query.count()
        return f"Database working! Users in database: {user_count}"
    except Exception as e:
        return f"Database error: {str(e)}"

# Authentication routes
@app.route('/')
def home():
    if 'user_id' in session:
        user = db.session.get(User, session['user_id'])
        return render_template('index.html', user=user)
    return redirect(url_for('auth'))

@app.route('/auth')
def auth():
    if 'user_id' in session:
        return redirect(url_for('home'))
    return render_template('auth.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('auth'))

@app.route('/signup', methods=['POST'])
def signup():
    try:
        email = request.json.get('email', '').lower().strip()
        password = request.json.get('password', '')
        name = request.json.get('name', '').strip()
        
        print(f"Signup attempt: {email}, {name}")  # Debug line
        
        # Validate ESTIN email format - anyname@estin.dz
        if not email.endswith('@estin.dz'):
            print("Email domain invalid")
            return jsonify({'success': False, 'message': 'Only ESTIN email addresses (@estin.dz) are allowed'})
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            print("User already exists")
            return jsonify({'success': False, 'message': 'Email already registered'})
        
        # Validate password length
        if len(password) < 6:
            print("Password too short")
            return jsonify({'success': False, 'message': 'Password must be at least 6 characters'})
        
        # Validate name
        if len(name) < 2:
            return jsonify({'success': False, 'message': 'Please enter your full name'})
        
        # Create new user
        user = User(
            email=email,
            name=name,
            is_estin_student=True
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        print(f"User created successfully: {user.id}")  # Debug line
        session['user_id'] = user.id
        
        return jsonify({'success': True, 'message': 'Account created successfully!'})
        
    except Exception as e:
        print(f"Signup error: {str(e)}")  # Debug line
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error creating account: {str(e)}'})

@app.route('/login', methods=['POST'])
def login():
    email = request.json.get('email', '').lower().strip()
    password = request.json.get('password', '')
    
    user = User.query.filter_by(email=email).first()
    
    if user and user.check_password(password):
        # Update login stats
        user.last_login = datetime.now(timezone.utc)
        user.login_count += 1
        db.session.commit()
        
        session['user_id'] = user.id
        return jsonify({'success': True, 'message': 'Login successful!'})
    else:
        return jsonify({'success': False, 'message': 'Invalid email or password'})

# Chat routes (protected)
@app.route('/send_message', methods=['POST'])
def send_message():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_id = session['user_id']
    user_message = request.json['message']
    bot_data = chatbot_engine.get_response(user_message) 
    bot_response = bot_data['text'] 

    try:
        # Save user message
        user_msg = ChatMessage(user_id=user_id, message=user_message, is_user=True)
        db.session.add(user_msg)
        
        # Save bot response (text only)
        bot_msg = ChatMessage(user_id=user_id, message=bot_response, is_user=False)
        db.session.add(bot_msg)
        
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Database error during message save: {e}")
        return jsonify({'error': 'Internal server error while saving chat history'}), 500   

    
    response_data = {
        'user_message': user_message,
        'bot_response': bot_response,
        'timestamp': datetime.now().strftime("%H:%M")
    }
    
    # Add image/pdf info if it's a schedule request
    file_info = bot_data.get('file')
    if file_info:
        file_path = file_info['path']
        file_type = file_info['type']
        
        folder_map = {
        'pdf': 'documents',  # Use 'documents' for PDFs
        'image': 'images'
        }

        folder_name = folder_map.get(file_type)

        # Check file existence (Crucial for security and error prevention)
        if folder_name and os.path.exists(f"{folder_name}/{file_path}"):
            if file_type == 'pdf':
                response_data['pdf'] = file_path
            elif file_type == 'image':
                response_data['image'] = file_path
            
            response_data['file_name'] = file_info['name']

    return jsonify(response_data)


@app.route('/chat_history')
def chat_history():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    # Get messages from the last 30 days
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    
    messages = ChatMessage.query.filter(
        ChatMessage.user_id == session['user_id'],
        ChatMessage.timestamp >= thirty_days_ago
    ).order_by(ChatMessage.timestamp.asc()).all()
    
    # Group messages by date
    history_by_date = {}
    for msg in messages:
        date_str = msg.timestamp.strftime('%Y-%m-%d')
        if date_str not in history_by_date:
            history_by_date[date_str] = []
        
        history_by_date[date_str].append({
            'message': msg.message,
            'is_user': msg.is_user,
            'time': msg.timestamp.strftime('%H:%M')
        })
    
    return jsonify(history_by_date)

@app.route('/delete_chat_history', methods=['POST'])
def delete_chat_history():
    print("DELETE_CHAT_HISTORY: Route called")  # Debug line
    if 'user_id' not in session:
        print("DELETE_CHAT_HISTORY: User not authenticated")  # Debug line
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    try:
        user_id = session['user_id']
        print(f"DELETE_CHAT_HISTORY: Deleting messages for user_id: {user_id}")  # Debug line
        
        # First, check how many messages exist
        message_count = ChatMessage.query.filter_by(user_id=user_id).count()
        print(f"DELETE_CHAT_HISTORY: Found {message_count} messages to delete")  # Debug line
        
        # Delete all chat messages for the current user
        deleted_count = ChatMessage.query.filter_by(user_id=user_id).delete()
        db.session.commit()
        
        print(f"DELETE_CHAT_HISTORY: Successfully deleted {deleted_count} messages")  # Debug line
        
        return jsonify({
            'success': True, 
            'message': f'Successfully deleted {deleted_count} messages from your chat history'
        })
        
    except Exception as e:
        print(f"DELETE_CHAT_HISTORY: Error: {str(e)}")  # Debug line
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error deleting history: {str(e)}'}), 500

@app.route('/images/<filename>')
def serve_image(filename):
    if 'user_id' not in session:
        return "Not authenticated", 401
    try:
        return send_file(f'images/{filename}', mimetype='image/png', as_attachment=False)
    except FileNotFoundError:
        return "Image not found", 404

@app.route('/documents/<filename>')
def serve_pdf(filename):
    if 'user_id' not in session:
        return "Not authenticated", 401
    try:
        return send_file(f'documents/{filename}', mimetype='application/pdf', as_attachment=True)
    except FileNotFoundError:
        return "PDF not found", 404

if __name__ == '__main__':
    app.run(debug=True)