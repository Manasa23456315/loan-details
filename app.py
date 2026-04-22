from flask import Flask, render_template, request, redirect, url_for, session, flash
from database import get_db_connection
from werkzeug.utils import secure_filename 
import os 
import datetime
import secrets

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

LOAN_DATA = {
    'education': {
        'name': 'Education Loan',
        'interest': '7.5',
        'max_amount': '50',
        'tenure': '180',
        'description': 'Empower your future with our education loans. We provide comprehensive financial support for higher studies in India and abroad, covering tuition fees, accommodation, and travel.',
        'image': 'images/education.png',
        'form': 'education_form'
    },
    'personal': {
        'name': 'Personal Loan',
        'interest': '10.5',
        'max_amount': '25',
        'tenure': '60',
        'description': 'Get instant funds for all your personal needs. From medical emergencies to dream vacations, our personal loans offer quick processing and competitive interest rates with zero collateral.',
        'image': 'images/personal.png',
        'form': 'personal_form'
    },
    'home': {
        'name': 'Home Loan',
        'interest': '8.2',
        'max_amount': '500',
        'tenure': '360',
        'description': 'Own your dream sanctuary today. Our home loans offer competitive interest rates, flexible tenures, and an easy application process for purchasing, constructing, or renovating your home.',
        'image': 'images/home.png',
        'form': 'home_form'
    },
    'business': {
        'name': 'Business Loan',
        'interest': '12.0',
        'max_amount': '100',
        'tenure': '84',
        'description': 'Fuel your business ambitions. Whether it is expanding your operations or managing working capital, our business loans provide the financial boost your enterprise needs.',
        'image': 'images/hero.png',
        'form': 'business_form'
    },
    'consumer': {
        'name': 'Consumer Durable Loan',
        'interest': '11.0',
        'max_amount': '5',
        'tenure': '24',
        'description': 'Upgrade your lifestyle instantly. Finance your electronics, luxury gadgets, and household appliances with our easy No-Cost EMI options and instant approvals.',
        'image': 'images/hero.png',
        'form': 'consumer'
    },
    'gold': {
        'name': 'Gold Loan',
        'interest': '9.0',
        'max_amount': '20',
        'tenure': '12',
        'description': 'Unlock the potential of your gold ornaments. Get instant cash with the lowest interest rates and highest per-gram value. Your gold is safe and insured in our lockers.',
        'image': 'images/hero.png',
        'form': 'gold_form'
    },
    'credit': {
        'name': 'Credit Card Loan',
        'interest': '15.0',
        'max_amount': '10',
        'tenure': '36',
        'description': 'Enjoy flexible spending power. Our credit card loans offer instant credit limits, exclusive rewards, and a seamless shopping experience for all your global transactions.',
        'image': 'images/hero.png',
        'form': 'credit_form'
    },
    'vehicle': {
        'name': 'Vehicle Loan',
        'interest': '9.5',
        'max_amount': '40',
        'tenure': '84',
        'description': 'Drive your favorite vehicle home today. We offer attractive interest rates on two-wheelers and four-wheelers with up to 100% on-road financing options.',
        'image': 'images/hero.png',
        'form': 'vehicle_form'
    },
    'agriculture': {
        'name': 'Agriculture Loan',
        'interest': '6.5',
        'max_amount': '15',
        'tenure': '36',
        'description': 'Support for our farmers and the backbone of our economy. Get specialized credit for seeds, fertilizers, machinery, and seasonal farm requirements at priority rates.',
        'image': 'images/hero.png',
        'form': 'agriculture_form'
    },
    'mortgage': {
        'name': 'Mortgage Loan',
        'interest': '10.0',
        'max_amount': '300',
        'tenure': '180',
        'description': 'Leverage your property to meet large financial goals. Get the highest loan-to-value ratio for your residential or commercial property with a hassle-free mortgage.',
        'image': 'images/hero.png',
        'form': 'mortgage_form'
    }
}

# 👇 ADD THIS BLOCK HERE (TOP, BEFORE app = Flask)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.makedirs(os.path.join(BASE_DIR, "uploads/identity"), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "uploads/income"), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "uploads/loan_docs"), exist_ok=True)

# Flask app
app = Flask(__name__,template_folder='templates')
app.secret_key = secrets.token_hex(16)


# ---------------- Finance Dashboard (Main) ----------------
@app.route('/')
def dashboard_view():
    if 'user_id' not in session:
        return render_template('landing.html')
        
    conn = get_db_connection()
    applications = conn.execute("SELECT * FROM loan_applications ORDER BY id DESC").fetchall()
    
    total_amount = sum([r['amount'] for r in applications])
    avg_amount = total_amount / len(applications) if applications else 0
    total_approved_amt = sum([r['amount'] for r in applications if r['status'] == 'Approved'])
    total_approved_count = len([r for r in applications if r['status'] == 'Approved'])
    total_rejected_amt = sum([r['amount'] for r in applications if r['status'] == 'Rejected'])
    total_rejected_count = len([r for r in applications if r['status'] == 'Rejected'])
    
    # Calculate real monthly trends for all applications
    trends = conn.execute("SELECT strftime('%Y-%m', created_at) as month, SUM(amount) as amt FROM loan_applications GROUP BY month ORDER BY month DESC LIMIT 12").fetchall()
    month_map = {'01':'Jan','02':'Feb','03':'Mar','04':'Apr','05':'May','06':'Jun','07':'Jul','08':'Aug','09':'Sep','10':'Oct','11':'Nov','12':'Dec'}
    
    trend_labels = []
    trend_amounts = []
    for t in reversed(trends):
        if not t['month']: continue
        y, m = t['month'].split('-')
        trend_labels.append(month_map[m])
        trend_amounts.append(t['amt'])
        
    # Calculate product distribution
    prod_counts = {}
    for r in applications:
        ptype = r['loan_type']
        prod_counts[ptype] = prod_counts.get(ptype, 0) + 1
    
    product_labels = list(prod_counts.keys())
    product_counts = list(prod_counts.values())

    # Get recent applications and group by date
    import datetime as dt_mod
    now = dt_mod.datetime.now()
    today = now.date()
    yesterday = today - dt_mod.timedelta(days=1)
    
    recent_grouped = {
        'Today': [],
        'Yesterday': [],
        'Earlier': []
    }
    
    for row_raw in applications[:20]: # Show up to 20 recent
        row = dict(row_raw) # Convert to dict to add relative_time
        created_at_str = row['created_at']
        
        try:
            # Parse full timestamp: 2026-03-26 11:47:34
            dt_obj = dt_mod.datetime.strptime(created_at_str, '%Y-%m-%d %H:%M:%S')
            date_only = dt_obj.date()
            
            # Calculate difference
            diff = now - dt_obj
            diff_m = diff.total_seconds() / 60
            
            if diff_m < 1:
                row['relative_time'] = "Just now"
            elif diff_m < 60:
                row['relative_time'] = f"{int(diff_m)} mins ago"
            elif diff_m < 1440: # within 24 hours
                row['relative_time'] = f"{int(diff_m/60)} hours ago"
            else:
                row['relative_time'] = dt_obj.strftime('%d %b, %H:%M')
                
        except:
            date_only = today
            row['relative_time'] = "Recently"

        if date_only == today:
            recent_grouped['Today'].append(row)
        elif date_only == yesterday:
            recent_grouped['Yesterday'].append(row)
        else:
            recent_grouped['Earlier'].append(row)

    stats = {
        'total_amount': total_amount,
        'avg_amount': avg_amount,
        'total_approved_amt': total_approved_amt,
        'total_approved_count': total_approved_count,
        'total_rejected_amt': total_rejected_amt,
        'total_rejected_count': total_rejected_count,
        'count': len(applications),
        'trend_labels': trend_labels,
        'trend_amounts': trend_amounts,
        'product_labels': product_labels,
        'product_counts': product_counts
    }
    
    conn.close()
    return render_template('finance_dashboard.html', stats=stats, recent_grouped=recent_grouped)

# ---------------- User Auth ----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password)).fetchone()
        conn.close()
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('dashboard_view'))
        else:
            error = "Invalid username or password"
    return render_template('login.html', error=error)

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        try:
            conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except:
            error = "Username already exists"
            conn.close()
    return render_template('register.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('dashboard_view'))

# ---------------- Application Selection (Old Index) ----------------
@app.route('/apply')
def index():
    return render_template('index.html')

@app.route('/details/<loan_type>')
def loan_details(loan_type):
    if loan_type not in LOAN_DATA:
        return redirect(url_for('index'))
    data = LOAN_DATA[loan_type]
    return render_template('loan_details.html', 
                          loan_name=data['name'], 
                          interest=data['interest'], 
                          max_amount=data['max_amount'], 
                          tenure=data['tenure'], 
                          description=data['description'], 
                          image_url=url_for('static', filename=data['image']),
                          form_url=url_for(data['form']))

# ---------------- Education Loan ----------------
@app.route('/education-loan-form')
def education_form():
    return render_template('education-loan-form.html')

@app.route('/education_submit', methods=['POST'])
def education_submit():
    name = request.form['name']
    email = request.form['Gmail']
    phone = request.form['phone']
    course = request.form['course']
    college = request.form['college']
    amount = request.form['amount']
    identity = request.files.get('identity_file')
    income = request.files.get('income_file')
    loan_doc = request.files.get('loan_file')
    identity_name = None
    income_name = None
    loan_name = None
    if identity and identity.filename !="":
       identity_name = secure_filename(identity.filename)
       identity.save(os.path.join('uploads/identity', identity_name))
    if income and income.filename !="":
       income_name = secure_filename(income.filename)
       income.save(os.path.join('uploads/income', income_name))
    if loan_doc and loan_doc.filename !="":
       loan_name = secure_filename(loan_doc.filename)
       loan_doc.save(os.path.join('uploads/loan_docs', loan_name))
    cibil_score = request.form.get('cibil_score', 0)
    
    # Check for unique Gmail
    conn = get_db_connection()
    existing = conn.execute("SELECT id FROM loan_applications WHERE email = ?", (email,)).fetchone()
    if existing:
        conn.close()
        return "Error: An application with this Gmail already exists. Please use a unique Gmail or track your status."
        
    import datetime
    now = datetime.datetime.now()
    now_str = now.strftime('%Y-%m-%d %H:%M:%S')
    today_str = now.strftime('%Y-%m-%d')
    
    # Calculate daily_id
    daily_count = conn.execute("SELECT COUNT(*) FROM loan_applications WHERE substr(created_at, 1, 10) = ?", (today_str,)).fetchone()[0]
    daily_id = daily_count + 1
    
    conn.execute(
        "INSERT INTO loan_applications (name, email, loan_type, amount, status, reason, identity_doc, income_doc, loan_doc, cibil_score, created_at, daily_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (name, email, 'Education Loan', amount, 'pending', 'Under verification', identity_name, income_name, loan_name, cibil_score, now_str, daily_id)
    )
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard_view'))

# ---------------- Personal Loan ----------------
@app.route('/personal-loan-form')
def personal_form():
    return render_template('personal-loan-form.html')

@app.route('/income_submit', methods=['POST'])
def income_submit():
    name = request.form['name']
    email = request.form['Gmail']
    phone = request.form['phone']
    employment_status = request.form['employment']
    monthly_income = request.form['monthly_income']
    amount = request.form['amount']
    identity = request.files.get('identity_file')
    income_file = request.files.get('income_file')
    loan_doc = request.files.get('loan_file')
    identity_name = None
    income_name = None
    loan_name = None
    if identity and identity.filename !="":
       identity_name = secure_filename(identity.filename)
       identity.save(os.path.join('uploads/identity', identity_name))
    if income_file and income_file.filename !="":
       income_name = secure_filename(income_file.filename)
       income_file.save(os.path.join('uploads/income', income_name))
    if loan_doc and loan_doc.filename !="":
       loan_name = secure_filename(loan_doc.filename)
       loan_doc.save(os.path.join('uploads/loan_docs', loan_name))
    
    cibil_score = request.form.get('cibil_score', 0)
    
    # Check for unique Gmail
    conn = get_db_connection()
    existing = conn.execute("SELECT id FROM loan_applications WHERE email = ?", (email,)).fetchone()
    if existing:
        conn.close()
        return "Error: An application with this Gmail already exists. Please use a unique Gmail or track your status."
        
    import datetime
    now = datetime.datetime.now()
    now_str = now.strftime('%Y-%m-%d %H:%M:%S')
    today_str = now.strftime('%Y-%m-%d')
    
    # Calculate daily_id
    daily_count = conn.execute("SELECT COUNT(*) FROM loan_applications WHERE substr(created_at, 1, 10) = ?", (today_str,)).fetchone()[0]
    daily_id = daily_count + 1
    
    conn.execute(
        "INSERT INTO loan_applications (name, email, loan_type, amount, status, reason, identity_doc, income_doc, loan_doc, cibil_score, created_at, daily_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (name, email, 'Personal Loan', amount, 'pending', 'Under verification', identity_name, income_name, loan_name, cibil_score, now_str, daily_id)
    )
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard_view'))

# ---------------- Home Loan ----------------
@app.route('/home-loan-form')
def home_form():
    return render_template('home-loan-form.html')

@app.route('/property_submit', methods=['POST'])
def property_submit():
    name = request.form['name']
    email = request.form['Gmail']
    phone = request.form['phone']
    amount = request.form['amount']
    identity = request.files.get('identity_file')
    income = request.files.get('income_file')
    loan_doc = request.files.get('loan_file')
    identity_name = None
    income_name = None
    loan_name = None
    if identity and identity.filename !="":
       identity_name = secure_filename(identity.filename)
       identity.save(os.path.join('uploads/identity', identity_name))
    if income and income.filename !="":
       income_name = secure_filename(income.filename)
       income.save(os.path.join('uploads/income', income_name))
    if loan_doc and loan_doc.filename !="":
       loan_name = secure_filename(loan_doc.filename)
       loan_doc.save(os.path.join('uploads/loan_docs', loan_name))
    
    cibil_score = request.form.get('cibil_score', 0)
    
    # Check for unique Gmail
    conn = get_db_connection()
    existing = conn.execute("SELECT id FROM loan_applications WHERE email = ?", (email,)).fetchone()
    if existing:
        conn.close()
        return "Error: An application with this Gmail already exists. Please use a unique Gmail or track your status."
        
    import datetime
    now = datetime.datetime.now()
    submit_time = now.strftime('%Y-%m-%d %H:%M:%S')
    today_str = now.strftime('%Y-%m-%d')
    
    # Calculate daily_id
    daily_count = conn.execute("SELECT COUNT(*) FROM loan_applications WHERE substr(created_at, 1, 10) = ?", (today_str,)).fetchone()[0]
    daily_id = daily_count + 1
    
    conn.execute(
        "INSERT INTO loan_applications (name, email, loan_type, amount, status, reason, identity_doc, income_doc, loan_doc, cibil_score, created_at, daily_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (name, email, 'Home Loan', amount, 'pending', 'under verification', identity_name, income_name, loan_name, cibil_score, submit_time, daily_id)
    )
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard_view'))

# ---------------- Business Loan ----------------
@app.route('/business-loan-form')
def business_form():
    return render_template('business-loan-form.html')

@app.route('/business_submit', methods=['POST'])
def business_submit():
    name = request.form.get('name', 'N/A')
    email = request.form.get('Gmail', 'N/A')
    amount = request.form['amount']
    identity = request.files.get('identity_file')
    income = request.files.get('income_file')
    loan_doc = request.files.get('loan_file')
    identity_name = None
    income_name = None
    loan_name = None
    if identity and identity.filename !="":
       identity_name = secure_filename(identity.filename)
       identity.save(os.path.join('uploads/identity', identity_name))
    if income and income.filename !="":
       income_name = secure_filename(income.filename)
       income.save(os.path.join('uploads/income', income_name))
    if loan_doc and loan_doc.filename !="":
       loan_name = secure_filename(loan_doc.filename)
       loan_doc.save(os.path.join('uploads/loan_docs', loan_name))
    
    cibil_score = request.form.get('cibil_score', 0)
    
    # Check for unique Gmail
    conn = get_db_connection()
    existing = conn.execute("SELECT id FROM loan_applications WHERE email = ?", (email,)).fetchone()
    if existing:
        conn.close()
        return "Error: An application with this Gmail already exists. Please use a unique Gmail or track your status."
        
    import datetime
    now = datetime.datetime.now()
    now_str = now.strftime('%Y-%m-%d %H:%M:%S')
    today_str = now.strftime('%Y-%m-%d')
    
    # Calculate daily_id
    daily_count = conn.execute("SELECT COUNT(*) FROM loan_applications WHERE substr(created_at, 1, 10) = ?", (today_str,)).fetchone()[0]
    daily_id = daily_count + 1
    
    conn.execute(
        "INSERT INTO loan_applications (name, email, loan_type, amount, status, reason, identity_doc, income_doc, loan_doc, cibil_score, created_at, daily_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (name, email, 'Business Loan', amount, 'pending', 'Under verification', identity_name, income_name, loan_name, cibil_score, now_str, daily_id)
    )
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard_view'))

# ---------------- Consumer Durable Loan ----------------
@app.route('/consumer-durable-loan-form')
def consumer():
    return render_template('consumer-durable-loan-form.html')

@app.route('/consumer_submit', methods=['POST'])
def consumer_submit():
    name = request.form['name']
    email = request.form['Gmail']
    amount = request.form['amount']
    identity = request.files.get('identity_file')
    income = request.files.get('income_file')
    loan_doc = request.files.get('loan_file')
    identity_name = None
    income_name = None
    loan_name = None
    if identity and identity.filename !="":
       identity_name = secure_filename(identity.filename)
       identity.save(os.path.join('uploads/identity', identity_name))
    if income and income.filename !="":
       income_name = secure_filename(income.filename)
       income.save(os.path.join('uploads/income', income_name))
    if loan_doc and loan_doc.filename !="":
       loan_name = secure_filename(loan_doc.filename)
       loan_doc.save(os.path.join('uploads/loan_docs', loan_name))

    cibil_score = request.form.get('cibil_score', 0)
    
    # Check for unique Gmail
    conn = get_db_connection()
    existing = conn.execute("SELECT id FROM loan_applications WHERE email = ?", (email,)).fetchone()
    if existing:
        conn.close()
        return "Error: An application with this Gmail already exists. Please use a unique Gmail or track your status."
        
    import datetime
    now = datetime.datetime.now()
    now_str = now.strftime('%Y-%m-%d %H:%M:%S')
    today_str = now.strftime('%Y-%m-%d')
    
    # Calculate daily_id
    daily_count = conn.execute("SELECT COUNT(*) FROM loan_applications WHERE substr(created_at, 1, 10) = ?", (today_str,)).fetchone()[0]
    daily_id = daily_count + 1
    
    conn.execute(
        "INSERT INTO loan_applications (name, email, loan_type, amount, status, reason, identity_doc, income_doc, loan_doc, cibil_score, created_at, daily_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (name, email, 'Consumer Durable Loan', amount, 'pending', 'Under verification', identity_name, income_name, loan_name, cibil_score, now_str, daily_id)
    )
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard_view'))

# ---------------- Credit Card Loan ----------------
@app.route('/credit-card-loan-form')
def credit_form():
    return render_template('credit-card-loan-form.html')

@app.route('/creditcard_submit', methods=['POST'])
def creditcard_submit():
    name = request.form['name']
    email = request.form['Gmail']
    amount = request.form['amount']
    identity = request.files.get('identity_file')
    income = request.files.get('income_file')
    loan_doc = request.files.get('loan_file')
    identity_name = None
    income_name = None
    loan_name = None
    if identity and identity.filename !="":
       identity_name = secure_filename(identity.filename)
       identity.save(os.path.join('uploads/identity', identity_name))
    if income and income.filename !="":
       income_name = secure_filename(income.filename)
       income.save(os.path.join('uploads/income', income_name))
    if loan_doc and loan_doc.filename !="":
       loan_name = secure_filename(loan_doc.filename)
       loan_doc.save(os.path.join('uploads/loan_docs', loan_name))
    
    cibil_score = request.form.get('cibil_score', 0)
    
    # Check for unique Gmail
    conn = get_db_connection()
    existing = conn.execute("SELECT id FROM loan_applications WHERE email = ?", (email,)).fetchone()
    if existing:
        conn.close()
        return "Error: An application with this Gmail already exists. Please use a unique Gmail or track your status."
        
    import datetime
    now = datetime.datetime.now()
    now_str = now.strftime('%Y-%m-%d %H:%M:%S')
    today_str = now.strftime('%Y-%m-%d')
    
    # Calculate daily_id
    daily_count = conn.execute("SELECT COUNT(*) FROM loan_applications WHERE substr(created_at, 1, 10) = ?", (today_str,)).fetchone()[0]
    daily_id = daily_count + 1
    
    conn.execute(
        "INSERT INTO loan_applications (name, email, loan_type, amount, status, reason, identity_doc, income_doc, loan_doc, cibil_score, created_at, daily_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (name, email, 'Credit Card Loan', amount, 'pending', 'Under verification', identity_name, income_name, loan_name, cibil_score, now_str, daily_id)
    )
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard_view'))

# ---------------- Gold Loan ----------------
@app.route('/gold-loan-form')
def gold_form():
    return render_template('gold-loan-form.html')

@app.route('/gold_submit', methods=['POST'])
def gold_submit():
    name = request.form['name']
    email = request.form['Gmail']
    amount = request.form['amount']
    identity = request.files.get('identity_file')
    income = request.files.get('income_file')
    loan_doc = request.files.get('loan_file')
    identity_name = None
    income_name = None
    loan_name = None
    if identity and identity.filename !="":
       identity_name = secure_filename(identity.filename)
       identity.save(os.path.join('uploads/identity', identity_name))
    if income and income.filename !="":
       income_name = secure_filename(income.filename)
       income.save(os.path.join('uploads/income', income_name))
    if loan_doc and loan_doc.filename !="":
       loan_name = secure_filename(loan_doc.filename)
       loan_doc.save(os.path.join('uploads/loan_docs', loan_name))

    cibil_score = request.form.get('cibil_score', 0)
    
    # Check for unique Gmail
    conn = get_db_connection()
    existing = conn.execute("SELECT id FROM loan_applications WHERE email = ?", (email,)).fetchone()
    if existing:
        conn.close()
        return "Error: An application with this Gmail already exists. Please use a unique Gmail or track your status."
        
    import datetime
    now = datetime.datetime.now()
    now_str = now.strftime('%Y-%m-%d %H:%M:%S')
    today_str = now.strftime('%Y-%m-%d')
    
    # Calculate daily_id
    daily_count = conn.execute("SELECT COUNT(*) FROM loan_applications WHERE substr(created_at, 1, 10) = ?", (today_str,)).fetchone()[0]
    daily_id = daily_count + 1
    
    conn.execute(
        "INSERT INTO loan_applications (name, email, loan_type, amount, status, reason, identity_doc, income_doc, loan_doc, cibil_score, created_at, daily_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (name, email, 'Gold Loan', amount, 'pending', 'Under verification', identity_name, income_name, loan_name, cibil_score, now_str, daily_id)
    )
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard_view'))

# ---------------- Vehicle Loan ----------------
@app.route('/vehicle-loan-form')
def vehicle_form():
    return render_template('vehicle-loan-form.html')

@app.route('/vehicle_submit', methods=['POST'])
def vehicle_submit():
    name = request.form['name']
    email = request.form['Gmail']
    amount = request.form['amount']
    identity = request.files.get('identity_file')
    income = request.files.get('income_file')
    loan_doc = request.files.get('loan_file')
    identity_name = None
    income_name = None
    loan_name = None
    if identity and identity.filename !="":
       identity_name = secure_filename(identity.filename)
       identity.save(os.path.join('uploads/identity', identity_name))
    if income and income.filename !="":
       income_name = secure_filename(income.filename)
       income.save(os.path.join('uploads/income', income_name))
    if loan_doc and loan_doc.filename !="":
       loan_name = secure_filename(loan_doc.filename)
       loan_doc.save(os.path.join('uploads/loan_docs', loan_name))

    cibil_score = request.form.get('cibil_score', 0)
    
    # Check for unique Gmail
    conn = get_db_connection()
    existing = conn.execute("SELECT id FROM loan_applications WHERE email = ?", (email,)).fetchone()
    if existing:
        conn.close()
        return "Error: An application with this Gmail already exists. Please use a unique Gmail or track your status."
        
    import datetime
    now = datetime.datetime.now()
    now_str = now.strftime('%Y-%m-%d %H:%M:%S')
    today_str = now.strftime('%Y-%m-%d')
    
    # Calculate daily_id
    daily_count = conn.execute("SELECT COUNT(*) FROM loan_applications WHERE substr(created_at, 1, 10) = ?", (today_str,)).fetchone()[0]
    daily_id = daily_count + 1
    
    conn.execute(
        "INSERT INTO loan_applications (name, email, loan_type, amount, status, reason, identity_doc, income_doc, loan_doc, cibil_score, created_at, daily_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (name, email, 'Vehicle Loan', amount, 'pending', 'Under verification', identity_name, income_name, loan_name, cibil_score, now_str, daily_id)
    )
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard_view'))

# ---------------- Agriculture Loan ----------------
@app.route('/agriculture-loan-form')
def agriculture_form():
    return render_template('agriculture-loan-form.html')

@app.route('/agriculture_submit', methods=['POST'])
def agriculture_submit():
    name = request.form['name']
    email = request.form['Gmail']
    amount = request.form['amount']
    identity = request.files.get('identity_file')
    income = request.files.get('income_file')
    loan_doc = request.files.get('loan_file')
    identity_name = None
    income_name = None
    loan_name = None
    if identity and identity.filename !="":
       identity_name = secure_filename(identity.filename)
       identity.save(os.path.join('uploads/identity', identity_name))
    if income and income.filename !="":
       income_name = secure_filename(income.filename)
       income.save(os.path.join('uploads/income', income_name))
    if loan_doc and loan_doc.filename !="":
       loan_name = secure_filename(loan_doc.filename)
       loan_doc.save(os.path.join('uploads/loan_docs', loan_name))

    cibil_score = request.form.get('cibil_score', 0)
    
    # Check for unique Gmail
    conn = get_db_connection()
    existing = conn.execute("SELECT id FROM loan_applications WHERE email = ?", (email,)).fetchone()
    if existing:
        conn.close()
        return "Error: An application with this Gmail already exists. Please use a unique Gmail or track your status."
        
    import datetime
    now = datetime.datetime.now()
    now_str = now.strftime('%Y-%m-%d %H:%M:%S')
    today_str = now.strftime('%Y-%m-%d')
    
    # Calculate daily_id
    daily_count = conn.execute("SELECT COUNT(*) FROM loan_applications WHERE substr(created_at, 1, 10) = ?", (today_str,)).fetchone()[0]
    daily_id = daily_count + 1
    
    conn.execute(
        "INSERT INTO loan_applications (name, email, loan_type, amount, status, reason, identity_doc, income_doc, loan_doc, cibil_score, created_at, daily_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (name, email, 'Agriculture Loan', amount, 'pending', 'Under verification', identity_name, income_name, loan_name, cibil_score, now_str, daily_id)
    )
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard_view'))
# ---------------- Mortgage Loan ----------------
@app.route('/mortgage-loan-form')
def mortgage_form():
    return render_template('mortgage-loan-form.html')
@app.route('/mortgage_submit', methods=['POST'])
def mortgage_submit():
    name = request.form['name']
    email = request.form['Gmail']
    amount = request.form['amount']
    identity = request.files.get('identity_file')
    income = request.files.get('income_file')
    loan_doc = request.files.get('loan_file')
    identity_name = None
    income_name = None
    loan_name = None
    if identity and identity.filename !="":
       identity_name = secure_filename(identity.filename)
       identity.save(os.path.join('uploads/identity', identity_name))
    if income and income.filename !="":
       income_name = secure_filename(income.filename)
       income.save(os.path.join('uploads/income', income_name))
    if loan_doc and loan_doc.filename !="":
       loan_name = secure_filename(loan_doc.filename)
       loan_doc.save(os.path.join('uploads/loan_docs', loan_name))

    cibil_score = request.form.get('cibil_score', 0)
    
    # Check for unique Gmail
    conn = get_db_connection()
    existing = conn.execute("SELECT id FROM loan_applications WHERE email = ?", (email,)).fetchone()
    if existing:
        conn.close()
        return "Error: An application with this Gmail already exists. Please use a unique Gmail or track your status."
        
    import datetime
    now = datetime.datetime.now()
    now_str = now.strftime('%Y-%m-%d %H:%M:%S')
    today_str = now.strftime('%Y-%m-%d')
    
    # Calculate daily_id
    daily_count = conn.execute("SELECT COUNT(*) FROM loan_applications WHERE substr(created_at, 1, 10) = ?", (today_str,)).fetchone()[0]
    daily_id = daily_count + 1
    
    conn.execute(
        "INSERT INTO loan_applications (name, email, loan_type, amount, status, reason, identity_doc, income_doc, loan_doc, cibil_score, created_at, daily_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (name, email, 'Mortgage Loan', amount, 'pending', 'Under verification', identity_name, income_name, loan_name, cibil_score, now_str, daily_id)
    )
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard_view'))


@app.route('/admin/advanced')
def admin_advanced():
    conn = get_db_connection()
    applications = conn.execute("SELECT * FROM loan_applications").fetchall()
    
    # Status Stats
    approved = [r for r in applications if r['status'] == 'Approved']
    pending = [r for r in applications if r['status'] == 'pending']
    rejected = [r for r in applications if r['status'] == 'Rejected']
    
    # Counts
    approved_count = len(approved)
    pending_count = len(pending)
    rejected_count = len(rejected)
    total_count = len(applications)
    
    # Amounts
    approved_amount = sum([r['amount'] for r in approved])
    pending_amount = sum([r['amount'] for r in pending])
    rejected_amount = sum([r['amount'] for r in rejected])
    total_amount = sum([r['amount'] for r in applications])
    
    # Approval Rate
    approval_rate = round((approved_count / total_count * 100)) if total_count > 0 else 0
    
    # Monthly Trends (Real data from created_at)
    from datetime import datetime
    trends = conn.execute("SELECT strftime('%Y-%m', created_at) as month, SUM(amount) as amt FROM loan_applications WHERE status='Approved' GROUP BY month ORDER BY month DESC LIMIT 12").fetchall()
    month_map = {'01':'Jan','02':'Feb','03':'Mar','04':'Apr','05':'May','06':'Jun','07':'Jul','08':'Aug','09':'Sep','10':'Oct','11':'Nov','12':'Dec'}
    trend_labels = []
    trend_amounts = []
    for t in reversed(trends):
        if not t['month']: continue
        y, m = t['month'].split('-')
        trend_labels.append(month_map[m])
        trend_amounts.append(t['amt'])
        
    # Product Stats
    product_stats = {}
    for r in applications:
        ptype = r['loan_type']
        if ptype not in product_stats:
            product_stats[ptype] = {'count': 0, 'amount': 0}
        product_stats[ptype]['count'] += 1
        product_stats[ptype]['amount'] += r['amount']
        
    product_labels = list(product_stats.keys())
    product_counts = [d['count'] for d in product_stats.values()]
    
    stats = {
        'approved_count': approved_count,
        'pending_count': pending_count,
        'rejected_count': rejected_count,
        'total_count': total_count,
        'approved_amount': approved_amount,
        'pending_amount': pending_amount,
        'rejected_amount': rejected_amount,
        'total_amount': total_amount,
        'approval_rate': approval_rate,
        'product_stats': product_stats,
        'product_labels': product_labels,
        'product_counts': product_counts,
        'trend_labels': trend_labels,
        'trend_amounts': trend_amounts
    }
    
    conn.close()
    return render_template('advanced_dashboard.html', stats=stats, current_tab='dashboard')

@app.route('/admin/leads')
def admin_leads():
    conn = get_db_connection()
    leads = conn.execute("SELECT * FROM users").fetchall()
    conn.close()
    return render_template('admin_leads.html', leads=leads, current_tab='leads')

@app.route('/admin/reports')
def admin_reports():
    conn = get_db_connection()
    daily = conn.execute("SELECT date(created_at) as d, COUNT(*) as c, SUM(amount) as s FROM loan_applications GROUP BY d ORDER BY d DESC").fetchall()
    conn.close()
    return render_template('admin_reports.html', daily_stats=daily, current_tab='reports')

@app.route('/admin/config')
def admin_config():
    settings = { 'System Name': 'Banku AI Loan v3.0', 'Admin Email': 'admin@banku.com', 'Auto Approval Threshold': '0.0 (Disabled)', 'Currency Symbol': '₹', 'Maintenance Mode': 'OFF' }
    return render_template('admin_config.html', settings=settings, current_tab='config')

@app.route('/admin/audit')
def admin_audit():
    logs = [
        {'time': '2026-03-26 12:01', 'user': 'admin', 'action': 'Approved Loan #21', 'ip': '127.0.0.1'},
        {'time': '2026-03-26 11:31', 'user': 'system', 'action': 'New User Registered: prasu', 'ip': '127.0.0.1'},
        {'time': '2026-03-26 11:00', 'user': 'admin', 'action': 'Login Success', 'ip': '127.0.0.1'}
    ]
    return render_template('admin_audit.html', logs=logs, current_tab='audit')

@app.route('/admin/advanced-applications')
def admin_advanced_apps():
    conn = get_db_connection()
    applications = conn.execute("SELECT * FROM loan_applications ORDER BY id DESC").fetchall()
    conn.close()
    return render_template('admin_advanced_apps.html', applications=applications, current_tab='applications')

@app.route('/admin/dashboard')
def admin_dashboard():
    conn = get_db_connection()
    applications = conn.execute("SELECT * FROM loan_applications ORDER BY id DESC").fetchall()
    
    stats = {
        'total': len(applications),
        'kyc': len([r for r in applications if r['status'] == 'Approved']),
        'pending': len([r for r in applications if r['status'] == 'pending']),
        'rejected': len([r for r in applications if r['status'] == 'Rejected'])
    }
    
    conn.close()
    return render_template('admin_dashboard.html', applications=applications, stats=stats)
@app.route('/approve/<int:id>')
def approve(id):
    conn = get_db_connection()
    conn.execute(
        "UPDATE loan_applications SET status = ?, reason = ? WHERE id = ?",
        ('Approved','Loan sanctioned successfully',id)
    )
    conn.commit()
    conn.close()
    return redirect(url_for('admin_dashboard'))
@app.route('/reject/<int:id>')
def reject_page(id):
    return f'''
        <form method="post" action="/reject/{id}">
            <h3>Reason for Rejection</h3>
            <textarea name="reason" required></textarea><br><br>
            <button type="submit">Reject</button>
        </form>
    '''
@app.route('/reject/<int:id>', methods=['POST'])
def reject(id):
    reason = request.form['reason']
    conn = get_db_connection()
    conn.execute(
        "UPDATE loan_applications SET status = ?, reason = ? WHERE id = ?",
        ('Rejected', reason, id)
    )
    conn.commit()
    conn.close()
    return redirect(url_for('admin_dashboard'))
@app.route('/loan-tracking', methods=['GET', 'POST'])
def loan_tracking():
    result = None
    if request.method == 'POST':
        username = request.form['username']
        gmail = request.form['gmail']
        

        conn = get_db_connection()
        result = conn.execute(
            "SELECT status, reason FROM loan_applications WHERE name=? AND email=?",
            (username, gmail)
        ).fetchone()
        conn.close()

    return render_template('loan_tracking.html', result=result)
@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            return redirect(url_for('admin_dashboard'))
        else:
            error = "Invalid Admin Login"
    return render_template('admin_login.html', error=error)

@app.route('/delete/<int:id>')
def delete(id):
    conn = get_db_connection()
    conn.execute("DELETE FROM loan_applications WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_dashboard'))
if __name__ == "__main__":
    app.run(debug=True)
