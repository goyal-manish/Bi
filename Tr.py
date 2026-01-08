import streamlit as st
import sqlite3
import hashlib
from datetime import datetime

# ---------------- CONFIG ----------------
st.set_page_config(page_title="RajdhaniTech Tuition", layout="centered")

DB = "rajdhani.db"

# ---------------- DATABASE ----------------
def get_db():
    return sqlite3.connect(DB, check_same_thread=False)

db = get_db()
cur = db.cursor()

# Users table
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT UNIQUE,
    password TEXT,
    role TEXT
)
""")

# Inquiry table
cur.execute("""
CREATE TABLE IF NOT EXISTS inquiries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_name TEXT,
    class TEXT,
    subject TEXT,
    parent_email TEXT,
    status TEXT,
    teacher TEXT,
    created_at TEXT
)
""")

db.commit()

# ---------------- UTILS ----------------
def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def signup(name, email, pw, role):
    try:
        cur.execute(
            "INSERT INTO users (name,email,password,role) VALUES (?,?,?,?)",
            (name, email, hash_pw(pw), role)
        )
        db.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def login(email, pw):
    cur.execute(
        "SELECT name, role FROM users WHERE email=? AND password=?",
        (email, hash_pw(pw))
    )
    return cur.fetchone()

# ---------------- UI ----------------
st.markdown("""
<h1 style='text-align:center;color:#0A3D62;'>RajdhaniTech – Home Tuition Services</h1>
<p style='text-align:center;'>Classes 1st–12th | CBSE / ICSE | Delhi NCR</p>
""", unsafe_allow_html=True)

menu = st.sidebar.radio("Menu", ["Login", "Signup"])

# ---------------- SIGNUP ----------------
if menu == "Signup":
    st.subheader("Create Account")

    name = st.text_input("Name")
    email = st.text_input("Email")
    pw = st.text_input("Password", type="password")
    role = st.selectbox("Role", ["parent", "teacher", "admin"])

    if st.button("Signup"):
        if signup(name, email, pw, role):
            st.success("Account created successfully ✅")
        else:
            st.error("Email already registered ❌")

# ---------------- LOGIN ----------------
if menu == "Login":
    st.subheader("Login")

    email = st.text_input("Email")
    pw = st.text_input("Password", type="password")

    if st.button("Login"):
        user = login(email, pw)
        if user:
            st.session_state.user = user
            st.session_state.email = email
            st.success(f"Welcome {user[0]} 👋")
        else:
            st.error("Invalid Login ❌")

# ---------------- DASHBOARD ----------------
if "user" in st.session_state:
    name, role = st.session_state.user
    st.divider()

    # ---------- PARENT ----------
    if role == "parent":
        st.subheader("Submit Tuition Inquiry")

        sname = st.text_input("Student Name")
        cls = st.selectbox("Class", [f"{i}th" for i in range(1,13)])
        sub = st.text_input("Subject")

        if st.button("Submit Inquiry"):
            cur.execute("""
                INSERT INTO inquiries
                (student_name,class,subject,parent_email,status,teacher,created_at)
                VALUES (?,?,?,?,?,?,?)
            """, (sname, cls, sub, st.session_state.email,
                  "Pending", "Not Assigned", datetime.now()))
            db.commit()
            st.success("Inquiry submitted successfully 📩")

    # ---------- TEACHER ----------
    if role == "teacher":
        st.subheader("Assigned Inquiries")

        cur.execute("SELECT * FROM inquiries WHERE teacher=?", (name,))
        rows = cur.fetchall()

        for r in rows:
            st.write(f"📘 {r[1]} | {r[2]} | {r[3]} | Status: {r[5]}")

    # ---------- ADMIN ----------
    if role == "admin":
        st.subheader("Admin Panel")

        cur.execute("SELECT * FROM inquiries")
        data = cur.fetchall()

        for r in data:
            with st.expander(f"Inquiry #{r[0]} – {r[1]}"):
                st.write(f"Class: {r[2]}")
                st.write(f"Subject: {r[3]}")
                st.write(f"Parent: {r[4]}")

                status = st.selectbox(
                    "Status", ["Pending", "Assigned", "Completed"],
                    index=["Pending","Assigned","Completed"].index(r[5]),
                    key=f"s{r[0]}"
                )

                teacher = st.text_input(
                    "Assign Teacher",
                    r[6],
                    key=f"t{r[0]}"
                )

                if st.button("Update", key=f"u{r[0]}"):
                    cur.execute("""
                        UPDATE inquiries SET status=?, teacher=? WHERE id=?
                    """, (status, teacher, r[0]))
                    db.commit()
                    st.success("Updated ✅")
