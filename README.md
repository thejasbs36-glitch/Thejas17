# 🎓 College Complaint & Infrastructure Management Portal

A full-stack web application built with **Python Flask + HTML/CSS/JS** styled like a Government of India portal.

---

## 📁 Project Structure

```
complaint_system/
├── app.py                    # Main Flask application (all routes, DB logic)
├── requirements.txt          # Python dependencies
├── college.db                # SQLite database (auto-created on first run)
├── static/
│   └── uploads/              # Uploaded complaint & updated photos
└── templates/
    ├── base.html             # Master layout (navbar, header, footer)
    ├── home.html             # Public home page with hero, about, contact
    ├── student_register.html # Student registration form
    ├── student_login.html    # Student login
    ├── student_dashboard.html# Student's complaints + stats
    ├── submit_complaint.html # Complaint submission form
    ├── teacher_login.html    # Teacher login
    ├── teacher_dashboard.html# Teacher: complaints, infra, orders
    ├── principal_login.html  # Principal login
    ├── principal_dashboard.html # Principal: approvals, SLA, orders
    └── infrastructure_public.html # Public infra viewer
```

---

## 🚀 How to Run

### 1. Install Python (3.8+)
Download from https://python.org

### 2. Install dependencies
```bash
cd complaint_system
pip install flask werkzeug
```

### 3. Run the application
```bash
python app.py
```

### 4. Open in browser
```
http://localhost:5000
```

---

## 🔐 Default Login Credentials

| Role      | Username    | Password       |
|-----------|-------------|----------------|
| Principal | principal   | principal123   |
| Teacher   | teacher1    | teacher123     |
| Student   | (register first, get approved by principal) | |

---

## 📌 Key Features

### 🏠 Home Page
- Government-style design (Navy + Saffron + Green tricolor theme)
- Hero section with college campus background photo
- Features, Portals, About, Contact sections
- Shareable student registration link

### 🎓 Student Module
- Register (requires Principal approval)
- Login with Student ID + Password
- Submit complaints: name, branch, room, issue, photo upload
- View ONLY their own complaints in table format
- See complaint status (Pending / In Progress / Resolved)

### 👩‍🏫 Teacher Module
- Default login (username/password)
- View ALL student complaints with photos
- Update complaint status + add remarks + upload updated photo
- Add/Edit/Delete infrastructure records (room must be unique)
- Infrastructure displayed branch-wise: BCA, BBA, BSC, Data Science, BVOC DSW
- Respond to Principal's orders
- Separate tabs for: Complaints | Principal Orders | Infrastructure | Add Infrastructure

### 🏛️ Principal Module
- View complaints pending > 6 hours (SLA alert)
- Send orders/directives to teachers about pending complaints
- Approve or reject student registrations
- View teacher responses to orders
- View all complaints, all infrastructure, all approved students
- Separate tabs for each section

### 🏫 Infrastructure (Public)
- Viewable by ALL (students, teachers, principal, public)
- Branch-wise table: benches, computers, projector, fans, fan status, electrical, windows, window condition

---

## 🔒 Security Features
- Passwords hashed with SHA-256
- Role-based session authentication
- Student registration gated by Principal approval
- Students can only view their own complaints

---

## 📸 Screenshots Preview

| Page | Description |
|------|-------------|
| Home | Government-style with hero image, tricolor bar |
| Student Dashboard | Stats cards + complaint table with photo thumbnails |
| Teacher Dashboard | Tabbed: Complaints / Orders / Infrastructure / Add Infra |
| Principal Dashboard | SLA alerts, approvals, orders, full oversight |

---

## ⚙️ Customization

- Change college name in `base.html` → `.header-text h1` and `.college-name`
- Add more branches: edit the `<select name="branch">` in all templates
- Increase 6-hour SLA: change `timedelta(hours=6)` in `app.py`
- Change theme colors: edit `:root` CSS variables in `base.html`
