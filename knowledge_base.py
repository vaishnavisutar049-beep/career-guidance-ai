# Comprehensive Knowledge Base for AI Chatbot
# This file contains career Q&A for career guidance

# ==================== PARENT-STUDENT CONFLICT ANALYZER ====================

# Career keywords mapping for conflict analysis
CAREER_KEYWORDS = {
    # Technology & IT (Student's interest in Game Development)
    'game_developer': {'category': 'technology', 'keywords': ['game', 'gaming', 'software', 'coding', 'programming', 'app', 'development', 'tech', 'IT'], 'stability': 'medium'},
    'technology': {'category': 'technology', 'keywords': ['software', 'developer', 'engineer', 'coding', 'programming', 'tech', 'IT', 'computer'], 'stability': 'medium'},
    'data': {'category': 'technology', 'keywords': ['data', 'analytics', 'science', 'AI', 'ML', 'machine learning'], 'stability': 'medium'},
    
    # Government Jobs (Parent's interest)
    'government': {'category': 'government', 'keywords': ['government', 'govt', 'job', 'MPSC', 'UPSC', 'bank', 'PSC', 'civil service', 'police', 'railway', 'admin'], 'stability': 'high'},
    'banking': {'category': 'government', 'keywords': ['bank', 'banking', 'PO', 'clerk', ' RBI', 'nationalized'], 'stability': 'high'},
    'teaching': {'category': 'education', 'keywords': ['teacher', 'teaching', 'professor', 'education', 'tutor'], 'stability': 'high'},
    
    # Healthcare
    'biology': {'category': 'healthcare', 'keywords': ['doctor', 'medical', 'MBBS', 'health', 'hospital', 'nurse', 'pharma'], 'stability': 'high'},
    'healthcare': {'category': 'healthcare', 'keywords': ['health', 'medical', 'nurse', 'pharmacy', 'hospital'], 'stability': 'high'},
    
    # Business & Finance
    'business': {'category': 'business', 'keywords': ['business', 'management', 'MBA', 'entrepreneur', 'company'], 'stability': 'medium'},
    'engineering': {'category': 'engineering', 'keywords': ['engineer', 'engineering', 'civil', 'mechanical', 'electrical'], 'stability': 'medium'},
    
    # Creative
    'drawing': {'category': 'creative', 'keywords': ['design', 'graphic', 'art', 'drawing', 'creative'], 'stability': 'low'},
    'singing': {'category': 'creative', 'keywords': ['singer', 'music', 'singing', 'audio'], 'stability': 'low'},
    'dancing': {'category': 'creative', 'keywords': ['dance', 'dancer', 'performer'], 'stability': 'low'},
    
    # Science
    'science': {'category': 'science', 'keywords': ['science', 'research', 'physics', 'chemistry', 'researcher'], 'stability': 'medium'},
    
    # Marketing
    'marketing': {'category': 'marketing', 'keywords': ['marketing', 'digital', 'sales', 'advertising', 'brand'], 'stability': 'medium'}
}

# Compromise career suggestions based on conflict types
COMPROMISE_SUGGESTIONS = {
    # Technology + Government = IT in Government
    ('technology', 'government'): {
        'suggestion': 'IT Sector in Government',
        'description': 'Combine your interest in technology with job security through government IT positions',
        'careers': ['Government IT Officer', 'PSU IT Jobs', 'Banking IT Sector', 'NIC Data Analyst'],
        'explanation': 'You can work in government IT departments, PSUs, banks, and nodal agencies while using your tech skills'
    },
    # Game Developer + Government = IT in Government Gaming
    ('technology', 'government'): {
        'suggestion': 'Government IT / Gaming in PSUs',
        'description': 'Use your tech skills in secure government IT roles or explore gaming wings in government organizations',
        'careers': ['NIC IT Specialist', 'PSU Software Developer', 'Government Digital Transformation Projects', 'E-Governance'],
        'explanation': 'Many PSUs and government organizations now have IT wings where you can develop applications and systems'
    },
    # Creative + Government = Government Media
    ('creative', 'government'): {
        'suggestion': 'Government Media & Cultural Sector',
        'description': 'Combine creativity with government job security',
        'careers': ['Directorate of Cultural Affairs', 'Doordarshan', 'All India Radio', 'Government Press'],
        'explanation': 'Government has various media and cultural departments that need creative professionals'
    },
    # Healthcare + Government = Government Healthcare
    ('healthcare', 'government'): {
        'suggestion': 'Government Healthcare Sector',
        'description': 'Best of both worlds - medical career with government job security',
        'careers': ['Government Doctor', 'AIIMS', 'PHC Doctor', 'Railway Doctor', 'CGHS'],
        'explanation': 'Government hospitals and health departments offer excellent job security with good salaries'
    },
    # Business + Government = Government Management
    ('business', 'government'): {
        'suggestion': 'Government Management Roles',
        'description': 'Business skills with government stability',
        'careers': ['PSU Manager', 'Banking Officer', 'Government Administrative Roles'],
        'explanation': 'PSUs and government banks offer management positions with excellent benefits'
    },
    # Science + Government = Research in Government Institutes
    ('science', 'government'): {
        'suggestion': 'Government Research Institutes',
        'description': 'Scientific research with government job security',
        'careers': ['DRDO', 'ISRO', 'CSIR', 'ICAR', 'DAE', 'Research Scientist'],
        'explanation': 'Top research institutes in India offer excellent career opportunities with job security'
    },
    # Same category - High agreement
    ('same', 'same'): {
        'suggestion': 'Perfect Match!',
        'description': 'You both want similar careers - this is great!',
        'careers': [],
        'explanation': 'Parent and student have similar interests, which makes the career path smoother'
    }
}

def analyze_conflict(student_choice, parent_choice):
    """
    Analyze conflict between student and parent career choices
    Returns: dict with agreement_level, compromise_suggestion, and details
    """
    # Normalize inputs
    student_choice = student_choice.lower().strip() if student_choice else ''
    parent_choice = parent_choice.lower().strip() if parent_choice else ''
    
    # Find matching career keys
    student_key = None
    parent_key = None
    
    for key, info in CAREER_KEYWORDS.items():
        # Check if any keyword matches
        for kw in info['keywords']:
            if kw in student_choice or student_choice in kw:
                student_key = key
                break
        for kw in info['keywords']:
            if kw in parent_choice or parent_choice in kw:
                parent_key = key
                break
        if student_key and parent_key:
            break
    
    # If no match found, try to infer from common terms
    if not student_key:
        if 'game' in student_choice:
            student_key = 'game_developer'
        elif any(w in student_choice for w in ['software', 'coding', 'programming', 'tech', 'IT']):
            student_key = 'technology'
        else:
            student_key = 'technology'  # Default to tech
    
    if not parent_key:
        if any(w in parent_choice for w in ['government', 'govt', 'job', 'MPSC', 'UPSC', 'PSC', 'bank', 'civil', 'admin']):
            parent_key = 'government'
        elif 'bank' in parent_choice:
            parent_key = 'banking'
        elif 'teach' in parent_choice:
            parent_key = 'teaching'
        else:
            parent_key = 'government'  # Default to government
    
    # Get categories
    student_cat = CAREER_KEYWORDS.get(student_key, {}).get('category', 'technology')
    parent_cat = CAREER_KEYWORDS.get(parent_key, {}).get('category', 'government')
    
    # Calculate agreement level
    if student_key == parent_key:
        agreement_level = 100
        agreement_text = "🎉 Perfect Match!"
        agreement_color = "green"
    elif student_cat == parent_cat:
        agreement_level = 75
        agreement_text = "👍 Good Match!"
        agreement_color = "lightgreen"
    elif student_cat == 'technology' and parent_cat == 'government':
        agreement_level = 60
        agreement_text = "💡 Good Compromise Possible"
        agreement_color = "yellow"
    elif student_cat == 'government' and parent_cat == 'technology':
        agreement_level = 60
        agreement_text = "💡 Good Compromise Possible"
        agreement_color = "yellow"
    elif student_cat == 'creative' and parent_cat == 'government':
        agreement_level = 45
        agreement_text = "🤝 Compromise Needed"
        agreement_color = "orange"
    elif parent_cat == 'creative' and student_cat == 'government':
        agreement_level = 45
        agreement_text = "🤝 Compromise Needed"
        agreement_color = "orange"
    else:
        agreement_level = 30
        agreement_text = "⚠️ Different Perspectives"
        agreement_color = "red"
    
    # Get compromise suggestion
    compromise_key = (student_cat, parent_cat)
    if compromise_key in COMPROMISE_SUGGESTIONS:
        compromise = COMPROMISE_SUGGESTIONS[compromise_key]
    else:
        # Reverse key
        compromise_key = (parent_cat, student_cat)
        if compromise_key in COMPROMISE_SUGGESTIONS:
            compromise = COMPROMISE_SUGGESTIONS[compromise_key]
        else:
            # Default compromise
            compromise = {
                'suggestion': 'Explore Related Fields',
                'description': 'Consider careers that blend both interests',
                'careers': ['Research combined careers', 'Consultant roles', 'Government + Private hybrid'],
                'explanation': 'Both career paths have merit - discuss further to find common ground'
            }
    
    return {
        'student_choice': student_choice.title(),
        'parent_choice': parent_choice.title(),
        'student_key': student_key,
        'parent_key': parent_key,
        'student_category': student_cat.title(),
        'parent_category': parent_cat.title(),
        'agreement_level': agreement_level,
        'agreement_text': agreement_text,
        'agreement_color': agreement_color,
        'compromise': compromise
    }


KNOWLEDGE_BASE = {
    # MPSC RELATED
    "mpsc": {
        "keywords": ["mpsc", "maharashtra public service", "state service", "rajya sev"],
        "category": "exam",
        "en": """<h3>📋 MPSC (Maharashtra Public Service Commission)</h3>

<strong>Exam Pattern:</strong>
• State Services (Pre) - 100 questions, 200 marks, 2 hours
• State Services (Main) - 9 papers (Preliminary qualifying)
• Interview - 275 marks

<strong>Eligibility:</strong>
• Graduate in any stream
• Age: 18-38 years (varies by category)

<strong>2-Year Study Plan:</strong>

<strong>Year 1:</strong>
<b>Months 1-3:</b> Understand exam pattern, collect study materials
<b>Months 4-6:</b> Complete Marathi & English, Basic GS
<b>Months 7-9:</b> Complete History, Geography, Polity
<b>Months 10-12:</b> Current Affairs, Practice MCQs

<strong>Year 2:</strong>
<b>Months 13-15:</b> Optional subject preparation
<b>Months 16-18:</b> Answer writing practice
<b>Months 19-21:</b> Full mock tests, thorough revision
<b>Months 22-24:</b> Final revision, attempt prelims

<strong>Recommended Books:</strong>
• History - Spectrum (Modern India)
• Geography - Majid Husain
• Polity - Laxmikant
• Economy - Ramesh Singh

<strong>Salary after selection:</strong> ₹40,000-₹1,50,000/month""",

        "mr": """<h3>📋 MPSC (महाराष्ट्र लोकसेवा आयोग)</h3>

<strong>परीक्षा पद्धत:</strong>
• राज्य सेवा (प्रारंभिक) - 100 प्रश्न, 200 गुण
• राज्य सेवा (मुख्य) - 9 पेपर
• मुलाखत - 275 गुण

<strong>पात्रता:</strong>
• कोणत्याही विद्याशाखेची पदवी
• वय: 18-38 वर्ष

<strong>2 वर्ष अभ्यास योजना:</strong>
<strong>वर्ष 1:</strong> महिने 1-3: परीक्षा पद्धत
महिने 4-6: मराठी व इंग्रजी
महिने 7-9: इतिहास, भूगोल
महिने 10-12: चालू घडामोडी

<strong>वर्ष 2:</strong>
महिने 13-15: पर्यायी विषय
महिने 16-18: उत्तर लेखन
महिने 19-21: मॉक टेस्ट

<strong>पुस्तके:</strong> लक्ष्मीकांत, स्पेक्ट्रम

<strong>पगार:</strong> ₹40,000-₹1,50,000/महिना""",

        "hi": """<h3>MPSC - Maharashtra Public Service Commission</h3>
<strong>Exam Pattern:</strong>
- State Services (Pre) - 100 questions, 200 marks
- State Services (Main) - 9 papers
- Interview - 275 marks

<strong>Eligibility:</strong>
- Graduate in any stream
- Age: 18-38 years

<strong>2-Year Study Plan:</strong>
Year 1: Pattern, Basic GS, History, Geography
Year 2: Optional, Answer Writing, Mocks

<strong>Books:</strong> Laxmikant, Spectrum
<strong>Salary:</strong> ₹40,000-₹1,50,000/month"""
    },

    # UPSC RELATED
    "upsc": {
        "keywords": ["upsc", "union public service", "ias", "ips", "ifs", "civil service"],
        "category": "exam",
        "en": """<h3>🏛️ UPSC (Union Public Service Commission)</h3>

<strong>Exam Pattern:</strong>
• Prelims - GS I (100 questions, 200 marks) + CSAT (80 questions, 200 marks)
• Mains - 9 papers (1750 marks)
• Interview - 275 marks
• Total: 2025 marks

<strong>Eligibility:</strong>
• Graduate in any stream
• Age: 21-32 years (general category)
• Attempts: 6 (general)

<strong>3-Year Preparation Plan:</strong>

<strong>Year 1 - Foundation:</strong>
<b>Months 1-2:</b> Understand syllabus, collect books
<b>Months 3-5:</b> Ancient & Medieval History
<b>Months 6-8:</b> Modern History, Geography
<b>Months 9-11:</b> Polity, Economy basics

<strong>Year 2 - Advanced:</strong>
<b>Months 12-15:</b> Complete Economy, Environment
<b>Months 16-18:</b> Science & Technology
<b>Months 19-22:</b> Current Affairs integration
<b>Months 23-24:</b> Optional subject start

<strong>Year 3 - Revision:</strong>
<b>Months 25-28:</b> Optional + Answer writing
<b>Months 29-32:</b> Test series, mocks
<b>Months 33-36:</b> Final revision, attempt exam

<strong>Recommended Books:</strong>
• History - NCERTs, Spectrum
• Geography - NCERTs, Majid Husain
• Polity - Laxmikant
• Economy - Ramesh Singh, Economic Survey

<strong>Salary after selection:</strong>
• IAS: ₹56,100-₹2,50,000/month
• IPS: ₹56,100-₹2,25,000/month""",

        "mr": """<h3>🏛️ UPSC (संघ लोकसेवा आयोग)</h3>

<strong>परीक्षा पद्धत:</strong>
• प्रारंभिक - GS I + CSAT
• मुख्य - 9 पेपर (1750 गुण)
• मुलाखत - 275 गुण

<strong>पात्रता:</strong>
• पदवीधर
• वय: 21-32 वर्ष

<strong>3 वर्ष तयारी योजना:</strong>
वर्ष 1: NCERT, इतिहास, भूगोल
वर्ष 2: राज्यव्यवस्था, अर्थशास्त्र
वर्ष 3: मॉक टेस्ट, पुनरावलोकन

<strong>पुस्तके:</strong> NCERT, लक्ष्मीकांत, स्पेक्ट्रम

<strong>पगार:</strong> ₹56,100-₹2,50,000/महिना""",

        "hi": """<h3>UPSC - Union Public Service Commission</h3>
<strong>Exam Pattern:</strong>
- Prelims - GS I + CSAT
- Mains - 9 papers (1750 marks)
- Interview - 275 marks

<strong>Eligibility:</strong>
- Graduate, Age: 21-32 years

<strong>3-Year Plan:</strong>
Year 1: Foundation, History, Geography
Year 2: Polity, Economy, Current Affairs
Year 3: Revision, Mock Tests

<strong>Books:</strong> NCERTs, Laxmikant, Spectrum
<strong>Salary:</strong> ₹56,100-₹2,50,000/month"""
    },

    # JEE RELATED
    "jee": {
        "keywords": ["jee", "joint entrance", "iit", "engineering", "tech", "computer science"],
        "category": "exam",
        "en": """<h3>🔬 JEE (Joint Entrance Examination)</h3>

<strong>Exam Pattern:</strong>
• JEE Main - 90 questions, 300 marks (NTA conducts 4 times/year)
• JEE Advanced - 54 questions, 180 marks (IIT conducts)

<strong>Eligibility:</strong>
• 10+2 with PCM (Physics, Chemistry, Mathematics)
• Age: No upper limit

<strong>2-Year Preparation Plan:</strong>

<strong>Class 11 (Year 1):</strong>
<b>Months 1-3:</b> Physics - Mechanics, Chemistry - Mole Concept
<b>Months 4-6:</b> Physics - Waves, Chemistry - Thermodynamics
<b>Months 7-9:</b> Mathematics - Algebra, Physics - Gravitation
<b>Months 10-12:</b> Complete syllabus, start revision

<strong>Class 12 (Year 2):</strong>
<b>Months 1-3:</b> Class 12th topics
<b>Months 4-6:</b> Complete Class 12th
<b>Months 7-9:</b> Full syllabus revision
<b>Months 10-12:</b> Mock tests, problem solving

<strong>Top IITs:</strong>
• IIT Bombay, Delhi, Madras, Kharagpur
• Average Package: ₹15-50 LPA

<strong>Career Options:</strong>
• Software Engineer, Data Scientist
• Machine Learning, AI
• Civil, Mechanical, Electrical Engineering""",

        "mr": """<h3>🔬 JEE (Joint Entrance Examination)</h3>

<strong>परीक्षा पद्धत:</strong>
• JEE Main - 90 प्रश्न, 300 गुण
• JEE Advanced - 54 प्रश्न, 180 गुण

<strong>पात्रता:</strong>
• 10+2 PCM सह

<strong>Top IITs:</strong> IIT Bombay, Delhi, Madras

<strong>पगार:</strong> ₹15-50 LPA""",

        "hi": """<h3>JEE - Joint Entrance Examination</h3>
<strong>Exam:</strong> JEE Main + Advanced
<strong>Eligibility:</strong> 10+2 with PCM
<strong>2-Year Plan:</strong> Class 11-12 syllabus
<strong>Top IITs:</strong> Bombay, Delhi, Madras, Kharagpur
<strong>Package:</strong> ₹15-50 LPA"""
    },

    # NEET RELATED
    "neet": {
        "keywords": ["neet", "medical", "mbbs", "doctor", "nursing", "bhms", "bams"],
        "category": "exam",
        "en": """<h3>⚕️ NEET (National Eligibility cum Entrance Test)</h3>

<strong>Exam Pattern:</strong>
• 180 questions, 720 marks
• Physics - 45 questions
• Chemistry - 45 questions
• Biology (Botany + Zoology) - 90 questions
• Duration - 3 hours 20 minutes

<strong>Eligibility:</strong>
• 10+2 with PCB (Physics, Chemistry, Biology)
• Age: 17-25 years
• Must be Indian citizen

<strong>2-Year Preparation Plan:</strong>

<strong>Year 1:</strong>
<b>Months 1-3:</b> Physics - Mechanics, Chemistry - Basic
<b>Months 4-6:</b> Biology - Diversity, Cell
<b>Months 7-9:</b> Physics - Modern Physics, Chemistry - Organic
<b>Months 10-12:</b> Biology - Human Physiology

<strong>Year 2:</strong>
<b>Months 1-3:</b> Complete Class 12th syllabus
<b>Months 4-6:</b> Full revision
<b>Months 7-9:</b> Mock tests, analysis
<b>Months 10-12:</b> Final preparation, exam

<strong>Medical Courses:</strong>
• MBBS (5.5 years) - Doctor
• BDS (5 years) - Dentist
• BAMS (5.5 years) - Ayurveda
• BHMS (5.5 years) - Homeopathy
• BSc Nursing (4 years)

<strong>Top Colleges:</strong>
• AIIMS Delhi, PGIMER, CMC Vellore
• Fees: ₹1,000-₹2,00,000/year (govt)
• Stipend during internship: ₹20,000+/month""",

        "mr": """<h3>⚕️ NEET (National Eligibility cum Entrance Test)</h3>

<strong>परीक्षा पद्धत:</strong>
• 180 प्रश्न, 720 गुण
• Physics, Chemistry, Biology

<strong>पात्रता:</strong>
• 10+2 PCB सह

<strong>Medical Courses:</strong>
• MBBS - डॉक्टर
• BDS - दंतचिकित्सक
• BAMS - आयुर्वेद
• BHMS - होमिओपॅथी

<strong>Top Colleges:</strong> AIIMS Delhi, PGIMER""",

        "hi": """<h3>NEET - National Eligibility cum Entrance Test</h3>
<strong>Exam:</strong> 180 questions, 720 marks
<strong>Subjects:</strong> Physics, Chemistry, Biology
<strong>Courses:</strong> MBBS, BDS, BAMS, BHMS, Nursing
<strong>Top Colleges:</strong> AIIMS, PGIMER, CMC"""
    },

    # ARMY/DEFENCE RELATED
    "army": {
        "keywords": ["army", "defence", "military", "nda", "cds", "ssb", "afcat", "air force", "navy", "territorial army"],
        "category": "career",
        "en": """<h3>🎖️ Indian Defence Forces Careers</h3>

<strong>Entry Options:</strong>

<b>1. NDA (National Defence Academy)</b>
• 10+2 pass (for Army: any stream, Air Force/Navy: PCM)
• Age: 16.5-19.5 years
• Duration: 3 years (academy) + 1 year training
• Monthly Stipend: ₹56,100+

<b>2. CDS (Combined Defence Services)</b>
• Graduate in any stream
• Age: 20-24 years (varies by service)
• Written Exam + SSB Interview

<b>3. AFCAT (Air Force)</b>
• Graduate (60% marks in Maths/Physics for Flying)
• Age: 20-24 years
• Entries: Flying, Technical, Ground Duty

<b>4. Indian Navy</b>
• 10+2 (PCM) or Graduate
• Entries: Navy, Air Wing

<strong>SSB Interview Process:</strong>
• Day 1: Screening (OIR, PP&DT)
• Day 2-4: Psychological Tests
• Day 5: Conference
• Total: 5 days

<strong>Physical Standards:</strong>
• Height: 157 cm (varies)
• 1.6 km run: 6 minutes 30 seconds
• 10 pushups, 10 situps
• Eye vision: 6/6 (correctable)

<strong>Salary (Lieutenant):</strong> ₹56,100 + Allowances (DA, HRA, TA)
<strong>Total Benefits:</strong> Free accommodation, medical, pension""",

        "mr": """<h3>🎖️ भारतीय सेना</h3>

<strong>प्रवेश पर्याय:</strong>
• NDA (10+2) - वय 16.5-19.5 वर्ष
• CDS (पदवीधर) - वय 20-24 वर्ष
• AFCAT (वायुसेना)

<strong>SSB प्रक्रिया:</strong> 5 दिवस

<strong>शारीरिक:</strong> उंची 157 सेमी, 1.6 किमी धावणे

<strong>पगार:</strong> ₹56,100 + भत्ते""",

        "hi": """<h3>Indian Defence Forces</h3>
<strong>Entries:</strong> NDA, CDS, AFCAT, TA
<strong>Age:</strong> 16.5-24 years
<strong>Process:</strong> Written + SSB (5 days)
<strong>Physical:</strong> 157cm height, 1.6km run
<strong>Salary:</strong> ₹56,100 + allowances"""
    },

    # COMMERCE CAREERS
    "commerce": {
        "keywords": ["commerce", "bcom", "bba", "mba", "ca", "cma", "cs", "accountant", "banking", "finance"],
        "category": "career",
        "en": """<h3>💼 Commerce & Finance Careers</h3>

<strong>Popular Courses:</strong>

<b>1. B.Com (Bachelor of Commerce)</b>
• Duration: 3 years
• Subjects: Accounting, Economics, Tax
• Colleges: SRCC, St. Xavier's, SYdenham
• Salary: ₹3-8 LPA

<b>2. BBA (Bachelor of Business Administration)</b>
• Duration: 3 years
• Subjects: Management, Marketing, Finance
• Top Colleges: IIMs (Indore, Rohtak), SIMSREE
• Salary: ₹4-12 LPA

<b>3. CA (Chartered Accountant)</b>
• Duration: 4-5 years (including articleship)
• Levels: Foundation, Intermediate, Final
• Salary: ₹6-20 LPA (after qualification)
• Top Firms: Big 4, Big CA Firms

<b>4. CMA (Cost & Management Accountant)</b>
• Duration: 2-3 years
• Salary: ₹5-15 LPA

<b>5. CS (Company Secretary)</b>
• Duration: 2-3 years
• Salary: ₹4-12 LPA

<b>6. MBA (Master of Business Administration)</b>
• Duration: 2 years
• Specializations: Finance, Marketing, HR, Operations
• Top IIMs: A, B, C, L, K
• Salary: ₹8-50 LPA

<strong>Banking Careers:</strong>
• PO (Probationary Officer) - ₹8-15 LPA
• Clerk - ₹4-8 LPA
• Exams: SBI PO, IBPS PO, RBI""",

        "mr": """<h3>💼 व्यापार आणि वित्त</h3>

<strong>लोकप्रिय कोर्सेस:</strong>
• B.Com - 3 वर्ष, ₹3-8 LPA
• BBA - 3 वर्ष, ₹4-12 LPA
• CA - 4-5 वर्ष, ₹6-20 LPA
• MBA - 2 वर्ष, ₹8-50 LPA

<strong>Banking:</strong> PO, Clerk - ₹4-15 LPA""",

        "hi": """<h3>Commerce Careers</h3>
<strong>Courses:</strong> B.Com, BBA, CA, CMA, MBA
<strong>Salary:</strong> ₹3-50 LPA
<strong>Banking:</strong> PO, Clerk positions"""
    },

    # ARTS CAREERS
    "arts": {
        "keywords": ["arts", "ba", "journalism", "psychology", "sociology", "history", "language", "law", "llb"],
        "category": "career",
        "en": """<h3>🎭 Arts & Humanities Careers</h3>

<strong>Popular Courses:</strong>

<b>1. BA (Bachelor of Arts)</b>
• Duration: 3 years
• Streams: History, Political Science, Sociology, Psychology, Economics, Languages
• Top Colleges: DU, St. Stephen's, JNU
• Salary: ₹3-8 LPA

<b>2. BA LLB (Law)</b>
• Duration: 5 years
• Salary: ₹5-15 LPA
• Top Colleges: NLSIU, NALSAR, NUJS

<b>3. Journalism & Mass Communication</b>
• Duration: 3 years
• Salary: ₹4-12 LPA
• Top: IIMC, Jamia, ACJ

<b>4. Psychology</b>
• BSc/MSc Psychology
• Salary: ₹4-20 LPA (Clinical Psychologist)

<b>5. Hotel Management</b>
• Duration: 3-4 years
• Salary: ₹4-15 LPA
• Top: IHM Mumbai, Delhi

<b>6. Fashion Design</b>
• Duration: 3-4 years
• Salary: ₹4-20 LPA
• Top: NIFT, FDDI

<strong>Career Options:</strong>
• Teacher/Professor
• Civil Services
• Content Writer
• Social Worker
• Law""",

        "mr": """<h3>🎭 कला आणि मानववंशशास्त्र</h3>

<strong>कोर्सेस:</strong>
• BA - 3 वर्ष
• BA LLB - 5 वर्ष
• Journalism - 3 वर्ष
• Psychology
• Hotel Management

<strong>पगार:</strong> ₹3-20 LPA""",

        "hi": """<h3>Arts Careers</h3>
<strong>Courses:</strong> BA, BA LLB, Journalism, Psychology
<strong>Salary:</strong> ₹3-20 LPA"""
    },

    # EXAM PREPARATION
    "preparation": {
        "keywords": ["preparation", "study", "how to prepare", "strategy", "tips", "plan", "timetable", "tenth", "twelfth"],
        "category": "guidance",
        "en": """<h3>📚 Exam Preparation Strategy</h3>

<strong>General Tips:</strong>

<b>1. Understand the Syllabus</b>
• Download official syllabus
• Mark important topics
• Know weightage of each section

<b>2. Create a Study Plan</b>
• Daily: 6-8 hours effective study
• Weekly: Complete 1-2 chapters
• Monthly: Revision + Tests

<b>3. Quality Study Material</b>
• For NCERT exams: NCERT books first
• Then reference books
• Finally, test series

<b>4. Practice is Key</b>
• Solve previous year questions (PYQs)
• Take mock tests regularly
• Analyze mistakes

<b>5. Current Affairs</b>
• Read newspaper daily (The Hindu, Indian Express)
• Watch news channels
• Use monthly magazines

<b>6. Revision Strategy</b>
• First revision: Within 7 days
• Second revision: Within 30 days
• Final revision: Before exam

<b>7. Stay Healthy</b>
• 7-8 hours sleep
• Regular exercise
• Healthy diet

<strong>For 10th/12th Students:</strong>
• Focus on basics
• NCERT is sufficient
• Solve all examples
• Previous year board papers""",

        "mr": """<h3>📚 परीक्षा तयारी</h3>

<strong>सामान्य टिप्स:</strong>
• अभ्यासक्रम समजून घेणे
• दैनिक 6-8 तास अभ्यास
• मॉक टेस्ट घेणे
• चालू घडामोडी वाचणे

<strong>शारीरिक:</strong> 7-8 तास झोप, व्यायाम""",

        "hi": """<h3>Exam Preparation</h3>
<strong>Tips:</strong>
- Understand syllabus
- 6-8 hours daily study
- Mock tests
- Current affairs
- Health: sleep, exercise"""
    },

    # SALARY & SCOPE
    "salary": {
        "keywords": ["salary", "package", "income", "earn", "money", "scope", "future", "demand"],
        "category": "guidance",
        "en": """<h3>💰 Career Salary & Future Scope</h3>

<strong>High Salary Careers (₹10-50+ LPA):</strong>
• Software Engineer (IT) - ₹8-40 LPA
• Data Scientist - ₹8-35 LPA
• Doctor (MBBS) - ₹6-50+ LPA
• Investment Banker - ₹12-50 LPA
• MBA (Top IIMs) - ₹15-50 LPA
• Pilot - ₹15-80 LPA

<strong>Medium Salary Careers (₹5-15 LPA):</strong>
• Teacher/Professor - ₹5-15 LPA
• Accountant (CA) - ₹7-20 LPA
• Graphic Designer - ₹4-12 LPA
• Digital Marketer - ₹5-15 LPA
• Journalist - ₹4-12 LPA

<strong>Government Jobs (₹4-20 LPA):</strong>
• Bank PO - ₹8-15 LPA
• SSC Jobs - ₹4-10 LPA
• State PSC - ₹5-15 LPA
• UPSC (IAS/IPS) - ₹6-25 LPA
• Defence - ₹6-15 LPA

<strong>Future Growth Sectors:</strong>
• Artificial Intelligence & Machine Learning
• Data Science & Analytics
• Cloud Computing
• Cybersecurity
• Renewable Energy
• Healthcare Technology
• E-commerce & Digital Marketing
• Electric Vehicles

<strong>Highest Demanded Skills 2024:</strong>
1. Python Programming
2. Data Analysis
3. Digital Marketing
4. Cloud Computing
5. AI/ML""",

        "mr": """<h3>💰 पगार आणि भविष्य</h3>

<strong>उच्च पगार:</strong>
• Software Engineer - ₹8-40 LPA
• Data Scientist - ₹8-35 LPA
• Doctor - ₹6-50 LPA
• MBA - ₹15-50 LPA

<strong>सरकारी नोकऱ्या:</strong>
• Bank PO - ₹8-15 LPA
• IAS/IPS - ₹6-25 LPA

<strong>भविष्यातील वाढ:</strong>
• AI/ML, Data Science
• Cloud Computing
• Cybersecurity""",

        "hi": """<h3>Salary & Scope</h3>
<strong>High Salary:</strong> ₹10-50+ LPA (IT, Doctor, MBA)
<strong>Medium:</strong> ₹5-15 LPA (Teacher, CA, Designer)
<strong>Government:</strong> ₹4-20 LPA
<strong>Future:</strong> AI, Data Science, Cloud"""
    },

    # COLLEGES
    "college": {
        "keywords": ["college", "university", "institute", "admission", "fees", "best", "top", "rank"],
        "category": "college",
        "en": """<h3>🎓 Top Colleges in India</h3>

<strong>Engineering (IITs):</strong>
• IIT Bombay - ₹2,09,050/year
• IIT Delhi - ₹2,23,000/year
• IIT Madras - ₹2,20,000/year
• IIT Kharagpur - ₹2,17,000/year

<strong>Medical:</strong>
• AIIMS Delhi - ₹1,628/year
• PGIMER Chandigarh - ₹3,000/year
• CMC Vellore - ₹45,000/year

<strong>Commerce:</strong>
• SRCC Delhi - ₹18,000/year
• St. Xavier's Mumbai - ₹1,16,000/year

<strong>Arts/Science:</strong>
• St. Stephen's College - ₹25,000/year
• Hindu College - ₹15,000/year

<strong>Law:</strong>
• NLSIU Bangalore - ₹2,80,000/year
• NALSAR Hyderabad - ₹2,50,000/year

<strong>Management:</strong>
• IIM Ahmedabad - ₹23,00,000/year
• IIM Bangalore - ₹25,00,000/year
• IIM Calcutta - ₹27,00,000/year

<strong>Admission Tips:</strong>
• Apply early
• Prepare for entrance exams
• Check eligibility criteria
• Consider location and fees""",

        "mr": """<h3>🎓 महाविद्यालये</h3>

<strong>Engineering:</strong>
• IIT Bombay, Delhi, Madras

<strong>Medical:</strong>
• AIIMS Delhi, PGIMER

<strong>Commerce:</strong>
• SRCC, St. Xavier's

<strong>Law:</strong>
• NLSIU, NALSAR

<strong>Management:</strong>
• IIM A, B, C""",

        "hi": """<h3>Top Colleges</h3>
<strong>Engineering:</strong> IITs
<strong>Medical:</strong> AIIMS, PGIMER
<strong>Commerce:</strong> SRCC, Xavier's
<strong>Law:</strong> NLSIU, NALSAR
<strong>Management:</strong> IIMs"""
    },

    # COURSES
    "course": {
        "keywords": ["course", "certificate", "diploma", "degree", "training", "certification", "online", "short term"],
        "category": "course",
        "en": """<h3>📖 Popular Courses After 12th</h3>

<strong>Science Stream (PCM):</strong>
• B.Tech/BE - 4 years
• B.Sc Physics/Chemistry/Maths - 3 years
• B.Arch - 5 years
• BCA - 3 years

<strong>Science Stream (PCB):</strong>
• MBBS - 5.5 years
• BDS - 5 years
• BAMS/BHMS - 5.5 years
• BSc Nursing - 4 years
• Pharmacy - 4 years

<strong>Commerce Stream:</strong>
• B.Com - 3 years
• BBA - 3 years
• CA/CMA/CS - 3-5 years
• Banking - 6 months to 2 years

<strong>Arts Stream:</strong>
• BA - 3 years
• BA LLB - 5 years
• BFA - 4 years
• Journalism - 3 years

<strong>Online Courses (Free/Cheap):</strong>
• Python - Coursera, edX
• Digital Marketing - Google Digital Garage
• Data Science - Kaggle, Udemy
• Web Development - freeCodeCamp

<strong>Short-term Certificates:</strong>
• TEFL (Teaching English) - 4-6 months
• Digital Marketing - 3-6 months
• Graphic Design - 6 months
• Data Analytics - 3-6 months""",

        "mr": """<h3>📖 कोर्सेस</h3>

<strong>Science PCM:</strong>
• B.Tech - 4 वर्ष
• B.Sc - 3 वर्ष
• BCA - 3 वर्ष

<strong>Science PCB:</strong>
• MBBS - 5.5 वर्ष
• BAMS/BHMS - 5.5 वर्ष

<strong>Commerce:</strong>
• B.Com, BBA - 3 वर्ष
• CA - 4-5 वर्ष

<strong>Arts:</strong>
• BA - 3 वर्ष
• BA LLB - 5 वर्ष

<strong>Online:</strong> Python, Digital Marketing""",

        "hi": """<h3>Courses After 12th</h3>
<strong>Science:</strong> B.Tech, MBBS, B.Sc
<strong>Commerce:</strong> B.Com, BBA, CA
<strong>Arts:</strong> BA, BA LLB
<strong>Online:</strong> Python, Digital Marketing"""
    },

    # JOBS & EMPLOYMENT
    "job": {
        "keywords": ["job", "placement", "internship", "hiring", "vacancy", "recruitment", "career", "work"],
        "category": "job",
        "en": """<h3>💼 Job & Career Guidance</h3>

<strong>How to Get a Job:</strong>

<b>1. Build Skills</b>
• Technical skills for your field
• Communication skills
• Problem-solving ability
• Teamwork

<b>2. Create Professional Profile</b>
• LinkedIn profile
• Resume building
• Portfolio (for creative jobs)

<b>3. Apply Strategically</b>
• Company websites
• Job portals (Naukri, Indeed, Monster)
• LinkedIn
• Campus placements

<b>4. Prepare for Interviews</b>
• Research company
• Practice common questions
• Mock interviews
• Dress professionally

<strong>High-Demand Jobs 2024:</strong>
• Software Developer
• Data Analyst
• Digital Marketer
• Project Manager
• Cybersecurity Expert
• Cloud Engineer

<strong>Internship Platforms:</strong>
• Internshala
• LinkedIn
• LetsIntern

<strong>Average Starting Salaries:</strong>
• IT Sector: ₹4-10 LPA
• Finance: ₹5-12 LPA
• Marketing: ₹4-8 LPA
• Core Jobs: ₹3-7 LPA""",

        "mr": """<h3>💼 नोकरी</h3>

<strong>कसे मिळवायचे:</strong>
• कौशल्य विकसित करा
• LinkedIn प्रोफाइल
• रिझ्युमे बनवा
• मॉक इंटरव्यू

<strong>मागणी असलेली नोकर्या:</strong>
• Software Developer
• Data Analyst
• Digital Marketer""",

        "hi": """<h3>Jobs</h3>
<strong>Tips:</strong> Build skills, LinkedIn, Resume
<strong>High Demand:</strong> Developer, Data Analyst
<strong>Platforms:</strong> Naukri, Indeed, Internshala"""
    },

    # SCHOLARSHIPS
    "scholarship": {
        "keywords": ["scholarship", "fellowship", "grant", "financial aid", "free education", "merit"],
        "category": "guidance",
        "en": """<h3>🎁 Scholarships in India</h3>

<strong>Central Government:</strong>
• National Means-cum-Merit Scholarship - ₹12,000/year
• Central Sector Scheme - ₹20,000/year
• Prime Minister's Scholarship - ₹2,50,000/year

<strong>State Governments:</strong>
• Maharashtra: Majhi Vasundhara, Vidyarthi Mahanidhi
• Various state-specific scholarships

<strong>Private/NGO:</strong>
• Tata Trusts Scholarship
• KVPY (Kishore Vaigyanik Protsahan Yojana) - ₹1,00,000/year
• INSPIRE Scholarship - ₹80,000/year

<strong>For Minorities:</strong>
• Pre-Matric Scholarship
• Post-Matric Scholarship
• Merit-cum-Means Scholarship

<strong>How to Apply:</strong>
1. Visit National Scholarship Portal (scholarships.gov.in)
2. Check eligibility
3. Gather documents
4. Apply before deadline

<strong>Tips:</strong>
• Start early
• Keep documents ready
• Apply to multiple scholarships""",

        "mr": """<h3>🎁 शिष्यवृत्त्या</h3>

<strong>केंद्रीय:</strong>
• National Means-cum-Merit - ₹12,000/year

<strong>खाजगी:</strong>
• Tata Trusts, KVPY, INSPIRE

<strong>Apply:</strong> scholarships.gov.in""",

        "hi": """<h3>Scholarships</h3>
<strong>Central:</strong> NMMS, Central Sector
<strong>Portal:</strong> scholarships.gov.in
<strong>Tips:</strong> Apply early, multiple scholarships"""
    },

    # COMPETITIVE EXAMS
    "exams": {
        "keywords": ["exam", "competitive", "entrance", "test", "ssc", "rrb", "bank po", "clat", "gate"],
        "category": "exam",
        "en": """<h3>📝 Competitive Exams in India</h3>

<strong>Banking Exams:</strong>
• SBI PO - Graduate, Age 21-30
• IBPS PO - Graduate, Age 20-30
• SBI Clerk - Graduate, Age 20-35
• IBPS Clerk - Graduate, Age 20-28
• RBI Grade B - Graduate, Age 21-30

<strong>SSC Exams:</strong>
• SSC CGL - Graduate, Age 18-32
• SSC CHSL - 10+2, Age 18-27
• SSC MTS - 10th, Age 18-25
• SSC GD - 10th, Age 18-23

<strong>Railway Exams:</strong>
• RRB NTPC - 10+2, Age 18-33
• RRB Group D - 10th, Age 18-33

<strong>Other Exams:</strong>
• CLAT - Law (5-year integrated)
• GATE - Engineering PG
• CAT - MBA entrance
• XAT - MBA (XLRI)

<strong>Exam Pattern (General):</strong>
• Tier 1: Objective (100-200 questions)
• Tier 2: Mains/Descriptive
• Tier 3: Skill Test/Interview

<strong>Preparation Time:</strong>
• Bank PO: 6-12 months
• SSC: 8-12 months
• Railway: 6-10 months""",

        "mr": """<h3>📝 स्पर्धात्मक परीक्षा</h3>

<strong>Banking:</strong> SBI PO, IBPS PO, Clerk
<strong>SSC:</strong> CGL, CHSL, MTS
<strong>Railway:</strong> NTPC, Group D
<strong>Law:</strong> CLAT
<strong>Management:</strong> CAT, XAT""",

        "hi": """<h3>Competitive Exams</h3>
<strong>Banking:</strong> PO, Clerk
<strong>SSC:</strong> CGL, CHSL
<strong>Railway:</strong> NTPC, Group D
<strong>Other:</strong> CLAT, GATE, CAT"""
    },

    # CAREER AFTER 10TH
    "after10": {
        "keywords": ["after 10th", "10th pass", "class 10", "career after 10"],
        "category": "guidance",
        "en": """<h3>🎓 Career Options After 10th</h3>

<strong>Science Stream (PCB):</strong>
• Medical (NEET) preparation
• Paramedical courses

<strong>Science Stream (PCM):</strong>
• Engineering (IIT-JEE)
• Polytechnic (Diploma)
• Architecture

<strong>Commerce Stream:</strong>
• Commerce with Maths
• Commerce without Maths

<strong>Arts/Humanities:</strong>
• Humanities
• Fine Arts
• Music/Dance

<strong>Vocational Courses:</strong>
• ITI (Industrial Training Institute)
• Diploma in Engineering
• Fashion Designing
• Hotel Management
• Computer Applications

<strong>Government Jobs after 10th:</strong>
• SSC GD
• Army (10+2 entries)
• Police
• Railway Group D

<strong>Skills to Develop:</strong>
• Basic computer skills
• English communication
• Mathematics
• Soft skills""",

        "mr": """<h3>10 वी नंतर</h3>

<strong>Science:</strong> PCM, PCB
<strong>Commerce:</strong>
<strong>Arts:</strong>
<strong>Vocational:</strong> ITI, Polytechnic""",

        "hi": """<h3>After 10th</h3>
<strong>Streams:</strong> Science, Commerce, Arts
<strong>Vocational:</strong> ITI, Diploma
<strong>Jobs:</strong> SSC GD, Army"""
    },

    # CAREER AFTER 12TH
    "after12": {
        "keywords": ["after 12th", "12th pass", "class 12", "career after 12", "what to do after"],
        "category": "guidance",
        "en": """<h3>🎓 Career Options After 12th</h3>

<strong>Science (PCB - Medical):</strong>
• MBBS, BDS, BAMS, BHMS, B.V.Sc
• Nursing, Pharmacy, Physiotherapy
• Paramedical courses

<strong>Science (PCM - Engineering):</strong>
• B.Tech/BE in various branches
• B.Arch, B.Sc
• BCA, B.Tech (Lateral Entry)

<strong>Commerce:</strong>
• B.Com, BBA, BAF
• CA, CS, CMA (Foundation)
• Banking, Finance

<strong>Arts:</strong>
• BA in various subjects
• BA LLB, BFA, BJMC
• Psychology, Sociology

<strong>Other Options:</strong>
• NDA (10+2 entry)
• Hotel Management (IHM)
• Fashion Design (NIFT)
• Animation, Gaming
• Photography

<strong>Online/Distance:</strong>
• BSc in Data Science
• BBA in Digital Marketing

<strong>Diploma Courses:</strong>
• Polytechnic Diplomas
• ITI Trades
• Vocational Training""",

        "mr": """<h3>12 वी नंतर</h3>

<strong>Science PCB:</strong> MBBS, BDS, BAMS
<strong>Science PCM:</strong> B.Tech, B.Arch
<strong>Commerce:</strong> B.Com, BBA, CA
<strong>Arts:</strong> BA, BA LLB, Journalism
<strong>Other:</strong> NDA, Hotel Management""",

        "hi": """<h3>After 12th</h3>
<strong>Science:</strong> MBBS, B.Tech
<strong>Commerce:</strong> B.Com, BBA, CA
<strong>Arts:</strong> BA, Law
<strong>Other:</strong> NDA, Hotel Management"""
    },

    # SKILLS
    "skill": {
        "keywords": ["skill", "skills", "ability", "learn", "training", "improve", "develop"],
        "category": "guidance",
        "en": """<h3>🛠️ Important Skills for Success</h3>

<strong>Technical Skills:</strong>
• Programming (Python, Java, C++)
• Data Analysis (Excel, SQL, Tableau)
• Digital Marketing
• Cloud Computing
• AI/Machine Learning basics

<strong>Soft Skills:</strong>
• Communication (written & verbal)
• Problem Solving
• Critical Thinking
• Time Management
• Teamwork
• Adaptability

<strong>Language Skills:</strong>
• English (very important)
• Hindi
• Regional language

<strong>How to Develop Skills:</strong>

<b>1. Online Courses</b>
• Coursera, edX, Udemy
• freeCodeCamp
• Khan Academy

<b>2. Practice</b>
• Personal projects
• Internships
• Freelancing

<b>3. Certifications</b>
• Google Digital Garage
• Microsoft Learn
• AWS Free Tier

<strong>Top Skills by Industry:</strong>
• IT: Python, Cloud, Cybersecurity
• Finance: Excel, Financial Modeling
• Marketing: SEO, Content, Analytics""",

        "mr": """<h3>🛠️ कौशल्य</h3>

<strong>Technical:</strong>
• Programming
• Data Analysis
• Digital Marketing

<strong>Soft Skills:</strong>
• Communication
• Problem Solving
• Time Management""",

        "hi": """<h3>Skills</h3>
<strong>Technical:</strong> Python, Data Analysis
<strong>Soft:</strong> Communication, Problem Solving
<strong>Learn:</strong> Online courses, Practice"""
    },

    # INTERNSHIP
    "internship": {
        "keywords": ["internship", "intern", "training", "work experience", "summer"],
        "category": "job",
        "en": """<h3>💼 Internship Guide</h3>

<strong>Why Internships Matter:</strong>
• Real work experience
• Industry exposure
• Resume building
• Network building
• Chance of pre-placement

<strong>Where to Find:</strong>
• Internshala
• LinkedIn
• College TPO
• Company websites
• AngelList (startups)

<strong>Types:</strong>
• Summer Internship (2-3 months)
• Winter Internship (1-2 months)
• Virtual/Remote Internship

<strong>How to Apply:</strong>
1. Update your resume
2. Create LinkedIn profile
3. Research companies
4. Apply to multiple places
5. Prepare for interviews

<strong>Stipend (Average):</strong>
• IT/Software: ₹5,000-25,000/month
• Marketing: ₹3,000-15,000/month
• Finance: ₹5,000-20,000/month

<strong>Top Companies for Internships:</strong>
• Google, Microsoft, Amazon
• Startups
• Investment Banks""",

        "mr": """<h3>💼 इंटर्नशिप</h3>

<strong>प्लॅटफॉर्म:</strong>
• Internshala
• LinkedIn

<strong>प्रकार:</b> Summer, Winter, Virtual

<strong>स्टायपेंड:</b> ₹3,000-25,000/महिना""",

        "hi": """<h3>Internship</h3>
<strong>Platforms:</strong> Internshala, LinkedIn
<strong>Stipend:</strong> ₹3,000-25,000/month
<strong>Companies:</strong> Google, Amazon, Startups"""
    },

    # GATE EXAM
    "gate": {
        "keywords": ["gate", "gate exam", "gate result", "gate score", "psu"],
        "category": "exam",
        "en": """<h3>🎯 GATE Exam (Graduate Aptitude Test in Engineering)</h3>

<strong>About GATE:</strong>
• For Engineering PG admissions
• Also for PSU recruitment
• Conducted by IIT (rotates yearly)

<strong>Eligibility:</strong>
• B.Tech/BE graduate (or final year)
• No age limit

<strong>Exam Pattern:</strong>
• 65 questions, 100 marks
• General Aptitude: 10 questions
• Technical: 55 questions
• Duration: 3 hours

<strong>PSU Recruitment through GATE:</strong>
• ONGC, IOCL, BHEL, NTPC
• Salary: ₹8-20 LPA

<strong>Top IITs for PG:</strong>
• IIT Bombay, Delhi, Madras
• IISc Bangalore
• NIT Trichy, Warangal

<strong>Preparation:</strong>
• 8-12 months recommended
• Focus on basics
• Solve previous papers
• Take mock tests""",

        "mr": """<h3>GATE</h3>

<strong>परीक्षा:</strong>
• Engineering PG साठी
• PSU भरती साठी

<strong>पैसा:</b> ₹8-20 LPA""",

        "hi": """<h3>GATE</h3>
<strong>For:</strong> Engineering PG, PSU jobs
<strong>Salary:</strong> ₹8-20 LPA"""
    },

    # CLAT EXAM
    "clat": {
        "keywords": ["clat", "law exam", "llb", "llm", "legal", "lawyer"],
        "category": "exam",
        "en": """<h3>⚖️ CLAT (Common Law Admission Test)</h3>

<strong>About CLAT:</strong>
• For 5-year integrated LLB courses
• Also for LLM programs
• 22 NLUs participate

<strong>Eligibility:</strong>
• 10+2 pass (45% - General, 40% - SC/ST)
• Age: No upper limit

<strong>Exam Pattern:</strong>
• 150 questions, 150 marks
• English, GK, Legal Reasoning, Logical, Quantitative
• Duration: 2 hours

<strong>Top NLUs:</strong>
• NLSIU Bangalore (Top)
• NALSAR Hyderabad
• NUJS Kolkata
• WBNUJS
• NLIU Bhopal

<strong>Career Options:</strong>
• Corporate Lawyer - ₹8-50 LPA
• Judge (after LLB + Judiciary)
• Legal Analyst
• Litigation
• Legal Journalism

<strong>Salary:</strong>
• Freshers: ₹5-12 LPA
• After 5 years: ₹15-40+ LPA""",

        "mr": """<h3>⚖️ CLAT</h3>

<strong>कोर्स:</strong> 5 वर्ष LLB

<strong>Top NLUs:</strong> Bangalore, Hyderabad, Kolkata

<strong>पगार:</b> ₹5-50 LPA""",

        "hi": """<h3>CLAT</h3>
<strong>Course:</strong> 5-year LLB
<strong>Top:</strong> NLSIU, NALSAR, NUJS
<strong>Salary:</strong> ₹5-50 LPA"""
    },

    # DIPLOMA COURSES
    "diploma": {
        "keywords": ["diploma", "polytechnic", "iti", "vocational", "certificate course"],
        "category": "course",
        "en": """<h3>📜 Diploma & Vocational Courses</h3>

<strong>Polytechnic Diplomas (3 years):</strong>
• Civil Engineering
• Mechanical Engineering
• Electrical Engineering
• Computer Science
• Electronics & Communication

<strong>After 10th ITI Courses:</strong>
• Electrician
• Fitter
• Welder
• Carpenter
• Plumber
• Mechanic

<parameter name="short-term Courses (6 months-1 year):</parameter>
• Computer Hardware
• Web Designing
• Tally
• Spoken English
• Beautician
• Tailoring

<strong>Career Opportunities:</strong>
• Junior Engineer - ₹3-8 LPA
• ITI Trades - ₹3-6 LPA
• Skilled Worker - ₹3-10 LPA

<strong>Benefits:</strong>
• Quick job opportunities
• Practical skills
• Less duration than degree""",

        "mr": """<h3>📜 डिप्लोमा</h3>

<strong>Polytechnic:</strong> 3 वर्ष
• Civil, Mechanical, Electrical

<strong>ITI:</strong>
• Electrician, Fitter, Welder

<strong>Short-term:</b> Hardware, Web Designing""",

        "hi": """<h3>Diploma Courses</h3>
<strong>Polytechnic:</strong> 3 years
<strong>ITI:</strong> Various trades
<strong>Short-term:</strong> 6 months - 1 year"""
    },

    # MBA
    "mba": {
        "keywords": ["mba", "master of business", "management", "pgdm", "executive mba"],
        "category": "course",
        "en": """<h3>📈 MBA (Master of Business Administration)</h3>

<strong>About MBA:</strong>
• Duration: 2 years
• Full-time, Part-time, Executive options

<strong>Top IIMs:</strong>
• IIM Ahmedabad (₹25 LPA avg)
• IIM Bangalore
• IIM Calcutta
• IIM Lucknow
• IIM Indore

<strong>Other Top B-Schools:</strong>
• XLRI Jamshedpur
• FMS Delhi
• SP Jain Mumbai
• ISB Hyderabad
• Symbiosis

<strong>Specializations:</strong>
• Finance
• Marketing
• Human Resources (HR)
• Operations
• Business Analytics
• Digital Marketing
• Entrepreneurship

<strong>Entrance Exams:</strong>
• CAT (Common Admission Test)
• XAT (XLRI)
• SNAP (Symbiosis)
• MAT, CMAT

<strong>Eligibility:</strong>
• Graduate in any stream (50%)
• Work experience (not mandatory for most)

<strong>Salary:</strong>
• Top IIMs: ₹20-50 LPA
• Other IIMs: ₹12-25 LPA
• Private B-Schools: ₹8-15 LPA""",

        "mr": """<h3>📈 MBA</h3>

<strong>Top:</b> IIM A, B, C, L
<strong>Duration:</b> 2 वर्ष

<strong>Specializations:</b> Finance, Marketing, HR

<strong>पगार:</b> ₹12-50 LPA""",

        "hi": """<h3>MBA</h3>
<strong>Top:</strong> IIMs, XLRI, FMS
<strong>Duration:</strong> 2 years
<strong>Salary:</strong> ₹12-50 LPA"""
    },

    # TEACHING CAREERS
    "teaching": {
        "keywords": ["teacher", "teaching", "professor", "education", "tutor", "coaching"],
        "category": "career",
        "en": """<h3>👨‍🏫 Teaching & Education Careers</h3>

<strong>School Teaching:</strong>
• TGT (Trained Graduate Teacher) - 10+2 + B.Ed
• PGT (Post Graduate Teacher) - Post Graduate + B.Ed
• Salary: ₹4-12 LPA

<strong>Higher Education:</strong>
• Assistant Professor - ₹8-15 LPA
• Associate Professor - ₹15-25 LPA
• Professor - ₹20-50 LPA

<strong>Entrance Exams:</strong>
• CTET (Central Teacher Eligibility Test)
• State TET
• UGC NET (for Assistant Professor)
• SET (State Eligibility Test)

<strong>Coaching/Private Tutor:</strong>
• Average: ₹500-2000/hour
• Online tutoring: ₹300-1000/hour

<strong>Online Teaching:</strong>
• Byju's, Unacademy, Vedantu
• Salary: ₹6-20 LPA""",

        "mr": """<h3>👨‍🏫 शिक्षण</h3>

<strong>School:</b> TGT, PGT - ₹4-12 LPA
<strong>College:</b> Professor - ₹8-50 LPA
<strong>Coaching:</b> ₹500-2000/hour""",

        "hi": """<h3>Teaching Careers</h3>
<strong>School:</strong> TGT, PGT
<strong>College:</strong> Professor
<strong>Salary:</strong> ₹4-50 LPA"""
    },

    # IT JOBS
    "it": {
        "keywords": ["it job", "software", "developer", "programmer", "coding", "tech job", "google", "amazon"],
        "category": "career",
        "en": """<h3>💻 IT & Software Careers</h3>

<strong>Top IT Companies:</strong>
• Google, Microsoft, Amazon, Meta
• TCS, Infosys, Wipro, HCL
• Startup ecosystem

<strong>Job Roles:</strong>
• Software Developer/Engineer
• Full Stack Developer
• Data Scientist
• Machine Learning Engineer
• DevOps Engineer
• Cloud Engineer
• Cybersecurity Expert
• QA Engineer

<strong>Required Skills:</strong>
• Programming: Python, Java, JavaScript, C++
• Web: HTML, CSS, React, Angular
• Database: SQL, MongoDB
• Tools: Git, Docker
• Cloud: AWS, Azure, GCP

<strong>Salary (India):</strong>
• Fresher: ₹4-10 LPA
• 2-3 years: ₹8-18 LPA
• 5+ years: ₹15-40+ LPA
• Top companies: ₹20-80+ LPA

<strong>Preparation:</strong>
• Data Structures & Algorithms
• System Design
• Problem Solving
• Build projects""",

        "mr": """<h3>💻 IT</h3>

<strong>कंपन्या:</b> Google, Microsoft, TCS

<strong>नोकर्या:</b> Developer, Data Scientist

<strong>कौशल्य:</b> Python, Java, JavaScript

<strong>पगार:</b> ₹4-80 LPA""",

        "hi": """<h3>IT Careers</h3>
<strong>Companies:</strong> Google, Microsoft, Amazon
<strong>Roles:</strong> Developer, Data Scientist
<strong>Skills:</strong> Python, Java, JavaScript
<strong>Salary:</strong> ₹4-80+ LPA"""
    }
}
