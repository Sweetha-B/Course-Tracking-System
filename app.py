from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this in production

# Configure file uploads
UPLOAD_FOLDER = 'submissions'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload size

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = ALLOWED_EXTENSIONS
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Database setup
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    with open('schema.sql') as f:
        conn.executescript(f.read())
    
    # Add default admin with new credentials
    admin_password = generate_password_hash("admin@cms2023")
    conn.execute('INSERT INTO users (username, email, password, role, user_id) VALUES (?, ?, ?, ?, ?)',
                ('admin', 'admin@example.com', admin_password, 'Admin', 'A12345'))
    
    # Add default student with new credentials (for development/testing)
    student_password = generate_password_hash("student@cms2023")
    conn.execute('INSERT INTO users (username, email, password, role, user_id) VALUES (?, ?, ?, ?, ?)',
                ('student', 'student@example.com', student_password, 'Student', 'S12345'))
    
    # Add default courses with syllabi
    courses = [
        ('Machine Learning', 'Learn about ML algorithms and implementations', 'Detailed content about Machine Learning', 
         'https://www.youtube.com/embed/JcI5Vnw0b2c', 
         'Week 1: Introduction to Machine Learning\nWeek 2: Supervised Learning\nWeek 3: Unsupervised Learning\nWeek 4: Neural Networks\nWeek 5: Deep Learning\nWeek 6: Reinforcement Learning\nWeek 7: Model Evaluation\nWeek 8: Project Work'),
        
        ('Python', 'Master Python programming language', 'Python fundamentals and advanced concepts', 
         'https://www.youtube.com/embed/kqtD5dpn9C8', 
         'Week 1: Getting Started with Python\nWeek 2: Data Types and Variables\nWeek 3: Control Flow\nWeek 4: Functions and Modules\nWeek 5: Object-Oriented Programming\nWeek 6: File I/O and Exception Handling\nWeek 7: Libraries and Frameworks\nWeek 8: Project Work'),
        
        ('Java', 'Java programming language course', 'Java syntax, OOP, and applications', 
         'https://www.youtube.com/embed/grEKMHGYyns', 
         'Week 1: Introduction to Java\nWeek 2: Variables and Data Types\nWeek 3: Control Flow Statements\nWeek 4: Object-Oriented Programming\nWeek 5: Inheritance and Polymorphism\nWeek 6: Exception Handling\nWeek 7: Collections and Generics\nWeek 8: Final Project'),
        
        ('React', 'Frontend development with React', 'Components, state management, and React hooks', 
         'https://www.youtube.com/embed/w7ejDZ8SWv8', 
         'Week 1: Introduction to React\nWeek 2: Components and Props\nWeek 3: State and Lifecycle\nWeek 4: Handling Events\nWeek 5: React Hooks\nWeek 6: Context API and Redux\nWeek 7: React Router\nWeek 8: Building a Complete React App'),
        
        ('Cloud', 'Cloud computing fundamentals', 'AWS, Azure, and Google Cloud Platform', 
         'https://www.youtube.com/embed/M988_fsOSWo', 
         'Week 1: Introduction to Cloud Computing\nWeek 2: Cloud Service Models\nWeek 3: AWS Fundamentals\nWeek 4: Azure Basics\nWeek 5: Google Cloud Platform\nWeek 6: Cloud Security\nWeek 7: DevOps in Cloud\nWeek 8: Cloud Project Implementation')
    ]
    
    for course in courses:
        conn.execute('INSERT INTO courses (course_name, description, content, video_url, syllabus) VALUES (?, ?, ?, ?, ?)', course)
    
    # Add sample quizzes
    quizzes = [
        (1, 'Machine Learning Basics', 20),
        (1, 'Neural Networks', 20),
        (2, 'Python Fundamentals', 20),
        (2, 'Advanced Python', 20),
        (3, 'Java Basics', 20),
        (3, 'Advanced Java', 20),
        (4, 'React Fundamentals', 20),
        (4, 'React Advanced', 20),
        (5, 'Cloud Basics', 20),
        (5, 'Cloud Deployment', 20)
    ]
    
    for quiz in quizzes:
        quiz_id = conn.execute('INSERT INTO quizzes (course_id, quiz_name, total_marks) VALUES (?, ?, ?)', quiz).lastrowid
        
        # Add sample questions for each quiz
        if quiz[0] == 1 and quiz[1] == 'Machine Learning Basics':  # ML Basics
            questions = [
                ('What is supervised learning?', 
                 'Learning with a teacher', 'Learning without a teacher', 'Learning with supervision', 'None of the above', 
                 'option_a'),
                ('Which of the following is a classification algorithm?', 
                 'Linear Regression', 'Decision Tree', 'K-means', 'Principal Component Analysis', 
                 'option_b'),
                ('What is the goal of machine learning?', 
                 'To create intelligent machines', 'To make predictions based on data', 'To replace human jobs', 'To create robots', 
                 'option_b'),
                ('What is overfitting in machine learning?', 
                 'When model performs well on training data but poorly on test data', 'When model performs poorly on training data', 
                 'When model takes too long to train', 'When model is too simple', 
                 'option_a'),
                ('Which of these is NOT a type of machine learning?', 
                 'Supervised Learning', 'Unsupervised Learning', 'Reinforcement Learning', 'Supportive Learning', 
                 'option_d')
            ]
        elif quiz[0] == 2 and quiz[1] == 'Python Fundamentals':  # Python Fundamentals
            questions = [
                ('What is Python?', 
                 'A snake', 'A programming language', 'A database', 'A web framework', 
                 'option_b'),
                ('Which of the following is a valid Python data type?', 
                 'integer', 'boolean', 'string', 'All of the above', 
                 'option_d'),
                ('What symbol is used for comments in Python?', 
                 '//', '/*', '#', '--', 
                 'option_c'),
                ('Which of these is a correct way to define a function in Python?', 
                 'function myFunc():', 'def myFunc():', 'func myFunc():', 'define myFunc():', 
                 'option_b'),
                ('What does the len() function do in Python?', 
                 'Returns the length of a string or collection', 'Returns the largest number in a list', 
                 'Returns the data type of a variable', 'Converts string to lowercase', 
                 'option_a')
            ]
        elif quiz[0] == 3 and quiz[1] == 'Java Basics':  # Java Basics
            questions = [
                ('Java is...', 
                 'A programming language', 'A database', 'An operating system', 'A web browser', 
                 'option_a'),
                ('What is the entry point of a Java program?', 
                 'public static void main(String[] args)', 'start()', 'run()', 'init()', 
                 'option_a'),
                ('Which keyword is used to define a class in Java?', 
                 'class', 'struct', 'type', 'object', 
                 'option_a'),
                ('What is the correct way to declare a variable in Java?', 
                 'var x = 10;', 'x = 10;', 'int x = 10;', 'x: int = 10;', 
                 'option_c'),
                ('Which of these is NOT a primitive data type in Java?', 
                 'int', 'float', 'string', 'boolean', 
                 'option_c')
            ]
        elif quiz[0] == 4 and quiz[1] == 'React Fundamentals':  # React Fundamentals
            questions = [
                ('What is React?', 
                 'A JavaScript library for building user interfaces', 'A programming language', 'A database system', 'An operating system', 
                 'option_a'),
                ('What is JSX in React?', 
                 'A database query language', 'A styling framework', 'A syntax extension for JavaScript', 'A testing framework', 
                 'option_c'),
                ('Which function is used to change state in a React class component?', 
                 'this.changeState()', 'this.modifyState()', 'this.updateState()', 'this.setState()', 
                 'option_d'),
                ('What is a React component?', 
                 'A reusable piece of code that returns HTML via a render function', 'A CSS file', 'A JavaScript library', 'A database table', 
                 'option_a'),
                ('In React, props are...', 
                 'Internal variables', 'Properties passed to a component', 'CSS properties', 'HTML attributes', 
                 'option_b')
            ]
        elif quiz[0] == 5 and quiz[1] == 'Cloud Basics':  # Cloud Basics
            questions = [
                ('What is cloud computing?', 
                 'Computing using flying servers', 'Delivery of computing services over the internet', 'A weather prediction system', 'A type of network setup', 
                 'option_b'),
                ('Which of these is NOT a major cloud service provider?', 
                 'AWS', 'Microsoft Azure', 'Google Cloud', 'Oracle NetSuite', 
                 'option_d'),
                ('What does IaaS stand for?', 
                 'Internet as a Service', 'Infrastructure as a Service', 'Integration as a Service', 'Information as a Service', 
                 'option_b'),
                ('Which deployment model keeps all resources on premises?', 
                 'Public cloud', 'Private cloud', 'Hybrid cloud', 'Community cloud', 
                 'option_b'),
                ('What is a key benefit of cloud computing?', 
                 'Cost savings', 'Increased security risks', 'Reduced scalability', 'Less flexibility', 
                 'option_a')
            ]
        else:
            questions = [
                ('Sample Question 1?', 'Option A', 'Option B', 'Option C', 'Option D', 'option_a'),
                ('Sample Question 2?', 'Option A', 'Option B', 'Option C', 'Option D', 'option_b'),
                ('Sample Question 3?', 'Option A', 'Option B', 'Option C', 'Option D', 'option_c'),
                ('Sample Question 4?', 'Option A', 'Option B', 'Option C', 'Option D', 'option_d'),
                ('Sample Question 5?', 'Option A', 'Option B', 'Option C', 'Option D', 'option_a')
            ]
        
        for question in questions:
            conn.execute('''
                INSERT INTO quiz_questions 
                (quiz_id, question_text, option_a, option_b, option_c, option_d, correct_answer) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (quiz_id, question[0], question[1], question[2], question[3], question[4], question[5]))
    
    # Add sample weekly challenges
    weekly_challenges = [
        (1, 1, 'ML Basics Challenge', 'Implement a simple linear regression model'),
        (1, 2, 'Supervised Learning Challenge', 'Create a classification model using decision trees'),
        (2, 1, 'Python Basics Challenge', 'Write a program to calculate factorial'),
        (2, 2, 'Python Functions Challenge', 'Create a function to find prime numbers'),
        (3, 1, 'Java Basics Challenge', 'Create a simple calculator program'),
        (3, 2, 'Java OOP Challenge', 'Implement inheritance with shapes'),
        (4, 1, 'React Components Challenge', 'Create a todo list component'),
        (4, 2, 'React State Challenge', 'Build a counter with state management'),
        (5, 1, 'Cloud Basics Challenge', 'Set up a simple EC2 instance'),
        (5, 2, 'Cloud Storage Challenge', 'Create and manage S3 buckets')
    ]
    
    for challenge in weekly_challenges:
        conn.execute('''
            INSERT INTO weekly_challenges 
            (course_id, week_number, challenge_title, challenge_description) 
            VALUES (?, ?, ?, ?)
        ''', challenge)
    
    conn.commit()
    conn.close()

def add_ratings_table():
    conn = get_db_connection()
    with open('add_ratings_table.sql') as f:
        conn.executescript(f.read())
    conn.close()

def update_db_add_weekly_challenges():
    conn = get_db_connection()
    try:
        conn.execute('SELECT COUNT(*) FROM weekly_challenges')
        # Table already exists, do nothing
    except sqlite3.OperationalError:
        # Table does not exist, create it
        with open('add_weekly_challenges_table.sql') as f:
            conn.executescript(f.read())
        conn.commit()
        print("Added weekly_challenges table.") # Optional: for confirmation during run
    finally:
        conn.close()

def update_db_add_challenge_due_date():
    conn = get_db_connection()
    try:
        # Check if due_date column exists
        conn.execute('SELECT due_date FROM weekly_challenges LIMIT 1')
        # Column exists, do nothing
    except sqlite3.OperationalError:
        # Column does not exist, add it
        conn.execute('ALTER TABLE weekly_challenges ADD COLUMN due_date TEXT')
        conn.commit()
        print("Added due_date column to weekly_challenges table.")
    finally:
        conn.close()

def update_db_add_challenge_dates():
    conn = get_db_connection()
    try:
        # Check if start_date column exists
        conn.execute('SELECT start_date FROM weekly_challenges LIMIT 1')
        # Column exists, do nothing
    except sqlite3.OperationalError:
        # Column does not exist, add it
        conn.execute('ALTER TABLE weekly_challenges ADD COLUMN start_date TEXT')
        conn.execute('ALTER TABLE weekly_challenges ADD COLUMN end_date TEXT')
        conn.commit()
        print("Added start_date and end_date columns to weekly_challenges table.")
    finally:
        conn.close()

def update_db_add_challenge_submissions_table():
    conn = get_db_connection()
    try:
        conn.execute('SELECT COUNT(*) FROM weekly_challenge_submissions')
        # Table already exists, do nothing
    except sqlite3.OperationalError:
        # Table does not exist, create it
        with open('create_challenge_submissions_table.sql') as f:
            conn.executescript(f.read())
        conn.commit()
        print("Added weekly_challenge_submissions table.") # Optional: for confirmation during run
    finally:
        conn.close()

def update_db_add_user_id():
    conn = get_db_connection()
    try:
        # Check if user_id column exists
        conn.execute('SELECT user_id FROM users LIMIT 1')
        # Column exists, do nothing
    except sqlite3.OperationalError:
        # Column does not exist, add it
        with open('add_user_id_to_users.sql') as f:
            conn.executescript(f.read())
        conn.commit()
        print("Added user_id column to users table.") # Optional: for confirmation during run
    finally:
        conn.close()

# Routes
@app.route('/')
def home():
    return render_template('index.html')

# Student routes
@app.route('/student/register', methods=['GET', 'POST'])
def student_register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        student_id = request.form['student_id']
        
        conn = get_db_connection()
        
        # Check if username already exists
        existing_user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        if existing_user:
            conn.close()
            flash('Username already exists. Please choose a different username.', 'danger')
            return render_template('student/register.html')
        
        # Check if email already exists
        existing_email = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        if existing_email:
            conn.close()
            flash('Email already registered. Please use a different email address.', 'danger')
            return render_template('student/register.html')
            
        # Check if student ID already exists
        existing_student_id = conn.execute('SELECT * FROM users WHERE user_id = ?', (student_id,)).fetchone()
        if existing_student_id:
            conn.close()
            flash('Student ID already registered. Please use a different student ID.', 'danger')
            return render_template('student/register.html')
        
        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return render_template('student/register.html')
        
        hashed_password = generate_password_hash(password)
        conn.execute('INSERT INTO users (username, email, password, role, user_id) VALUES (?, ?, ?, ?, ?)',
                   (username, email, hashed_password, 'Student', student_id))
        conn.commit()
        conn.close()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('student_login'))
    
    return render_template('student/register.html')

@app.route('/student/login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ? AND role = "Student"', 
                          (username,)).fetchone()
        
        if not user:
            conn.close()
            flash('Invalid username or user is not a student', 'danger')
            return render_template('student/login.html')
            
        if not check_password_hash(user['password'], password):
            conn.close()
            flash('Invalid password', 'danger')
            return render_template('student/login.html')
        
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['role'] = user['role']
        session['student_id'] = user['user_id']
        conn.close()
        return redirect(url_for('student_dashboard'))
    
    return render_template('student/login.html')

@app.route('/student/dashboard')
def student_dashboard():
    if 'user_id' not in session or session['role'] != 'Student':
        return redirect(url_for('student_login'))
    
    conn = get_db_connection()
    student = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    
    enrollments = conn.execute('''
        SELECT c.*,
               COUNT(DISTINCT e.student_id) as enrollment_count,
               AVG(cr.rating) as avg_rating
        FROM courses c
        JOIN enrollments e ON c.id = e.course_id
        LEFT JOIN course_ratings cr ON c.id = cr.course_id
        WHERE e.student_id = ?
        GROUP BY c.id
    ''', (session['user_id'],)).fetchall()
    
    # Fetch weekly challenges for enrolled courses and student submissions
    weekly_challenges_data = conn.execute('''
        SELECT wc.*, c.course_name
        FROM weekly_challenges wc
        JOIN courses c ON wc.course_id = c.id
        JOIN enrollments e ON c.id = e.course_id
        WHERE e.student_id = ?
        ORDER BY wc.week_number, c.course_name
    ''', (session['user_id'],)).fetchall()
    
    updated_challenges = []
    for challenge in weekly_challenges_data:
        challenge_dict = dict(challenge)
        
        # Convert date strings to date objects
        if challenge_dict['start_date']:
            try:
                challenge_dict['start_date'] = datetime.strptime(challenge_dict['start_date'], '%Y-%m-%d').date()
            except (ValueError, TypeError):
                challenge_dict['start_date'] = None
        else:
            challenge_dict['start_date'] = None
            
        if challenge_dict['end_date']:
            try:
                challenge_dict['end_date'] = datetime.strptime(challenge_dict['end_date'], '%Y-%m-%d').date()
            except (ValueError, TypeError):
                challenge_dict['end_date'] = None
        else:
            challenge_dict['end_date'] = None

        # Fetch student's submission for this challenge
        submission = conn.execute('SELECT * FROM weekly_challenge_submissions WHERE student_id = ? AND challenge_id = ?', 
                                (session['user_id'], challenge_dict['id'])).fetchone()
        challenge_dict['submission'] = submission
            
        updated_challenges.append(challenge_dict)

    conn.close()
    
    return render_template('student/dashboard.html', 
                         student=student, 
                         enrollments=enrollments, 
                         weekly_challenges=updated_challenges,
                         now=datetime.now())

@app.route('/student/course/<int:course_id>')
def course_details(course_id):
    if 'user_id' not in session or session['role'] != 'Student':
        return redirect(url_for('student_login'))
    
    conn = get_db_connection()
    course = conn.execute('SELECT * FROM courses WHERE id = ?', (course_id,)).fetchone()
    
    # Get user's rating for this course
    user_rating = conn.execute('SELECT * FROM course_ratings WHERE course_id = ? AND student_id = ?',
                             (course_id, session['user_id'])).fetchone()
    
    quizzes = conn.execute('''
        SELECT q.*, 
               (SELECT score FROM quiz_scores 
                WHERE student_id = ? AND quiz_id = q.id) as user_score
        FROM quizzes q
        WHERE q.course_id = ?
    ''', (session['user_id'], course_id)).fetchall()
    
    conn.close()
    
    if not course:
        flash('Course not found')
        return redirect(url_for('student_dashboard'))
    
    return render_template('student/course_details.html', 
                         course=course, 
                         quizzes=quizzes,
                         user_rating=user_rating)

@app.route('/student/rate_course/<int:course_id>', methods=['POST'])
def rate_course(course_id):
    if 'user_id' not in session or session['role'] != 'Student':
        return redirect(url_for('student_login'))
    
    rating = request.form.get('rating', type=int)
    review = request.form.get('review', '').strip()
    
    if not rating or rating < 1 or rating > 5:
        flash('Invalid rating value', 'danger')
        return redirect(url_for('course_details', course_id=course_id))
    
    conn = get_db_connection()
    
    # Check if user has already rated this course
    existing_rating = conn.execute('SELECT * FROM course_ratings WHERE course_id = ? AND student_id = ?',
                                 (course_id, session['user_id'])).fetchone()
    
    if existing_rating:
        # Update existing rating
        conn.execute('UPDATE course_ratings SET rating = ?, review = ? WHERE id = ?',
                   (rating, review, existing_rating['id']))
        flash('Your rating has been updated', 'success')
    else:
        # Insert new rating
        conn.execute('INSERT INTO course_ratings (course_id, student_id, rating, review) VALUES (?, ?, ?, ?)',
                   (course_id, session['user_id'], rating, review))
        flash('Thank you for rating this course', 'success')
    
    conn.commit()
    conn.close()
    
    return redirect(url_for('course_details', course_id=course_id))

@app.route('/student/quiz/<int:quiz_id>', methods=['GET', 'POST'])
def take_quiz(quiz_id):
    if 'user_id' not in session or session['role'] != 'Student':
        return redirect(url_for('student_login'))
    
    conn = get_db_connection()
    quiz = conn.execute('SELECT * FROM quizzes WHERE id = ?', (quiz_id,)).fetchone()
    
    if not quiz:
        conn.close()
        flash('Quiz not found')
        return redirect(url_for('student_dashboard'))
    
    # Check if student already took this quiz
    score_record = conn.execute('SELECT * FROM quiz_scores WHERE student_id = ? AND quiz_id = ?', 
                             (session['user_id'], quiz_id)).fetchone()
    
    if request.method == 'POST' and not score_record:
        # Process the submitted answers
        score = 0
        answers = {}
        
        # Get all questions for this quiz
        questions = conn.execute('SELECT * FROM quiz_questions WHERE quiz_id = ?', (quiz_id,)).fetchall()
        
        for question in questions:
            question_id = str(question['id'])
            submitted_answer = request.form.get(f'question_{question_id}', '')
            correct_answer = question['correct_answer']
            
            # Store the answer
            answers[question_id] = submitted_answer
            
            # Check if the answer is correct
            if submitted_answer == correct_answer:
                score += quiz['total_marks'] / len(questions)  # Distribute points evenly
        
        # Round the score to nearest integer
        score = round(score)
        
        # Save score and answers to database
        conn.execute('INSERT INTO quiz_scores (student_id, quiz_id, score, answers) VALUES (?, ?, ?, ?)',
                   (session['user_id'], quiz_id, score, str(answers)))
        conn.commit()
        flash('Quiz submitted successfully!')
        return redirect(url_for('course_details', course_id=quiz['course_id']))
    
    # Get all questions for this quiz
    questions = conn.execute('SELECT * FROM quiz_questions WHERE quiz_id = ?', (quiz_id,)).fetchall()
    conn.close()
    
    if score_record:
        flash('You have already taken this quiz')
        return redirect(url_for('course_details', course_id=quiz['course_id']))
    
    return render_template('student/take_quiz.html', quiz=quiz, questions=questions)

@app.route('/student/enroll/<int:course_id>')
def enroll_course(course_id):
    if 'user_id' not in session or session['role'] != 'Student':
        return redirect(url_for('student_login'))
    
    conn = get_db_connection()
    # Check if already enrolled
    enrollment = conn.execute('SELECT * FROM enrollments WHERE student_id = ? AND course_id = ?', 
                           (session['user_id'], course_id)).fetchone()
    
    if not enrollment:
        conn.execute('INSERT INTO enrollments (student_id, course_id) VALUES (?, ?)',
                   (session['user_id'], course_id))
        conn.commit()
        flash('Successfully enrolled in the course')
    else:
        flash('You are already enrolled in this course')
    
    conn.close()
    return redirect(url_for('student_dashboard'))

@app.route('/courses')
def available_courses():
    if 'user_id' not in session or session['role'] != 'Student':
        return redirect(url_for('student_login'))
    
    conn = get_db_connection()
    courses = conn.execute('''
        SELECT c.*, 
               (SELECT COUNT(*) FROM enrollments WHERE course_id = c.id AND student_id = ?) as is_enrolled
        FROM courses c
    ''', (session['user_id'],)).fetchall()
    conn.close()
    
    return render_template('student/courses.html', courses=courses)

@app.route('/student/challenge/submit/<int:challenge_id>', methods=['POST'])
def upload_challenge_submission(challenge_id):
    if 'user_id' not in session or session['role'] != 'Student':
        return redirect(url_for('student_login'))

    # Check if the post request has the file part
    if 'submission_file' not in request.files:
        flash('No file part in the request', 'danger')
        return redirect(url_for('student_dashboard'))

    file = request.files['submission_file']
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(url_for('student_dashboard'))

    # Check if submission is before due date
    conn = get_db_connection()
    challenge = conn.execute('SELECT * FROM weekly_challenges WHERE id = ?', (challenge_id,)).fetchone()
    
    if not challenge:
        conn.close()
        flash('Challenge not found', 'danger')
        return redirect(url_for('student_dashboard'))

    if challenge['end_date'] and datetime.strptime(challenge['end_date'], '%Y-%m-%d').date() < datetime.now().date():
        conn.close()
        flash('Submission period has ended', 'danger')
        return redirect(url_for('student_dashboard'))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Create submissions directory if it doesn't exist
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
        
        # Save the file
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Save submission record
        conn.execute('''
            INSERT INTO weekly_challenge_submissions 
            (student_id, challenge_id, filename, timestamp) 
            VALUES (?, ?, ?, ?)
        ''', (session['user_id'], challenge_id, filename, datetime.now()))
        conn.commit()
        conn.close()
        
        flash('File uploaded successfully', 'success')
    else:
        conn.close()
        flash('Invalid file type. Please upload PDF or Word documents only.', 'danger')
    
    return redirect(url_for('student_dashboard'))

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/student/submissions/<int:submission_id>')
def view_student_submission(submission_id):
    if 'user_id' not in session or session['role'] != 'Student':
        return redirect(url_for('student_login'))
    
    conn = get_db_connection()
    submission = conn.execute('SELECT * FROM weekly_challenge_submissions WHERE id = ? AND student_id = ?', 
                             (submission_id, session['user_id'])).fetchone()
    conn.close()
    
    if not submission:
        flash('Submission not found or you do not have permission to view it.', 'danger')
        return redirect(url_for('student_dashboard'))
    
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], secure_filename(submission['filename']))
    except FileNotFoundError:
        flash('Submission file not found', 'danger')
        return redirect(url_for('student_dashboard'))

# Admin routes
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['admin_id']
        password = request.form['password']
        
        conn = get_db_connection()
        admin = conn.execute('SELECT * FROM users WHERE username = ? AND role = "Admin"', 
                           (username,)).fetchone()
        conn.close()
        
        if admin and check_password_hash(admin['password'], password):
            session['user_id'] = admin['id']
            session['username'] = admin['username']
            session['role'] = 'Admin'
            return redirect(url_for('admin_dashboard'))
        
        flash('Invalid admin ID or password')
    
    return render_template('admin/login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('admin_login'))
    
    return render_template('admin/dashboard.html')

@app.route('/admin/students')
def admin_students():
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    students = conn.execute('SELECT * FROM users WHERE role = "Student"').fetchall()
    conn.close()
    
    return render_template('admin/students.html', students=students)

@app.route('/admin/student/<int:student_id>')
def student_report(student_id):
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    student = conn.execute('SELECT * FROM users WHERE id = ? AND role = "Student"', (student_id,)).fetchone()
    
    quiz_scores = conn.execute('''
        SELECT qs.*, q.quiz_name, q.total_marks, c.course_name
        FROM quiz_scores qs
        JOIN quizzes q ON qs.quiz_id = q.id
        JOIN courses c ON q.course_id = c.id
        WHERE qs.student_id = ?
        ORDER BY qs.score DESC
    ''', (student_id,)).fetchall()
    
    conn.close()
    
    if not student:
        flash('Student not found')
        return redirect(url_for('admin_students'))
    
    return render_template('admin/student_report.html', student=student, scores=quiz_scores)

@app.route('/admin/delete_student/<int:student_id>')
def delete_student(student_id):
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    conn.execute('DELETE FROM users WHERE id = ? AND role = "Student"', (student_id,))
    conn.execute('DELETE FROM enrollments WHERE student_id = ?', (student_id,))
    conn.execute('DELETE FROM quiz_scores WHERE student_id = ?', (student_id,))
    conn.commit()
    conn.close()
    
    flash('Student deleted successfully')
    return redirect(url_for('admin_students'))

@app.route('/admin/courses')
def admin_courses():
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    courses = conn.execute('''
        SELECT c.*,
               COUNT(DISTINCT e.student_id) as enrollment_count,
               AVG(cr.rating) as avg_rating
        FROM courses c
        LEFT JOIN enrollments e ON c.id = e.course_id
        LEFT JOIN course_ratings cr ON c.id = cr.course_id
        GROUP BY c.id
    ''').fetchall()
    conn.close()
    
    return render_template('admin/courses.html', courses=courses)

@app.route('/admin/course/<int:course_id>', methods=['GET', 'POST'])
def edit_course(course_id):
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    course = conn.execute('SELECT * FROM courses WHERE id = ?', (course_id,)).fetchone()
    
    if request.method == 'POST':
        course_name = request.form['course_name']
        description = request.form['description']
        content = request.form['content']
        video_url = request.form['video_url']
        
        conn.execute('UPDATE courses SET course_name = ?, description = ?, content = ?, video_url = ? WHERE id = ?',
                   (course_name, description, content, video_url, course_id))
        conn.commit()
        flash('Course updated successfully')
        return redirect(url_for('admin_courses'))
    
    conn.close()
    
    if not course:
        flash('Course not found')
        return redirect(url_for('admin_courses'))
    
    return render_template('admin/edit_course.html', course=course)

@app.route('/admin/add_course', methods=['GET', 'POST'])
def add_course():
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('admin_login'))
    
    if request.method == 'POST':
        course_name = request.form['course_name']
        description = request.form['description']
        content = request.form['content']
        video_url = request.form['video_url']
        
        conn = get_db_connection()
        conn.execute('INSERT INTO courses (course_name, description, content, video_url) VALUES (?, ?, ?, ?)',
                   (course_name, description, content, video_url))
        conn.commit()
        conn.close()
        
        flash('Course added successfully')
        return redirect(url_for('admin_courses'))
    
    return render_template('admin/add_course.html')

@app.route('/admin/delete_course/<int:course_id>')
def delete_course(course_id):
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    conn.execute('DELETE FROM courses WHERE id = ?', (course_id,))
    conn.execute('DELETE FROM enrollments WHERE course_id = ?', (course_id,))
    conn.execute('DELETE FROM quizzes WHERE course_id = ?', (course_id,))
    conn.commit()
    conn.close()
    
    flash('Course deleted successfully')
    return redirect(url_for('admin_courses'))

@app.route('/admin/quizzes/<int:course_id>')
def course_quizzes(course_id):
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    course = conn.execute('SELECT * FROM courses WHERE id = ?', (course_id,)).fetchone()
    quizzes = conn.execute('SELECT * FROM quizzes WHERE course_id = ?', (course_id,)).fetchall()
    conn.close()
    
    if not course:
        flash('Course not found')
        return redirect(url_for('admin_courses'))
    
    return render_template('admin/course_quizzes.html', course=course, quizzes=quizzes)

@app.route('/admin/add_quiz/<int:course_id>', methods=['GET', 'POST'])
def add_quiz(course_id):
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    course = conn.execute('SELECT * FROM courses WHERE id = ?', (course_id,)).fetchone()
    
    if not course:
        conn.close()
        flash('Course not found')
        return redirect(url_for('admin_courses'))
    
    if request.method == 'POST':
        quiz_name = request.form['quiz_name']
        total_marks = request.form['total_marks']
        
        conn.execute('INSERT INTO quizzes (course_id, quiz_name, total_marks) VALUES (?, ?, ?)',
                   (course_id, quiz_name, total_marks))
        conn.commit()
        conn.close()
        
        flash('Quiz added successfully')
        return redirect(url_for('course_quizzes', course_id=course_id))
    
    conn.close()
    return render_template('admin/add_quiz.html', course=course)

@app.route('/admin/edit_quiz/<int:quiz_id>', methods=['GET', 'POST'])
def edit_quiz(quiz_id):
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    quiz = conn.execute('SELECT * FROM quizzes WHERE id = ?', (quiz_id,)).fetchone()
    
    if not quiz:
        conn.close()
        flash('Quiz not found')
        return redirect(url_for('admin_courses'))
    
    if request.method == 'POST':
        quiz_name = request.form['quiz_name']
        total_marks = request.form['total_marks']
        
        conn.execute('UPDATE quizzes SET quiz_name = ?, total_marks = ? WHERE id = ?',
                   (quiz_name, total_marks, quiz_id))
        conn.commit()
        flash('Quiz updated successfully')
        return redirect(url_for('course_quizzes', course_id=quiz['course_id']))
    
    conn.close()
    return render_template('admin/edit_quiz.html', quiz=quiz)

@app.route('/admin/delete_quiz/<int:quiz_id>')
def delete_quiz(quiz_id):
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    quiz = conn.execute('SELECT * FROM quizzes WHERE id = ?', (quiz_id,)).fetchone()
    
    if not quiz:
        conn.close()
        flash('Quiz not found')
        return redirect(url_for('admin_courses'))
    
    course_id = quiz['course_id']
    
    conn.execute('DELETE FROM quizzes WHERE id = ?', (quiz_id,))
    conn.execute('DELETE FROM quiz_scores WHERE quiz_id = ?', (quiz_id,))
    conn.commit()
    conn.close()
    
    flash('Quiz deleted successfully')
    return redirect(url_for('course_quizzes', course_id=course_id))

@app.route('/admin/quiz_questions/<int:quiz_id>', methods=['GET'])
def quiz_questions(quiz_id):
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    quiz = conn.execute('SELECT q.*, c.course_name FROM quizzes q JOIN courses c ON q.course_id = c.id WHERE q.id = ?', (quiz_id,)).fetchone()
    
    if not quiz:
        conn.close()
        flash('Quiz not found')
        return redirect(url_for('admin_courses'))
    
    questions = conn.execute('SELECT * FROM quiz_questions WHERE quiz_id = ?', (quiz_id,)).fetchall()
    conn.close()
    
    return render_template('admin/quiz_questions.html', quiz=quiz, questions=questions)

@app.route('/admin/add_question/<int:quiz_id>', methods=['GET', 'POST'])
def add_question(quiz_id):
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    quiz = conn.execute('SELECT q.*, c.course_name FROM quizzes q JOIN courses c ON q.course_id = c.id WHERE q.id = ?', (quiz_id,)).fetchone()
    
    if not quiz:
        conn.close()
        flash('Quiz not found')
        return redirect(url_for('admin_courses'))
    
    if request.method == 'POST':
        question_text = request.form['question_text']
        option_a = request.form['option_a']
        option_b = request.form['option_b']
        option_c = request.form['option_c']
        option_d = request.form['option_d']
        correct_answer = request.form['correct_answer']
        
        conn.execute('''
            INSERT INTO quiz_questions 
            (quiz_id, question_text, option_a, option_b, option_c, option_d, correct_answer) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (quiz_id, question_text, option_a, option_b, option_c, option_d, correct_answer))
        conn.commit()
        conn.close()
        
        flash('Question added successfully')
        return redirect(url_for('quiz_questions', quiz_id=quiz_id))
    
    conn.close()
    return render_template('admin/add_question.html', quiz=quiz)

@app.route('/admin/edit_question/<int:question_id>', methods=['GET', 'POST'])
def edit_question(question_id):
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    question = conn.execute('SELECT * FROM quiz_questions WHERE id = ?', (question_id,)).fetchone()
    
    if not question:
        conn.close()
        flash('Question not found')
        return redirect(url_for('admin_courses'))
    
    quiz = conn.execute('SELECT q.*, c.course_name FROM quizzes q JOIN courses c ON q.course_id = c.id WHERE q.id = ?', (question['quiz_id'],)).fetchone()
    
    if request.method == 'POST':
        question_text = request.form['question_text']
        option_a = request.form['option_a']
        option_b = request.form['option_b']
        option_c = request.form['option_c']
        option_d = request.form['option_d']
        correct_answer = request.form['correct_answer']
        
        conn.execute('''
            UPDATE quiz_questions 
            SET question_text = ?, option_a = ?, option_b = ?, option_c = ?, option_d = ?, correct_answer = ? 
            WHERE id = ?
        ''', (question_text, option_a, option_b, option_c, option_d, correct_answer, question_id))
        conn.commit()
        
        flash('Question updated successfully')
        return redirect(url_for('quiz_questions', quiz_id=question['quiz_id']))
    
    conn.close()
    return render_template('admin/edit_question.html', question=question, quiz=quiz)

@app.route('/admin/delete_question/<int:question_id>')
def delete_question(question_id):
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    question = conn.execute('SELECT * FROM quiz_questions WHERE id = ?', (question_id,)).fetchone()
    
    if not question:
        conn.close()
        flash('Question not found')
        return redirect(url_for('admin_courses'))
    
    quiz_id = question['quiz_id']
    
    conn.execute('DELETE FROM quiz_questions WHERE id = ?', (question_id,))
    conn.commit()
    conn.close()
    
    flash('Question deleted successfully')
    return redirect(url_for('quiz_questions', quiz_id=quiz_id))

@app.route('/admin/quiz_participants/<int:quiz_id>')
def quiz_participants(quiz_id):
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    quiz = conn.execute('SELECT q.*, c.course_name FROM quizzes q JOIN courses c ON q.course_id = c.id WHERE q.id = ?', (quiz_id,)).fetchone()
    
    if not quiz:
        conn.close()
        flash('Quiz not found')
        return redirect(url_for('admin_courses'))
    
    participants = conn.execute('''
        SELECT u.id, u.username, u.user_id, u.email, qs.score, qs.id as score_id
        FROM users u
        JOIN quiz_scores qs ON u.id = qs.student_id
        WHERE qs.quiz_id = ?
        ORDER BY qs.score DESC
    ''', (quiz_id,)).fetchall()
    
    conn.close()
    
    return render_template('admin/quiz_participants.html', quiz=quiz, participants=participants)

@app.route('/admin/course_ratings/<int:course_id>')
def course_ratings(course_id):
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    course = conn.execute('SELECT * FROM courses WHERE id = ?', (course_id,)).fetchone()
    
    if not course:
        conn.close()
        flash('Course not found')
        return redirect(url_for('admin_courses'))
    
    ratings = conn.execute('''
        SELECT cr.*, u.username
        FROM course_ratings cr
        JOIN users u ON cr.student_id = u.id
        WHERE cr.course_id = ?
        ORDER BY cr.created_at DESC
    ''', (course_id,)).fetchall()
    
    # Calculate rating statistics
    stats = conn.execute('''
        SELECT 
            COUNT(*) as total_ratings,
            AVG(rating) as avg_rating,
            MIN(rating) as min_rating,
            MAX(rating) as max_rating,
            COUNT(CASE WHEN rating = 5 THEN 1 END) as five_star,
            COUNT(CASE WHEN rating = 4 THEN 1 END) as four_star,
            COUNT(CASE WHEN rating = 3 THEN 1 END) as three_star,
            COUNT(CASE WHEN rating = 2 THEN 1 END) as two_star,
            COUNT(CASE WHEN rating = 1 THEN 1 END) as one_star
        FROM course_ratings
        WHERE course_id = ?
    ''', (course_id,)).fetchone()
    
    conn.close()
    
    return render_template('admin/course_ratings.html', 
                         course=course, 
                         ratings=ratings, 
                         stats=stats)

@app.route('/admin/course/<int:course_id>/students')
def course_students(course_id):
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    course = conn.execute('SELECT * FROM courses WHERE id = ?', (course_id,)).fetchone()
    
    if not course:
        conn.close()
        flash('Course not found')
        return redirect(url_for('admin_courses'))
    
    # Get enrolled students with their details
    students = conn.execute('''
        SELECT u.*, 
               (SELECT COUNT(*) FROM quiz_scores qs 
                JOIN quizzes q ON qs.quiz_id = q.id 
                WHERE q.course_id = ? AND qs.student_id = u.id) as quizzes_taken,
               (SELECT AVG(qs.score) FROM quiz_scores qs 
                JOIN quizzes q ON qs.quiz_id = q.id 
                WHERE q.course_id = ? AND qs.student_id = u.id) as avg_score
        FROM users u
        JOIN enrollments e ON u.id = e.student_id
        WHERE e.course_id = ?
        ORDER BY u.username
    ''', (course_id, course_id, course_id)).fetchall()
    
    conn.close()
    
    return render_template('admin/course_students.html', course=course, students=students)

@app.route('/admin/add_weekly_challenge/<int:course_id>', methods=['GET', 'POST'])
def add_weekly_challenge(course_id):
    if request.method == 'POST':
        week_number = request.form['week_number']
        challenge_title = request.form['challenge_title']
        challenge_description = request.form['challenge_description']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO weekly_challenges 
            (course_id, week_number, challenge_title, challenge_description, start_date, end_date) 
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (course_id, week_number, challenge_title, challenge_description, start_date, end_date))
        conn.commit()
        conn.close()
        flash('Weekly challenge added successfully!', 'success')
        return redirect(url_for('admin_weekly_challenges'))
    return render_template('admin/add_weekly_challenge.html', course_id=course_id)

@app.route('/admin/weekly_challenges')
def admin_weekly_challenges():
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    
    # Get filter parameters
    selected_course = request.args.get('filter_course', type=int)
    selected_week = request.args.get('filter_week', type=int)
    
    # Get all courses for the dropdown
    courses = conn.execute('SELECT * FROM courses ORDER BY course_name').fetchall()
    
    # Build the query with filters
    query = '''
        SELECT wc.*, c.course_name
        FROM weekly_challenges wc
        JOIN courses c ON wc.course_id = c.id
        WHERE 1=1
    '''
    params = []
    
    if selected_course:
        query += ' AND wc.course_id = ?'
        params.append(selected_course)
    
    if selected_week:
        query += ' AND wc.week_number = ?'
        params.append(selected_week)
    
    query += ' ORDER BY wc.course_id, wc.week_number'
    
    challenges = conn.execute(query, params).fetchall()
    conn.close()
    
    return render_template('admin/weekly_challenges.html', 
                         challenges=challenges,
                         courses=courses,
                         selected_course=selected_course,
                         selected_week=selected_week)

@app.route('/admin/edit_weekly_challenge/<int:challenge_id>', methods=['GET', 'POST'])
def edit_weekly_challenge(challenge_id):
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    challenge = conn.execute('SELECT * FROM weekly_challenges WHERE id = ?', (challenge_id,)).fetchone()
    
    if not challenge:
        conn.close()
        flash('Weekly challenge not found', 'danger')
        return redirect(url_for('admin_weekly_challenges'))
    
    if request.method == 'POST':
        week_number = request.form['week_number']
        challenge_title = request.form['challenge_title']
        challenge_description = request.form['challenge_description']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        
        conn.execute('''
            UPDATE weekly_challenges 
            SET week_number = ?, challenge_title = ?, challenge_description = ?, 
                start_date = ?, end_date = ? 
            WHERE id = ?
        ''', (week_number, challenge_title, challenge_description, start_date, end_date, challenge_id))
        conn.commit()
        conn.close()
        flash('Weekly challenge updated successfully!', 'success')
        return redirect(url_for('admin_weekly_challenges'))
    
    conn.close()
    return render_template('admin/edit_weekly_challenge.html', challenge=challenge)

@app.route('/admin/delete_weekly_challenge/<int:challenge_id>')
def delete_weekly_challenge(challenge_id):
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    challenge = conn.execute('SELECT * FROM weekly_challenges WHERE id = ?', (challenge_id,)).fetchone()
    
    if not challenge:
        conn.close()
        flash('Weekly challenge not found', 'danger')
        return redirect(url_for('admin_weekly_challenges'))
    
    conn.execute('DELETE FROM weekly_challenges WHERE id = ?', (challenge_id,))
    conn.commit()
    conn.close()
    flash('Weekly challenge deleted successfully!', 'success')
    return redirect(url_for('admin_weekly_challenges'))

@app.route('/admin/challenge_submissions/<int:challenge_id>')
def admin_challenge_submissions(challenge_id):
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    challenge = conn.execute('''
        SELECT wc.*, c.course_name
        FROM weekly_challenges wc
        JOIN courses c ON wc.course_id = c.id
        WHERE wc.id = ?
    ''', (challenge_id,)).fetchone()
    
    if not challenge:
        conn.close()
        flash('Weekly challenge not found', 'danger')
        return redirect(url_for('admin_weekly_challenges'))
    
    submissions = conn.execute('''
        SELECT wcs.*, u.username, u.user_id
        FROM weekly_challenge_submissions wcs
        JOIN users u ON wcs.student_id = u.id
        WHERE wcs.challenge_id = ?
        ORDER BY wcs.timestamp DESC
    ''', (challenge_id,)).fetchall()
    
    conn.close()
    
    return render_template('admin/challenge_submissions.html', challenge=challenge, submissions=submissions)

@app.route('/admin/delete_challenge_submission/<int:submission_id>')
def delete_challenge_submission(submission_id):
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    submission = conn.execute('SELECT * FROM weekly_challenge_submissions WHERE id = ?', (submission_id,)).fetchone()
    
    if not submission:
        conn.close()
        flash('Submission not found', 'danger')
        return redirect(url_for('admin_dashboard')) # Or redirect to challenge submissions page
    
    challenge_id = submission['challenge_id']
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(submission['filename']))
    
    # Delete file from server
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except OSError as e:
            flash(f'Error deleting file: {e}', 'danger')
            # Decide whether to continue deleting the database record or not
            # For now, we will continue to delete the record
            
    # Delete record from database
    conn.execute('DELETE FROM weekly_challenge_submissions WHERE id = ?', (submission_id,))
    conn.commit()
    conn.close()
    
    flash('Submission deleted successfully!', 'success')
    return redirect(url_for('admin_challenge_submissions', challenge_id=challenge_id))

@app.route('/admin/submissions/<filename>')
def view_submission_file(filename):
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('admin_login'))
    
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], secure_filename(filename))
    except FileNotFoundError:
        flash('Submission file not found', 'danger')
        return redirect(url_for('admin_dashboard')) # Or a more specific redirect if needed

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    if not os.path.exists('database.db'):
        init_db()
    else:
        # Add the ratings table to existing database
        add_ratings_table()
        # Add the weekly_challenges table to existing database if missing
        update_db_add_weekly_challenges()
        # Add the due_date column to weekly_challenges table if missing
        update_db_add_challenge_due_date()
        # Add the start_date and end_date columns to weekly_challenges table if missing
        update_db_add_challenge_dates()
        # Add the weekly_challenge_submissions table to existing database if missing
        update_db_add_challenge_submissions_table()
        # Add the user_id column to users table if missing
        update_db_add_user_id()
    app.run(debug=True) 