import os, re, secrets
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, request, jsonify, g
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'learnai-local-demo-change-me')
db_url = os.getenv('DATABASE_URL', f"sqlite:///{os.path.join(BASE_DIR, 'learnai.db')}")
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
CORS(app, resources={r"/api/*": {"origins": ["http://localhost:5173", "http://127.0.0.1:5173"]}})
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    token = db.Column(db.String(96), unique=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    profile = db.relationship('StudentProfile', backref='user', uselist=False, cascade='all, delete-orphan')

class StudentProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    degree = db.Column(db.String(100), default='')
    specialization = db.Column(db.String(150), default='')
    year = db.Column(db.String(30), default='')
    weak_topics = db.Column(db.Text, default='')
    interests = db.Column(db.Text, default='')
    career_goal = db.Column(db.String(150), default='')
    onboarding_complete = db.Column(db.Boolean, default=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class QuizAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    quiz_key = db.Column(db.String(100), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    total = db.Column(db.Integer, nullable=False)
    answers_json = db.Column(db.Text, default='{}')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

COURSES = [
 {'id':'eng-python','title':'Python Fundamentals','category':'Engineering / Computing','degree_tags':['Engineering','BSc','Other undergraduate degree'],'topics':'python programming coding functions problem solving automation','level':'Beginner','duration':'3 weeks','description':'Build programming foundations, variables, decisions, loops, functions and small programs.','skills':['Programming','Problem solving'],'resources':[{'title':'Python official tutorial','url':'https://docs.python.org/3/tutorial/','type':'Guide'},{'title':'freeCodeCamp Python course search','url':'https://www.youtube.com/results?search_query=freecodecamp+python+beginner','type':'Video'}], 'roadmap':['Variables and data types','Conditions and loops','Functions and collections','Files and small projects']},
 {'id':'eng-dsa','title':'Data Structures & Algorithms','category':'Engineering / Computing','degree_tags':['Engineering','BSc','Other undergraduate degree'],'topics':'data structures algorithms arrays strings searching sorting complexity problem solving','level':'Beginner to Intermediate','duration':'4 weeks','description':'Practice arrays, strings, searching, sorting and basic time complexity.','skills':['DSA','Problem solving'],'resources':[{'title':'VisuAlgo','url':'https://visualgo.net/en','type':'Interactive'},{'title':'DSA visualizations video search','url':'https://www.youtube.com/results?search_query=data+structures+algorithms+visualization','type':'Video'}], 'roadmap':['Arrays and strings','Searching and sorting','Stacks and queues','Complexity and practice problems']},
 {'id':'eng-ml','title':'Machine Learning Foundations','category':'Engineering / AI & Data','degree_tags':['Engineering','BSc','Other undergraduate degree'],'topics':'machine learning artificial intelligence data science python statistics regression classification clustering model evaluation','level':'Intermediate','duration':'5 weeks','description':'Understand datasets, features, regression, classification, clustering and evaluation.','skills':['Machine Learning','Data analysis'],'resources':[{'title':'Google Machine Learning Crash Course','url':'https://developers.google.com/machine-learning/crash-course','type':'Course'},{'title':'scikit-learn tutorials','url':'https://scikit-learn.org/stable/tutorial/index.html','type':'Guide'}], 'roadmap':['Python and data handling','Statistics basics','Regression and classification','Evaluation and mini project']},
 {'id':'eng-web','title':'Web Development Basics','category':'Engineering / Computing','degree_tags':['Engineering','BSc','BCom','BA','Business / Management','Other undergraduate degree'],'topics':'html css javascript web development frontend website design','level':'Beginner','duration':'4 weeks','description':'Create accessible web pages using HTML, CSS and JavaScript.','skills':['HTML','CSS','JavaScript'],'resources':[{'title':'MDN Learn Web Development','url':'https://developer.mozilla.org/en-US/docs/Learn','type':'Guide'},{'title':'HTML CSS beginner videos','url':'https://www.youtube.com/results?search_query=html+css+beginner+course','type':'Video'}], 'roadmap':['HTML structure','CSS layout and responsive design','JavaScript interactions','Build and publish a small site']},
 {'id':'pharm-found','title':'Pharmaceutics Foundations','category':'Pharmacy','degree_tags':['Pharmacy'],'topics':'pharmacy pharmaceutics dosage forms formulation tablets capsules drug delivery pharmaceutical calculations','level':'Beginner','duration':'4 weeks','description':'Starter review of dosage forms, formulation concepts and pharmaceutical calculations.','skills':['Pharmaceutics','Calculation'],'resources':[{'title':'NCBI Bookshelf biomedical resources','url':'https://www.ncbi.nlm.nih.gov/books/','type':'Reference'},{'title':'Pharmaceutics lectures search','url':'https://www.youtube.com/results?search_query=pharmaceutics+basics+lecture','type':'Video'}], 'roadmap':['Pharmacy terminology','Dosage forms','Formulation principles','Practice calculations']},
 {'id':'pharm-pharmaco','title':'Pharmacology Foundations','category':'Pharmacy','degree_tags':['Pharmacy'],'topics':'pharmacology drugs mechanisms action receptors pharmacokinetics pharmacodynamics safety','level':'Beginner to Intermediate','duration':'5 weeks','description':'Learn introductory drug action, pharmacokinetics, pharmacodynamics and safety concepts.','skills':['Pharmacology','Scientific reading'],'resources':[{'title':'NCBI Bookshelf pharmacology search','url':'https://www.ncbi.nlm.nih.gov/books/?term=pharmacology','type':'Reference'},{'title':'Pharmacology basics video search','url':'https://www.youtube.com/results?search_query=pharmacology+basics+for+students','type':'Video'}], 'roadmap':['Drug terminology','Pharmacokinetics','Pharmacodynamics','Safety and revision']},
 {'id':'med-anatomy','title':'Human Anatomy & Physiology','category':'Medical / Health Sciences','degree_tags':['Medical / Health Sciences'],'topics':'medical anatomy physiology human body organs systems cells tissues physiology','level':'Beginner','duration':'6 weeks','description':'Review major body systems, anatomical terms and basic physiological functions.','skills':['Anatomy','Scientific reasoning'],'resources':[{'title':'OpenStax Anatomy and Physiology','url':'https://openstax.org/details/books/anatomy-and-physiology-2e','type':'Textbook'},{'title':'Anatomy physiology videos','url':'https://www.youtube.com/results?search_query=anatomy+physiology+basics+students','type':'Video'}], 'roadmap':['Anatomical terms','Cells and tissues','Organ systems','System-wise revision']},
 {'id':'med-biochem','title':'Biochemistry Basics','category':'Medical / Health Sciences','degree_tags':['Medical / Health Sciences','BSc'],'topics':'biochemistry proteins carbohydrates lipids enzymes metabolism cells biology','level':'Beginner','duration':'4 weeks','description':'Understand biomolecules, enzymes and introductory metabolism.','skills':['Biochemistry','Scientific concepts'],'resources':[{'title':'OpenStax Biology 2e','url':'https://openstax.org/details/books/biology-2e','type':'Textbook'},{'title':'Biochemistry basics video search','url':'https://www.youtube.com/results?search_query=biochemistry+basics+for+students','type':'Video'}], 'roadmap':['Biomolecules','Enzymes','Carbohydrate and lipid metabolism','Revision questions']},
 {'id':'biz-accounting','title':'Accounting Fundamentals','category':'Business / Commerce','degree_tags':['Business / Management','BCom','Other undergraduate degree'],'topics':'accounting commerce financial statements debit credit balance sheet profit loss business finance','level':'Beginner','duration':'4 weeks','description':'Practice basic accounting terms, journal entries and financial statements.','skills':['Accounting','Numeracy'],'resources':[{'title':'OpenStax Principles of Accounting','url':'https://openstax.org/subjects/business','type':'Textbook'},{'title':'Accounting basics video search','url':'https://www.youtube.com/results?search_query=accounting+basics+for+beginners','type':'Video'}], 'roadmap':['Accounting equation','Debit and credit','Journal and ledger','Financial statements']},
 {'id':'biz-marketing','title':'Marketing & Business Communication','category':'Business / Management','degree_tags':['Business / Management','BBA','BA','BCom','Other undergraduate degree'],'topics':'marketing management communication consumer behavior branding market research business','level':'Beginner','duration':'3 weeks','description':'Learn core marketing concepts, audience research and professional communication.','skills':['Marketing','Communication'],'resources':[{'title':'OpenStax Principles of Marketing','url':'https://openstax.org/subjects/business','type':'Textbook'},{'title':'Marketing fundamentals video search','url':'https://www.youtube.com/results?search_query=marketing+fundamentals+course','type':'Video'}], 'roadmap':['Marketing basics','Customer and market research','Branding and promotion','Communication practice']},
 {'id':'arts-writing','title':'Academic Writing & Critical Thinking','category':'BA / Humanities','degree_tags':['BA','Other undergraduate degree'],'topics':'arts humanities academic writing reading critical thinking research essay communication','level':'Beginner','duration':'3 weeks','description':'Improve structured writing, evidence use, reading and argument evaluation.','skills':['Writing','Critical thinking'],'resources':[{'title':'Purdue Online Writing Lab','url':'https://owl.purdue.edu/','type':'Guide'},{'title':'Critical thinking videos','url':'https://www.youtube.com/results?search_query=critical+thinking+for+students','type':'Video'}], 'roadmap':['Reading and notes','Build an argument','Use evidence and citations','Write and revise an essay']},
 {'id':'sci-research','title':'Scientific Method & Data Skills','category':'BSc / Science','degree_tags':['BSc','Medical / Health Sciences','Pharmacy','Other undergraduate degree'],'topics':'science research scientific method experiments data interpretation graphs biology chemistry physics statistics','level':'Beginner','duration':'4 weeks','description':'Learn variables, fair tests, interpreting graphs and basic research literacy.','skills':['Research','Data interpretation'],'resources':[{'title':'OpenStax free textbooks','url':'https://openstax.org/subjects/science','type':'Textbook'},{'title':'Scientific method video search','url':'https://www.youtube.com/results?search_query=scientific+method+students','type':'Video'}], 'roadmap':['Question and hypothesis','Variables and method','Tables and graphs','Interpret results']},
 {'id':'aptitude','title':'Placement Aptitude & Reasoning','category':'All undergraduate degrees','degree_tags':['Engineering','Pharmacy','Medical / Health Sciences','Business / Management','BBA','BA','BSc','BCom','Other undergraduate degree'],'topics':'aptitude percentages ratio proportion profit loss time work speed distance number series logical reasoning placement quantitative verbal interview','level':'Beginner','duration':'Ongoing practice','description':'Build placement-ready quantitative aptitude, logical reasoning and verbal skills.','skills':['Quantitative aptitude','Reasoning','Verbal ability'],'resources':[{'title':'IndiaBix aptitude practice','url':'https://www.indiabix.com/aptitude/questions-and-answers/','type':'Practice'},{'title':'Khan Academy arithmetic and algebra','url':'https://www.khanacademy.org/math','type':'Course'}], 'roadmap':['Percentages and ratios','Profit, loss and averages','Time and work, speed and distance','Number series and reasoning','Timed mixed practice']},
]

QUIZZES = {
 'eng-python': [
  ('Which keyword defines a function in Python?',['func','def','function','make'],'def','The def keyword starts a function definition.'),
  ('Which type stores True or False?',['str','int','bool','list'],'bool','bool represents Boolean values.'),
  ('What does len([4, 7, 9]) return?',['2','3','4','9'],'3','There are three elements in the list.'),
  ('Which symbol starts a comment in Python?',['//','#','<!--','**'],'#','A single-line Python comment begins with #.'),
  ('What is 3 ** 2 in Python?',['5','6','9','8'],'9','The ** operator means exponentiation.'),
  ('Which collection is ordered and changeable?',['tuple','list','set','int'],'list','Lists are ordered and mutable.'),
  ('Which loop iterates over a sequence?',['repeat','foreach','for','loop'],'for','A for loop iterates through items in a sequence.'),
  ('What does input() return by default?',['integer','string','float','Boolean'],'string','input() returns text; convert it when needed.'),
  ('Which index accesses the first list element?',['1','-1','0','first'],'0','Python sequence indexing starts at zero.'),
  ('What is the result of 10 // 3?',['3.33','3','1','4'],'3','// performs floor division.'),
 ],
 'aptitude': [
  ('What is 20% of 150?',['15','20','30','35'],'30','20% = 0.2; 0.2 × 150 = 30.'),
  ('A ratio is 2:3 and total is 25. What is the smaller part?',['5','10','12','15'],'10','Total parts = 5; each part = 25/5 = 5; smaller part = 2×5.'),
  ('An item costs ₹400 and sells for ₹460. Profit percentage?',['10%','12%','15%','20%'],'15%','Profit = 60; profit % = 60/400 × 100 = 15%.'),
  ('A can finish a job in 6 days. What fraction is done in one day?',['1/3','1/6','1/12','6'],'1/6','One-day work is the reciprocal of 6 days.'),
  ('Find the next number: 2, 4, 8, 16, __',['18','24','30','32'],'32','Each number is multiplied by 2.'),
  ('Average of 4, 6 and 8?',['5','6','7','8'],'6','(4 + 6 + 8) / 3 = 6.'),
  ('A car travels 120 km in 3 hours. Average speed?',['30 km/h','40 km/h','60 km/h','90 km/h'],'40 km/h','Speed = distance / time = 120/3.'),
  ('If 5 pens cost ₹50, what do 8 pens cost at the same rate?',['₹60','₹70','₹80','₹100'],'₹80','Each pen costs ₹10, so 8 cost ₹80.'),
  ('Choose the odd one out.',['2','4','8','9'],'9','2, 4 and 8 are powers of 2; 9 is not.'),
  ('If today is Monday, what day will it be after 10 days?',['Wednesday','Thursday','Friday','Saturday'],'Thursday','10 days later is 3 days after Monday.'),
  ('A 25% discount on ₹800 is?',['₹100','₹150','₹200','₹250'],'₹200','0.25 × 800 = 200.'),
  ('Complete: 3, 6, 11, 18, 27, __',['34','36','38','40'],'38','Differences are 3, 5, 7, 9; next difference is 11.'),
  ('If x + 7 = 19, x = ?',['10','11','12','13'],'12','Subtract 7 from both sides.'),
  ('A person buys for ₹250 and sells for ₹200. Loss percentage?',['10%','15%','20%','25%'],'20%','Loss = 50; 50/250 × 100 = 20%.'),
  ('Which is the largest fraction?',['1/2','2/3','3/5','5/8'],'2/3','Compare decimals: .5, .667, .6, .625.'),
  ('If 12 workers finish in 5 days, ideal time for 6 workers?',['2.5 days','5 days','10 days','12 days'],'10 days','Half as many workers take twice the time.'),
  ('What is 15% of 200 plus 10?',['30','35','40','45'],'40','15% of 200 is 30; 30 + 10 = 40.'),
  ('Book is to reading as fork is to __.',['writing','eating','walking','drawing'],'eating','A fork is commonly used for eating.'),
  ('Which number is prime?',['21','27','29','33'],'29','29 has no divisors other than 1 and itself.'),
  ('If 3 notebooks cost ₹ ninety, cost of 1 notebook?',['₹20','₹25','₹30','₹35'],'₹30','90 / 3 = 30.'),
 ]
}

def default_profile(user_id):
    p=StudentProfile.query.filter_by(user_id=user_id).first()
    if not p:
        p=StudentProfile(user_id=user_id); db.session.add(p); db.session.commit()
    return p

def profile_dict(p):
    return {'degree':p.degree or '', 'specialization':p.specialization or '', 'year':p.year or '', 'weakTopics':[x for x in (p.weak_topics or '').split('|') if x], 'interests':[x for x in (p.interests or '').split('|') if x], 'careerGoal':p.career_goal or '', 'onboardingComplete':bool(p.onboarding_complete)}

def user_dict(u):
    return {'id':u.id,'name':u.name,'email':u.email,'profile':profile_dict(default_profile(u.id))}

def auth_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        header=request.headers.get('Authorization','')
        token=header[7:] if header.startswith('Bearer ') else ''
        user=User.query.filter_by(token=token).first() if token else None
        if not user: return jsonify({'error':'Please log in again.'}),401
        g.current_user=user
        return fn(*args, **kwargs)
    return wrapper

def course_public(c):
    return {k:c[k] for k in ['id','title','category','degree_tags','topics','level','duration','description','skills','resources','roadmap']}

def recommendation_score(course, profile):
    text=' '.join([profile.degree,profile.specialization,profile.career_goal,' '.join(profile.interests.split('|')),' '.join(profile.weak_topics.split('|'))])
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        docs=[text or 'undergraduate learning']+[c['title']+' '+c['category']+' '+c['topics']+' '+c['description']+' '+' '.join(c['skills']) for c in COURSES]
        matrix=TfidfVectorizer(stop_words='english').fit_transform(docs)
        scores=cosine_similarity(matrix[0:1],matrix[1:]).flatten()
        return float(scores[COURSES.index(course)])
    except Exception:
        words=set(re.findall(r'[a-z0-9]+',text.lower()))
        target=set(re.findall(r'[a-z0-9]+',(course['title']+' '+course['category']+' '+course['topics']+' '+course['description']).lower()))
        return len(words & target)/max(1,len(words | target))

@app.get('/api/health')
def health(): return jsonify({'status':'ok','service':'LearnAI API'})

@app.post('/api/auth/register')
def register():
    data=request.get_json(silent=True) or {}
    name=(data.get('name') or '').strip(); email=(data.get('email') or '').strip().lower(); password=data.get('password') or ''
    if len(name)<2: return jsonify({'error':'Enter your full name (at least 2 characters).'}),400
    if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$',email): return jsonify({'error':'Enter a valid email address.'}),400
    if len(password)<6: return jsonify({'error':'Password must contain at least 6 characters.'}),400
    if User.query.filter_by(email=email).first(): return jsonify({'error':'An account with this email already exists. Please log in.'}),409
    u=User(name=name,email=email,password_hash=generate_password_hash(password),token=secrets.token_urlsafe(40)); db.session.add(u); db.session.flush(); db.session.add(StudentProfile(user_id=u.id)); db.session.commit()
    return jsonify({'token':u.token,'user':user_dict(u)}),201

@app.post('/api/auth/login')
def login():
    data=request.get_json(silent=True) or {}; email=(data.get('email') or '').strip().lower(); password=data.get('password') or ''
    u=User.query.filter_by(email=email).first()
    if not u or not check_password_hash(u.password_hash,password): return jsonify({'error':'Email or password is incorrect.'}),401
    u.token=secrets.token_urlsafe(40); db.session.commit()
    return jsonify({'token':u.token,'user':user_dict(u)})

@app.post('/api/auth/logout')
@auth_required
def logout():
    g.current_user.token=None; db.session.commit(); return jsonify({'message':'Logged out.'})

@app.get('/api/me')
@auth_required
def me(): return jsonify({'user':user_dict(g.current_user)})

@app.put('/api/profile')
@auth_required
def update_profile():
    data=request.get_json(silent=True) or {}; p=default_profile(g.current_user.id)
    for key,field in [('degree','degree'),('specialization','specialization'),('year','year'),('careerGoal','career_goal')]:
        if key in data: setattr(p,field,str(data.get(key) or '').strip()[:150])
    for key,field in [('weakTopics','weak_topics'),('interests','interests')]:
        if key in data:
            val=data.get(key) or []
            if isinstance(val,str): val=[x.strip() for x in val.split(',') if x.strip()]
            setattr(p,field,'|'.join(str(x).strip()[:100] for x in val if str(x).strip())[:2000])
    if 'onboardingComplete' in data: p.onboarding_complete=bool(data['onboardingComplete'])
    elif p.degree and p.year and p.career_goal: p.onboarding_complete=True
    db.session.commit(); return jsonify({'user':user_dict(g.current_user)})

@app.get('/api/courses')
@auth_required
def courses():
    p=default_profile(g.current_user.id); rows=[]
    for c in COURSES:
        s=recommendation_score(c,p)
        if p.degree and p.degree in c['degree_tags']: s += .20
        rows.append((s,c))
    rows.sort(key=lambda x:x[0],reverse=True)
    return jsonify({'courses':[dict(course_public(c),matchScore=round(min(score,1)*100)) for score,c in rows]})

@app.get('/api/courses/<course_id>')
@auth_required
def course_detail(course_id):
    c=next((x for x in COURSES if x['id']==course_id),None)
    if not c: return jsonify({'error':'Course not found.'}),404
    return jsonify({'course':course_public(c),'quizKey':course_id,'quiz':quiz_public(course_id)})

def quiz_questions(key):
    if key=='aptitude': raw=QUIZZES['aptitude']
    elif key in QUIZZES: raw=QUIZZES[key]
    else:
        # Reuse aptitude starter questions for other course tracks, with a distinct quiz key.
        raw=QUIZZES['aptitude'][:10]
    return [{'id':i+1,'question':q,'options':opts,'answer':ans,'explanation':exp} for i,(q,opts,ans,exp) in enumerate(raw)]

def quiz_public(key):
    return [{'id':q['id'],'question':q['question'],'options':q['options']} for q in quiz_questions(key)]

@app.get('/api/quizzes/<quiz_key>')
@auth_required
def get_quiz(quiz_key):
    key=quiz_key if quiz_key in QUIZZES or any(c['id']==quiz_key for c in COURSES) else None
    if not key: return jsonify({'error':'Quiz not found.'}),404
    return jsonify({'quizKey':key,'title':'Aptitude Practice' if key=='aptitude' else 'Course Assessment','questions':quiz_public(key)})

@app.post('/api/quizzes/<quiz_key>/submit')
@auth_required
def submit_quiz(quiz_key):
    data=request.get_json(silent=True) or {}; answers=data.get('answers') or {}
    if quiz_key not in QUIZZES and not any(c['id']==quiz_key for c in COURSES): return jsonify({'error':'Quiz not found.'}),404
    questions=quiz_questions(quiz_key); correct=0; results=[]
    for q in questions:
        selected=answers.get(str(q['id']))
        is_correct=selected==q['answer']
        correct+=int(is_correct)
        results.append({'id':q['id'],'correct':is_correct,'correctAnswer':q['answer'],'explanation':q['explanation']})
    attempt=QuizAttempt(user_id=g.current_user.id,quiz_key=quiz_key,score=correct,total=len(questions),answers_json=json.dumps(answers)); db.session.add(attempt); db.session.commit()
    return jsonify({'score':correct,'total':len(questions),'percentage':round(correct/len(questions)*100) if questions else 0,'results':results})

@app.get('/api/progress')
@auth_required
def progress():
    attempts=QuizAttempt.query.filter_by(user_id=g.current_user.id).order_by(QuizAttempt.created_at.desc()).limit(50).all()
    total=sum(a.total for a in attempts); score=sum(a.score for a in attempts)
    return jsonify({'attempts':[{'id':a.id,'quizKey':a.quiz_key,'score':a.score,'total':a.total,'percentage':round(a.score/a.total*100) if a.total else 0,'createdAt':a.created_at.isoformat()+'Z'} for a in attempts], 'quizzesCompleted':len(attempts),'averageScore':round(score/total*100) if total else 0,'questionsAnswered':total})

@app.get('/api/roadmap')
@auth_required
def roadmap():
    p=default_profile(g.current_user.id)
    recs=[]
    for c in COURSES:
        if (p.degree and p.degree in c['degree_tags']) or c['id']=='aptitude': recs.append(c)
    if not recs: recs=[c for c in COURSES if c['id'] in ('eng-python','aptitude','sci-research')]
    # Order weak-topic matches first, then aptitude and the other degree-related tracks.
    weak=(p.weak_topics or '').lower()
    recs.sort(key=lambda c:(0 if any(w.strip().lower() in (c['topics']+' '+c['title']).lower() for w in weak.split('|') if w.strip()) else 1, 0 if c['id']=='aptitude' else 1))
    steps=[]
    for c in recs:
        for i,item in enumerate(c['roadmap']): steps.append({'courseId':c['id'],'courseTitle':c['title'],'step':item,'order':len(steps)+1,'level':'Start' if i==0 else ('Practice' if i==len(c['roadmap'])-1 else 'Build')})
    return jsonify({'steps':steps,'note':'Suggested starter roadmap based on your profile. Follow your institution syllabus for course-specific requirements.'})

@app.get('/api/resources')
@auth_required
def resources():
    p=default_profile(g.current_user.id); selected=[]
    for c in COURSES:
        if (p.degree and p.degree in c['degree_tags']) or c['id']=='aptitude':
            for r in c['resources']: selected.append(dict(r,courseTitle=c['title'],courseId=c['id']))
    return jsonify({'resources':selected})

@app.get('/api/careers')
@auth_required
def careers():
    p=default_profile(g.current_user.id); goal=p.career_goal or 'Explore career options'
    suggestions={
      'AI / ML Engineer':['Python programming','Statistics and linear algebra','Machine learning fundamentals','Model evaluation and responsible AI','Build 2–3 explainable projects'],
      'Software Developer':['One programming language','Data structures and algorithms','Git and debugging','Databases and APIs','Build and document projects'],
      'Full Stack Developer':['HTML, CSS and JavaScript','React fundamentals','Backend APIs','SQL and authentication','Deploy a full-stack project'],
      'Data Scientist':['Python and SQL','Statistics and data cleaning','Data visualization','Machine learning foundations','Communicate findings in projects'],
      'Pharmacy / Healthcare':['Core degree subjects and lab practice','Scientific reading and documentation','Relevant safety and ethics standards','Communication and aptitude','Explore approved role requirements'],
      'Business / Management':['Accounting and business fundamentals','Excel and data interpretation','Communication and presentations','Marketing/finance specialization','Internship and case-study practice'],
      'Research / Academia':['Strong subject foundations','Research methods','Academic writing','Data interpretation','Seek supervised projects']}
    match=next((v for k,v in suggestions.items() if k.lower() in goal.lower()),None)
    if not match:
        if 'pharm' in (p.degree+' '+goal).lower() or 'medical' in (p.degree+' '+goal).lower(): match=suggestions['Pharmacy / Healthcare']
        elif any(x in (p.degree+' '+goal).lower() for x in ['business','bcom','bba','management']): match=suggestions['Business / Management']
        elif p.degree=='BA': match=suggestions['Research / Academia']
        else: match=suggestions['Software Developer']
    return jsonify({'goal':goal,'suggestions':match,'disclaimer':'These are learning directions to explore, not a prediction or guarantee of employment.'})

@app.post('/api/assistant')
@auth_required
def assistant():
    data=request.get_json(silent=True) or {}; q=(data.get('question') or '').strip()
    if not q: return jsonify({'error':'Type a question first.'}),400
    p=default_profile(g.current_user.id); lower=q.lower()
    if any(x in lower for x in ['aptitude','percentage','reasoning','placement']): answer='Start with percentages and ratios, then profit and loss, averages, time and work, speed and distance, number series, and logical reasoning. Practice a small timed set daily and review every wrong answer.'
    elif any(x in lower for x in ['weak','improve','study plan','roadmap']): answer='Use your roadmap in prerequisite order. Study one small concept, make short notes, solve 5–10 questions, and review mistakes. Update your weak topics in Profile so recommendations can adapt.'
    elif any(x in lower for x in ['course','recommend']): answer=f"Your selected degree is {p.degree or 'not set yet'} and your career goal is {p.career_goal or 'not set yet'}. Open Courses to see matches, and complete your profile to improve recommendations."
    else: answer='Try this learning cycle: (1) read one short concept, (2) write a 3–5 line summary, (3) solve practice questions without looking at the answer, (4) review mistakes, and (5) build a small example. Tell me the exact subject or topic for more specific guidance.'
    return jsonify({'answer':answer})

with app.app_context():
    db.create_all()

if __name__=='__main__':
    app.run(debug=True, port=int(os.getenv('PORT','5000')))
