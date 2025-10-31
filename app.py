from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import json
import re
import os
import secrets
from datetime import datetime

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///estin_chatbot.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    is_estin_student = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, default=datetime.utcnow)
    login_count = db.Column(db.Integer, default=0)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Create database tables
with app.app_context():
    db.create_all()
    print("Database tables created!")

# Load the knowledge base
with open('data.json', 'r', encoding='utf-8') as f:
    knowledge_base = json.load(f)

# Define rules matching your scope
rules = {
    "greeting_hello": ["hello", "hey", "hi", "greetings", "good morning", "good afternoon", "good evening"],
    "greeting_hi": ["hi", "hey", "hello", "what's up", "yo"],
    "greeting_how_are_you": ["how are you", "how do you do", "how's it going", "how are things"],
    "greeting_goodbye": ["bye", "goodbye", "see you", "see ya", "farewell", "quit", "exit"],
    
    "library_opening": ["library", "opens", "opening", "time", "what time", "opens at"],
    "library_closing": ["library", "closes", "closing", "close", "what time", "closes at"],
    "library_weekend": ["library", "weekend", "saturday", "sunday", "weekend hours"],
    "courses_start": ["courses", "start", "begin", "what time", "starting", "first session"],
    "last_session": ["last", "session", "ends", "ending", "what time", "final", "last class"],
    "administration_hours": ["administration", "available", "when", "open", "hours", "works"],
    "second_year_program": ["program", "2cs", "second year", "1st", "first semester", "schedule", "timetable"],
    "first_year_program": ["first year", "1cs", "1st year", "freshman", "schedule"],
    "third_year_program": ["third year", "3cs", "3rd year", "junior", "schedule"],
    "specialties_number": ["specialties", "specialities", "how many", "estin has", "branches", "majors"],
    
    "academic_calendar_pdf": ["academic calendar", "university calendar", "yearly schedule", "academic schedule"],
    "course_catalog_pdf": ["course catalog", "catalogue", "all courses", "available courses", "course list"],
    "exam_schedule_pdf": ["exam schedule", "exam timetable", "examination dates", "exam calendar"],
    "registration_guide_pdf": ["registration guide", "how to register", "registration manual", "enrollment guide"],
    "student_handbook_pdf": ["student handbook", "student manual", "university guide", "student guide"],
    
    "exam_period": ["exam", "exams", "period", "when", "dates", "schedule"],
    "registration_deadline": ["registration", "deadline", "register", "when", "last date"],
    "tuition_fees": ["tuition", "fees", "cost", "price", "how much", "fee"],
    "scholarship_info": ["scholarship", "financial aid", "bursary", "grant"],
    "academic_calendar": ["academic", "calendar", "semester", "year", "schedule"],
    "it_department": ["it", "department", "computer", "support", "technical"],
    "student_clubs": ["clubs", "student", "activities", "extracurricular", "groups"],
    "wifi_access": ["wifi", "internet", "connection", "network", "connect"],
    "transcript_request": ["transcript", "grades", "marks", "record", "request"],
    "id_card_loss": ["id", "card", "lost", "missing", "student id", "replacement"],
    "parking_info": ["parking", "car", "vehicle", "permit"],
    "cafeteria_hours": ["cafeteria", "food", "restaurant", "eat", "lunch", "breakfast"],
    "sports_facilities": ["sports", "gym", "basketball", "football", "exercise", "fitness"],
    "professor_office": ["professor", "office", "hours", "teacher", "instructor"],
    "book_rental": ["book", "rental", "textbook", "borrow", "library book"],
    "graduation_requirements": ["graduation", "graduate", "requirements", "degree", "complete"],
    "internship_opportunities": ["internship", "training", "work", "placement", "career"],
    "coding_club": ["coding", "club", "programming", "meeting", "wednesday"],
    "contact_email": ["contact", "email", "address", "how to contact", "reach"],
    "holiday_schedule": ["holiday", "break", "vacation", "time off"],
    "lab_access": ["lab", "computer lab", "access", "laboratory", "computers"]
}

def get_response(user_input):
    user_input_lower = user_input.lower()
    
    # Special case for greetings that should have priority
    greeting_words = ["hello", "hi", "hey", "how are you", "good morning", "good afternoon", "good evening"]
    for word in greeting_words:
        if word in user_input_lower:
            if "how are you" in user_input_lower:
                return knowledge_base.get("greeting_how_are_you")
            elif any(greet in user_input_lower for greet in ["hi", "hey"]):
                return knowledge_base.get("greeting_hi")
            elif any(greet in user_input_lower for greet in ["hello", "good morning", "good afternoon", "good evening"]):
                return knowledge_base.get("greeting_hello")
    
    # Special case for goodbye
    goodbye_words = ["bye", "goodbye", "see you", "quit", "exit"]
    if any(word in user_input_lower for word in goodbye_words):
        return knowledge_base.get("greeting_goodbye")
    
    # Count matches for each intent (YOUR EXISTING SYSTEM)
    scores = {}
    for intent, keywords in rules.items():
        score = 0
        for keyword in keywords:
            if re.search(rf'\b{keyword}\b', user_input_lower):
                score += 1
        scores[intent] = score
    
    # Get the intent with the highest score
    best_intent = max(scores, key=scores.get)
    
    # Only return a response if we have a reasonable match
    if scores[best_intent] > 0:
        return knowledge_base.get(best_intent, "I'm sorry, I don't have an answer for that yet.")
    else:
        # 🚀 NEW SMART FALLBACK SYSTEM
        return smart_fallback(user_input_lower)

def smart_fallback(user_input_lower):
    """Intelligent fallback responses based on question patterns"""
    # Add synonym detection
    synonyms = {
        "timing": ["when", "what time", "schedule", "hours", "open", "close"],
        "procedures": ["how", "where can i", "how to", "process", "procedure"],
        "information": ["what", "tell me about", "information", "explain"]
    }
    
    # Add context awareness
    if "thank" in user_input_lower:
        return "You're welcome! 😊 Is there anything else about ESTIN I can help with?"
    
    # Add personality
    responses = [
        "I'd love to help with ESTIN! Try asking about...",
        "Great question! For ESTIN information, you might want to know about...",
        "I specialize in ESTIN University! You could ask me about..."
    ]
    
    # Question type detection
    if any(word in user_input_lower for word in ["when", "what time", "what date", "schedule", "hours"]):
        return "I can help with timing questions! Try asking about:\n• Library hours\n• Course schedules\n• Exam periods\n• Administration availability"
    
    elif any(word in user_input_lower for word in ["how", "where can i", "how to", "where is", "how can i"]):
        return "I can assist with procedures and locations! Try asking about:\n• How to get a student certificate\n• Where to find administration\n• How to register for courses\n• Library access procedures"
    
    elif any(word in user_input_lower for word in ["what", "tell me about", "information about", "explain"]):
        return "I have information about ESTIN! Try asking about:\n• University specialties\n• Student clubs\n• Sports facilities\n• Academic programs"
    
    elif any(word in user_input_lower for word in ["why", "reason", "purpose"]):
        return "I can explain university policies and procedures! Try asking about specific ESTIN rules or requirements."
    
    elif any(word in user_input_lower for word in ["who", "professor", "teacher", "head of"]):
        return "I can help you find people at ESTIN! Try asking about department heads or specific professors."
    
    elif any(word in user_input_lower for word in ["cost", "price", "fee", "how much"]):
        return "I have information about costs! Try asking about tuition fees or other university expenses."
    
    else:
        # General fallback with suggestions
        return "I'm not sure I understand. I can help you with:\n• Course schedules and timetables\n• Library and administration hours\n• University procedures and documents\n• ESTIN facilities and services\n\nTry asking about specific ESTIN-related topics!"
    
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
        user = User.query.get(session['user_id'])
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
        user.last_login = datetime.utcnow()
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
    
    user_message = request.json['message']
    bot_response = get_response(user_message)
    
    response_data = {
        'user_message': user_message,
        'bot_response': bot_response,
        'timestamp': datetime.now().strftime("%H:%M")
    }
    
    # Add image/pdf info if it's a schedule request
    user_input_lower = user_message.lower()
    
    if "schedule" in user_input_lower or "program" in user_input_lower or "timetable" in user_input_lower:
        if "2cs" in user_input_lower or "second" in user_input_lower:
            if os.path.exists('documents/2cs_schedule.pdf'):
                response_data['pdf'] = '2cs_schedule.pdf'
                response_data['file_name'] = '2CS Schedule PDF'
            elif os.path.exists('images/2cs_schedule.png'):
                response_data['image'] = '2cs_schedule.png'
                response_data['file_name'] = '2CS Schedule'
                
        elif "1st" in user_input_lower or "first" in user_input_lower:
            if os.path.exists('documents/1st_year_schedule.pdf'):
                response_data['pdf'] = '1st_year_schedule.pdf'
                response_data['file_name'] = '1st Year Schedule PDF'
            elif os.path.exists('images/1st_year_schedule.png'):
                response_data['image'] = '1st_year_schedule.png'
                response_data['file_name'] = '1st Year Schedule'
                
        elif "3rd" in user_input_lower or "third" in user_input_lower:
            if os.path.exists('documents/3rd_year_schedule.pdf'):
                response_data['pdf'] = '3rd_year_schedule.pdf'
                response_data['file_name'] = '3rd Year Schedule PDF'
            elif os.path.exists('images/3rd_year_schedule.png'):
                response_data['image'] = '3rd_year_schedule.png'
                response_data['file_name'] = '3rd Year Schedule'
    
    # Add PDF info for document requests
    pdf_mappings = {
        "academic_calendar_pdf": {"file": "academic_calendar.pdf", "name": "Academic Calendar"},
        "course_catalog_pdf": {"file": "course_catalog.pdf", "name": "Course Catalog"},
        "exam_schedule_pdf": {"file": "exam_schedule.pdf", "name": "Exam Schedule"},
        "registration_guide_pdf": {"file": "registration_guide.pdf", "name": "Registration Guide"},
        "student_handbook_pdf": {"file": "student_handbook.pdf", "name": "Student Handbook"}
    }
    
    for intent_key, pdf_info in pdf_mappings.items():
        if knowledge_base.get(intent_key, "").strip() in bot_response:
            pdf_path = f"documents/{pdf_info['file']}"
            if os.path.exists(pdf_path):
                response_data['pdf'] = pdf_info['file']
                response_data['file_name'] = pdf_info['name']
            break
    
    return jsonify(response_data)

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