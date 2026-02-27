from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import hashlib

app = Flask(__name__)
app.secret_key = 'career_guidance_secret_key_2024'

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
        'study_plan': 'Year 1: Learn Python/HTML/CSS || Year 2: JavaScript & React || Year 3: Projects & Internship || Year 4: Full Stack & Placement'
    },
    # Design/Art
    'drawing': {
        'career': 'Graphic Designer / Illustrator',
        'skills': 'Adobe Photoshop, Illustrator, Figma, Typography, Color Theory, Visual Design, Creativity',
        'courses': 'Graphic Design Certification, Fine Arts, Animation, UX Design, Digital Art',
        'salary': '₹3-15 LPA (Entry to Senior)',
        'future_scope': 'Freelance opportunities, digital media growth, brand identity design',
        'study_plan': 'Year 1: Learn Design Tools (PS/AI) || Year 2: Typography & Color Theory || Year 3: Portfolio Building || Year 4: Freelancing/Job'
    },
    # Music
    'singing': {
        'career': 'Professional Singer / Music Composer',
        'skills': 'Vocal Training, Music Theory, Keyboard/Instrument, Recording, Stage Performance, Songwriting',
        'courses': 'Music Certification, Classical Training, Audio Engineering, Music Production',
        'salary': '₹3-20+ LPA (varies by fame)',
        'future_scope': 'Music industry, streaming platforms, live performances, content creation',
        'study_plan': 'Year 1: Vocal Training || Year 2: Music Theory & Instruments || Year 3: Recording & Production || Year 4: Live Shows & Albums'
    },
    # Dance
    'dancing': {
        'career': 'Professional Dancer / Choreographer',
        'skills': 'Various Dance Forms, Choreography, Stage Performance, Fitness, Expression, Teaching',
        'courses': 'Dance Certification, Performing Arts, Choreography Courses, Dance Therapy',
        'salary': '₹3-18 LPA (Entry to Senior)',
        'future_scope': 'Bollywood, stage shows, choreography, dance studios, online content',
        'study_plan': 'Year 1: Basic Dance Forms || Year 2: Advanced Choreography || Year 3: Stage Performances || Year 4: Industry Work'
    },
    # Biology/Medical
    'biology': {
        'career': 'Doctor / Medical Professional',
        'skills': 'Medical Knowledge, Patient Care, Diagnosis, Surgery, Research, Communication',
        'courses': 'MBBS, MD, MS, Nursing, Pharmacy, Biotechnology, Medical Research',
        'salary': '₹6-50+ LPA (varies by specialization)',
        'future_scope': 'High demand, healthcare industry growth, research opportunities',
        'study_plan': 'Year 1-2: NEET Prep || Year 3-5: MBBS Studies || Year 6-7: Internship || Year 8+: Specialization'
    },
    # Science/Research
    'science': {
        'career': 'Research Scientist',
        'skills': 'Scientific Methods, Research, Data Analysis, Laboratory Skills, Critical Thinking, Publications',
        'courses': 'B.Sc/M.Sc, PhD, JEE, Research Fellowships, Indian Institute of Science',
        'salary': '₹4-20 LPA (Entry to Senior)',
        'future_scope': 'Research institutes, universities, DRDO, ISRO, pharmaceutical companies',
        'study_plan': 'Year 1-2: Foundation (PCM) || Year 3-4: B.Sc Focus || Year 5-6: M.Sc || Year 7+: PhD/Research'
    },
    # Business
    'business': {
        'career': 'Business Analyst',
        'skills': 'Data Analysis, SQL, Excel, Communication, Problem Solving, Domain Knowledge',
        'courses': 'MBA, Business Analytics Certification, Tableau/PowerBI',
        'salary': '₹5-20 LPA (Entry to Senior)',
        'future_scope': 'High demand across industries, consulting opportunities',
        'study_plan': 'Year 1-2: Graduation || Year 3: Aptitude & CAT Prep || Year 4-5: MBA || Year 6+: Job'
    },
    # Data
    'data': {
        'career': 'Data Scientist',
        'skills': 'Python, R, Statistics, Machine Learning, Data Visualization, SQL, Big Data',
        'courses': 'Data Science Certification, Machine Learning, Deep Learning',
        'salary': '₹6-30 LPA (Entry to Senior)',
        'future_scope': 'Very high demand, AI/ML integration, excellent growth',
        'study_plan': 'Year 1: Python & Statistics || Year 2: Machine Learning || Year 3: Projects & Kaggle || Year 4: Data Science Job'
    },
    # Marketing
    'marketing': {
        'career': 'Digital Marketing Manager',
        'skills': 'SEO, SEM, Social Media, Content Creation, Analytics, Email Marketing',
        'courses': 'Digital Marketing Certification, Google Ads, Analytics',
        'salary': '₹4-15 LPA (Entry to Senior)',
        'future_scope': 'E-commerce boom, remote work options, growing field',
        'study_plan': 'Year 1: SEO & Social Media || Year 2: Google Ads & Analytics || Year 3: Live Projects || Year 4: Digital Marketing Job'
    },
    # Healthcare
    'healthcare': {
        'career': 'Healthcare Administrator',
        'skills': 'Healthcare Management, Medical Terminology, Data Analysis, Leadership',
        'courses': 'Healthcare Management MBA, Hospital Administration, Public Health',
        'salary': '₹5-20 LPA (Entry to Senior)',
        'future_scope': 'Stable growth, healthcare industry expansion',
        'study_plan': 'Year 1-2: Graduation || Year 3: Healthcare Mgmt Prep || Year 4-5: MBA Healthcare || Year 6+: Hospital Job'
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
} 
    'hi': {

<strong>परीक्षा पैटर्न:</strong>
• राज्य सेवा (प्री) - 100 प्रश्न, 200 अंक
• राज्य सेवा (मेन्स) - 9 पेपर
• इंटरव्यू - 275 अंक

<strong>2 साल की तैयारी योजना:</strong>

<strong>साल 1:</strong>
<b>महीने 1-3:</b> परीक्षा पैटर्न समझें
<b>महीने 4-6:</b> मराठी और अंग्रेजी, बुनियादी GS
<b>महीने 7-9:</b> इतिहास, भूगोल, राजनीति
<b>महीने 10-12:</b> करंट अफेयर्स, MCQ प्रैक्टिस

<strong>साल 2:</strong>
<b>महीने 13-15:</b> वैकल्पिक विषय
<b>महीने 16-18:</b> उत्तर लेखन अभ्यास
<b>महीने 19-21:</b> पूर्ण मॉक टेस्ट
<b>महीने 22-24:</b> अंतिम रिवीज़न

<strong>किताबें:</strong> लक्ष्मीकांत, स्पेक्ट्रम''',

        'upsc': '''<h3>🏛️ UPSC (संघ लोक सेवा आयोग)</h3>

<strong>परीक्षा पैटर्न:</strong>
• प्रीलिम्स - GS I + CSAT
• मेन्स - 9 पेपर
• इंटरव्यू - 275 अंक

<strong>2 साल की तैयारी:</strong>

<strong>साल 1:</b>
<b>महीने 1-2:</b> सिलेबस समझें
<b>महीने 3-5:</b> इतिहास
<b>महीने 6-8:</b> भूगोल
<b>महीने 9-11:</b> राजनीति, अर्थव्यवस्था

<strong>साल 2:</b>
<b>महीने 13-15:</b> ऑप्शनल + करंट अफेयर्स
<b>महीने 16-18:</b> उत्तर लेखन
<b>महीने 19-21:</b> टेस्ट सीरीज
<b>महीने 22-24:</b> फाइनल मॉक

<strong>किताबें:</strong> NCERT, लक्ष्मीकांत, स्पेक्ट्रम''',

        'army': '''<h3>🎖️ भारतीय सेना करियर</h3>

<strong>प्रवेश विकल्प:</strong>
• NDA (10+2) - आयु 16.5-19.5 वर्ष
• CDS (स्नातक) - आयु 20-24 वर्ष
• AFCAT (वायुसेना)

<strong>तैयारी:</strong>
• लिखित परीक्षा + SSB
• शारीरिक फिटनेस जरूरी
• 1.6 किमी दौड़ना - 6 मिनट

<strong>वेतन:</strong> लेफ्टिनेंट - ₹56,100 + भत्ते''',
    }
}

# Mock AI responses for career guidance
def get_career_response(user_message, language='en'):
    user_message = user_message.lower()
    
    # Get responses for selected language
    responses = CAREER_RESPONSES.get(language, CAREER_RESPONSES['en'])
    
    for key, response in responses.items():
        if key in user_message:
            return response
    
    return "I'm here to help with career guidance! Ask me about MPSC, UPSC, Army, Commerce careers, Arts careers, or any other career path."


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

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
