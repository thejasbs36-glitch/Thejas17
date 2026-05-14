from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3, hashlib, os, uuid
from datetime import datetime, timedelta
from functools import wraps
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'college_complaint_secret_2024'
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_db():
    conn = sqlite3.connect('college.db')
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.executescript('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            branch TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            approved INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            password TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS principals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            password TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            student_name TEXT NOT NULL,
            branch TEXT NOT NULL,
            room_number TEXT NOT NULL,
            issue_description TEXT NOT NULL,
            photo_path TEXT,
            updated_photo TEXT,
            status TEXT DEFAULT 'Pending',
            teacher_response TEXT,
            date_submitted TEXT DEFAULT CURRENT_TIMESTAMP,
            date_updated TEXT
        );
        CREATE TABLE IF NOT EXISTS infrastructure (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            branch TEXT NOT NULL,
            room_number TEXT UNIQUE NOT NULL,
            num_benches INTEGER DEFAULT 0,
            num_computers INTEGER DEFAULT 0,
            projector TEXT DEFAULT 'No',
            num_fans INTEGER DEFAULT 0,
            fan_status TEXT DEFAULT 'Working',
            electrical_status TEXT DEFAULT 'Good',
            num_windows INTEGER DEFAULT 0,
            window_condition TEXT DEFAULT 'Good',
            updated_by TEXT,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS principal_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint_id INTEGER NOT NULL,
            order_text TEXT NOT NULL,
            teacher_response TEXT,
            sent_at TEXT DEFAULT CURRENT_TIMESTAMP,
            responded_at TEXT
        );
    ''')
    # Default principal
    c.execute("INSERT OR IGNORE INTO principals (username, name, password) VALUES (?, ?, ?)",
              ('principal', 'Dr. Principal', hash_password('principal123')))
    # Default teacher
    c.execute("INSERT OR IGNORE INTO teachers (username, name, password) VALUES (?, ?, ?)",
              ('teacher1', 'Prof. Teacher', hash_password('teacher123')))
    conn.commit()
    conn.close()

def login_required(role):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'user_id' not in session or session.get('role') != role:
                flash('Please login first.', 'error')
                return redirect(url_for(f'{role}_login'))
            return f(*args, **kwargs)
        return decorated
    return decorator

# ─── HOME ────────────────────────────────────────────────
@app.route('/')
def home():
    return render_template('home.html')

# ─── STUDENT AUTH ────────────────────────────────────────
@app.route('/student/register', methods=['GET','POST'])
def student_register():
    if request.method == 'POST':
        sid = request.form['student_id'].strip()
        name = request.form['name'].strip()
        branch = request.form['branch'].strip()
        email = request.form['email'].strip()
        pw = hash_password(request.form['password'])
        conn = get_db()
        try:
            conn.execute("INSERT INTO students (student_id,name,branch,email,password) VALUES (?,?,?,?,?)",
                         (sid, name, branch, email, pw))
            conn.commit()
            flash('Registration submitted! Awaiting principal approval.', 'success')
            return redirect(url_for('student_login'))
        except sqlite3.IntegrityError:
            flash('Student ID or Email already exists.', 'error')
        finally:
            conn.close()
    return render_template('student_register.html')

@app.route('/student/login', methods=['GET','POST'])
def student_login():
    if request.method == 'POST':
        sid = request.form['student_id'].strip()
        pw = hash_password(request.form['password'])
        conn = get_db()
        s = conn.execute("SELECT * FROM students WHERE student_id=? AND password=?", (sid, pw)).fetchone()
        conn.close()
        if s and s['approved']:
            session.update({'user_id': s['id'], 'role': 'student', 'name': s['name'], 'student_id': sid})
            return redirect(url_for('student_dashboard'))
        elif s and not s['approved']:
            flash('Account pending principal approval.', 'error')
        else:
            flash('Invalid credentials.', 'error')
    return render_template('student_login.html')

@app.route('/student/dashboard')
@login_required('student')
def student_dashboard():
    conn = get_db()
    complaints = conn.execute("SELECT * FROM complaints WHERE student_id=? ORDER BY date_submitted DESC",
                              (session['student_id'],)).fetchall()
    conn.close()
    return render_template('student_dashboard.html', complaints=complaints)

@app.route('/student/complaint/submit', methods=['GET','POST'])
@login_required('student')
def submit_complaint():
    if request.method == 'POST':
        photo_path = None
        if 'photo' in request.files:
            f = request.files['photo']
            if f and allowed_file(f.filename):
                fname = secure_filename(f"{uuid.uuid4()}_{f.filename}")
                f.save(os.path.join(app.config['UPLOAD_FOLDER'], fname))
                photo_path = fname
        conn = get_db()
        conn.execute("""INSERT INTO complaints (student_id,student_name,branch,room_number,issue_description,photo_path)
                        VALUES (?,?,?,?,?,?)""",
                     (session['student_id'], session['name'],
                      request.form['branch'], request.form['room_number'],
                      request.form['issue_description'], photo_path))
        conn.commit()
        conn.close()
        flash('Complaint submitted successfully!', 'success')
        return redirect(url_for('student_dashboard'))
    return render_template('submit_complaint.html', student_name=session['name'])

@app.route('/student/logout')
def student_logout():
    session.clear()
    return redirect(url_for('home'))

# ─── TEACHER AUTH ────────────────────────────────────────
@app.route('/teacher/login', methods=['GET','POST'])
def teacher_login():
    if request.method == 'POST':
        uname = request.form['username'].strip()
        pw = hash_password(request.form['password'])
        conn = get_db()
        t = conn.execute("SELECT * FROM teachers WHERE username=? AND password=?", (uname, pw)).fetchone()
        conn.close()
        if t:
            session.update({'user_id': t['id'], 'role': 'teacher', 'name': t['name'], 'username': uname})
            return redirect(url_for('teacher_dashboard'))
        flash('Invalid credentials.', 'error')
    return render_template('teacher_login.html')

@app.route('/teacher/dashboard')
@login_required('teacher')
def teacher_dashboard():
    conn = get_db()
    complaints = conn.execute("SELECT * FROM complaints ORDER BY date_submitted DESC").fetchall()
    infra = conn.execute("SELECT * FROM infrastructure ORDER BY branch, room_number").fetchall()
    orders = conn.execute("""SELECT po.*, c.room_number, c.issue_description 
                             FROM principal_orders po JOIN complaints c ON po.complaint_id=c.id
                             WHERE po.teacher_response IS NULL ORDER BY po.sent_at DESC""").fetchall()
    conn.close()
    return render_template('teacher_dashboard.html', complaints=complaints, infra=infra, orders=orders)

@app.route('/teacher/complaint/update/<int:cid>', methods=['POST'])
@login_required('teacher')
def update_complaint(cid):
    status = request.form['status']
    response = request.form.get('teacher_response', '')
    updated_photo = None
    if 'updated_photo' in request.files:
        f = request.files['updated_photo']
        if f and allowed_file(f.filename):
            fname = secure_filename(f"{uuid.uuid4()}_{f.filename}")
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], fname))
            updated_photo = fname
    conn = get_db()
    if updated_photo:
        conn.execute("UPDATE complaints SET status=?, teacher_response=?, date_updated=?, updated_photo=? WHERE id=?",
                     (status, response, datetime.now().isoformat(), updated_photo, cid))
    else:
        conn.execute("UPDATE complaints SET status=?, teacher_response=?, date_updated=? WHERE id=?",
                     (status, response, datetime.now().isoformat(), cid))
    conn.commit()
    conn.close()
    flash('Complaint updated!', 'success')
    return redirect(url_for('teacher_dashboard'))

@app.route('/teacher/order/respond/<int:oid>', methods=['POST'])
@login_required('teacher')
def respond_order(oid):
    resp = request.form['response']
    conn = get_db()
    conn.execute("UPDATE principal_orders SET teacher_response=?, responded_at=? WHERE id=?",
                 (resp, datetime.now().isoformat(), oid))
    conn.commit()
    conn.close()
    flash('Response sent to principal.', 'success')
    return redirect(url_for('teacher_dashboard'))

@app.route('/teacher/infrastructure/add', methods=['POST'])
@login_required('teacher')
def add_infrastructure():
    data = request.form
    conn = get_db()
    try:
        conn.execute("""INSERT INTO infrastructure 
            (branch,room_number,num_benches,num_computers,projector,num_fans,fan_status,electrical_status,num_windows,window_condition,updated_by,updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (data['branch'], data['room_number'], data['num_benches'], data['num_computers'],
             data['projector'], data['num_fans'], data['fan_status'], data['electrical_status'],
             data['num_windows'], data['window_condition'], session['name'], datetime.now().isoformat()))
        conn.commit()
        flash('Infrastructure added!', 'success')
    except sqlite3.IntegrityError:
        flash('Room number already exists!', 'error')
    finally:
        conn.close()
    return redirect(url_for('teacher_dashboard'))

@app.route('/teacher/infrastructure/update/<int:iid>', methods=['POST'])
@login_required('teacher')
def update_infrastructure(iid):
    data = request.form
    conn = get_db()
    conn.execute("""UPDATE infrastructure SET branch=?,num_benches=?,num_computers=?,projector=?,
                    num_fans=?,fan_status=?,electrical_status=?,num_windows=?,window_condition=?,
                    updated_by=?,updated_at=? WHERE id=?""",
                 (data['branch'], data['num_benches'], data['num_computers'], data['projector'],
                  data['num_fans'], data['fan_status'], data['electrical_status'],
                  data['num_windows'], data['window_condition'], session['name'],
                  datetime.now().isoformat(), iid))
    conn.commit()
    conn.close()
    flash('Infrastructure updated!', 'success')
    return redirect(url_for('teacher_dashboard'))

@app.route('/teacher/infrastructure/delete/<int:iid>', methods=['POST'])
@login_required('teacher')
def delete_infrastructure(iid):
    conn = get_db()
    conn.execute("DELETE FROM infrastructure WHERE id=?", (iid,))
    conn.commit()
    conn.close()
    flash('Infrastructure record deleted!', 'success')
    return redirect(url_for('teacher_dashboard'))

@app.route('/teacher/logout')
def teacher_logout():
    session.clear()
    return redirect(url_for('home'))

# ─── PRINCIPAL AUTH ───────────────────────────────────────
@app.route('/principal/login', methods=['GET','POST'])
def principal_login():
    if request.method == 'POST':
        uname = request.form['username'].strip()
        pw = hash_password(request.form['password'])
        conn = get_db()
        p = conn.execute("SELECT * FROM principals WHERE username=? AND password=?", (uname, pw)).fetchone()
        conn.close()
        if p:
            session.update({'user_id': p['id'], 'role': 'principal', 'name': p['name']})
            return redirect(url_for('principal_dashboard'))
        flash('Invalid credentials.', 'error')
    return render_template('principal_login.html')

@app.route('/principal/dashboard')
@login_required('principal')
def principal_dashboard():
    conn = get_db()
    six_hours_ago = (datetime.now() - timedelta(hours=6)).isoformat()

    # Complaints where teacher has NOT updated status within 6 hours of submission:
    # Condition: submitted more than 6 hours ago AND (date_updated is NULL OR status still Pending)
    pending_over_6h = conn.execute("""
        SELECT * FROM complaints
        WHERE date_submitted < ?
          AND (
            status = 'Pending'
            OR (status != 'Resolved' AND (date_updated IS NULL OR date_updated < ?))
          )
        ORDER BY date_submitted ASC
    """, (six_hours_ago, six_hours_ago)).fetchall()

    all_complaints = conn.execute("SELECT * FROM complaints ORDER BY date_submitted DESC").fetchall()
    infra = conn.execute("SELECT * FROM infrastructure ORDER BY branch, room_number").fetchall()
    orders = conn.execute("""SELECT po.*, c.room_number, c.student_id, c.student_name, c.issue_description
                             FROM principal_orders po JOIN complaints c ON po.complaint_id=c.id
                             ORDER BY po.sent_at DESC""").fetchall()
    pending_students = conn.execute("SELECT * FROM students WHERE approved=0 ORDER BY created_at DESC").fetchall()
    all_students = conn.execute("SELECT * FROM students WHERE approved=1").fetchall()

    # Calculate hours elapsed for each overdue complaint
    now = datetime.now()
    overdue_with_hours = []
    for c in pending_over_6h:
        submitted = datetime.fromisoformat(c['date_submitted'])
        hours_elapsed = round((now - submitted).total_seconds() / 3600, 1)
        overdue_with_hours.append({'complaint': c, 'hours': hours_elapsed})

    conn.close()
    return render_template('principal_dashboard.html',
                           pending_over_6h=pending_over_6h,
                           overdue_with_hours=overdue_with_hours,
                           all_complaints=all_complaints,
                           infra=infra,
                           orders=orders,
                           pending_students=pending_students,
                           all_students=all_students)

@app.route('/principal/send_order/<int:cid>', methods=['POST'])
@login_required('principal')
def send_order(cid):
    order_text = request.form['order_text']
    conn = get_db()
    conn.execute("INSERT INTO principal_orders (complaint_id, order_text) VALUES (?,?)", (cid, order_text))
    conn.commit()
    conn.close()
    flash('Order sent to teacher!', 'success')
    return redirect(url_for('principal_dashboard'))

@app.route('/principal/approve_student/<int:sid>', methods=['POST'])
@login_required('principal')
def approve_student(sid):
    conn = get_db()
    conn.execute("UPDATE students SET approved=1 WHERE id=?", (sid,))
    conn.commit()
    conn.close()
    flash('Student approved!', 'success')
    return redirect(url_for('principal_dashboard'))

@app.route('/principal/reject_student/<int:sid>', methods=['POST'])
@login_required('principal')
def reject_student(sid):
    conn = get_db()
    conn.execute("DELETE FROM students WHERE id=?", (sid,))
    conn.commit()
    conn.close()
    flash('Student registration rejected.', 'success')
    return redirect(url_for('principal_dashboard'))

@app.route('/principal/logout')
def principal_logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/infrastructure')
def view_infrastructure():
    conn = get_db()
    infra = conn.execute("SELECT * FROM infrastructure ORDER BY branch, room_number").fetchall()
    conn.close()
    return render_template('infrastructure_public.html', infra=infra)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
