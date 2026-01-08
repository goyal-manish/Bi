import streamlit as st
import sqlite3
import bcrypt
import smtplib
from email.mime.text import MIMEText
from twilio.rest import Client

# ================== BRANDING ==================
APP_NAME = "RajdhaniTech – Home Tuition Services"
st.set_page_config(APP_NAME, "📚")

# ================== OPTIONAL ALERT TOGGLES ==================
ENABLE_EMAIL = False
ENABLE_WHATSAPP = False

# ================== EMAIL CONFIG ==================
EMAIL_ID = "yourgmail@gmail.com"
EMAIL_PASS = "APP_PASSWORD"
ADMIN_EMAIL = "admin@gmail.com"

# ================== WHATSAPP CONFIG ==================
TWILIO_SID = "TWILIO_SID"
TWILIO_TOKEN = "TWILIO_TOKEN"
TWILIO_FROM = "whatsapp:+14155238886"
ADMIN_WHATSAPP = "whatsapp:+91XXXXXXXXXX"

# ================== DATABASE ==================
DB = "rajdhani_tuition.db"

def db_conn():
    return sqlite3.connect(DB, check_same_thread=False)

def init_db():
    con = db_conn()
    cur = con.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT,
        role TEXT
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS teachers(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        subjects TEXT
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS inquiries(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student TEXT,
        class TEXT,
        subjects TEXT,
        location TEXT,
        contact TEXT,
        status TEXT DEFAULT 'Pending',
        teacher TEXT,
        fees INTEGER
    )""")

    con.commit()
    con.close()

init_db()

# ================== SECURITY ==================
def hash_pw(p): return bcrypt.hashpw(p.encode(), bcrypt.gensalt()).decode()
def check_pw(p,h): return bcrypt.checkpw(p.encode(), h.encode())

# ================== ALERTS ==================
def send_email(msg):
    if not ENABLE_EMAIL: return
    mail = MIMEText(msg)
    mail["Subject"] = "RajdhaniTech Tuition Alert"
    mail["From"] = EMAIL_ID
    mail["To"] = ADMIN_EMAIL
    server = smtplib.SMTP_SSL("smtp.gmail.com",465)
    server.login(EMAIL_ID, EMAIL_PASS)
    server.send_message(mail)
    server.quit()

def send_whatsapp(msg):
    if not ENABLE_WHATSAPP: return
    client = Client(TWILIO_SID, TWILIO_TOKEN)
    client.messages.create(from_=TWILIO_FROM, to=ADMIN_WHATSAPP, body=msg)

# ================== AUTH ==================
def login(email, pw):
    con = db_conn()
    cur = con.cursor()
    cur.execute("SELECT * FROM users WHERE email=?", (email,))
    u = cur.fetchone()
    con.close()
    if u and check_pw(pw, u[3]):
        return u
    return None

def signup(name,email,pw,role):
    con = db_conn()
    cur = con.cursor()
    cur.execute("INSERT INTO users VALUES(NULL,?,?,?,?)",
                (name,email,hash_pw(pw),role))
    con.commit()
    con.close()

# ================== DASHBOARDS ==================
def parent_dashboard():
    st.subheader("📋 Tuition Inquiry")

    with st.form("inq"):
        s = st.text_input("Student Name")
        c = st.selectbox("Class",[f"{i}th" for i in range(1,13)])
        sub = st.multiselect("Subjects",["Maths","Science","English","Hindi"])
        loc = st.text_input("Location")
        con = st.text_input("Contact")

        if st.form_submit_button("Submit Inquiry"):
            db = db_conn()
            cur = db.cursor()
            cur.execute("""
            INSERT INTO inquiries(student,class,subjects,location,contact)
            VALUES(?,?,?,?,?)
            """,(s,c,",".join(sub),loc,con))
            db.commit()
            db.close()

            send_email("New Tuition Inquiry Received")
            send_whatsapp("📢 New Tuition Inquiry - RajdhaniTech")

            st.success("Inquiry Submitted Successfully ✅")

def teacher_dashboard(uid):
    st.subheader("👨‍🏫 Teacher Profile")
    subjects = st.multiselect("Subjects You Teach",
                              ["Maths","Science","English","Physics","Chemistry"])

    if st.button("Save"):
        db = db_conn()
        cur = db.cursor()
        cur.execute("INSERT INTO teachers VALUES(NULL,?,?)",(uid,",".join(subjects)))
        db.commit()
        db.close()
        st.success("Profile Saved")

def admin_dashboard():
    st.subheader("📊 Admin Panel")

    db = db_conn()
    cur = db.cursor()

    cur.execute("SELECT name FROM users WHERE role='teacher'")
    teachers = [t[0] for t in cur.fetchall()]

    cur.execute("SELECT * FROM inquiries")
    rows = cur.fetchall()

    for r in rows:
        with st.expander(f"Inquiry #{r[0]} – {r[1]}"):
            st.write("Class:",r[2])
            st.write("Subjects:",r[3])
            st.write("Contact:",r[5])

            status = st.selectbox("Status",
                        ["Pending","Assigned","Completed"],
                        index=["Pending","Assigned","Completed"].index(r[6]),
                        key=f"s{r[0]}")

            teacher = st.selectbox("Assign Teacher",
                        ["None"]+teachers,
                        key=f"t{r[0]}")

            fees = st.number_input("Fees (₹)",0,100000,r[8] or 0,key=f"f{r[0]}")

            if st.button("Update",key=f"u{r[0]}"):
                cur.execute("""
                UPDATE inquiries
                SET status=?, teacher=?, fees=?
                WHERE id=?
                """,(status,teacher,fees,r[0]))
                db.commit()
                st.success("Updated")

    db.close()

# ================== UI ==================
st.title(APP_NAME)
st.caption("Classes 1st–12th | CBSE / ICSE | Delhi NCR")

if "user" not in st.session_state:
    st.session_state.user = None

menu = st.sidebar.radio("Menu",["Login","Signup"])

if not st.session_state.user:
    if menu=="Login":
        e = st.text_input("Email")
        p = st.text_input("Password",type="password")
        if st.button("Login"):
            u = login(e,p)
            if u:
                st.session_state.user = u
                st.experimental_rerun()
            else:
                st.error("Invalid Login")

    if menu=="Signup":
        n = st.text_input("Name")
        e = st.text_input("Email")
        p = st.text_input("Password",type="password")
        r = st.selectbox("Role",["parent","teacher"])
        if st.button("Signup"):
            signup(n,e,p,r)
            st.success("Account Created")

else:
    u = st.session_state.user
    st.sidebar.success(f"Logged in as {u[4]}")

    if u[4]=="parent":
        parent_dashboard()
    elif u[4]=="teacher":
        teacher_dashboard(u[0])
    elif u[4]=="admin":
        admin_dashboard()

    if st.sidebar.button("Logout"):
        st.session_state.user=None
        st.experimental_rerun()
