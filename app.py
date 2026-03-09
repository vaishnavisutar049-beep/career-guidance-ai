from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file, jsonify
import sqlite3
import hashlib
import os
import requests
import json
from werkzeug.utils import secure_filename
from translations import get_all_texts

# YouTube Data API Configuration
YOUTUBE_API_KEY = os.environ.get('YOUTUBE_API_KEY', '')
YOUTUBE_API_BASE_URL = 'https://www.googleapis.com/youtube/v3'

def search_youtube_videos(query, max_results=8):
    """Search YouTube videos using the YouTube Data API"""
    if not YOUTUBE_API_KEY:
        return None  # Return None if no API key is configured
    
    try:
        search_url = f"{YOUTUBE_API_BASE_URL}/search"
        params = {
            'part': 'snippet',
            'q': query,
            'type': 'video',
            'maxResults': max_results,
            'key': YOUTUBE_API_KEY
        }
        
        response = requests.get(search_url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            videos = []
            
            for item in data.get('items', []):
                video_id = item['id']['videoId']
                snippet = item['snippet']
                
                videos.append({
                    'title': snippet['title'],
                    'channel': snippet['channelTitle'],
                    'video_id': video_id,
                    'description': snippet.get('description', '')[:100],
                    'thumbnail': snippet['thumbnails']['high']['url'] if 'high' in snippet['thumbnails'] else snippet['thumbnails']['medium']['url']
                })
            
            return videos
        else:
            print(f"YouTube API Error: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"YouTube API Error: {str(e)}")
        return None

def get_video_details(video_ids):
    """Get detailed information about YouTube videos including duration"""
    if not YOUTUBE_API_KEY or not video_ids:
        return []
    
    try:
        videos_url = f"{YOUTUBE_API_BASE_URL}/videos"
        params = {
            'part': 'contentDetails,snippet',
            'id': ','.join(video_ids),
            'key': YOUTUBE_API_KEY
        }
        
        response = requests.get(videos_url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            videos = []
            
            for item in data.get('items', []):
                snippet = item['snippet']
                content = item['contentDetails']
                
                # Parse ISO 8601 duration
                duration_iso = content.get('duration', 'PT0M0S')
                duration = parse_youtube_duration(duration_iso)
                
                videos.append({
                    'title': snippet['title'],
                    'channel': snippet['channelTitle'],
                    'video_id': item['id'],
                    'duration': duration,
                    'link': f"https://www.youtube.com/watch?v={item['id']}"
                })
            
            return videos
        else:
            return []
            
    except Exception as e:
        print(f"YouTube API Error: {str(e)}")
        return []

def parse_youtube_duration(iso_duration):
    """Parse YouTube ISO 8601 duration to human readable format"""
    import re
    
    match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', iso_duration)
    if not match:
        return '0:00'
    
    hours, minutes, seconds = match.groups()
    hours = int(hours) if hours else 0
    minutes = int(minutes) if minutes else 0
    seconds = int(seconds) if seconds else 0
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes}:{seconds:02d}"

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
    
    # Get chat history from database
    chat_history = []
    messages = []
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # Check for clear parameter
    if request.args.get('clear') == 'true':
        c.execute('DELETE FROM chat_messages WHERE user_id = ?', (session['user_id'],))
        conn.commit()
    
    # Get chat sessions
    try:
        c.execute('SELECT id, title FROM chat_sessions WHERE user_id = ? ORDER BY id DESC LIMIT 10', (session['user_id'],))
        chat_history = c.fetchall()
    except:
        pass
    
    # Get current chat messages
    chat_id = request.args.get('chat_id')
    if chat_id:
        try:
            c.execute('SELECT message, response, created_at FROM chat_messages WHERE user_id = ? AND session_id = ? ORDER BY id ASC', (session['user_id'], chat_id))
            rows = c.fetchall()
            for row in rows:
                messages.append({'type': 'user', 'text': row[0]})
                messages.append({'type': 'bot', 'text': row[1]})
        except:
            pass
    
    conn.close()
    
    return render_template('chat.html', chat_history=chat_history, messages=messages, name=session['name'])

@app.route('/get', methods=['POST'])
def get_chat_response():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_message = request.form.get('message', '')
    language = request.form.get('language', 'en')
    response = get_career_response(user_message, language)
    
    # Save chat to database
    try:
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        
        # Create tables if not exist
        c.execute('''CREATE TABLE IF NOT EXISTS chat_sessions 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, title TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        c.execute('''CREATE TABLE IF NOT EXISTS chat_messages 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, session_id INTEGER, message TEXT, response TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        
        # Get or create chat session
        c.execute('SELECT id FROM chat_sessions WHERE user_id = ? ORDER BY id DESC LIMIT 1', (session['user_id'],))
        session_row = c.fetchone()
        
        if session_row:
            session_id = session_row[0]
        else:
            c.execute('INSERT INTO chat_sessions (user_id, title) VALUES (?, ?)', (session['user_id'], user_message[:50]))
            session_id = c.lastrowid
        
        # Save message and response
        c.execute('INSERT INTO chat_messages (user_id, session_id, message, response) VALUES (?, ?, ?, ?)',
                 (session['user_id'], session_id, user_message, response))
        conn.commit()
        conn.close()
    except:
        pass
    
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

# ==================== AFTER 10TH CAREER GUIDANCE ====================

@app.route('/after-10th')
def after_10th():
    """Career guidance after 10th standard"""
    # Career options after 10th
    after_10th_options = [
        {
            'stream': 'Science ( विज्ञान )',
            'icon': 'flask',
            'description': 'Best for students interested in medical, engineering, and research fields',
            'courses': [
                {'name': 'Medical (PCB)', 'duration': '2 Years', 'after': 'MBBS, BAMS, BHMS, Nursing'},
                {'name': 'Engineering (PCM)', 'duration': '2 Years', 'after': 'B.Tech, B.E., Diploma'},
                {'name': 'Commerce with Maths', 'duration': '2 Years', 'after': 'B.Com, CA, BBA'},
                {'name': 'Commerce without Maths', 'duration': '2 Years', 'after': 'B.Com, BBA, Banking'},
                {'name': 'Arts/Humanities', 'duration': '2 Years', 'after': 'BA, Law, Journalism'},
                {'name': 'Diploma in ITI', 'duration': '1-2 Years', 'after': 'Technical Jobs'},
                {'name': 'Vocational Courses', 'duration': '1 Year', 'after': 'Skilled Jobs'},
            ]
        },
        {
            'stream': 'Commerce ( वाणिज्य )',
            'icon': 'chart-line',
            'description': 'For students interested in business, finance, and accounting',
            'courses': [
                {'name': 'Commerce with Mathematics', 'duration': '2 Years', 'after': 'CA, CS, B.Com (Hons)'},
                {'name': 'Commerce without Mathematics', 'duration': '2 Years', 'after': 'B.Com, BBA, Banking'},
                {'name': 'Commerce + Computer', 'duration': '2 Years', 'after': 'Tally, Accounting'},
            ]
        },
        {
            'stream': 'Arts ( कला )',
            'icon': 'palette',
            'description': 'For creative students interested in design, media, and humanities',
            'courses': [
                {'name': 'Arts with History', 'duration': '2 Years', 'after': 'BA History, Civil Services'},
                {'name': 'Arts with Psychology', 'duration': '2 Years', 'after': 'Psychologist, Counselor'},
                {'name': 'Arts with Economics', 'duration': '2 Years', 'after': 'Economist, Analyst'},
                {'name': 'Fine Arts', 'duration': '2-4 Years', 'after': 'Artist, Designer'},
                {'name': 'Fashion Design', 'duration': '2-4 Years', 'after': 'Fashion Designer'},
            ]
        },
        {
            'stream': 'Vocational ( व्यावसायिक )',
            'icon': 'tools',
            'description': 'Practical skills for immediate employment',
            'courses': [
                {'name': 'ITI - Electrician', 'duration': '2 Years', 'after': 'Electrician'},
                {'name': 'ITI - Fitter', 'duration': '2 Years', 'after': 'Mechanic'},
                {'name': 'ITI - Welder', 'duration': '1 Year', 'after': 'Welder'},
                {'name': 'Polytechnic Diploma', 'duration': '3 Years', 'after': 'Engineer'},
                {'name': 'Hospitality Management', 'duration': '1-2 Years', 'after': 'Hotel Jobs'},
                {'name': 'Paramedical Courses', 'duration': '1-2 Years', 'after': 'Nurse, Technician'},
            ]
        }
    ]
    
    return render_template('after_10th.html', options=after_10th_options)

# ==================== AFTER 12TH CAREER GUIDANCE ====================

@app.route('/after-12th')
def after_12th():
    """Career guidance after 12th standard"""
    # Career options after 12th
    after_12th_options = [
        {
            'stream': 'Engineering ( अभियांत्रिकी )',
            'icon': 'cogs',
            'description': 'For students interested in technology and engineering',
            'courses': [
                {'name': 'B.Tech/B.E. in CSE', 'duration': '4 Years', 'salary': '3-20 LPA', 'jobs': 'Software Engineer, Developer'},
                {'name': 'B.Tech in AI/ML', 'duration': '4 Years', 'salary': '4-25 LPA', 'jobs': 'AI Engineer, Data Scientist'},
                {'name': 'B.Tech in Mechanical', 'duration': '4 Years', 'salary': '3-15 LPA', 'jobs': 'Mechanical Engineer'},
                {'name': 'B.Tech in Civil', 'duration': '4 Years', 'salary': '3-12 LPA', 'jobs': 'Civil Engineer'},
                {'name': 'B.Tech in Electrical', 'duration': '4 Years', 'salary': '3-15 LPA', 'jobs': 'Electrical Engineer'},
                {'name': 'B.Tech in Electronics', 'duration': '4 Years', 'salary': '3-18 LPA', 'jobs': 'Electronics Engineer'},
                {'name': 'B.Tech in Biotechnology', 'duration': '4 Years', 'salary': '3-12 LPA', 'jobs': 'Biotech Researcher'},
                {'name': 'Diploma in Engineering', 'duration': '3 Years', 'salary': '2-8 LPA', 'jobs': 'Junior Engineer'},
            ]
        },
        {
            'stream': 'Medical ( वैद्यकीय )',
            'icon': 'user-md',
            'description': 'For students interested in healthcare and medicine',
            'courses': [
                {'name': 'MBBS', 'duration': '5.5 Years', 'salary': '5-30 LPA', 'jobs': 'Doctor, Surgeon'},
                {'name': 'BAMS (Ayurvedic)', 'duration': '5.5 Years', 'salary': '3-15 LPA', 'jobs': 'Ayurvedic Doctor'},
                {'name': 'BHMS (Homeopathy)', 'duration': '5.5 Years', 'salary': '3-12 LPA', 'jobs': 'Homeopathic Doctor'},
                {'name': 'BDS (Dental)', 'duration': '5 Years', 'salary': '4-20 LPA', 'jobs': 'Dentist'},
                {'name': 'B.Sc. Nursing', 'duration': '4 Years', 'salary': '3-10 LPA', 'jobs': 'Nurse, Healthcare'},
                {'name': 'B.Pharma', 'duration': '4 Years', 'salary': '2-8 LPA', 'jobs': 'Pharmacist, Researcher'},
                {'name': 'Paramedical Courses', 'duration': '2-4 Years', 'salary': '2-10 LPA', 'jobs': 'Technician, Therapist'},
            ]
        },
        {
            'stream': 'Commerce ( वाणिज्य )',
            'icon': 'briefcase',
            'description': 'For students interested in business and finance',
            'courses': [
                {'name': 'B.Com (Hons)', 'duration': '3 Years', 'salary': '3-12 LPA', 'jobs': 'Accountant, Analyst'},
                {'name': 'BBA', 'duration': '3 Years', 'salary': '3-15 LPA', 'jobs': 'Manager, Entrepreneur'},
                {'name': 'CA (Chartered Accountant)', 'duration': '4-5 Years', 'salary': '5-30 LPA', 'jobs': 'Chartered Accountant'},
                {'name': 'CS (Company Secretary)', 'duration': '3-4 Years', 'salary': '4-20 LPA', 'jobs': 'Company Secretary'},
                {'name': 'Banking & Insurance', 'duration': '3 Years', 'salary': '3-10 LPA', 'jobs': 'Bank Officer, PO'},
                {'name': 'Actuarial Science', 'duration': '3-4 Years', 'salary': '5-25 LPA', 'jobs': 'Actuary'},
            ]
        },
        {
            'stream': 'Arts & Humanities ( कला व मानवविज्ञान )',
            'icon': 'graduation-cap',
            'description': 'For creative and socially inclined students',
            'courses': [
                {'name': 'BA in Economics', 'duration': '3 Years', 'salary': '3-12 LPA', 'jobs': 'Economist, Analyst'},
                {'name': 'BA in Psychology', 'duration': '3 Years', 'salary': '3-10 LPA', 'jobs': 'Psychologist, Counselor'},
                {'name': 'BA in Journalism', 'duration': '3 Years', 'salary': '3-15 LPA', 'jobs': 'Journalist, Reporter'},
                {'name': 'LLB (Law)', 'duration': '3-5 Years', 'salary': '4-20 LPA', 'jobs': 'Lawyer, Advocate'},
                {'name': 'Design (Fashion/Interior)', 'duration': '3-4 Years', 'salary': '3-15 LPA', 'jobs': 'Designer'},
                {'name': 'Film & Media', 'duration': '3-4 Years', 'salary': '3-18 LPA', 'jobs': 'Filmmaker, Editor'},
                {'name': 'Hotel Management', 'duration': '3-4 Years', 'salary': '3-12 LPA', 'jobs': 'Hotel Manager'},
            ]
        },
        {
            'stream': 'Science ( विज्ञान )',
            'icon': 'flask',
            'description': 'For students interested in pure sciences and research',
            'courses': [
                {'name': 'B.Sc. in Physics', 'duration': '3 Years', 'salary': '3-10 LPA', 'jobs': 'Researcher, Teacher'},
                {'name': 'B.Sc. in Chemistry', 'duration': '3 Years', 'salary': '3-10 LPA', 'jobs': 'Chemist, Researcher'},
                {'name': 'B.Sc. in Mathematics', 'duration': '3 Years', 'salary': '3-12 LPA', 'jobs': 'Analyst, Teacher'},
                {'name': 'B.Sc. in Biology', 'duration': '3 Years', 'salary': '3-10 LPA', 'jobs': 'Biologist, Researcher'},
                {'name': 'B.Sc. in Computer Science', 'duration': '3 Years', 'salary': '3-15 LPA', 'jobs': 'Programmer, Developer'},
                {'name': 'Data Science', 'duration': '3 Years', 'salary': '4-20 LPA', 'jobs': 'Data Scientist, Analyst'},
                {'name': 'Research (M.Sc/PhD)', 'duration': '5-6 Years', 'salary': '3-15 LPA', 'jobs': 'Research Scientist'},
            ]
        },
        {
            'stream': 'Computer & IT ( संगणक )',
            'icon': 'laptop-code',
            'description': 'For students interested in software and IT',
            'courses': [
                {'name': 'BCA', 'duration': '3 Years', 'salary': '3-12 LPA', 'jobs': 'Software Developer'},
                {'name': 'B.Sc. IT', 'duration': '3 Years', 'salary': '3-12 LPA', 'jobs': 'IT Professional'},
                {'name': 'Web Development', 'duration': '6 Months-1 Year', 'salary': '2-10 LPA', 'jobs': 'Web Developer'},
                {'name': 'App Development', 'duration': '6 Months-1 Year', 'salary': '3-12 LPA', 'jobs': 'App Developer'},
                {'name': 'Cloud Computing', 'duration': '1 Year', 'salary': '4-15 LPA', 'jobs': 'Cloud Engineer'},
                {'name': 'Cybersecurity', 'duration': '1 Year', 'salary': '4-18 LPA', 'jobs': 'Security Analyst'},
            ]
        },
        {
            'stream': 'Government Jobs ( सरकारी नोकरी )',
            'icon': 'landmark',
            'description': 'For students seeking stable government careers',
            'courses': [
                {'name': 'UPSC Civil Services', 'duration': '1-2 Years', 'salary': '5-30 LPA', 'jobs': 'IAS, IPS, IRS'},
                {'name': 'SSC CGL', 'duration': '6 Months-1 Year', 'salary': '3-12 LPA', 'jobs': 'Govt Officer'},
                {'name': 'State Police', 'duration': '1 Year', 'salary': '4-8 LPA', 'jobs': 'Police Officer'},
                {'name': 'Banking (PO/Clerk)', 'duration': '6 Months-1 Year', 'salary': '4-10 LPA', 'jobs': 'Bank PO, Clerk'},
                {'name': 'Teaching (TET/CTET)', 'duration': '6 Months-1 Year', 'salary': '3-8 LPA', 'jobs': 'Teacher'},
                {'name': 'Railway Jobs', 'duration': '1 Year', 'salary': '4-10 LPA', 'jobs': 'Railway Officer'},
            ]
        }
    ]
    
    return render_template('after_12th.html', options=after_12th_options)

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


@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    """Student Feedback Page"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    message = ''
    
    if request.method == 'POST':
        feedback_text = request.form.get('feedback', '')
        rating = request.form.get('rating', '5')
        
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        
        try:
            c.execute('INSERT INTO feedback (user_id, feedback_text, rating) VALUES (?, ?, ?)',
                     (session['user_id'], feedback_text, rating))
            conn.commit()
            message = 'Thank you for your feedback!'
        except:
            # Create table if not exists
            c.execute('CREATE TABLE IF NOT EXISTS feedback (id INTEGER PRIMARY KEY, user_id INTEGER, feedback_text TEXT, rating INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
            c.execute('INSERT INTO feedback (user_id, feedback_text, rating) VALUES (?, ?, ?)',
                     (session['user_id'], feedback_text, rating))
            conn.commit()
            message = 'Thank you for your feedback!'
        
        conn.close()
    
    return render_template('feedback.html', message=message)


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
    
    # Get all users with their results - just basic columns
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
    
    # Get counts
    c.execute('SELECT COUNT(*) FROM results WHERE user_id = ?', (user_id,))
    result_count = c.fetchone()[0]
    
    try:
        c.execute('SELECT COUNT(*) FROM certificates WHERE user_id = ?', (user_id,))
        cert_count = c.fetchone()[0]
    except:
        cert_count = 0
    
    try:
        c.execute('SELECT COUNT(*) FROM courses WHERE user_id = ?', (user_id,))
        course_count = c.fetchone()[0]
    except:
        course_count = 0
    
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
    
    # Format results for template
    user_results = []
    for r in results:
        user_results.append({'test': 'Career Test', 'result': r[0], 'date': r[3]})
    for p in personality_tests:
        user_results.append({'test': 'Personality Test', 'result': p[0], 'date': 'N/A'})
    for a in aptitude_tests:
        user_results.append({'test': 'Aptitude Test', 'result': f"Score: {a[0]}%", 'date': a[2] if a[2] else 'N/A'})
    
    return render_template('admin_user_details.html',
                          user=user,
                          result_count=result_count,
                          cert_count=cert_count,
                          course_count=course_count,
                          user_results=user_results)

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

@app.route('/admin-youtube-api', methods=['GET', 'POST'])
def admin_youtube_api():
    """Configure YouTube API Key - Admin only"""
    # Check if admin is logged in
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    
    global YOUTUBE_API_KEY
    config_file = 'youtube_api_config.txt'
    api_key_status = "Not configured"
    
    if request.method == 'POST':
        youtube_api_key = request.form.get('youtube_api_key', '').strip()
        if youtube_api_key:
            try:
                with open(config_file, 'w') as f:
                    f.write(youtube_api_key)
                # Update the global variable
                YOUTUBE_API_KEY = youtube_api_key
                flash('YouTube API Key saved successfully!', 'success')
            except Exception as e:
                flash(f'Error saving API key: {str(e)}', 'error')
        else:
            flash('Please enter a valid API key', 'error')
    
    # Check if config file exists
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                saved_key = f.read().strip()
                if saved_key:
                    # Show only first and last few characters for security
                    if len(saved_key) > 10:
                        api_key_status = f"Configured: {saved_key[:4]}...{saved_key[-4:]}"
                    else:
                        api_key_status = "Configured"
                    # Also update global variable
                    YOUTUBE_API_KEY = saved_key
        except:
            api_key_status = "Error reading config"
    
    return render_template('admin_youtube_api.html', api_key_status=api_key_status)

@app.route('/admin-feedback')
def admin_feedback():
    """View all student feedback - Admin only"""
    # Check if admin is logged in
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # Get all feedback with user names
    try:
        c.execute('''SELECT f.id, f.feedback_text, f.rating, f.created_at, u.name, u.email 
                     FROM feedback f 
                     JOIN users u ON f.user_id = u.id 
                     ORDER BY f.created_at DESC''')
        feedback_list = c.fetchall()
    except:
        feedback_list = []
    
    conn.close()
    
    return render_template('admin_feedback.html', feedback_list=feedback_list)

# Load YouTube API key from config file on startup
def load_youtube_api_key():
    global YOUTUBE_API_KEY
    config_file = 'youtube_api_config.txt'
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                key = f.read().strip()
                if key:
                    YOUTUBE_API_KEY = key
                    print(f"YouTube API Key loaded successfully")
        except:
            pass

# Load API key when app starts
load_youtube_api_key()

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
    """User progress tracking with all test results"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # Get personality test result
    personality_result = None
    try:
        c.execute("SELECT personality_type, strengths, weaknesses, suitable_careers FROM personality_tests WHERE user_id = ? ORDER BY id DESC LIMIT 1", (session['user_id'],))
        personality_result = c.fetchone()
    except:
        pass
    
    # Get aptitude test result
    aptitude_result = None
    try:
        c.execute("SELECT overall_score, recommendation FROM aptitude_tests WHERE user_id = ? ORDER BY id DESC LIMIT 1", (session['user_id'],))
        aptitude_result = c.fetchone()
    except:
        pass
    
    # Get career test result
    career_result = None
    try:
        c.execute("SELECT career, skills, salary FROM results WHERE user_id = ? ORDER BY id DESC LIMIT 1", (session['user_id'],))
        career_result = c.fetchone()
    except:
        pass
    
    # Get progress data
    try:
        c.execute("SELECT * FROM progress WHERE user_id = ? ORDER BY date_updated DESC", (session['user_id'],))
        progress_data = c.fetchall()
    except:
        progress_data = []
    
    conn.close()
    
    return render_template('progress.html', 
                          progress=progress_data,
                          personality_result=personality_result,
                          aptitude_result=aptitude_result,
                          career_result=career_result)

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
    # Removed login requirement - courses should be accessible to all users
    
    # Get user's recommended career (if logged in)
    user_id = session.get('user_id')
    user_career = "Software Developer"  # Default career
    
    if user_id:
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT career FROM results WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,))
        result = c.fetchone()
        if result:
            user_career = result[0]
        conn.close()
    else:
        user_career = "Software Developer"
    
    # Get selected category
    selected_category = request.args.get('category', 'all')
    
    # All courses and videos data with real YouTube video links
    COURSES_DATA = {
        'Technology': {
            'courses': [
                {'name': 'Python Programming Masterclass', 'provider': 'Great Learning', 'link': 'https://www.greatlearning.com/python-programming', 'duration': '12 hours', 'level': 'Beginner', 'video_id': 'hT_nqWdeWV4'},
                {'name': 'Full Stack Web Development', 'provider': 'Scaler Academy', 'link': 'https://www.scaler.com/topics/full-stack-development/', 'duration': '6 months', 'level': 'Intermediate', 'video_id': 'qdkbKkBQnpA'},
                {'name': 'Data Science with Python', 'provider': 'Simplilearn', 'link': 'https://www.simplilearn.com/data-scientist-master-certificate-training', 'duration': '11 months', 'level': 'Advanced', 'video_id': 'ua-CiDNNj30'},
                {'name': 'Machine Learning A-Z', 'provider': 'Udemy', 'link': 'https://www.udemy.com/course/machinelearning/', 'duration': '44 hours', 'level': 'All Levels', 'video_id': '0UnQnYhT4L0'},
                {'name': 'Cloud Computing Fundamentals', 'provider': 'AWS Training', 'link': 'https://aws.amazon.com/training/', 'duration': '20 hours', 'level': 'Beginner', 'video_id': 'SSo_EIwHSd4'},
                {'name': 'Java Programming Complete', 'provider': 'Coursera', 'link': 'https://www.coursera.org/specializations/java-programming', 'duration': '6 months', 'level': 'Beginner', 'video_id': 'DKlT8-lCZj0'},
            ],
            'videos': [
    {
        'title': 'Python Tutorial for Beginners',
        'channel': 'Programming with Mosh',
        'video_id': 'hT_nqWdeWV4',
        'duration': '1:30:00',
        'link': 'https://www.youtube.com/watch?v=hT_nqWdeWV4'
    },
    {
        'title': 'Web Development Full Course',
        'channel': 'Programming with Mosh',
        'video_id': 'qdkbKkBQnpA',
        'duration': '2:00:00',
        'link': 'https://www.youtube.com/watch?v=qdkbKkBQnpA'
    },
    {
        'title': 'Data Science Complete Guide',
        'channel': 'Krish Naik',
        'video_id': 'ua-CiDNNj30',
        'duration': '8:00:00',
        'link': 'https://www.youtube.com/watch?v=ua-CiDNNj30'
    },
    {
        'title': 'Machine Learning Tutorial',
        'channel': 'Simplilearn',
        'video_id': '0UnQnYhT4L0',
        'duration': '45:00',
        'link': 'https://www.youtube.com/watch?v=0UnQnYhT4L0'
    },
    {
        'title': 'AI Trends 2025 - Complete Guide',
        'channel': 'Krish Naik',
        'video_id': 'V2nKfjB5Lqw',
        'duration': '30:00',
        'link': 'https://www.youtube.com/watch?v=V2nKfjB5Lqw'
    },
    {
        'title': 'Full Stack Development 2025',
        'channel': 'Apna College',
        'video_id': 'DKlT8-lCZj0',
        'duration': '25:00',
        'link': 'https://www.youtube.com/watch?v=DKlT8-lCZj0'
    },
    {
        'title': 'Data Science Jobs 2026',
        'channel': 'Simplilearn',
        'video_id': 'Y7uZo8GgKF0',
        'duration': '20:00',
        'link': 'https://www.youtube.com/watch?v=Y7uZo8GgKF0'
    },
    {
        'title': 'Web3 and Blockchain 2025',
        'channel': 'Tech Lead',
        'video_id': 'SSo_EIwHSd4',
        'duration': '35:00',
        'link': 'https://www.youtube.com/watch?v=SSo_EIwHSd4'
    }
]
        },
        'Healthcare': {
            'courses': [
                {'name': 'MBBS Preparation Course', 'provider': 'PrepLadder', 'link': 'https://www.prepladder.com/', 'duration': '2 years', 'level': 'Intermediate', 'video_id': 'YzKqjKfqE8I'},
                {'name': 'Nursing Fundamentals', 'provider': 'Coursera', 'link': 'https://www.coursera.org/browse/health-science', 'duration': '6 months', 'level': 'Beginner', 'video_id': 'Y8V-GG9BzQ8'},
                {'name': 'Healthcare Management MBA', 'provider': 'TISS', 'link': 'https://www.tiss.edu/', 'duration': '2 years', 'level': 'Advanced', 'video_id': 'O7GkX3TZ0pE'},
                {'name': 'Pharmacy Degree Course', 'provider': 'B Pharmacy', 'link': 'https://www.pharmacy.gov.in/', 'duration': '4 years', 'level': 'Graduate', 'video_id': 'iLWTnMzWtj4'},
                {'name': 'Medical Coding Training', 'provider': 'AAPC', 'link': 'https://www.aapc.com/', 'duration': '6 months', 'level': 'Beginner', 'video_id': 'PW3cq5wqRZ8'},
                {'name': 'Hospital Administration', 'provider': 'Apollo MedSkills', 'link': 'https://www.apollomedskills.com/', 'duration': '1 year', 'level': 'Intermediate', 'video_id': 'Y6lUu5FqMw0'},
            ],
            'videos': [
                {'title': 'How to Become a Doctor in India', 'channel': 'Motion Education', 'video_id': 'YzKqjKfqE8I', 'duration': '15:00'},
                {'title': 'MBBS Full Details', 'channel': 'Gyan Tara', 'video_id': 'Y8V-GG9BzQ8', 'duration': '20:00'},
                {'title': 'NEET Preparation Strategy', 'channel': 'Vedantu', 'video_id': 'O7GkX3TZ0pE', 'duration': '25:00'},
                {'title': 'Healthcare Careers', 'channel': 'TED Talks', 'video_id': 'iCgDuz6U7j4', 'duration': '10:00'},
                {'title': 'Medical Entrance Exam 2025', 'channel': 'Physics Wallah', 'video_id': 'PW3cq5wqRZ8', 'duration': '40:00'},
                {'title': 'Healthcare Technology 2025', 'channel': 'Ninja Nerds', 'video_id': 'Y6lUu5FqMw0', 'duration': '30:00'},
                {'title': 'Nursing Career Guide 2026', 'channel': 'MedCourse', 'video_id': 'L8KnAww6k0I', 'duration': '25:00'},
                {'title': 'AIIMS Preparation 2026', 'channel': 'Vedantu', 'video_id': 'M7oT7jR6gZY', 'duration': '35:00'},
            ]
        },
        'Business': {
            'courses': [
                {'name': 'Business Analytics with Excel', 'provider': 'Coursera', 'link': 'https://www.coursera.org/learn/excel-analytics', 'duration': '20 hours', 'level': 'Beginner', 'video_id': 'iLWTnMzWtj4'},
                {'name': 'Digital Marketing Masterclass', 'provider': 'Udemy', 'link': 'https://www.udemy.com/course/digital-marketing-course/', 'duration': '40 hours', 'level': 'All Levels', 'video_id': 'd3Xj3oMT5v0'},
                {'name': 'MBA Foundation Course', 'provider': 'IMS', 'link': 'https://www.imsindia.com/', 'duration': '1 year', 'level': 'Intermediate', 'video_id': 'QIlARzVynos'},
                {'name': 'Financial Modeling Course', 'provider': 'Wall Street Mojo', 'link': 'https://www.wallstreetmojo.com/financial-modeling-course/', 'duration': '30 hours', 'level': 'Advanced', 'video_id': 'hY9mUZgZ2vU'},
                {'name': 'Banking & Finance Course', 'provider': 'IBPS', 'link': 'https://www.ibps.in/', 'duration': '6 months', 'level': 'Beginner', 'video_id': 'vN26Z5c5k5w'},
                {'name': 'Startup Entrepreneurship', 'provider': 'Startup India', 'link': 'https://www.startupindia.gov.in/', 'duration': '3 months', 'level': 'All Levels', 'video_id': 'E9oR8d2oN8U'},
            ],
            'videos': [
                {'title': 'Business Analyst Full Course', 'channel': 'Simplilearn', 'video_id': 'iLWTnMzWtj4', 'duration': '3:00:00'},
                {'title': 'Digital Marketing Tutorial', 'channel': 'Simplilearn', 'video_id': 'd3Xj3oMT5v0', 'duration': '2:30:00'},
                {'title': 'How to Prepare for CAT', 'channel': 'Unacademy', 'video_id': 'QIlARzVynos', 'duration': '45:00'},
                {'title': 'Startup Ideas for Students', 'channel': 'Ankur Warikoo', 'video_id': 'hY9mUZgZ2vU', 'duration': '20:00'},
                {'title': 'Business Trends 2025', 'channel': 'UPSC Wallah', 'video_id': 'vN26Z5c5k5w', 'duration': '30:00'},
                {'title': 'Marketing Strategy 2025', 'channel': 'Digital Deepak', 'video_id': 'E9oR8d2oN8U', 'duration': '25:00'},
                {'title': 'Finance Careers 2026', 'channel': 'CA Parag Gupta', 'video_id': 'G8wK9wT7gZo', 'duration': '35:00'},
                {'title': 'Entrepreneurship Guide 2026', 'channel': 'Ankur Warikoo', 'video_id': 'R4m7qsq1xXw', 'duration': '40:00'},
            ]
        },
        'Creative Arts': {
            'courses': [
                {'name': 'Graphic Design Masterclass', 'provider': 'Udemy', 'link': 'https://www.udemy.com/course/graphic-design/', 'duration': '15 hours', 'level': 'Beginner', 'video_id': '9A-ysHr7O4E'},
                {'name': 'UI/UX Design Complete', 'provider': 'Coursera', 'link': 'https://www.coursera.org/profional-certificate/google-ux-design', 'duration': '6 months', 'level': 'Beginner', 'video_id': 'c4ZtB4yF1Cw'},
                {'name': 'Video Editing Pro Course', 'provider': 'Premiere Pro', 'link': 'https://www.adobe.com/education/expression-education/', 'duration': '20 hours', 'level': 'Intermediate', 'video_id': 'RtSm6Og1wmU'},
                {'name': 'Animation & VFX Course', 'provider': 'MAAC', 'link': 'https://www.maacindia.com/', 'duration': '2 years', 'level': 'Advanced', 'video_id': '4Yq3PRd0jQw'},
                {'name': 'Photography Masterclass', 'provider': 'National Geographic', 'link': 'https://www.nationalgeographic.com/education/', 'duration': '10 hours', 'level': 'All Levels', 'video_id': 'xK7PqhR8q5U'},
                {'name': 'Music Production Course', 'provider': 'Berklee Online', 'link': 'https://online.berklee.edu/', 'duration': '1 year', 'level': 'Beginner', 'video_id': 'JUTJ5qVjPVw'},
            ],
            'videos': [
                {'title': 'Graphic Design Tutorial', 'channel': 'GFXMentor', 'video_id': '9A-ysHr7O4E', 'duration': '1:00:00'},
                {'title': 'UI/UX Design Complete', 'channel': 'Google Design', 'video_id': 'c4ZtB4yF1Cw', 'duration': '2:00:00'},
                {'title': 'Photoshop Full Course', 'channel': 'Phlearn', 'video_id': 'RtSm6Og1wmU', 'duration': '3:00:00'},
                {'title': 'Music Theory Basics', 'channel': 'Adam Neely', 'video_id': '4Yq3PRd0jQw', 'duration': '30:00'},
                {'title': 'Design Trends 2025', 'channel': 'GFXMentor', 'video_id': 'xK7PqhR8q5U', 'duration': '25:00'},
                {'title': 'Digital Art Tutorial 2025', 'channel': 'Ctrl+Paint', 'video_id': 'JUTJ5qVjPVw', 'duration': '30:00'},
                {'title': 'Animation Career 2026', 'channel': 'Blender Guru', 'video_id': 'U1i8V4VZ3Kw', 'duration': '35:00'},
                {'title': 'Content Creation 2026', 'channel': 'MrBeast', 'video_id': 'kJQP7kiw5Fk', 'duration': '20:00'},
            ]
        },
        'Science': {
            'courses': [
                {'name': 'B.Sc Physics/Chemistry/Math', 'provider': 'IIT Coaching', 'link': 'https://www.vedantu.com/', 'duration': '2 years', 'level': 'Intermediate', 'video_id': '3CRmu8mBT_k'},
                {'name': 'Research Methodology', 'provider': 'NPTEL', 'link': 'https://nptel.ac.in/', 'duration': '12 weeks', 'level': 'Advanced', 'video_id': 'N2Jax7vK3cM'},
                {'name': 'Chemistry Olympiad Prep', 'provider': 'HBCSE', 'link': 'https://www.hbcse.tifr.res.in/', 'duration': '1 year', 'level': 'Advanced', 'video_id': 'V3WjGDU4Giw'},
                {'name': 'Biotechnology Course', 'provider': 'BIONITY', 'link': 'https://www.biotecnika.org/', 'duration': '6 months', 'level': 'Intermediate', 'video_id': '8m66k-QXc6A'},
                {'name': 'Environmental Science', 'provider': 'UGC', 'link': 'https://ugc.ac.in/', 'duration': '1 year', 'level': 'Graduate', 'video_id': 'Yb0cZ9HmZ7U'},
                {'name': 'Forensic Science Course', 'provider': 'CBI', 'link': 'https://cbi.gov.in/', 'duration': '1 year', 'level': 'Advanced', 'video_id': 'M9vK6L5wX8Y'},
            ],
            'videos': [
                {'title': 'Physics Complete Class 11-12', 'channel': 'Physics Wallah', 'video_id': '3CRmu8mBT_k', 'duration': '10:00:00'},
                {'title': 'Chemistry Full Course', 'channel': 'Vedantu', 'video_id': 'N2Jax7vK3cM', 'duration': '8:00:00'},
                {'title': 'Maths JEE Preparation', 'channel': 'Maths Wallah', 'video_id': 'V3WjGDU4Giw', 'duration': '15:00:00'},
                {'title': 'Biology NEET Prep', 'channel': 'Vedantu', 'video_id': '8m66k-QXc6A', 'duration': '12:00:00'},
                {'title': 'JEE Advanced 2025 Strategy', 'channel': 'Physics Wallah', 'video_id': 'Yb0cZ9HmZ7U', 'duration': '45:00'},
                {'title': 'Science Careers After 12th 2025', 'channel': 'Vedantu', 'video_id': 'M9vK6L5wX8Y', 'duration': '30:00'},
                {'title': 'Research Opportunities 2026', 'channel': 'IIT Delhi', 'video_id': 'N3wJP2LkqHo', 'duration': '35:00'},
                {'title': 'BScIT Career Guide 2026', 'channel': 'Apna College', 'video_id': 'R5yK9jHwP2M', 'duration': '25:00'},
            ]
        }
    }
    
    # Default courses for all users
    default_courses = [
        {'name': 'Career Development Workshop', 'provider': 'LinkedIn Learning', 'link': 'https://www.linkedin.com/learning/', 'duration': '4 hours', 'level': 'Beginner', 'video_id': 'Cv5gR9tSSzw'},
        {'name': 'Communication Skills', 'provider': 'Coursera', 'link': 'https://www.coursera.org/learn/communication-skills', 'duration': '8 hours', 'level': 'Beginner', 'video_id': '2L2lnxIcNts'},
        {'name': 'Interview Preparation', 'provider': 'InterviewBit', 'link': 'https://www.interviewbit.com/', 'duration': '20 hours', 'level': 'Intermediate', 'video_id': 'iCgDuz6U7j4'},
        {'name': 'Resume Writing Masterclass', 'provider': 'Udemy', 'link': 'https://www.udemy.com/course/resume-writing/', 'duration': '2 hours', 'level': 'Beginner', 'video_id': 'Y5Z9KlQhN0w'},
        {'name': 'Time Management', 'provider': 'Great Learning', 'link': 'https://www.greatlearning.com/time-management', 'duration': '6 hours', 'level': 'Beginner', 'video_id': 'v2L3nVt4VZw'},
        {'name': 'Leadership Skills', 'provider': 'EdX', 'link': 'https://www.edx.org/', 'duration': '12 hours', 'level': 'Intermediate', 'video_id': 'R4m7qsq1xXw'},
    ]
    
    default_videos = [
        {'title': 'How to Write a Resume', 'channel': 'Indeed', 'video_id': 'Cv5gR9tSSzw', 'duration': '5:00'},
        {'title': 'Interview Tips 2024', 'channel': 'Hiration', 'video_id': '2L2lnxIcNts', 'duration': '10:00'},
        {'title': 'Career Guidance for Students', 'channel': 'TED Talks', 'video_id': 'iCgDuz6U7j4', 'duration': '15:00'},
        {'title': 'Resume Building 2025', 'channel': 'Hiration', 'video_id': 'Y5Z9KlQhN0w', 'duration': '12:00'},
        {'title': 'Interview Preparation 2025', 'channel': 'Interview Bit', 'video_id': 'v2L3nVt4VZw', 'duration': '20:00'},
        {'title': 'Career Planning 2026', 'channel': 'TEDx Talks', 'video_id': 'xK8PqhR8q5U', 'duration': '18:00'},
        {'title': 'Job Search Strategies 2025', 'channel': 'LinkedIn', 'video_id': 'hT_nqWdeWV4', 'duration': '15:00'},
        {'title': 'Future of Work 2026', 'channel': 'McKinsey', 'video_id': 'iCgDuz6U7j4', 'duration': '25:00'},
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
    
    # YouTube API Video Search - Fetch dynamic videos if API key is configured
    youtube_videos = None
    use_youtube_api = False
    
    if YOUTUBE_API_KEY and selected_category in ['all', 'videos']:
        # Try to get videos from YouTube API based on career
        search_query = f"{user_career} career guide tutorial"
        youtube_videos = search_youtube_videos(search_query, max_results=8)
        
        if youtube_videos:
            # Get detailed video information including duration
            video_ids = [v['video_id'] for v in youtube_videos]
            detailed_videos = get_video_details(video_ids)
            
            if detailed_videos:
                videos = detailed_videos
                use_youtube_api = True
    
    # Get selected data (only if not using YouTube API)
    if not use_youtube_api:
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
    
    # Get all available categories
    all_categories = list(COURSES_DATA.keys())
    
    return render_template('courses.html', 
                          career=user_career,
                          recommended_courses=recommended_courses,
                          videos=videos,
                          category=category,
                          all_categories=all_categories,
                          selected_category=selected_category)

# ==================== VIDEOS ROUTE ====================

# Video library with categories
VIDEO_LIBRARY = [
    # Programming & Development
    {
        "title": "Python Full Course for Beginners",
        "channel": "freeCodeCamp",
        "video_id": "rfscVS0vtbw",
        "duration": "4:30:00",
        "embed": "https://www.youtube.com/embed/rfscVS0vtbw",
        "category": "programming",
        "keywords": ["python", "programming", "beginners", "coding"]
    },
    {
        "title": "Web Development Full Course",
        "channel": "freeCodeCamp",
        "video_id": "zJSY8tbf_ys",
        "duration": "6:00:00",
        "embed": "https://www.youtube.com/embed/zJSY8tbf_ys",
        "category": "web_development",
        "keywords": ["web", "html", "css", "javascript", "development"]
    },
    {
        "title": "Machine Learning Basics",
        "channel": "Simplilearn",
        "video_id": "ukzFI9rgwfU",
        "duration": "1:20:00",
        "embed": "https://www.youtube.com/embed/ukzFI9rgwfU",
        "category": "data_science",
        "keywords": ["machine learning", "ML", "AI", "data science"]
    },
    {
        "title": "Data Science for Beginners",
        "channel": "freeCodeCamp",
        "video_id": "ua-CiDNNj30",
        "duration": "8:00:00",
        "embed": "https://www.youtube.com/embed/ua-CiDNNj30",
        "category": "data_science",
        "keywords": ["data science", "python", "analytics", "machine learning"]
    },
    {
        "title": "UI/UX Design Course",
        "channel": "DesignCourse",
        "video_id": "c9Wg6Cb_YlU",
        "duration": "3:00:00",
        "embed": "https://www.youtube.com/embed/c9Wg6Cb_YlU",
        "category": "design",
        "keywords": ["UI", "UX", "design", "figma", "user experience"]
    },
    {
        "title": "Flutter Complete Course",
        "channel": "Sanjay Singh",
        "video_id": "tWbVnNxgwYY",
        "duration": "2:30:00",
        "embed": "https://www.youtube.com/embed/tWbVnNxgwYY",
        "category": "mobile_development",
        "keywords": ["flutter", "mobile", "app", "dart", "android", "ios"]
    },
    {
        "title": "AWS Cloud Practitioner",
        "channel": "Free AWS Training",
        "video_id": "SOTamWNgDKc",
        "duration": "2:00:00",
        "embed": "https://www.youtube.com/embed/SOTamWNgDKc",
        "category": "cloud_computing",
        "keywords": ["AWS", "cloud", "amazon", "devops"]
    },
    {
        "title": "Artificial Intelligence Course",
        "channel": "Simplilearn",
        "video_id": "GwGTw75y1-8",
        "duration": "5:00:00",
        "embed": "https://www.youtube.com/embed/GwGTw75y1-8",
        "category": "data_science",
        "keywords": ["AI", "artificial intelligence", "deep learning", "neural network"]
    },
    {
        "title": "Cybersecurity Fundamentals",
        "channel": "ITProTV",
        "video_id": "yr3PilqMnkw",
        "duration": "4:00:00",
        "embed": "https://www.youtube.com/embed/yr3PilqMnkw",
        "category": "cybersecurity",
        "keywords": ["security", "cybersecurity", "hacking", "network"]
    },
    {
        "title": "JavaScript Complete Guide",
        "channel": "Academind",
        "video_id": "W6NZfCO5SIk",
        "duration": "12:00:00",
        "embed": "https://www.youtube.com/embed/W6NZfCO5SIk",
        "category": "programming",
        "keywords": ["javascript", "JS", "programming", "web", "frontend"]
    },
    {
        "title": "React JS Full Course",
        "channel": "Clever Programmer",
        "video_id": "Ke90Tje7VS0",
        "duration": "3:00:00",
        "embed": "https://www.youtube.com/embed/Ke90Tje7VS0",
        "category": "web_development",
        "keywords": ["react", "javascript", "frontend", "web", "framework"]
    },
    {
        "title": "Data Structures & Algorithms",
        "channel": "freeCodeCamp",
        "video_id": "8hly31qpq2U",
        "duration": "5:00:00",
        "embed": "https://www.youtube.com/embed/8hly31qpq2U",
        "category": "programming",
        "keywords": ["DSA", "algorithms", "data structures", "programming", "interview"]
    },
    # Business & Entrepreneurship
    {
        "title": "Business Fundamentals Course",
        "channel": "HubSpot",
        "video_id": "JKq_3hTfhCw",
        "duration": "2:30:00",
        "embed": "https://www.youtube.com/embed/JKq_3hTfhCw",
        "category": "business",
        "keywords": ["business", "entrepreneurship", "startup", "management"]
    },
    {
        "title": "How to Start a Startup",
        "channel": "Y Combinator",
        "video_id": "EFmt6CAR-Gs",
        "duration": "5:00:00",
        "embed": "https://www.youtube.com/embed/EFmt6CAR-Gs",
        "category": "business",
        "keywords": ["startup", "entrepreneurship", "business", "venture"]
    },
    # Marketing & Digital Marketing
    {
        "title": "Digital Marketing Course",
        "channel": "Simplilearn",
        "video_id": "b4xqaT73xKc",
        "duration": "3:00:00",
        "embed": "https://www.youtube.com/embed/b4xqaT73xKc",
        "category": "marketing",
        "keywords": ["digital marketing", "SEO", "social media", "marketing"]
    },
    {
        "title": "Social Media Marketing Tutorial",
        "channel": "HubSpot",
        "video_id": "sITkVWD1Yb4",
        "duration": "2:00:00",
        "embed": "https://www.youtube.com/embed/sITkVWD1Yb4",
        "category": "marketing",
        "keywords": ["social media", "marketing", "branding", "facebook", "instagram"]
    },
    # Finance & Accounting
    {
        "title": "Finance Basics Explained",
        "channel": "The Plain Bagel",
        "video_id": "8nL7C8o-9gA",
        "duration": "1:30:00",
        "embed": "https://www.youtube.com/embed/8nL7C8o-9gA",
        "category": "finance",
        "keywords": ["finance", "investing", "stocks", "banking", "accounting"]
    },
    {
        "title": "Investment Banking Explained",
        "channel": "Wall Street Oasis",
        "video_id": "qFfy6_ZbZcU",
        "duration": "2:00:00",
        "embed": "https://www.youtube.com/embed/qFfy6_ZbZcU",
        "category": "finance",
        "keywords": ["investment banking", "finance", "career", "stocks", "IPO"]
    },
    # Career & Soft Skills
    {
        "title": "Career Planning Guide",
        "channel": "Anthony NN",
        "video_id": "Kv-7WJG1MVM",
        "duration": "1:00:00",
        "embed": "https://www.youtube.com/embed/Kv-7WJG1MVM",
        "category": "career",
        "keywords": ["career", "job", "resume", "interview", "placement"]
    },
    {
        "title": "Communication Skills Course",
        "channel": "ImproveyourSkills",
        "video_id": "DcxVUNx2ocM",
        "duration": "1:30:00",
        "embed": "https://www.youtube.com/embed/DcxVUNx2ocM",
        "category": "soft_skills",
        "keywords": ["communication", "soft skills", "personality", "presentation"]
    },
    {
        "title": "Leadership Skills Training",
        "channel": "Simplilearn",
        "video_id": "0WqT3BV6jVQ",
        "duration": "2:00:00",
        "embed": "https://www.youtube.com/embed/0WqT3BV6jVQ",
        "category": "soft_skills",
        "keywords": ["leadership", "management", "team", "soft skills"]
    },
    # Mathematics
    {
        "title": "Math for Data Science",
        "channel": "Krish Naik",
        "video_id": "N2T4zfVjs4I",
        "duration": "2:30:00",
        "embed": "https://www.youtube.com/embed/N2T4zfVjs4I",
        "category": "mathematics",
        "keywords": ["math", "mathematics", "calculus", "statistics", "data science"]
    },
    # Engineering
    {
        "title": "Civil Engineering Basics",
        "channel": "NPTEL",
        "video_id": "xDtUpZlt4eU",
        "duration": "3:00:00",
        "embed": "https://www.youtube.com/embed/xDtUpZlt4eU",
        "category": "engineering",
        "keywords": ["civil engineering", "engineering", "construction", "architecture"]
    },
    {
        "title": "Electrical Engineering Course",
        "channel": "NPTEL",
        "video_id": "9kDvpB1Y9X8",
        "duration": "4:00:00",
        "embed": "https://www.youtube.com/embed/9kDvpB1Y9X8",
        "category": "engineering",
        "keywords": ["electrical engineering", "electronics", "circuit", "engineering"]
    },
    # Healthcare & Medical
    {
        "title": "Nursing Fundamentals",
        "channel": "NCLEX Review",
        "video_id": "D14WnZIUkQU",
        "duration": "2:00:00",
        "embed": "https://www.youtube.com/embed/D14WnZIUkQU",
        "category": "healthcare",
        "keywords": ["nursing", "healthcare", "medical", "hospital"]
    },
    {
        "title": "Psychology Introduction",
        "channel": "NPTEL",
        "video_id": "Yo0Xo-5kC1A",
        "duration": "3:00:00",
        "embed": "https://www.youtube.com/embed/Yo0Xo-5kC1A",
        "category": "healthcare",
        "keywords": ["psychology", "mental health", "counseling", "therapy"]
    },
    # Law & Legal
    {
        "title": "Introduction to Law",
        "channel": "LawShala",
        "video_id": "0lreT8S3qT4",
        "duration": "2:00:00",
        "embed": "https://www.youtube.com/embed/0lreT8S3qT4",
        "category": "law",
        "keywords": ["law", "legal", "court", "advocate", "justice"]
    },
    # Data Analysis
    {
        "title": "Excel Data Analysis Course",
        "channel": "Alex the Analyst",
        "video_id": "QIZTor9bN74",
        "duration": "2:00:00",
        "embed": "https://www.youtube.com/embed/QIZTor9bN74",
        "category": "data_analysis",
        "keywords": ["excel", "data analysis", "spreadsheet", "analytics"]
    },
    {
        "title": "Power BI Tutorial",
        "channel": "Microsoft Power BI",
        "video_id": "aoxX2F-dHsA",
        "duration": "1:30:00",
        "embed": "https://www.youtube.com/embed/aoxX2F-dHsA",
        "category": "data_analysis",
        "keywords": ["power bi", "data visualization", "dashboard", "analytics"]
    },
    # Journalism & Media
    {
        "title": "Journalism Basics",
        "channel": "Al Jazeera",
        "video_id": "CvR2fDF8c9M",
        "duration": "1:30:00",
        "embed": "https://www.youtube.com/embed/CvR2fDF8c9M",
        "category": "journalism",
        "keywords": ["journalism", "media", "news", "reporting", "anchoring"]
    },
    # Hotel Management
    {
        "title": "Hotel Management Course",
        "channel": "IHTTI",
        "video_id": "lQjQyCnYCvM",
        "duration": "2:00:00",
        "embed": "https://www.youtube.com/embed/lQjQyCnYCvM",
        "category": "hospitality",
        "keywords": ["hotel management", "hospitality", "tourism", "travel"]
    },
    # Teaching & Education
    {
        "title": "Teaching Methods Course",
        "channel": "Education",
        "video_id": "SY0aEwD8Qbc",
        "duration": "2:00:00",
        "embed": "https://www.youtube.com/embed/SY0aEwD8Qbc",
        "category": "education",
        "keywords": ["teaching", "education", "teacher", "classroom"]
    }
]

# Interest to category mapping
INTEREST_CATEGORY_MAP = {
    # Data Science & AI
    "data": "data_science",
    "machine learning": "data_science",
    "ml": "data_science",
    "ai": "data_science",
    "artificial intelligence": "data_science",
    "data science": "data_science",
    "deep learning": "data_science",
    "neural": "data_science",
    # Web Development
    "web": "web_development",
    "website": "web_development",
    "development": "web_development",
    "react": "web_development",
    "angular": "web_development",
    "vue": "web_development",
    # Programming
    "coding": "programming",
    "code": "programming",
    "python": "programming",
    "java": "programming",
    "javascript": "programming",
    "c++": "programming",
    "c programming": "programming",
    "dsa": "programming",
    "algorithms": "programming",
    # Design
    "design": "design",
    "ui": "design",
    "ux": "design",
    "graphics": "design",
    "figma": "design",
    "photoshop": "design",
    # Mobile Development
    "mobile": "mobile_development",
    "app": "mobile_development",
    "flutter": "mobile_development",
    "android": "mobile_development",
    "ios": "mobile_development",
    "react native": "mobile_development",
    # Cloud Computing
    "cloud": "cloud_computing",
    "aws": "cloud_computing",
    "devops": "cloud_computing",
    "azure": "cloud_computing",
    "google cloud": "cloud_computing",
    # Cybersecurity
    "security": "cybersecurity",
    "cyber": "cybersecurity",
    "hacking": "cybersecurity",
    "ethical hacking": "cybersecurity",
    "network security": "cybersecurity",
    # Business & Entrepreneurship
    "business": "business",
    "entrepreneur": "business",
    "startup": "business",
    "management": "business",
    "entrepreneurship": "business",
    "venture": "business",
    # Marketing
    "marketing": "marketing",
    "digital marketing": "marketing",
    "seo": "marketing",
    "social media": "marketing",
    "branding": "marketing",
    # Finance
    "finance": "finance",
    "financial": "finance",
    "investment": "finance",
    "banking": "finance",
    "accounting": "finance",
    "stocks": "finance",
    "trading": "finance",
    # Career & Soft Skills
    "career": "career",
    "job": "career",
    "resume": "career",
    "interview": "career",
    "placement": "career",
    "communication": "soft_skills",
    "soft skills": "soft_skills",
    "leadership": "soft_skills",
    "personality": "soft_skills",
    "presentation": "soft_skills",
    # Mathematics
    "math": "mathematics",
    "mathematics": "mathematics",
    "statistics": "mathematics",
    "calculus": "mathematics",
    # Engineering
    "engineering": "engineering",
    "civil": "engineering",
    "electrical": "engineering",
    "mechanical": "engineering",
    "computer science": "engineering",
    # Healthcare
    "medical": "healthcare",
    "nursing": "healthcare",
    "healthcare": "healthcare",
    "psychology": "healthcare",
    "mental health": "healthcare",
    # Law
    "law": "law",
    "legal": "law",
    "advocate": "law",
    # Data Analysis
    "data analysis": "data_analysis",
    "excel": "data_analysis",
    "power bi": "data_analysis",
    "tableau": "data_analysis",
    "analytics": "data_analysis",
    # Journalism & Media
    "journalism": "journalism",
    "media": "journalism",
    "news": "journalism",
    "reporting": "journalism",
    # Hospitality
    "hotel": "hospitality",
    "hospitality": "hospitality",
    "tourism": "hospitality",
    "travel": "hospitality",
    # Education
    "teacher": "education",
    "teaching": "education",
    "education": "education"
}

@app.route('/api/recommend-videos', methods=['POST'])
def recommend_videos():
    """Get video recommendations based on user interest and skills"""
    data = request.get_json()
    interest = data.get('interest', '').lower()
    skills = data.get('skills', '').lower()
    
    # Combine interest and skills for matching
    search_text = interest + " " + skills
    
    # Find matching category
    matched_category = None
    for key, category in INTEREST_CATEGORY_MAP.items():
        if key in search_text:
            matched_category = category
            break
    
    # Filter videos
    recommended = []
    if matched_category:
        # Get videos from matching category
        for video in VIDEO_LIBRARY:
            if video['category'] == matched_category:
                recommended.append(video)
    
    # If no matches, return popular videos
    if not recommended:
        recommended = VIDEO_LIBRARY[:6]  # Return first 6 videos
    
    return jsonify({
        'videos': recommended,
        'category': matched_category or 'general'
    })

from flask import jsonify

@app.route('/videos')
def videos():
    """Dedicated Videos Page - Educational Video Library"""
    
    # Static video library data as provided
    video_library = [
        {
            "title": "Python Full Course for Beginners",
            "channel": "freeCodeCamp",
            "video_id": "rfscVS0vtbw",
            "duration": "4:30:00",
            "embed": "https://www.youtube.com/embed/rfscVS0vtbw"
        },
        {
            "title": "Web Development Full Course",
            "channel": "freeCodeCamp",
            "video_id": "zJSY8tbf_ys",
            "duration": "6:00:00",
            "embed": "https://www.youtube.com/embed/zJSY8tbf_ys"
        },
        {
            "title": "Machine Learning Basics",
            "channel": "Simplilearn",
            "video_id": "ukzFI9rgwfU",
            "duration": "1:20:00",
            "embed": "https://www.youtube.com/embed/ukzFI9rgwfU"
        },
        {
            "title": "Data Science for Beginners",
            "channel": "freeCodeCamp",
            "video_id": "ua-CiDNNj30",
            "duration": "8:00:00",
            "embed": "https://www.youtube.com/embed/ua-CiDNNj30"
        },
        {
            "title": "Python Django Tutorial",
            "channel": "Programming with Mosh",
            "video_id": "F5mRW0jo-U4",
            "duration": "1:30:00",
            "embed": "https://www.youtube.com/embed/F5mRW0jo-U4"
        },
        {
            "title": "Full Stack Development Guide",
            "channel": "Apna College",
            "video_id": "zJSY8tbf_ys",
            "duration": "2:00:00",
            "embed": "https://www.youtube.com/embed/zJSY8tbf_ys"
        },
        {
            "title": "Artificial Intelligence Basics",
            "channel": "Simplilearn",
            "video_id": "2ePf9rue1Ao",
            "duration": "45:00",
            "embed": "https://www.youtube.com/embed/2ePf9rue1Ao"
        },
        {
            "title": "Career in Data Science",
            "channel": "Krish Naik",
            "video_id": "7eh4d6sabA0",
            "duration": "30:00",
            "embed": "https://www.youtube.com/embed/7eh4d6sabA0"
        }
    ]
    
    return render_template('videos.html', videos=video_library)

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
    
    try:
        c.execute('SELECT COUNT(*) FROM certificates')
        cert_count = c.fetchone()[0]
    except:
        cert_count = 0
    
    try:
        c.execute('SELECT COUNT(*) FROM courses')
        course_count = c.fetchone()[0]
    except:
        course_count = 0
    
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

# Interview Practice Routes
@app.route('/interview', methods=['GET', 'POST'])
def interview_practice():
    """Interview Practice with Real Company Questions"""
    
    # Interview questions database organized by company
    INTERVIEW_QUESTIONS = {
        'Google': [
            {'text': 'Tell me about a time when you had to deal with a difficult team member. How did you handle it?', 
             'tips': 'Use STAR method. Focus on your approach and positive outcome.'},
            {'text': 'Describe a situation where you had to meet a tight deadline. How did you prioritize your tasks?', 
             'tips': 'Show your time management and organizational skills.'},
            {'text': 'Tell me about a time when you failed. What did you learn from it?', 
             'tips': 'Be honest about failure but emphasize growth and lessons learned.'},
            {'text': 'Why do you want to work at Google?', 
             'tips': 'Research Google\'s mission and values. Be specific about what attracts you.'},
            {'text': 'Describe a complex technical problem you solved. What was your approach?', 
             'tips': 'Explain the problem, your solution process, and the result.'}
        ],
        'Microsoft': [
            {'text': 'Tell me about yourself and why you want to join Microsoft.', 
             'tips': 'Connect your background to Microsoft\'s products and culture.'},
            {'text': 'Describe a time when you had to learn something quickly. How did you do it?', 
             'tips': 'Show your learning ability and adaptability.'},
            {'text': 'Tell me about a project you\'re most proud of.', 
             'tips': 'Choose a project that demonstrates relevant skills.'},
            {'text': 'How do you handle disagreements with teammates?', 
             'tips': 'Show conflict resolution and communication skills.'},
            {'text': 'Where do you see yourself in 5 years?', 
             'tips': 'Show ambition but also loyalty to the company.'}
        ],
        'Amazon': [
            {'text': 'Tell me about a time when you had to make a decision without all the information you needed.', 
             'tips': 'Show decision-making under uncertainty.'},
            {'text': 'Describe a situation where you had to deliver bad news to a customer or team member.', 
             'tips': 'Focus on transparency and empathy.'},
            {'text': 'Tell me about a time when you went above and beyond for a customer.', 
             'tips': 'Amazon is customer-centric. Show your customer obsession.'},
            {'text': 'Describe a time when you had to work with a difficult stakeholder.', 
             'tips': 'Show your stakeholder management skills.'},
            {'text': 'Why Amazon?', 
             'tips': 'Know Amazon\'s Leadership Principles. Be specific.'}
        ],
        'Meta': [
            {'text': 'Tell me about a time you had to pivot your strategy quickly.', 
             'tips': 'Show agility and adaptability.'},
            {'text': 'Describe a time when you had to motivate a team.', 
             'tips': 'Show leadership and people skills.'},
            {'text': 'Why Meta? Which product do you like the most and why?', 
             'tips': 'Be familiar with Meta\'s products and recent developments.'},
            {'text': 'Tell me about a technical challenge you faced and how you solved it.', 
             'tips': 'Be specific about the technical problem and your solution.'},
            {'text': 'How do you stay updated with the latest technology trends?', 
             'tips': 'Show curiosity and continuous learning.'}
        ],
        'Apple': [
            {'text': 'Why Apple? What product has impacted you the most?', 
             'tips': 'Show genuine passion for Apple\'s products and design philosophy.'},
            {'text': 'Tell me about a time when you had to pay attention to detail.', 
             'tips': 'Apple values perfection. Give a specific example.'},
            {'text': 'Describe a time when you had to work on a project with minimal guidance.', 
             'tips': 'Show self-motivation and independence.'},
            {'text': 'How would you design a better user experience for a specific Apple product?', 
             'tips': 'Think about simplicity and user-centric design.'},
            {'text': 'Tell me about a time you disagreed with your manager.', 
             'tips': 'Show professional disagreement and communication.'}
        ],
        'Netflix': [
            {'text': 'Why Netflix? What do you think about their culture?', 
             'tips': 'Know Netflix\'s culture memo. Be prepared to discuss freedom and responsibility.'},
            {'text': 'Describe a time when you had to be creative to solve a problem.', 
             'tips': 'Show innovative thinking.'},
            {'text': 'Tell me about a time you had to handle high-pressure situations.', 
             'tips': 'Show composure and stress management.'},
            {'text': 'How would you improve Netflix\'s recommendation algorithm?', 
             'tips': 'Show technical knowledge and business understanding.'},
            {'text': 'Tell me about a time when you had to make a quick decision.', 
             'tips': 'Show decision-making speed and accuracy.'}
        ],
        'TCS': [
            {'text': 'Tell me about yourself.', 
             'tips': 'Keep it professional and relevant to the job.'},
            {'text': 'Why do you want to join TCS?', 
             'tips': 'Show knowledge about TCS and its values.'},
            {'text': 'What are your strengths and weaknesses?', 
             'tips': 'Be honest but frame weaknesses positively.'},
            {'text': 'Where do you see yourself in 5 years?', 
             'tips': 'Show long-term commitment and career planning.'},
            {'text': 'Are you willing to relocate?', 
             'tips': 'Be positive and flexible.'}
        ],
        'Infosys': [
            {'text': 'Tell me about your final year project.', 
             'tips': 'Be thorough about your technical project.'},
            {'text': 'Why Infosys?', 
             'tips': 'Research Infosys training programs and culture.'},
            {'text': 'What programming languages are you comfortable with?', 
             'tips': 'Be honest about your technical skills.'},
            {'text': 'Are you willing to work in any location?', 
             'tips': 'Show flexibility and adaptability.'},
            {'text': 'How do you keep yourself updated with technology?', 
             'tips': 'Show continuous learning attitude.'}
        ],
        'Wipro': [
            {'text': 'Tell me about yourself.', 
             'tips': 'Give a concise professional summary.'},
            {'text': 'Why Wipro?', 
             'tips': 'Know about Wipro\'s values and projects.'},
            {'text': 'What are your career goals?', 
             'tips': 'Align with Wipro\'s growth opportunities.'},
            {'text': 'How do you handle teamwork?', 
             'tips': 'Show collaborative skills.'},
            {'text': 'What are your technical strengths?', 
             'tips': 'Be specific about your tech stack.'}
        ],
        'Accenture': [
            {'text': 'Why Accenture?', 
             'tips': 'Know about Accenture\'s global presence and diverse projects.'},
            {'text': 'Tell me about a time you solved a problem creatively.', 
             'tips': 'Show problem-solving and innovation.'},
            {'text': 'How do you handle working under pressure?', 
             'tips': 'Show stress management skills.'},
            {'text': 'Describe your teamwork experience.', 
             'tips': 'Give specific examples of collaboration.'},
            {'text': 'What are your expectations from this role?', 
             'tips': 'Show realistic expectations and enthusiasm.'}
        ],
        'Deloitte': [
            {'text': 'Why Deloitte?', 
             'tips': 'Show knowledge about consulting and Deloitte\'s services.'},
            {'text': 'Tell me about a time you handled a difficult client.', 
             'tips': 'Show client management skills.'},
            {'text': 'How do you prioritize multiple deadlines?', 
             'tips': 'Show organizational and time management skills.'},
            {'text': 'Describe your analytical skills with an example.', 
             'tips': 'Show data analysis and problem-solving.'},
            {'text': 'What areas of consulting interest you most?', 
             'tips': 'Show awareness of different consulting domains.'}
        ],
        'Goldman Sachs': [
            {'text': 'Why Goldman Sachs?', 
             'tips': 'Show knowledge about financial services and Goldman\'s culture.'},
            {'text': 'Tell me about a time you demonstrated leadership.', 
             'tips': 'Show leadership in academic or extracurricular activities.'},
            {'text': 'How do you handle ethical dilemmas?', 
             'tips': 'Show integrity and strong values.'},
            {'text': 'Describe a time you had to work with numbers.', 
             'tips': 'Show analytical and quantitative skills.'},
            {'text': 'Where do you see yourself in finance?', 
             'tips': 'Show career clarity in finance sector.'}
        ],
        'Flipkart': [
            {'text': 'Why Flipkart?', 
             'tips': 'Show knowledge about e-commerce and Flipkart\'s journey.'},
            {'text': 'Tell me about a time you improved a process.', 
             'tips': 'Show process improvement and efficiency.'},
            {'text': 'How would you handle a customer complaint?', 
             'tips': 'Show customer-centric problem solving.'},
            {'text': 'Describe a technical project you worked on.', 
             'tips': 'Be specific about your technical contributions.'},
            {'text': 'What excites you about e-commerce?', 
             'tips': 'Show passion for the industry.'}
        ],
        'Swiggy': [
            {'text': 'Why Swiggy?', 
             'tips': 'Show knowledge about food tech and Swiggy\'s operations.'},
            {'text': 'Tell me about a time you worked in a fast-paced environment.', 
             'tips': 'Show adaptability to quick changes.'},
            {'text': 'How would you optimize food delivery routes?', 
             'tips': 'Show problem-solving and logical thinking.'},
            {'text': 'Describe your experience with teamwork.', 
             'tips': 'Show collaborative skills.'},
            {'text': 'What do you know about Swiggy\'s business model?', 
             'tips': 'Research Swiggy\'s marketplace model.'}
        ],
        'Byju\'s': [
            {'text': 'Why Byju\'s?', 
             'tips': 'Show passion for education and Byju\'s mission.'},
            {'text': 'How would you explain a complex concept to a student?', 
             'tips': 'Show communication and teaching skills.'},
            {'text': 'Tell me about a time you made learning fun.', 
             'tips': 'Show creativity in education.'},
            {'text': 'What teaching methods do you prefer?', 
             'tips': 'Show understanding of modern education.'},
            {'text': 'How do you handle students who are struggling?', 
             'tips': 'Show patience and adaptive teaching.'}
        ]
    }
    
    selected_company = request.args.get('company', '')
    
    if selected_company and selected_company in INTERVIEW_QUESTIONS:
        questions = INTERVIEW_QUESTIONS[selected_company]
        return render_template('interview_practice.html', 
                            selected_company=selected_company,
                            questions=questions)
    
    return render_template('interview_practice.html', selected_company=None)

@app.route('/interview/submit', methods=['POST'])
def interview_submit():
    """Submit interview practice answers"""
    company = request.form.get('company', '')
    
    INTERVIEW_QUESTIONS = {
        'Google': [
            {'text': 'Tell me about a time when you had to deal with a difficult team member. How did you handle it?', 
             'tips': 'Use STAR method. Focus on your approach and positive outcome.'},
            {'text': 'Describe a situation where you had to meet a tight deadline. How did you prioritize your tasks?', 
             'tips': 'Show your time management and organizational skills.'},
            {'text': 'Tell me about a time when you failed. What did you learn from it?', 
             'tips': 'Be honest about failure but emphasize growth and lessons learned.'},
            {'text': 'Why do you want to work at Google?', 
             'tips': 'Research Google\'s mission and values. Be specific about what attracts you.'},
            {'text': 'Describe a complex technical problem you solved. What was your approach?', 
             'tips': 'Explain the problem, your solution process, and the result.'}
        ],
        'Microsoft': [
            {'text': 'Tell me about yourself and why you want to join Microsoft.', 
             'tips': 'Connect your background to Microsoft\'s products and culture.'},
            {'text': 'Describe a time when you had to learn something quickly. How did you do it?', 
             'tips': 'Show your learning ability and adaptability.'},
            {'text': 'Tell me about a project you\'re most proud of.', 
             'tips': 'Choose a project that demonstrates relevant skills.'},
            {'text': 'How do you handle disagreements with teammates?', 
             'tips': 'Show conflict resolution and communication skills.'},
            {'text': 'Where do you see yourself in 5 years?', 
             'tips': 'Show ambition but also loyalty to the company.'}
        ],
        'Amazon': [
            {'text': 'Tell me about a time when you had to make a decision without all the information you needed.', 
             'tips': 'Show decision-making under uncertainty.'},
            {'text': 'Describe a situation where you had to deliver bad news to a customer or team member.', 
             'tips': 'Focus on transparency and empathy.'},
            {'text': 'Tell me about a time when you went above and beyond for a customer.', 
             'tips': 'Amazon is customer-centric. Show your customer obsession.'},
            {'text': 'Describe a time when you had to work with a difficult stakeholder.', 
             'tips': 'Show your stakeholder management skills.'},
            {'text': 'Why Amazon?', 
             'tips': 'Know Amazon\'s Leadership Principles. Be specific.'}
        ],
        'Meta': [
            {'text': 'Tell me about a time you had to pivot your strategy quickly.', 
             'tips': 'Show agility and adaptability.'},
            {'text': 'Describe a time when you had to motivate a team.', 
             'tips': 'Show leadership and people skills.'},
            {'text': 'Why Meta? Which product do you like the most and why?', 
             'tips': 'Be familiar with Meta\'s products and recent developments.'},
            {'text': 'Tell me about a technical challenge you faced and how you solved it.', 
             'tips': 'Be specific about the technical problem and your solution.'},
            {'text': 'How do you stay updated with the latest technology trends?', 
             'tips': 'Show curiosity and continuous learning.'}
        ],
        'Apple': [
            {'text': 'Why Apple? What product has impacted you the most?', 
             'tips': 'Show genuine passion for Apple\'s products and design philosophy.'},
            {'text': 'Tell me about a time you had to pay attention to detail.', 
             'tips': 'Apple values perfection. Give a specific example.'},
            {'text': 'Describe a time when you had to work on a project with minimal guidance.', 
             'tips': 'Show self-motivation and independence.'},
            {'text': 'How would you design a better user experience for a specific Apple product?', 
             'tips': 'Think about simplicity and user-centric design.'},
            {'text': 'Tell me about a time you disagreed with your manager.', 
             'tips': 'Show professional disagreement and communication.'}
        ],
        'Netflix': [
            {'text': 'Why Netflix? What do you think about their culture?', 
             'tips': 'Know Netflix\'s culture memo. Be prepared to discuss freedom and responsibility.'},
            {'text': 'Describe a time when you had to be creative to solve a problem.', 
             'tips': 'Show innovative thinking.'},
            {'text': 'Tell me about a time you had to handle high-pressure situations.', 
             'tips': 'Show composure and stress management.'},
            {'text': 'How would you improve Netflix\'s recommendation algorithm?', 
             'tips': 'Show technical knowledge and business understanding.'},
            {'text': 'Tell me about a time when you had to make a quick decision.', 
             'tips': 'Show decision-making speed and accuracy.'}
        ],
        'TCS': [
            {'text': 'Tell me about yourself.', 
             'tips': 'Keep it professional and relevant to the job.'},
            {'text': 'Why do you want to join TCS?', 
             'tips': 'Show knowledge about TCS and its values.'},
            {'text': 'What are your strengths and weaknesses?', 
             'tips': 'Be honest but frame weaknesses positively.'},
            {'text': 'Where do you see yourself in 5 years?', 
             'tips': 'Show long-term commitment and career planning.'},
            {'text': 'Are you willing to relocate?', 
             'tips': 'Be positive and flexible.'}
        ],
        'Infosys': [
            {'text': 'Tell me about your final year project.', 
             'tips': 'Be thorough about your technical project.'},
            {'text': 'Why Infosys?', 
             'tips': 'Research Infosys training programs and culture.'},
            {'text': 'What programming languages are you comfortable with?', 
             'tips': 'Be honest about your technical skills.'},
            {'text': 'Are you willing to work in any location?', 
             'tips': 'Show flexibility and adaptability.'},
            {'text': 'How do you keep yourself updated with technology?', 
             'tips': 'Show continuous learning attitude.'}
        ],
        'Wipro': [
            {'text': 'Tell me about yourself.', 
             'tips': 'Give a concise professional summary.'},
            {'text': 'Why Wipro?', 
             'tips': 'Know about Wipro\'s values and projects.'},
            {'text': 'What are your career goals?', 
             'tips': 'Align with Wipro\'s growth opportunities.'},
            {'text': 'How do you handle teamwork?', 
             'tips': 'Show collaborative skills.'},
            {'text': 'What are your technical strengths?', 
             'tips': 'Be specific about your tech stack.'}
        ],
        'Accenture': [
            {'text': 'Why Accenture?', 
             'tips': 'Know about Accenture\'s global presence and diverse projects.'},
            {'text': 'Tell me about a time you solved a problem creatively.', 
             'tips': 'Show problem-solving and innovation.'},
            {'text': 'How do you handle working under pressure?', 
             'tips': 'Show stress management skills.'},
            {'text': 'Describe your teamwork experience.', 
             'tips': 'Give specific examples of collaboration.'},
            {'text': 'What are your expectations from this role?', 
             'tips': 'Show realistic expectations and enthusiasm.'}
        ],
        'Deloitte': [
            {'text': 'Why Deloitte?', 
             'tips': 'Show knowledge about consulting and Deloitte\'s services.'},
            {'text': 'Tell me about a time you handled a difficult client.', 
             'tips': 'Show client management skills.'},
            {'text': 'How do you prioritize multiple deadlines?', 
             'tips': 'Show organizational and time management skills.'},
            {'text': 'Describe your analytical skills with an example.', 
             'tips': 'Show data analysis and problem-solving.'},
            {'text': 'What areas of consulting interest you most?', 
             'tips': 'Show awareness of different consulting domains.'}
        ],
        'Goldman Sachs': [
            {'text': 'Why Goldman Sachs?', 
             'tips': 'Show knowledge about financial services and Goldman\'s culture.'},
            {'text': 'Tell me about a time you demonstrated leadership.', 
             'tips': 'Show leadership in academic or extracurricular activities.'},
            {'text': 'How do you handle ethical dilemmas?', 
             'tips': 'Show integrity and strong values.'},
            {'text': 'Describe a time you had to work with numbers.', 
             'tips': 'Show analytical and quantitative skills.'},
            {'text': 'Where do you see yourself in finance?', 
             'tips': 'Show career clarity in finance sector.'}
        ],
        'Flipkart': [
            {'text': 'Why Flipkart?', 
             'tips': 'Show knowledge about e-commerce and Flipkart\'s journey.'},
            {'text': 'Tell me about a time you improved a process.', 
             'tips': 'Show process improvement and efficiency.'},
            {'text': 'How would you handle a customer complaint?', 
             'tips': 'Show customer-centric problem solving.'},
            {'text': 'Describe a technical project you worked on.', 
             'tips': 'Be specific about your technical contributions.'},
            {'text': 'What excites you about e-commerce?', 
             'tips': 'Show passion for the industry.'}
        ],
        'Swiggy': [
            {'text': 'Why Swiggy?', 
             'tips': 'Show knowledge about food tech and Swiggy\'s operations.'},
            {'text': 'Tell me about a time you worked in a fast-paced environment.', 
             'tips': 'Show adaptability to quick changes.'},
            {'text': 'How would you optimize food delivery routes?', 
             'tips': 'Show problem-solving and logical thinking.'},
            {'text': 'Describe your experience with teamwork.', 
             'tips': 'Show collaborative skills.'},
            {'text': 'What do you know about Swiggy\'s business model?', 
             'tips': 'Research Swiggy\'s marketplace model.'}
        ],
        'Byju\'s': [
            {'text': 'Why Byju\'s?', 
             'tips': 'Show passion for education and Byju\'s mission.'},
            {'text': 'How would you explain a complex concept to a student?', 
             'tips': 'Show communication and teaching skills.'},
            {'text': 'Tell me about a time you made learning fun.', 
             'tips': 'Show creativity in education.'},
            {'text': 'What teaching methods do you prefer?', 
             'tips': 'Show understanding of modern education.'},
            {'text': 'How do you handle students who are struggling?', 
             'tips': 'Show patience and adaptive teaching.'}
        ]
    }
    
    if company not in INTERVIEW_QUESTIONS:
        flash('Invalid company selection')
        return redirect(url_for('interview_practice'))
    
    questions = INTERVIEW_QUESTIONS[company]
    total = len(questions)
    answered = 0
    
    # Count answered questions
    for i in range(1, total + 1):
        answer = request.form.get(f'answer_{i}', '').strip()
        if answer:
            answered += 1
    
    # Calculate score based on answered questions
    if total > 0:
        score = int((answered / total) * 100)
    else:
        score = 0
    
    # Generate message based on score
    if score >= 80:
        message = "Excellent! You\'re well prepared!"
    elif score >= 60:
        message = "Good job! Keep practicing to improve further."
    elif score >= 40:
        message = "Not bad! Review the tips and try again."
    else:
        message = "Keep practicing! Answer all questions for better results."
    
    # Pass all form data for review
    answers = request.form
    
    return render_template('interview_result.html',
                          company=company,
                          questions=questions,
                          answers=answers,
                          score=score,
                          message=message,
                          total_questions=total,
                          answered=answered)

@app.route('/certificate/download/<int:cert_id>')
def certificate_download(cert_id):
    """Download certificate as PDF"""
    from io import BytesIO
    try:
        from reportlab.lib.pagesizes import landscape, A4
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        from reportlab.pdfgen import canvas
    except ImportError:
        flash('PDF generation requires reportlab. Please install it: pip install reportlab')
        return redirect(url_for('certificates'))
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    c.execute('SELECT * FROM certificates WHERE id = ?', (cert_id,))
    certificate = c.fetchone()
    conn.close()
    
    if not certificate:
        flash('Certificate not found')
        return redirect(url_for('certificates'))
    
    # certificate format: (id, user_id, career, title, date, score)
    cert_id, user_id, career, title, date, score = certificate
    
    # Get user name
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('SELECT name FROM users WHERE id = ?', (user_id,))
    user_result = c.fetchone()
    user_name = user_result[0] if user_result else 'Student'
    conn.close()
    
    # Create PDF
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)
    
    # Background
    p.setFillColor(colors.white)
    p.rect(0, 0, width, height, fill=1)
    
    # Border
    p.setStrokeColor(colors.HexColor('#667eea'))
    p.setLineWidth(3)
    p.rect(20, 20, width-40, height-40, fill=0)
    
    # Inner border
    p.setStrokeColor(colors.HexColor('#764ba2'))
    p.setLineWidth(1)
    p.rect(30, 30, width-60, height-60, fill=0)
    
    # Title
    p.setFont("Helvetica-Bold", 36)
    p.setFillColor(colors.HexColor('#667eea'))
    p.drawCentredString(width/2, height-80, "Certificate of Achievement")
    
    # Decorative line
    p.setStrokeColor(colors.HexColor('#f093fb'))
    p.setLineWidth(2)
    p.line(width/2-150, height-95, width/2+150, height-95)
    
    # Subtitle
    p.setFont("Helvetica", 16)
    p.setFillColor(colors.gray)
    p.drawCentredString(width/2, height-130, "This is to certify that")
    
    # User Name
    p.setFont("Helvetica-Bold", 32)
    p.setFillColor(colors.HexColor('#333333'))
    p.drawCentredString(width/2, height-170, user_name)
    
    # Achievement text
    p.setFont("Helvetica", 14)
    p.setFillColor(colors.gray)
    p.drawCentredString(width/2, height-210, "has successfully completed the")
    
    # Course/Career title
    p.setFont("Helvetica-Bold", 24)
    p.setFillColor(colors.HexColor('#764ba2'))
    p.drawCentredString(width/2, height-250, title)
    
    # Career path
    p.setFont("Helvetica", 14)
    p.setFillColor(colors.gray)
    p.drawCentredString(width/2, height-290, f"Career Path: {career}")
    
    # Date and Score
    p.setFont("Helvetica", 12)
    p.setFillColor(colors.gray)
    p.drawCentredString(width/2-100, height-340, f"Date: {date}")
    p.drawCentredString(width/2+100, height-340, f"Score: {score}%")
    
    # Footer
    p.setFont("Helvetica-Oblique", 10)
    p.setFillColor(colors.lightgrey)
    p.drawCentredString(width/2, 50, "Career Guidance AI - Empowering Future Leaders")
    
    # Logo placeholder
    p.setFont("Helvetica-Bold", 40)
    p.setFillColor(colors.HexColor('#667eea'))
    p.drawCentredString(width/2, height-400, "🏆")
    
    p.showPage()
    p.save()
    
    buffer.seek(0)
    
    return send_file(buffer, 
                    as_attachment=True, 
                    download_name=f'certificate_{cert_id}.pdf',
                    mimetype='application/pdf')

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
