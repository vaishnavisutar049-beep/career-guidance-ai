from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import hashlib
import os
from werkzeug.utils import secure_filename
from translations import get_all_texts

app = Flask(__name__)
app.secret_key = 'career_guidance_secret_key_2024'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Language context processor - makes translations available to all templates
@app.context_processor
def inject_translations():
    lang = session.get('lang', 'en')
    return dict(t=get_all_texts(lang), current_lang=lang)

# Language switching route
@app.route('/set_language/<lang>')
def set_language(lang):
    if lang in ['en', 'mr', 'hi']:
        session['lang'] = lang
    else:
        session['lang'] = 'en'
    # Redirect back to the previous page
    return redirect(request.referrer or url_for('index'))

# Create uploads directory if not exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Database setup
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                 name TEXT NOT NULL, 
                 email TEXT UNIQUE NOT NULL, 
                 password TEXT NOT NULL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS results 
                (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                 user_id INTEGER, 
                 career TEXT, 
                 skills TEXT, 
                 courses TEXT, 
                 salary TEXT, 
                 future_scope TEXT,
                 FOREIGN KEY(user_id) REFERENCES users(id))''')
    
    # Create resumes table with photo column
    c.execute('''CREATE TABLE IF NOT EXISTS resumes 
                (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                 user_id INTEGER, 
                 resume_data TEXT, 
                 career_target TEXT,
                 photo TEXT,
                 FOREIGN KEY(user_id) REFERENCES users(id))''')
    
    # Add photo column if it doesn't exist (for existing databases)
    try:
        c.execute("ALTER TABLE resumes ADD COLUMN photo TEXT")
    except:
        pass  # Column already exists
    
    # Create admins table for admin login
    c.execute('''CREATE TABLE IF NOT EXISTS admins 
                (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                 username TEXT UNIQUE NOT NULL, 
                 password TEXT NOT NULL)''')
    
    # Create mentors table
    c.execute('''CREATE TABLE IF NOT EXISTS mentors
                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 name TEXT NOT NULL,
                 expertise TEXT,
                 available TEXT DEFAULT 'yes',
                 contact TEXT)''')
    
    # Create certificates table
    c.execute('''CREATE TABLE IF NOT EXISTS certificates
                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 user_id INTEGER,
                 course_name TEXT,
                 issue_date DATE,
                 certificate_id TEXT)''')
    
    # Create progress table
    c.execute('''CREATE TABLE IF NOT EXISTS progress
                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 user_id INTEGER,
                 course_name TEXT,
                 completion_percentage INTEGER,
                 date_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Check if admin exists, if not create default admin
    c.execute("SELECT COUNT(*) FROM admins")
    if c.fetchone()[0] == 0:
        # Create default admin (username: admin, password: admin123)
        default_password = hashlib.sha256('admin123'.encode()).hexdigest()
        c.execute("INSERT INTO admins (username, password) VALUES (?, ?)", ('admin', default_password))
    
    # Add sample mentors if not exist
    c.execute("SELECT COUNT(*) FROM mentors")
    if c.fetchone()[0] == 0:
        mentors_data = [
            ('Dr. Priya Sharma', 'Career Counseling', 'yes', 'priya@carrerai.com'),
            ('Prof. Rajesh Kumar', 'Engineering Admissions', 'yes', 'rajesh@carrerai.com'),
            ('Ms. Anita Desai', 'Medical Career Guide', 'yes', 'anita@carrerai.com'),
            ('Mr. Suresh Jadhav', 'MPSC/UPSC Expert', 'yes', 'suresh@carrerai.com'),
        ]
        c.executemany('INSERT INTO mentors (name, expertise, available, contact) VALUES (?, ?, ?, ?)', mentors_data)
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

# Career recommendations database
CAREER_DATA = {
    # Technology
    'technology': {
        'career': 'Software Developer/Engineer',
        'skills': 'Programming (Python, Java, JavaScript), Data Structures, Algorithms, Problem Solving, Database Management',
        'courses': 'Computer Science Degree, Full Stack Development, Cloud Computing, Machine Learning',
        'salary': '₹5-25 LPA (Entry to Senior)',
        'future_scope': 'High demand, remote work options, continuous growth opportunities',
        'study_plan': 'Year 1: Learn Python/HTML/CSS || Year 2: JavaScript & React || Year 3: Projects & Internship || Year 4: Full Stack & Placement',
        'stability': 'Medium-High',
        'risk_level': 'Medium',
        'government_path': 'Can apply for government IT positions, PSU jobs, and banking sector IT roles'
    },
    # Design/Art
    'drawing': {
        'career': 'Graphic Designer / Illustrator',
        'skills': 'Adobe Photoshop, Illustrator, Figma, Typography, Color Theory, Visual Design, Creativity',
        'courses': 'Graphic Design Certification, Fine Arts, Animation, UX Design, Digital Art',
        'salary': '₹3-15 LPA (Entry to Senior)',
        'future_scope': 'Freelance opportunities, digital media growth, brand identity design',
        'study_plan': 'Year 1: Learn Design Tools (PS/AI) || Year 2: Typography & Color Theory || Year 3: Portfolio Building || Year 4: Freelancing/Job',
        'stability': 'Medium',
        'risk_level': 'Medium-High',
        'government_path': 'Limited government opportunities - can work in government media units, publications, and cultural departments'
    },
    # Music
    'singing': {
        'career': 'Professional Singer / Music Composer',
        'skills': 'Vocal Training, Music Theory, Keyboard/Instrument, Recording, Stage Performance, Songwriting',
        'courses': 'Music Certification, Classical Training, Audio Engineering, Music Production',
        'salary': '₹3-20+ LPA (varies by fame)',
        'future_scope': 'Music industry, streaming platforms, live performances, content creation',
        'study_plan': 'Year 1: Vocal Training || Year 2: Music Theory & Instruments || Year 3: Recording & Production || Year 4: Live Shows & Albums',
        'stability': 'Low-Medium',
        'risk_level': 'High',
        'government_path': 'Can work in All India Radio, Doordarshan, Sangeet Natak Akademi, and cultural ministry positions'
    },
    # Dance
    'dancing': {
        'career': 'Professional Dancer / Choreographer',
        'skills': 'Various Dance Forms, Choreography, Stage Performance, Fitness, Expression, Teaching',
        'courses': 'Dance Certification, Performing Arts, Choreography Courses, Dance Therapy',
        'salary': '₹3-18 LPA (Entry to Senior)',
        'future_scope': 'Bollywood, stage shows, choreography, dance studios, online content',
        'study_plan': 'Year 1: Basic Dance Forms || Year 2: Advanced Choreography || Year 3: Stage Performances || Year 4: Industry Work',
        'stability': 'Low-Medium',
        'risk_level': 'High',
        'government_path': 'Can work in cultural ministry, Sangeet Natak Akademi, and government dance troupes'
    },
    # Biology/Medical
    'biology': {
        'career': 'Doctor / Medical Professional',
        'skills': 'Medical Knowledge, Patient Care, Diagnosis, Surgery, Research, Communication',
        'courses': 'MBBS, MD, MS, Nursing, Pharmacy, Biotechnology, Medical Research',
        'salary': '₹6-50+ LPA (varies by specialization)',
        'future_scope': 'High demand, healthcare industry growth, research opportunities',
        'study_plan': 'Year 1-2: NEET Prep || Year 3-5: MBBS Studies || Year 6-7: Internship || Year 8+: Specialization',
        'stability': 'Very High',
        'risk_level': 'Low',
        'government_path': 'Excellent government opportunities - Government doctors, AIIMS, PHC, CGHS, Railway doctors, ESI doctors, and municipal corporation positions'
    },
    # Science/Research
    'science': {
        'career': 'Research Scientist',
        'skills': 'Scientific Methods, Research, Data Analysis, Laboratory Skills, Critical Thinking, Publications',
        'courses': 'B.Sc/M.Sc, PhD, JEE, Research Fellowships, Indian Institute of Science',
        'salary': '₹4-20 LPA (Entry to Senior)',
        'future_scope': 'Research institutes, universities, DRDO, ISRO, pharmaceutical companies',
        'study_plan': 'Year 1-2: Foundation (PCM) || Year 3-4: B.Sc Focus || Year 5-6: M.Sc || Year 7+: PhD/Research',
        'stability': 'Medium-High',
        'risk_level': 'Low-Medium',
        'government_path': 'Excellent - DRDO, ISRO, CSIR, ICAR, DAE, Indian research institutes, and university positions'
    },
    # Business
    'business': {
        'career': 'Business Analyst',
        'skills': 'Data Analysis, SQL, Excel, Communication, Problem Solving, Domain Knowledge',
        'courses': 'MBA, Business Analytics Certification, Tableau/PowerBI',
        'salary': '₹5-20 LPA (Entry to Senior)',
        'future_scope': 'High demand across industries, consulting opportunities',
        'study_plan': 'Year 1-2: Graduation || Year 3: Aptitude & CAT Prep || Year 4-5: MBA || Year 6+: Job',
        'stability': 'Medium-High',
        'risk_level': 'Medium',
        'government_path': 'MBA in government management institutes, government PSUs, and administrative roles through competitive exams'
    },
    # Data
    'data': {
        'career': 'Data Scientist',
        'skills': 'Python, R, Statistics, Machine Learning, Data Visualization, SQL, Big Data',
        'courses': 'Data Science Certification, Machine Learning, Deep Learning',
        'salary': '₹6-30 LPA (Entry to Senior)',
        'future_scope': 'Very high demand, AI/ML integration, excellent growth',
        'study_plan': 'Year 1: Python & Statistics || Year 2: Machine Learning || Year 3: Projects & Kaggle || Year 4: Data Science Job',
        'stability': 'Medium-High',
        'risk_level': 'Medium',
        'government_path': 'Growing opportunities in government analytics projects, NIC, NITI Aayog, and data-driven government initiatives'
    },
    # Marketing
    'marketing': {
        'career': 'Digital Marketing Manager',
        'skills': 'SEO, SEM, Social Media, Content Creation, Analytics, Email Marketing',
        'courses': 'Digital Marketing Certification, Google Ads, Analytics',
        'salary': '₹4-15 LPA (Entry to Senior)',
        'future_scope': 'E-commerce boom, remote work options, growing field',
        'study_plan': 'Year 1: SEO & Social Media || Year 2: Google Ads & Analytics || Year 3: Live Projects || Year 4: Digital Marketing Job',
        'stability': 'Medium',
        'risk_level': 'Medium-High',
        'government_path': 'Limited - can work in tourism ministry, cultural ministry, and government advertising agencies'
    },
    # Healthcare
    'healthcare': {
        'career': 'Healthcare Administrator',
        'skills': 'Healthcare Management, Medical Terminology, Data Analysis, Leadership',
        'courses': 'Healthcare Management MBA, Hospital Administration, Public Health',
        'salary': '₹5-20 LPA (Entry to Senior)',
        'future_scope': 'Stable growth, healthcare industry expansion',
        'study_plan': 'Year 1-2: Graduation || Year 3: Healthcare Mgmt Prep || Year 4-5: MBA Healthcare || Year 6+: Hospital Job',
        'stability': 'High',
        'risk_level': 'Low',
        'government_path': 'Excellent - Government hospitals, AIIMS, PHC, municipal health departments, and health ministry positions'
    }
}

# Career responses in different languages
CAREER_RESPONSES = {
    'en': {
        'mpsc': '''<h3>📋 MPSC (Maharashtra Public Service Commission)</h3>

<strong>Exam Pattern:</strong>
• State Services (Pre) - 100 questions, 200 marks
• State Services (Main) - 9 papers
• Interview - 275 marks

<strong>2-Year Study Plan:</strong>

<strong>Year 1:</strong>
<b>Months 1-3:</b> Understand exam pattern, collect materials
<b>Months 4-6:</b> Complete Marathi & English, Basic GS
<b>Months 7-9:</b> Complete History, Geography, Polity
<b>Months 10-12:</b> Current Affairs, Practice MCQs

<strong>Year 2:</strong>
<b>Months 13-15:</b> Optional subject preparation
<b>Months 16-18:</b> Answer writing practice
<b>Months 19-21:</b> Full mock tests, revision
<b>Months 22-24:</b> Final revision, attempt prelims

<strong>Books:</strong> Laxmikant, Spectrum, Mahesh Barnwal''',

        'upsc': '''<h3>🏛️ UPSC (Union Public Service Commission)</h3>

<strong>Exam Pattern:</strong>
• Prelims - GS I + CSAT
• Mains - 9 papers
• Interview - 275 marks

<strong>2-Year Study Plan:</strong>

<strong>Year 1:</strong>
<b>Months 1-2:</b> Understand syllabus, collect books
<b>Months 3-5:</b> History
<b>Months 6-8:</b> Geography
<b>Months 9-11:</b> Polity, Economy

<strong>Year 2:</strong>
<b>Months 13-15:</b> Optional + Current Affairs
<b>Months 16-18:</b> Answer writing
<b>Months 19-21:</b> Test series
<b>Months 22-24:</b> Final mocks

<strong>Books:</strong> NCERTs, Laxmikant, Spectrum''',

        'army': '''<h3>🎖️ Indian Army Careers</h3>

<strong>Entry Options:</strong>
• NDA (10+2) - Age 16.5-19.5 yrs
• CDS (Graduate) - Age 20-24 yrs
• AFCAT (Air Force)
• TA (Territorial Army)

<strong>Preparation:</strong>
• Written Exam + SSB
• Physical Fitness required
• 1.6 km run - 6 minutes

<strong>Salary:</strong> Lieutenant - ₹56,100 + allowances''',
    },
    'mr': {
        'mpsc': '''<h3>📋 MPSC (महाराष्ट्र लोकसेवा आयोग)</h3>

<strong>परीक्षा पद्धत:</strong>
• राज्य सेवा (प्रारंभिक) - 100 प्रश्न, 200 गुण
• राज्य सेवा (मुख्य) - 9 पेपर
• मुलाखत - 275 गुण

<strong>2 वर्ष अभ्यास योजना:</strong>

<strong>वर्ष 1:</strong>
<b>महिने 1-3:</b> परीक्षा पद्धत समजून घेणे
<b>महिने 4-6:</b> मराठी व इंग्रजी, मूलभूत GS
<b>महिने 7-9:</b> इतिहास, भूगोल, राज्यव्यवस्था
<b>महिने 10-12:</b> चालू घडामोडी, MCQ सराव

<strong>वर्ष 2:</strong>
<b>महिने 13-15:</b> पर्यायी विषय
<b>महिने 16-18:</b> उत्तर लेखन सराव
<b>महिने 19-21:</b> पूर्ण मॉक टेस्ट
<b>महिने 22-24:</b> अंतिम पुनरावलोकन

<strong>पुस्तके:</strong> लक्ष्मीकांत, स्पेक्ट्रम''',

        'upsc': '''<h3>🏛️ UPSC (संघ लोकसेवा आयोग)</h3>

<strong>परीक्षा पद्धत:</strong>
• प्रारंभिक - GS I + CSAT
• मुख्य - 9 पेपर
• मुलाखत - 275 गुण

<strong>2 वर्ष अभ्यास योजना:</strong>

<strong>वर्ष 1:</b>
<b>महिने 1-2:</b> अभ्यासक्रम समजून घेणे
<b>महिने 3-5:</b> इतिहास
<b>महिने 6-8:</b> भूगोल
<b>महिने 9-11:</b> राज्यव्यवस्था, अर्थशास्त्र

<strong>वर्ष 2:</b>
<b>महिने 13-15:</b> पर्यायी + चालू घडामोडी
<b>महिने 16-18:</b> उत्तर लेखन
<b>महिने 19-21:</b> टेस्ट सीरीज
<b>महिने 22-24:</b> अंतिम मॉक

<strong>पुस्तके:</b> NCERT, लक्ष्मीकांत, स्पेक्ट्रम''',

        'army': '''<h3>🎖️ भारतीय सेना</h3>

<strong>प्रवेश पर्याय:</strong>
• NDA (10+2) - वय 16.5-19.5 वर्ष
• CDS (पदवीधर) - वय 20-24 वर्ष
• AFCAT (वायुसेना)

<strong>तयारी:</strong>
• लिखित परीक्षा + SSB
• शारीरिक फिटनेस आवश्यक
• 1.6 किमी धावणे - 6 मिनिटे

<strong>पगार:</strong> लेफ्टनंट - ₹56,100 + भत्ते''',
    },
    'hi': {
        'mpsc': '''<h3>MPSC - Maharashtra Public Service Commission</h3>
<strong>Exam Pattern:</strong>
- State Services (Pre) - 100 questions, 200 marks
- State Services (Main) - 9 papers
- Interview - 275 marks

<strong>2-Year Study Plan:</strong>
Year 1: Months 1-3: Understand exam pattern
Year 1: Months 4-6: Complete basic GS
Year 2: Months 7-12: Current Affairs, Practice MCQs

<strong>Books:</strong> Laxmikant, Spectrum''',

        'upsc': '''<h3>UPSC - Union Public Service Commission</h3>

<strong>Exam Pattern:</strong>
- Prelims - GS I + CSAT
- Mains - 9 papers
- Interview - 275 marks

<strong>2-Year Study Plan:</strong>
Year 1: History, Geography, Polity
Year 2: Optional + Current Affairs, Answer writing

<strong>Books:</strong> NCERTs, Laxmikant, Spectrum''',

        'army': '''<h3>Indian Army Careers</h3>

<strong>Entry Options:</strong>
- NDA (10+2) - Age 16.5-19.5 yrs
- CDS (Graduate) - Age 20-24 yrs

<strong>Preparation:</strong>
- Written Exam + SSB
- Physical Fitness required

<strong>Salary:</strong> Lieutenant - Rs.56,100 + allowances'''
    }
}

# Import Knowledge Base
from knowledge_base import KNOWLEDGE_BASE, analyze_conflict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Initialize TF-IDF vectorizer for ML-based matching
vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2))
knowledge_texts = []
knowledge_keys = []

# Build knowledge base for ML matching
for key, data in KNOWLEDGE_BASE.items():
    keywords_text = ' '.join(data.get('keywords', []))
    response_text = data.get('en', '')[:500]  # Use first 500 chars
    combined = keywords_text + ' ' + response_text
    knowledge_texts.append(combined)
    knowledge_keys.append(key)

# Fit vectorizer
if knowledge_texts:
    tfidf_matrix = vectorizer.fit_transform(knowledge_texts)

# Smart response using TF-IDF
def smart_response(user_message, language='en'):
    """ML-based response matching using TF-IDF"""
    user_vec = vectorizer.transform([user_message])
    similarities = cosine_similarity(user_vec, tfidf_matrix)[0]
    
    # Get best match
    best_idx = np.argmax(similarities)
    best_score = similarities[best_idx]
    
    if best_score > 0.05:  # Lower threshold for better matching
        best_key = knowledge_keys[best_idx]
        data = KNOWLEDGE_BASE.get(best_key, {})
        return data.get(language, data.get('en', ''))
    
    # Default response - handle general questions
    default_responses = {
        'en': """<h3>🤖 I'm here to help with career guidance!</h3>

I can answer questions about:

<b>📋 Competitive Exams:</b> MPSC, UPSC, SSC, Bank PO, RRB, JEE, NEET, GATE, CLAT

<b>🎓 Careers:</b> Engineering, Medical, Commerce, Arts, Defence, IT, Teaching, Banking

<b>📚 Courses:</b> After 10th, After 12th, Degree, Diploma, Online, Certificate

<b>💼 Jobs:</b> Government jobs, Private sector, Internships, Skills required

<b>💰 Salary:</b> Career packages, Future scope, Highest paying jobs

<b>🎓 Colleges:</b> Top institutes, Admissions, Fees, Scholarships

<b>📝 Preparation:</b> Study plans, Strategy, Books, Tips

<b>Other:</b> Career change, Skills, Jobs after graduation

Just ask me anything! Examples:
• What courses after 12th science?
• How to prepare for UPSC?
• Salary of software engineer
• Best colleges for MBA""",        
        'mr': """<h3>🤖 मी करिअर मार्गदर्शनासाठी मदत करायला आलो आहे!</h3>

मी खालील विषयाबद्दल उत्तर देऊ शकतो:

<b>📋 परीक्षा:</b> MPSC, UPSC, SSC, Bank PO, JEE, NEET

<b>🎓 करिअर:</b> Engineering, Medical, Commerce, Defence, IT

<b>📚 कोर्स:</b> 10वी/12वी नंतर, Diploma, Degree

<b>💰 पगार:</b> Career packages, Future scope

<b>🎓 महाविद्यालये:</b> Top colleges, Fees

फक्त विचारा!""",
        
        'hi': """<h3>🤖 Main career guidance ke liye yahan hoon!</h3>

Main in topics ke baare mein bata sakta hoon:

<b>Exams:</b> MPSC, UPSC, SSC, JEE, NEET
<b>Careers:</b> Engineering, Medical, Commerce, IT
<b>Courses:</b> After 10th, 12th
<b>Salary:</b> Career packages
<b>Colleges:</b> Top institutes

Bas poochho!"""
    }
    return default_responses.get(language, default_responses['en'])

# Language detection function for Marathi/Hindi/English
def detect_language(text):
    """Detect if the user message is in Marathi, Hindi, or English"""
    if not text:
        return 'en'
    
    text = text.strip()
    
    # Marathi characters (Devanagari script for Marathi)
    # Marathi specific: ०-९ (Marathi digits), क-ह (basic), ् (virama), etc.
    marathi_chars = len([c for c in text if '\u0900' <= c <= '\u097F'])
    
    # Check for Marathi-specific characters and common Marathi words
    marathi_indicators = ['आहे', 'आहेत', 'मी', 'तू', 'का', 'कसा', 'काय', 'शी', 'ला', 'मध्ये', 
                         'वर', 'खाली', 'पासून', 'पर्यंत', 'हा', 'हे', 'ती', 'ते', 'कोण',
                         'कुठे', 'किती', 'केव्हा', 'मग', 'पण', 'किंवा', 'आणि', 'नाही',
                         'असे', 'अशी', 'जसे', 'जसा', 'करू', 'होऊ', 'द्यावे', 'घ्यावे',
                         'बाबत', 'संबंधी', 'कारण', 'साठी', 'नंतर', 'आधी', 'वेळेला']
    
    # Hindi common words
    hindi_indicators = ['है', 'हैं', 'मैं', 'तू', 'क्या', 'कैसा', 'कौन', 'कहाँ', 'कितना', 
                       'कब', 'फिर', 'लेकिन', 'या', 'और', 'नहीं', 'इस', 'उस', 'जो', 'वो',
                       'होगा', 'करूंगा', 'दूंगा', 'लेना', 'देना', 'के लिए', 'में', 'पर',
                       'से', 'तक', 'बाद', 'पहले', 'समय']
    
    # Calculate Marathi score
    marathi_score = 0
    for word in marathi_indicators:
        if word in text:
            marathi_score += 1
    marathi_score += marathi_chars // 3  # Weight for Devanagari characters
    
    # Calculate Hindi score
    hindi_score = 0
    for word in hindi_indicators:
        if word in text:
            hindi_score += 1
    hindi_score += marathi_chars // 4  # Some overlap with Devanagari
    
    # Decision logic
    if marathi_score > hindi_score and marathi_score > 0:
        return 'mr'
    elif hindi_score > marathi_score and hindi_score > 0:
        return 'hi'
    elif marathi_chars > len(text) * 0.3:  # More than 30% Devanagari
        return 'mr'
    else:
        return 'en'

# Mock AI responses for career guidance
def get_career_response(user_message, language='en'):
    user_message = user_message.lower()
    
    # Auto-detect language if not provided or if user wants auto-detection
    if language == 'auto' or language == 'en':
        detected_lang = detect_language(user_message)
        if detected_lang != 'en':
            language = detected_lang
    
    # Get responses for selected language
    responses = KNOWLEDGE_BASE.copy()
    
    # First, try exact keyword match
    for key, data in responses.items():
        for keyword in data.get('keywords', []):
            if keyword in user_message:
                return data.get(language, data.get('en', ''))
    
    # Try TF-IDF semantic matching
    return smart_response(user_message, language)


@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = hashlib.sha256(request.form['password'].encode()).hexdigest()
        
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT id, name FROM users WHERE email = ? AND password = ?", (email, password))
        user = c.fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user[0]
            session['name'] = user[1]
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = hashlib.sha256(request.form['password'].encode()).hexdigest()
        
        try:
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            c.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)", 
                     (name, email, password))
            conn.commit()
            conn.close()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Email already registered', 'error')
    
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', name=session['name'])

@app.route('/test', methods=['GET', 'POST'])
def test():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        q1 = request.form.get('q1', '')
        q2 = request.form.get('q2', '')
        q3 = request.form.get('q3', '')
        q4 = request.form.get('q4', '')
        
        # Calculate result based on answers
        scores = {'technology': 0, 'drawing': 0, 'singing': 0, 'dancing': 0, 'biology': 0, 'science': 0, 'business': 0, 'data': 0, 'marketing': 0, 'healthcare': 0}
        
        # Q1: Skills
        if q1 == 'coding':
            scores['technology'] += 2
            scores['data'] += 1
        elif q1 == 'drawing':
            scores['drawing'] += 2
        elif q1 == 'singing':
            scores['singing'] += 2
        elif q1 == 'dancing':
            scores['dancing'] += 2
        elif q1 == 'biology':
            scores['biology'] += 2
            scores['science'] += 1
        elif q1 == 'science':
            scores['science'] += 2
            scores['technology'] += 1
        elif q1 == 'communication':
            scores['business'] += 1
            scores['marketing'] += 2
        
        # Q2: Interest
        if q2 == 'technology':
            scores['technology'] += 2
        elif q2 == 'drawing':
            scores['drawing'] += 2
        elif q2 == 'singing':
            scores['singing'] += 2
        elif q2 == 'dancing':
            scores['dancing'] += 2
        elif q2 == 'biology':
            scores['biology'] += 2
        elif q2 == 'science':
            scores['science'] += 2
        elif q2 == 'business':
            scores['business'] += 2
        
        # Q3: Work style
        if q3 == 'computer':
            scores['technology'] += 2
            scores['data'] += 2
        elif q3 == 'creative':
            scores['drawing'] += 2
        elif q3 == 'performing':
            scores['singing'] += 1
            scores['dancing'] += 2
        elif q3 == 'lab':
            scores['science'] += 2
            scores['biology'] += 2
        elif q3 == 'people':
            scores['business'] += 1
            scores['marketing'] += 2
            scores['biology'] += 1
        
        # Q4: Goal
        if q4 == 'money':
            scores['technology'] += 1
            scores['data'] += 1
            scores['biology'] += 1
        elif q4 == 'fame':
            scores['singing'] += 2
            scores['dancing'] += 2
        elif q4 == 'impact':
            scores['biology'] += 2
            scores['science'] += 1
            scores['healthcare'] += 2
        elif q4 == 'growth':
            scores['technology'] += 2
            scores['data'] += 1
        elif q4 == 'helping':
            scores['biology'] += 2
            scores['healthcare'] += 2
        
        # Get highest score
        result = max(scores, key=scores.get)
        career_info = CAREER_DATA.get(result, CAREER_DATA['technology'])
        
        # Save result to database
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("INSERT INTO results (user_id, career, skills, courses, salary, future_scope) VALUES (?, ?, ?, ?, ?, ?)",
                  (session['user_id'], career_info['career'], career_info['skills'], 
                   career_info['courses'], career_info['salary'], career_info['future_scope']))
        conn.commit()
        conn.close()
        
        return render_template('result.html', career=career_info['career'], 
                               skills=career_info['skills'], courses=career_info['courses'],
                               salary=career_info['salary'], future_scope=career_info['future_scope'])
    
    return render_template('test.html')

@app.route('/result')
def result():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Get user's last result
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT career, skills, courses, salary, future_scope FROM results WHERE user_id = ? ORDER BY id DESC LIMIT 1",
              (session['user_id'],))
    result = c.fetchone()
    conn.close()
    
    if result:
        # Find matching career data to get study plan
        study_plan = ""
        career_key = result[0].lower().replace("/", " ").replace(" ", "")
        for key, data in CAREER_DATA.items():
            if result[0].lower() in data['career'].lower():
                study_plan = data.get('study_plan', '')
                break
        return render_template('result.html', career=result[0], skills=result[1], 
                               courses=result[2], salary=result[3], future_scope=result[4],
                               study_plan=study_plan)
    return redirect(url_for('test'))

@app.route('/chat')
def chat():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('chat.html')

@app.route('/get', methods=['POST'])
def get_chat_response():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_message = request.form.get('message', '')
    language = request.form.get('language', 'en')
    response = get_career_response(user_message, language)
    return response

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ==================== NEW FEATURES ====================

# Career Categories for suggestions
CAREER_CATEGORIES = {
    'Technology': ['technology', 'data'],
    'Healthcare': ['biology', 'healthcare'],
    'Business & Finance': ['business'],
    'Creative Arts': ['drawing', 'singing', 'dancing'],
    'Education': ['teacher'],
    'Science & Research': ['science'],
    'Marketing': ['marketing']
}

# Salary expectations mapping
SALARY_EXPECTATIONS = {
    'low': ['teacher', 'drawing', 'ba'],
    'medium': ['business', 'marketing', 'bca', 'bcom', 'healthcare'],
    'high': ['technology', 'data', 'biology', 'science', 'engineering']
}

# Difficulty levels
DIFFICULTY_MAP = {
    'easy': ['teacher', 'drawing', 'marketing', 'beauty', 'ba'],
    'medium': ['business', 'bca', 'bcom', 'healthcare', 'banking'],
    'hard': ['technology', 'data', 'science', 'law', 'engineering'],
    'very_hard': ['biology']
}

# ==================== CAREER SUGGESTION ROUTES ====================

@app.route('/career-suggestions', methods=['GET', 'POST'])
def career_suggestions():
    """Smart Career Suggestion Feature - Most Important!"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    suggestions = []
    selected_interest = ''
    selected_skills = ''
    selected_salary = ''
    selected_difficulty = ''
    
    if request.method == 'POST':
        selected_interest = request.form.get('interest', '')
        selected_skills = request.form.get('skills', '')
        selected_salary = request.form.get('salary_expectation', '')
        selected_difficulty = request.form.get('difficulty', '')
        
        # Calculate career scores based on preferences
        career_scores = {}
        
        for key, career in CAREER_DATA.items():
            score = 0
            
            # Interest matching
            if selected_interest:
                interest_map = {
                    'tech': ['technology', 'data', 'bca'],
                    'medical': ['biology', 'healthcare'],
                    'business': ['business', 'bcom', 'banking'],
                    'creative': ['drawing', 'singing', 'dancing'],
                    'science': ['science', 'technology'],
                    'teaching': ['teacher'],
                    'law': ['law'],
                    'marketing': ['marketing']
                }
                if selected_interest in interest_map:
                    if key in interest_map[selected_interest]:
                        score += 5
            
            # Skills matching
            if selected_skills:
                skills_map = {
                    'coding': ['technology', 'data', 'bca'],
                    'creative': ['drawing', 'singing', 'dancing'],
                    'communication': ['business', 'marketing', 'teacher'],
                    'analytical': ['data', 'science', 'business'],
                    'medical': ['biology', 'healthcare'],
                    'legal': ['law']
                }
                if selected_skills in skills_map:
                    if key in skills_map[selected_skills]:
                        score += 4
            
            # Salary expectation matching
            if selected_salary:
                if selected_salary == 'low' and key in ['teacher', 'drawing', 'ba', 'beauty']:
                    score += 3
                elif selected_salary == 'medium' and key in ['business', 'marketing', 'bca', 'bcom', 'healthcare']:
                    score += 3
                elif selected_salary == 'high' and key in ['technology', 'data', 'biology', 'science']:
                    score += 3
            
            # Difficulty matching
            if selected_difficulty:
                if selected_difficulty == 'easy' and key in ['teacher', 'drawing', 'marketing', 'beauty', 'ba']:
                    score += 2
                elif selected_difficulty == 'medium' and key in ['business', 'bca', 'bcom', 'healthcare', 'banking']:
                    score += 2
                elif selected_difficulty == 'hard' and key in ['technology', 'data', 'science', 'law', 'engineering']:
                    score += 2
                elif selected_difficulty == 'very_hard' and key in ['biology']:
                    score += 2
            
            if score > 0:
                career_scores[key] = score
        
        # Sort by score and get top suggestions
        sorted_careers = sorted(career_scores.items(), key=lambda x: x[1], reverse=True)
        
        for career_key, score in sorted_careers[:5]:
            career_info = CAREER_DATA[career_key].copy()
            career_info['match_score'] = min(score * 10, 100)
            career_info['key'] = career_key
            suggestions.append(career_info)
        
        # If no suggestions based on filters, show all careers
        if not suggestions:
            for key, career in CAREER_DATA.items():
                career_info = career.copy()
                career_info['match_score'] = 50
                career_info['key'] = key
                suggestions.append(career_info)
            suggestions = suggestions[:5]
    
    return render_template('career_suggestions.html', 
                          suggestions=suggestions,
                          selected_interest=selected_interest,
                          selected_skills=selected_skills,
                          selected_salary=selected_salary,
                          selected_difficulty=selected_difficulty)

# ==================== PARENT-STUDENT CONFLICT ANALYZER ====================

@app.route('/conflict-analyzer', methods=['GET', 'POST'])
def conflict_analyzer():
    """Parent-Student Decision Conflict Analyzer - Unique Feature!"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    result = None
    
    if request.method == 'POST':
        student_choice = request.form.get('student_choice', '').strip()
        parent_choice = request.form.get('parent_choice', '').strip()
        
        if student_choice and parent_choice:
            result = analyze_conflict(student_choice, parent_choice)
        else:
            flash('Please enter both choices!', 'error')
    
    return render_template('conflict_analyzer.html', result=result)


@app.route('/career-details/<career_key>')
def career_details(career_key):
    """Show detailed information about a specific career"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    career_info = CAREER_DATA.get(career_key)
    if not career_info:
        flash('Career not found', 'error')
        return redirect(url_for('career_suggestions'))
    
    # Get related careers (same category)
    related_careers = []
    for cat_name, cat_careers in CAREER_CATEGORIES.items():
        if career_key in cat_careers:
            for c in cat_careers:
                if c != career_key and c in CAREER_DATA:
                    related_careers.append({'key': c, **CAREER_DATA[c]})
            break
    
    return render_template('career_details.html', 
                          career=career_info,
                          career_key=career_key,
                          related_careers=related_careers[:3])

@app.route('/browse-careers')
def browse_careers():
    """Browse all careers by category"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    return render_template('browse_careers.html', 
                          categories=CAREER_CATEGORIES,
                          careers=CAREER_DATA)

# ==================== ADMIN PANEL ROUTES ====================

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    """Admin Login"""
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = hashlib.sha256(request.form.get('password', '').encode()).hexdigest()
        
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        try:
            c.execute("SELECT id, username FROM admins WHERE username = ? AND password = ?", (username, password))
            admin = c.fetchone()
            
            if admin:
                session['admin_id'] = admin[0]
                session['admin_username'] = admin[1]
                return redirect(url_for('admin_dashboard'))
            else:
                flash('Invalid admin credentials', 'error')
        except sqlite3.Error as e:
            flash(f'Database error: {str(e)}', 'error')
        finally:
            conn.close()
    
    return render_template('admin_login.html')

@app.route('/admin-register', methods=['GET', 'POST'])
def admin_register():
    """Admin Registration - Create new admin account"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if not username or not password:
            flash('Please fill all fields', 'error')
            return render_template('admin_register.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('admin_register.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters', 'error')
            return render_template('admin_register.html')
        
        # Hash password
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        try:
            # Check if username already exists
            c.execute("SELECT id FROM admins WHERE username = ?", (username,))
            if c.fetchone():
                flash('Username already exists', 'error')
                return render_template('admin_register.html')
            
            # Insert new admin
            c.execute("INSERT INTO admins (username, password) VALUES (?, ?)", (username, hashed_password))
            conn.commit()
            
            flash('Admin registered successfully! Please login.', 'success')
            return redirect(url_for('admin_login'))
        except sqlite3.Error as e:
            flash(f'Database error: {str(e)}', 'error')
        finally:
            conn.close()
    
    return render_template('admin_register.html')

@app.route('/admin-dashboard')
def admin_dashboard():
    """Admin Dashboard - User Management"""
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # Get all users
    c.execute("SELECT id, name, email FROM users ORDER BY id DESC")
    users = c.fetchall()
    
    # Get total users count
    c.execute("SELECT COUNT(*) FROM users")
    total_users = c.fetchone()[0]
    
    # Get total results count
    c.execute("SELECT COUNT(*) FROM results")
    total_results = c.fetchone()[0]
    
    # Get career distribution
    c.execute("SELECT career, COUNT(*) as count FROM results GROUP BY career ORDER BY count DESC LIMIT 10")
    career_stats = c.fetchall()
    
    # Get recent users
    c.execute("SELECT id, name, email FROM users ORDER BY id DESC LIMIT 10")
    recent_users = c.fetchall()
    
    conn.close()
    
    return render_template('admin_dashboard.html',
                          users=users,
                          total_users=total_users,
                          total_results=total_results,
                          career_stats=career_stats,
                          recent_users=recent_users)

@app.route('/admin-users')
def admin_users():
    """View all users - Admin only"""
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # Get all users with their results
    c.execute("""
        SELECT u.id, u.name, u.email, 
               (SELECT COUNT(*) FROM results WHERE user_id = u.id) as result_count,
               (SELECT COUNT(*) FROM certificates WHERE user_id = u.id) as cert_count
        FROM users u 
        ORDER BY u.id DESC
    """)
    users = c.fetchall()
    
    conn.close()
    
    return render_template('admin_users.html', users=users)

@app.route('/admin-user/<int:user_id>')
def admin_user_details(user_id):
    """View specific user details - Admin only"""
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # Get user info
    c.execute("SELECT id, name, email FROM users WHERE id = ?", (user_id,))
    user = c.fetchone()
    
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('admin_users'))
    
    # Get user's career results
    c.execute("SELECT career, skills, salary, date_created FROM results WHERE user_id = ? ORDER BY id DESC", (user_id,))
    results = c.fetchall()
    
    # Get user's personality tests
    c.execute("SELECT personality_type, strengths, weaknesses, suitable_careers FROM personality_tests WHERE user_id = ? ORDER BY id DESC", (user_id,))
    personality_tests = c.fetchall()
    
    # Get user's aptitude tests
    c.execute("SELECT overall_score, recommendation, date_taken FROM aptitude_tests WHERE user_id = ? ORDER BY id DESC", (user_id,))
    aptitude_tests = c.fetchall()
    
    conn.close()
    
    return render_template('admin_user_details.html',
                          user=user,
                          results=results,
                          personality_tests=personality_tests,
                          aptitude_tests=aptitude_tests)

@app.route('/admin-delete-user/<int:user_id>')
def admin_delete_user(user_id):
    """Delete a user - Admin only"""
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    try:
        # Delete user's data from all related tables
        c.execute("DELETE FROM results WHERE user_id = ?", (user_id,))
        c.execute("DELETE FROM personality_tests WHERE user_id = ?", (user_id,))
        c.execute("DELETE FROM aptitude_tests WHERE user_id = ?", (user_id,))
        c.execute("DELETE FROM progress WHERE user_id = ?", (user_id,))
        c.execute("DELETE FROM user_courses WHERE user_id = ?", (user_id,))
        c.execute("DELETE FROM certificates WHERE user_id = ?", (user_id,))
        c.execute("DELETE FROM resumes WHERE user_id = ?", (user_id,))
        c.execute("DELETE FROM mentor_sessions WHERE user_id = ?", (user_id,))
        c.execute("DELETE FROM chat_history WHERE user_id = ?", (user_id,))
        c.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        flash('User deleted successfully', 'success')
    except Exception as e:
        flash(f'Error deleting user: {str(e)}', 'error')
    
    conn.close()
    return redirect(url_for('admin_users'))

@app.route('/admin-logout')
def admin_logout():
    """Admin Logout"""
    session.pop('admin_id', None)
    session.pop('admin_username', None)
    return redirect(url_for('admin_login'))

# ==================== ADDITIONAL FEATURE ROUTES ====================

@app.route('/personality-test', methods=['GET', 'POST'])
def personality_test():
    """Personality Test"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    questions = [
        {'question': 'How do you prefer to work?', 
         'options': [{'value': 'alone', 'text': 'Alone'}, {'value': 'team', 'text': 'In a team'}, {'value': 'both', 'text': 'Both fine'}]},
        {'question': 'When making decisions, you rely more on:', 
         'options': [{'value': 'logic', 'text': 'Logic and analysis'}, {'value': 'feelings', 'text': 'Values and emotions'}]},
        {'question': 'In social situations, you usually:', 
         'options': [{'value': 'listen', 'text': 'Listen and observe'}, {'value': 'talk', 'text': 'Talk and lead'}, {'value': 'both', 'text': 'Mix both'}]},
        {'question': 'When learning something new, you prefer:', 
         'options': [{'value': 'theory', 'text': 'Reading and theory'}, {'value': 'practice', 'text': 'Hands-on practice'}]},
        {'question': 'When planning your day, you prefer to:', 
         'options': [{'value': 'planned', 'text': 'Have a detailed plan'}, {'value': 'flexible', 'text': 'Be spontaneous'}]}
    ]
    
    if request.method == 'POST':
        answers = []
        for i in range(1, 6):
            answer = request.form.get(f'q{i}', '')
            answers.append(answer)
        
        # Calculate personality type
        introvert_score = sum([1 for a in answers if a in ['alone', 'listen', 'theory', 'planned']])
        extrovert_score = sum([1 for a in answers if a in ['team', 'talk', 'both']])
        
        if introvert_score > extrovert_score:
            personality_type = "Introvert"
            strengths = "Deep thinking, focused, independent, good listener, analytical"
            weaknesses = "May struggle with large groups, can overthink"
            suitable_careers = "Research, Writing, Programming, Science, Engineering, Accounting"
        elif extrovert_score > introvert_score:
            personality_type = "Extrovert"
            strengths = "Outgoing, great communicator, networking skills, energetic"
            weaknesses = "May avoid solitude, can be impulsive"
            suitable_careers = "Sales, Marketing, Public Relations, Entertainment, Politics"
        else:
            personality_type = "Ambivert"
            strengths = "Balanced approach, adaptable, good communicator, flexible"
            weaknesses = "May struggle to commit to one style"
            suitable_careers = "Business, Marketing, Management, Teaching, Healthcare"
        
        # Save to database
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("INSERT INTO personality_tests (user_id, personality_type, strengths, weaknesses, suitable_careers) VALUES (?, ?, ?, ?, ?)",
                  (session['user_id'], personality_type, strengths, weaknesses, suitable_careers))
        conn.commit()
        conn.close()
        
        return render_template('personality_result.html',
                              personality_type=personality_type,
                              strengths=strengths,
                              weaknesses=weaknesses,
                              suitable_careers=suitable_careers)
    
    return render_template('personality_test.html', questions=questions)

@app.route('/aptitude-test', methods=['GET', 'POST'])
def aptitude_test():
    """Aptitude Test"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    questions = {
        'logical': [
            {'question': 'What comes next: 2, 6, 12, 20, 30, ?', 'options': ['40', '42', '44', '46'], 'answer': '42'},
            {'question': 'If A=1, B=2, what is the value of CAB?', 'options': ['12', '9', '6', '3'], 'answer': '12'},
            {'question': 'Find the odd one out: Apple, Mango, Carrot, Orange', 'options': ['Apple', 'Mango', 'Carrot', 'Orange'], 'answer': 'Carrot'}
        ],
        'verbal': [
            {'question': 'Opposite of "Artificial" is?', 'options': ['Natural', 'Synthetic', 'Fake', 'Man-made'], 'answer': 'Natural'},
            {'question': 'Synonym of "Happy" is?', 'options': ['Sad', 'Joyful', 'Angry', 'Tired'], 'answer': 'Joyful'},
            {'question': 'Complete: Time and ___ wait for no man', 'options': ['Money', 'Tide', 'Opportunity', 'Death'], 'answer': 'Tide'}
        ],
        'numerical': [
            {'question': 'What is 25% of 200?', 'options': ['25', '50', '75', '100'], 'answer': '50'},
            {'question': 'If 3 workers complete a job in 6 days, how many days will 6 workers take?', 'options': ['3 days', '4 days', '6 days', '12 days'], 'answer': '3 days'},
            {'question': 'Find average: 10, 20, 30, 40', 'options': ['20', '25', '30', '35'], 'answer': '25'}
        ]
    }
    
    if request.method == 'POST':
        logical_score = 0
        verbal_score = 0
        numerical_score = 0
        
        # Check logical answers
        for i, q in enumerate(questions['logical']):
            answer = request.form.get(f'logical_{i}', '')
            if answer == q['answer']:
                logical_score += 1
        
        # Check verbal answers
        for i, q in enumerate(questions['verbal']):
            answer = request.form.get(f'verbal_{i}', '')
            if answer == q['answer']:
                verbal_score += 1
        
        # Check numerical answers
        for i, q in enumerate(questions['numerical']):
            answer = request.form.get(f'numerical_{i}', '')
            if answer == q['answer']:
                numerical_score += 1
        
        total_score = logical_score + verbal_score + numerical_score
        overall_score = int((total_score / 9) * 100)
        
        # Determine recommendation
        if overall_score >= 80:
            recommendation = "Excellent! You can pursue any career. Consider fields like Data Science, Research, Engineering, or Management."
        elif overall_score >= 60:
            recommendation = "Good! You have strong analytical skills. Consider Business Analysis, Marketing, or Technical fields."
        elif overall_score >= 40:
            recommendation = "Average. Focus on improving your skills. Consider careers that match your interests rather than aptitude."
        else:
            recommendation = "Consider exploring careers based on your interests and passions rather than aptitude scores."
        
        # Save to database
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("INSERT INTO aptitude_tests (user_id, logical_score, verbal_score, numerical_score, overall_score, recommendation) VALUES (?, ?, ?, ?, ?, ?)",
                  (session['user_id'], logical_score, verbal_score, numerical_score, overall_score, recommendation))
        conn.commit()
        conn.close()
        
        return render_template('aptitude_result.html',
                              logical_score=logical_score,
                              verbal_score=verbal_score,
                              numerical_score=numerical_score,
                              overall_score=overall_score,
                              recommendation=recommendation)
    
    return render_template('aptitude_test.html', questions=questions)

@app.route('/mentors')
def mentors():
    """Mentor listing page"""
    # Removed login requirement - mentors should be publicly accessible
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM mentors WHERE available = 'yes'")
    mentors = c.fetchall()
    conn.close()
    
    return render_template('mentors.html', mentors=mentors)

@app.route('/certificates')
def certificates():
    """User certificates"""
    # Removed login requirement - certificates page shows info to all users
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # Check if user is logged in
    if 'user_id' in session:
        c.execute("SELECT * FROM certificates WHERE user_id = ? ORDER BY issue_date DESC", (session['user_id'],))
        certificates = c.fetchall()
    else:
        certificates = []
    
    conn.close()
    
    return render_template('certificates.html', certificates=certificates)

@app.route('/progress')
def progress():
    """User progress tracking"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM progress WHERE user_id = ? ORDER BY date_updated DESC", (session['user_id'],))
    progress_data = c.fetchall()
    conn.close()
    
    return render_template('progress.html', progress=progress_data)

@app.route('/resume-builder', methods=['GET', 'POST'])
def resume_builder():
    """AI Resume Builder"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        resume_data = {
            'name': request.form.get('name', ''),
            'email': request.form.get('email', ''),
            'phone': request.form.get('phone', ''),
            'location': request.form.get('location', ''),
            'linkedin': request.form.get('linkedin', ''),
            'portfolio': request.form.get('portfolio', ''),
            'summary': request.form.get('summary', ''),
            'education': request.form.get('education', ''),
            'skills': request.form.get('skills', ''),
            'internship': request.form.get('internship', ''),
            'experience': request.form.get('experience', ''),
            'projects': request.form.get('projects', ''),
            'certifications': request.form.get('certifications', ''),
            'languages': request.form.get('languages', ''),
            'hobbies': request.form.get('hobbies', '')
        }
        
        # Handle photo upload
        photo_filename = None
        if 'photo' in request.files:
            photo = request.files['photo']
            if photo and allowed_file(photo.filename):
                filename = secure_filename(photo.filename)
                # Add unique identifier to filename
                photo_filename = f"resume_{session['user_id']}_{filename}"
                photo.save(os.path.join(app.config['UPLOAD_FOLDER'], photo_filename))
        
        # Get career target from form
        career_target = request.form.get('career_target', '')
        
        # Save resume with photo filename
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("INSERT INTO resumes (user_id, resume_data, career_target, photo) VALUES (?, ?, ?, ?)",
                  (session['user_id'], str(resume_data), career_target, photo_filename))
        conn.commit()
        conn.close()
        
        flash('Resume saved successfully!', 'success')
        return redirect(url_for('resume_preview'))
    
    return render_template('resume_builder.html')

@app.route('/resume-preview')
def resume_preview():
    """Preview resume"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM resumes WHERE user_id = ? ORDER BY id DESC LIMIT 1", (session['user_id'],))
    resume = c.fetchone()
    conn.close()
    
    if resume:
        import ast
        resume_data = ast.literal_eval(resume[2])
        return render_template('resume_preview.html', resume=resume_data, career_target=resume[3], photo=resume[4] if len(resume) > 4 else None)
    
    return redirect(url_for('resume_builder'))

# ==================== SALARY PREDICTION ROUTE ====================

@app.route('/salary-predict', methods=['GET', 'POST'])
def salary_predict():
    """Salary Prediction Feature"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Get user's recommended career
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT career FROM results WHERE user_id = ? ORDER BY id DESC LIMIT 1", (session['user_id'],))
    result = c.fetchone()
    
    career = result[0] if result else "Software Developer"
    
    # Detailed salary data for each career
    salary_data = {
        'entry': '₹3-5 LPA',
        'mid': '₹8-15 LPA',
        'senior': '₹20-40 LPA',
        'growth_rate': '15-20% annually'
    }
    
    # Map career to detailed salary data
    career_salary_map = {
        'Software Developer': {'entry': '₹4-8 LPA', 'mid': '₹12-25 LPA', 'senior': '₹30-50+ LPA', 'growth_rate': '20-25% annually'},
        'Graphic Designer': {'entry': '₹2-4 LPA', 'mid': '₹6-12 LPA', 'senior': '₹15-25 LPA', 'growth_rate': '12-18% annually'},
        'Singer': {'entry': '₹2-5 LPA', 'mid': '₹8-15 LPA', 'senior': '₹20-50+ LPA', 'growth_rate': 'Variable'},
        'Dancer': {'entry': '₹2-5 LPA', 'mid': '₹8-18 LPA', 'senior': '₹20-40+ LPA', 'growth_rate': '15-20% annually'},
        'Doctor': {'entry': '₹6-12 LPA', 'mid': '₹15-30 LPA', 'senior': '₹40-100+ LPA', 'growth_rate': '18-25% annually'},
        'Research Scientist': {'entry': '₹4-8 LPA', 'mid': '₹12-20 LPA', 'senior': '₹25-45 LPA', 'growth_rate': '12-18% annually'},
        'Business Analyst': {'entry': '₹4-8 LPA', 'mid': '₹10-20 LPA', 'senior': '₹25-40 LPA', 'growth_rate': '15-20% annually'},
        'Data Scientist': {'entry': '₹6-12 LPA', 'mid': '₹15-30 LPA', 'senior': '₹35-60+ LPA', 'growth_rate': '22-28% annually'},
        'Digital Marketing Manager': {'entry': '₹3-6 LPA', 'mid': '₹8-15 LPA', 'senior': '₹20-35 LPA', 'growth_rate': '18-22% annually'},
        'Healthcare Administrator': {'entry': '₹4-8 LPA', 'mid': '₹10-18 LPA', 'senior': '₹22-40 LPA', 'growth_rate': '14-18% annually'}
    }
    
    for key, data in career_salary_map.items():
        if key.lower() in career.lower():
            salary_data = data
            break
    
    conn.close()
    
    return render_template('salary_predict.html', career=career, salary_data=salary_data)

# ==================== COLLEGES ROUTE ====================

@app.route('/colleges', methods=['GET', 'POST'])
def colleges():
    """Colleges Recommendation Feature"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Get user's recommended career
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT career FROM results WHERE user_id = ? ORDER BY id DESC LIMIT 1", (session['user_id'],))
    result = c.fetchone()
    
    career = result[0] if result else "Software Developer"
    
    # Colleges data for each career
    colleges_map = {
        'Software Developer': {
            'colleges': ['IIT Bombay', 'IIT Delhi', 'IIT Bangalore', 'NIT Trichy', 'BITS Pilani', 'VIT Vellore', 'COEP Pune'],
            'entrance_exams': 'JEE Main, JEE Advanced, BITSAT, VITEEE'
        },
        'Graphic Designer': {
            'colleges': ['National Institute of Design', 'MIT Institute of Design', 'Pearl Academy', 'Shrishti School of Design', 'JD Institute'],
            'entrance_exams': 'NID DAT, UCEED, NIFT'
        },
        'Singer': {
            'colleges': ['Berklee College of Music', 'Bhatkhande Music Institute', 'Shankar Mahadevan Academy', 'KM Music Conservatory'],
            'entrance_exams': 'Audition Based'
        },
        'Dancer': {
            'colleges': ['Kalakshetra Foundation', 'National School of Drama', 'Pingal Khan Academy', 'Mudra Institute'],
            'entrance_exams': 'Audition Based'
        },
        'Doctor': {
            'colleges': ['AIIMS Delhi', 'PGIMER Chandigarh', 'CMC Vellore', 'SGPGI Lucknow', 'KEM Mumbai', 'Grant Medical College'],
            'entrance_exams': 'NEET PG, NEET UG'
        },
        'Research Scientist': {
            'colleges': ['IISc Bangalore', 'IIT Delhi', 'IIT Bombay', 'TIFR Mumbai', 'IACS Kolkata', 'IITs'],
            'entrance_exams': 'JEE Advanced, GATE, JEST'
        },
        'Business Analyst': {
            'colleges': ['IIM Ahmedabad', 'IIM Bangalore', 'IIM Calcutta', 'ISB Hyderabad', 'JBIMS Mumbai', 'SP Jain'],
            'entrance_exams': 'CAT, XAT, GMAT'
        },
        'Data Scientist': {
            'colleges': ['IIT Bombay', 'IIT Delhi', 'IIIT Bangalore', 'BITS Pilani', 'Great Lakes', 'UpGrad'],
            'entrance_exams': 'GATE, GRE, CAT'
        },
        'Digital Marketing Manager': {
            'colleges': ['Digital Marketing Institute', 'IIDE Mumbai', 'Manipal ProLearn', 'Simplilearn', 'UpGrad'],
            'entrance_exams': 'No specific exam required'
        },
        'Healthcare Administrator': {
            'colleges': ['AIIMS', 'IIM Ahmedabad (Healthcare)', 'TISS Mumbai', 'NIHFW', 'Apollo Hospitals Training'],
            'entrance_exams': 'CAT, TISSNET'
        }
    }
    
    colleges_list = ['IIT Bombay', 'IIT Delhi', 'NIT Trichy', 'BITS Pilani']
    entrance_exams = 'JEE Main, JEE Advanced'
    
    for key, data in colleges_map.items():
        if key.lower() in career.lower():
            colleges_list = data['colleges']
            entrance_exams = data['entrance_exams']
            break
    
    conn.close()
    
    return render_template('colleges.html', career=career, colleges=colleges_list, entrance_exams=entrance_exams)

# ==================== COURSES & VIDEOS ROUTE ====================

@app.route('/courses', methods=['GET', 'POST'])
def courses():
    """Courses and Videos Learning Platform"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Get user's recommended career
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT career FROM results WHERE user_id = ? ORDER BY id DESC LIMIT 1", (session['user_id'],))
    result = c.fetchone()
    
    user_career = result[0] if result else "Software Developer"
    
    # Get selected category
    selected_category = request.args.get('category', 'all')
    
    # All courses and videos data with real YouTube video links
    COURSES_DATA = {
        'Technology': {
            'courses': [
                {'name': 'Python Programming Masterclass', 'provider': 'Great Learning', 'link': 'https://www.greatlearning.com/python-programming', 'duration': '12 hours', 'level': 'Beginner'},
                {'name': 'Full Stack Web Development', 'provider': 'Scaler Academy', 'link': 'https://www.scaler.com/topics/full-stack-development/', 'duration': '6 months', 'level': 'Intermediate'},
                {'name': 'Data Science with Python', 'provider': 'Simplilearn', 'link': 'https://www.simplilearn.com/data-scientist-master-certificate-training', 'duration': '11 months', 'level': 'Advanced'},
                {'name': 'Machine Learning A-Z', 'provider': 'Udemy', 'link': 'https://www.udemy.com/course/machinelearning/', 'duration': '44 hours', 'level': 'All Levels'},
                {'name': 'Cloud Computing Fundamentals', 'provider': 'AWS Training', 'link': 'https://aws.amazon.com/training/', 'duration': '20 hours', 'level': 'Beginner'},
                {'name': 'Java Programming Complete', 'provider': 'Coursera', 'link': 'https://www.coursera.org/specializations/java-programming', 'duration': '6 months', 'level': 'Beginner'},
            ],
            'videos': [
                {'title': 'Python Tutorial for Beginners', 'channel': 'Code With Harry', 'video_id': 'qp8xa-frhwE', 'duration': '1:30:00'},
                {'title': 'Web Development Full Course', 'channel': 'Apna College', 'video_id': 'l1EssrL9LSw', 'duration': '12:00:00'},
                {'title': 'Data Science Complete Guide', 'channel': 'Krish Naik', 'video_id': 'ua-CiDNNj30', 'duration': '8:00:00'},
                {'title': 'Machine Learning Tutorial', 'channel': 'StatQuest with Josh Starmer', 'video_id': 'GwzzE4C2fF0', 'duration': '45:00'},
            ]
        },
        'Healthcare': {
            'courses': [
                {'name': 'MBBS Preparation Course', 'provider': 'PrepLadder', 'link': 'https://www.prepladder.com/', 'duration': '2 years', 'level': 'Intermediate'},
                {'name': 'Nursing Fundamentals', 'provider': 'Coursera', 'link': 'https://www.coursera.org/browse/health-science', 'duration': '6 months', 'level': 'Beginner'},
                {'name': 'Healthcare Management MBA', 'provider': 'TISS', 'link': 'https://www.tiss.edu/', 'duration': '2 years', 'level': 'Advanced'},
                {'name': 'Pharmacy Degree Course', 'provider': 'B Pharmacy', 'link': 'https://www.pharmacy.gov.in/', 'duration': '4 years', 'level': 'Graduate'},
                {'name': 'Medical Coding Training', 'provider': 'AAPC', 'link': 'https://www.aapc.com/', 'duration': '6 months', 'level': 'Beginner'},
                {'name': 'Hospital Administration', 'provider': 'Apollo MedSkills', 'link': 'https://www.apollomedskills.com/', 'duration': '1 year', 'level': 'Intermediate'},
            ],
            'videos': [
                {'title': 'How to Become a Doctor in India', 'channel': 'Motion Education', 'video_id': 'YzKqjKfqE8I', 'duration': '15:00'},
                {'title': 'MBBS Full Details', 'channel': 'Gyan Tara', 'video_id': 'Y8V-GG9BzQ8', 'duration': '20:00'},
                {'title': 'NEET Preparation Strategy', 'channel': 'Vedantu', 'video_id': 'O7GkX3TZ0pE', 'duration': '25:00'},
                {'title': 'Healthcare Management Overview', 'channel': 'IIM Ahmedabad', 'video_id': 'x8f8f8f8f8f8', 'duration': '10:00'},
            ]
        },
        'Business': {
            'courses': [
                {'name': 'Business Analytics with Excel', 'provider': 'Coursera', 'link': 'https://www.coursera.org/learn/excel-analytics', 'duration': '20 hours', 'level': 'Beginner'},
                {'name': 'Digital Marketing Masterclass', 'provider': 'Udemy', 'link': 'https://www.udemy.com/course/digital-marketing-course/', 'duration': '40 hours', 'level': 'All Levels'},
                {'name': 'MBA Foundation Course', 'provider': 'IMS', 'link': 'https://www.imsindia.com/', 'duration': '1 year', 'level': 'Intermediate'},
                {'name': 'Financial Modeling Course', 'provider': 'Wall Street Mojo', 'link': 'https://www.wallstreetmojo.com/financial-modeling-course/', 'duration': '30 hours', 'level': 'Advanced'},
                {'name': 'Banking & Finance Course', 'provider': 'IBPS', 'link': 'https://www.ibps.in/', 'duration': '6 months', 'level': 'Beginner'},
                {'name': 'Startup Entrepreneurship', 'provider': 'Startup India', 'link': 'https://www.startupindia.gov.in/', 'duration': '3 months', 'level': 'All Levels'},
            ],
            'videos': [
                {'title': 'Business Analyst Full Course', 'channel': 'Edureka', 'video_id': 'Q0iL8xD3s4U', 'duration': '3:00:00'},
                {'title': 'Digital Marketing Tutorial', 'channel': 'Simplilearn', 'video_id': 'd3Xj3oMT5v0', 'duration': '2:30:00'},
                {'title': 'How to Prepare for CAT', 'channel': 'Unacademy', 'video_id': 'd5Y6Xh9J2cM', 'duration': '45:00'},
                {'title': 'Startup Ideas for Students', 'channel': 'Ankur Warikoo', 'video_id': 'hY9mUZgZ2vU', 'duration': '20:00'},
            ]
        },
        'Creative Arts': {
            'courses': [
                {'name': 'Graphic Design Masterclass', 'provider': 'Udemy', 'link': 'https://www.udemy.com/course/graphic-design/', 'duration': '15 hours', 'level': 'Beginner'},
                {'name': 'UI/UX Design Complete', 'provider': 'Coursera', 'link': 'https://www.coursera.org/profional-certificate/google-ux-design', 'duration': '6 months', 'level': 'Beginner'},
                {'name': 'Video Editing Pro Course', 'provider': 'Premiere Pro', 'link': 'https://www.adobe.com/education/expression-education/', 'duration': '20 hours', 'level': 'Intermediate'},
                {'name': 'Animation & VFX Course', 'provider': 'MAAC', 'link': 'https://www.maacindia.com/', 'duration': '2 years', 'level': 'Advanced'},
                {'name': 'Photography Masterclass', 'provider': 'National Geographic', 'link': 'https://www.nationalgeographic.com/education/', 'duration': '10 hours', 'level': 'All Levels'},
                {'name': 'Music Production Course', 'provider': 'Berklee Online', 'link': 'https://online.berklee.edu/', 'duration': '1 year', 'level': 'Beginner'},
            ],
            'videos': [
                {'title': 'Graphic Design Tutorial', 'channel': 'GFXMentor', 'video_id': 'W-z-0M3WcS8', 'duration': '1:00:00'},
                {'title': 'UI/UX Design Complete', 'channel': 'Figma', 'video_id': 'q4yJ7c6S8fU', 'duration': '2:00:00'},
                {'title': 'Photoshop Full Course', 'channel': 'Phlearn', 'video_id': 'N2W3t5P4k9E', 'duration': '3:00:00'},
                {'title': 'Music Theory Basics', 'channel': 'Adam Neely', 'video_id': 'K2I8g8f8f8', 'duration': '30:00'},
            ]
        },
        'Science': {
            'courses': [
                {'name': 'B.Sc Physics/Chemistry/Math', 'provider': 'IIT Coaching', 'link': 'https://www.vedantu.com/', 'duration': '2 years', 'level': 'Intermediate'},
                {'name': 'Research Methodology', 'provider': 'NPTEL', 'link': 'https://nptel.ac.in/', 'duration': '12 weeks', 'level': 'Advanced'},
                {'name': 'Chemistry Olympiad Prep', 'provider': 'HBCSE', 'link': 'https://www.hbcse.tifr.res.in/', 'duration': '1 year', 'level': 'Advanced'},
                {'name': 'Biotechnology Course', 'provider': 'BIONITY', 'link': 'https://www.biotecnika.org/', 'duration': '6 months', 'level': 'Intermediate'},
                {'name': 'Environmental Science', 'provider': 'UGC', 'link': 'https://ugc.ac.in/', 'duration': '1 year', 'level': 'Graduate'},
                {'name': 'Forensic Science Course', 'provider': 'CBI', 'link': 'https://cbi.gov.in/', 'duration': '1 year', 'level': 'Advanced'},
            ],
            'videos': [
                {'title': 'Physics Complete Class 11-12', 'channel': 'Physics Wallah', 'video_id': '3CRmu8mBT_k', 'duration': '10:00:00'},
                {'title': 'Chemistry Full Course', 'channel': 'Vedantu', 'video_id': 'N2Jax7vK3cM', 'duration': '8:00:00'},
                {'title': 'Maths JEE Preparation', 'channel': 'Maths NCERT', 'video_id': 'M8Y8Xh9K2fU', 'duration': '15:00:00'},
                {'title': 'Biology NEET Prep', 'channel': 'Biology byju', 'video_id': 'K9Y8Xh7V3cM', 'duration': '12:00:00'},
            ]
        }
    }
    
    # Default courses for all users
    default_courses = [
        {'name': 'Career Development Workshop', 'provider': 'LinkedIn Learning', 'link': 'https://www.linkedin.com/learning/', 'duration': '4 hours', 'level': 'Beginner'},
        {'name': 'Communication Skills', 'provider': 'Coursera', 'link': 'https://www.coursera.org/learn/communication-skills', 'duration': '8 hours', 'level': 'Beginner'},
        {'name': 'Interview Preparation', 'provider': 'InterviewBit', 'link': 'https://www.interviewbit.com/', 'duration': '20 hours', 'level': 'Intermediate'},
        {'name': 'Resume Writing Masterclass', 'provider': 'Udemy', 'link': 'https://www.udemy.com/course/resume-writing/', 'duration': '2 hours', 'level': 'Beginner'},
        {'name': 'Time Management', 'provider': 'Great Learning', 'link': 'https://www.greatlearning.com/time-management', 'duration': '6 hours', 'level': 'Beginner'},
        {'name': 'Leadership Skills', 'provider': 'EdX', 'link': 'https://www.edx.org/', 'duration': '12 hours', 'level': 'Intermediate'},
    ]
    
    default_videos = [
        {'title': 'How to Write a Resume', 'channel': 'Indeed', 'video_id': 'y8MmFcm7T4w', 'duration': '5:00'},
        {'title': 'Interview Tips 2024', 'channel': 'Hiration', 'video_id': '8d8X8X8X8X8', 'duration': '10:00'},
        {'title': 'Career Guidance for Students', 'channel': 'Career Ride', 'video_id': '9a9b9b9b9b9b', 'duration': '15:00'},
    ]
    
    # Get courses based on career category
    def get_career_category(career):
        career_lower = career.lower()
        if 'software' in career_lower or 'developer' in career_lower or 'data' in career_lower or 'engineer' in career_lower or 'technology' in career_lower:
            return 'Technology'
        elif 'doctor' in career_lower or 'medical' in career_lower or 'health' in career_lower or 'nurse' in career_lower or 'biology' in career_lower:
            return 'Healthcare'
        elif 'business' in career_lower or 'marketing' in career_lower or 'analyst' in career_lower or 'manager' in career_lower or 'finance' in career_lower:
            return 'Business'
        elif 'design' in career_lower or 'artist' in career_lower or 'singer' in career_lower or 'dance' in career_lower or 'creative' in career_lower:
            return 'Creative Arts'
        elif 'science' in career_lower or 'research' in career_lower or 'teacher' in career_lower:
            return 'Science'
        else:
            return 'Technology'  # Default
    
    category = get_career_category(user_career)
    
    # Get selected data
    if selected_category == 'all':
        recommended_courses = COURSES_DATA.get(category, {}).get('courses', default_courses)
        videos = COURSES_DATA.get(category, {}).get('videos', default_videos)
    elif selected_category == 'courses':
        recommended_courses = COURSES_DATA.get(category, {}).get('courses', default_courses)
        videos = []
    elif selected_category == 'videos':
        recommended_courses = []
        videos = COURSES_DATA.get(category, {}).get('videos', default_videos)
    elif selected_category == 'default':
        recommended_courses = default_courses
        videos = default_videos
    else:
        recommended_courses = COURSES_DATA.get(selected_category, {}).get('courses', default_courses)
        videos = COURSES_DATA.get(selected_category, {}).get('videos', default_videos)
    
    conn.close()
    
    # Get all available categories
    all_categories = list(COURSES_DATA.keys())
    
    return render_template('courses.html', 
                          career=user_career,
                          recommended_courses=recommended_courses,
                          videos=videos,
                          category=category,
                          all_categories=all_categories,
                          selected_category=selected_category)

# ==================== PARENTS CORNER ROUTE ====================

@app.route('/parents-corner')
def parents_corner():
    """Parents Corner - Information for parents about career guidance"""
    return render_template('parents_corner.html')

# ==================== ADMIN PAGE ROUTE ====================

@app.route('/admin')
def admin():
    """Simple Admin Page - Overview stats"""
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # Get counts
    c.execute('SELECT COUNT(*) FROM users')
    user_count = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM results')
    result_count = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM certificates')
    cert_count = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM courses')
    course_count = c.fetchone()[0]
    
    # Get recent users
    c.execute('SELECT id, name, email FROM users ORDER BY id DESC LIMIT 5')
    recent_users = c.fetchall()
    
    conn.close()
    
    return render_template('admin.html', 
                          user_count=user_count,
                          result_count=result_count,
                          cert_count=cert_count,
                          course_count=course_count,
                          recent_users=recent_users)

# ==================== CERTIFICATE VIEW ROUTE ====================

@app.route('/certificate/<int:cert_id>')
def certificate_view(cert_id):
    """View individual certificate"""
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    c.execute('SELECT * FROM certificates WHERE id = ?', (cert_id,))
    certificate = c.fetchone()
    
    conn.close()
    
    if certificate:
        return render_template('certificate_view.html', certificate=certificate)
    else:
        flash('Certificate not found')
        return redirect(url_for('certificates'))

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
