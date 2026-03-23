import io
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import plotly.graph_objects as go
import os
import time
import uuid
import PyPDF2
import smtplib
import secrets
import hmac
import hashlib
import struct
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from readability import ReadabilityAnalyzer
import streamlit as st
import json
from datetime import datetime, timedelta
from db import *
from auth import *
from config import *
import base64
import vector_store
import nlp_engine
import knowledge_graph
import pandas as pd
import plotly.express as px
from streamlit_option_menu import option_menu
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh
import pandas as pd
import re

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="PolicyNav",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

APP_DIR = os.environ.get("APP_DIR", ".")
AVATAR_DIR = os.path.join(APP_DIR, "avatars")
os.makedirs(AVATAR_DIR, exist_ok=True)

# ============================================================
# GLOBAL STYLES  — Junaid's dark theme
# ============================================================
def apply_theme():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&family=Inter:wght@300;400;500;600&display=swap');

    /* ── Root ── */
    html, body, .stApp {
        background: #0a0e1a !important;
        font-family: 'Inter', sans-serif !important;
        color: #e2e8f0 !important;
    }

    /* ── Hide default Streamlit chrome ── */
    #MainMenu, footer { visibility: hidden; }
    .block-container { padding: 2rem 2.5rem 2rem 2.5rem !important; max-width: 1200px; }

    /* ── Headings ── */
    h1, h2, h3 {
        font-family: 'Poppins', sans-serif !important;
    }

    h1 { font-size: 2rem !important; font-weight: 700 !important;
        color: #f1f5f9 !important; letter-spacing: -0.5px; letter-spacing: 0.3px; }

    h2 { font-size: 1.4rem !important; font-weight: 600 !important; color: #cbd5e1 !important; letter-spacing: 0.3px;}

    h3 { font-size: 1.1rem !important; font-weight: 600 !important; color: #94a3b8 !important; letter-spacing: 0.3px;}

    /* ── Inputs ── */
    .stTextInput > div > div > input,
    .stTextArea  > div > div > textarea {
        background: #111827 !important;
        border: 1px solid #1e293b !important;
        border-radius: 10px !important;
        color: #f1f5f9 !important;
        font-family: 'Inter', sans-serif !important;
        padding: 10px 14px !important;
        transition: border-color 0.2s, box-shadow 0.2s;
    }
    .stTextInput > div > div > input:focus,
    .stTextArea  > div > div > textarea:focus {
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 3px rgba(99,102,241,0.15) !important;
        outline: none !important;
    }

    /* ── Select box ── */
    .stSelectbox > div > div {
        background: #111827 !important;
        border: 1px solid #1e293b !important;
        border-radius: 10px !important;
        color: #f1f5f9 !important;
    }

    /* ── Buttons ── */
    .stButton > button {
        background: linear-gradient(135deg, #6366f1, #4f46e5) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 10px !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        padding: 10px 20px !important;
        transition: all 0.25s ease !important;
        box-shadow: 0 2px 8px rgba(99,102,241,0.3) !important;
        width: 100%;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #818cf8, #6366f1) !important;
        box-shadow: 0 4px 20px rgba(99,102,241,0.5) !important;
        transform: translateY(-1px) !important;
    }
    .stButton > button:active { transform: translateY(0px) !important; }

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {
        background: #080c18 !important;
        border-right: 1px solid #1e293b !important;
    }
    section[data-testid="stSidebar"] .block-container { padding: 1.5rem 1rem !important; }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] {
        background: #111827;
        border-radius: 12px;
        padding: 4px;
        gap: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent !important;
        color: #64748b !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
        font-size: 14px !important;
        padding: 8px 18px !important;
        border: none !important;
    }
    .stTabs [aria-selected="true"] {
        background: #6366f1 !important;
        color: #ffffff !important;
    }

    /* ── Metrics ── */
    [data-testid="stMetricValue"] { color: #6366f1 !important; font-weight: 700 !important; }
    [data-testid="stMetricLabel"] { color: #64748b !important; font-size: 13px !important; }

    /* ── Expanders ── */
    .streamlit-expanderHeader {
        background: #111827 !important;
        border-radius: 8px !important;
        color: #94a3b8 !important;
        font-size: 13px !important;
    }

    /* ── Alerts ── */
    .stAlert { border-radius: 10px !important; font-size: 14px !important; }

    /* ── Divider ── */
    hr { border-color: #1e293b !important; }

    /* ── Password strength ── */
    .pw-weak   { color: #f87171; font-weight: 600; font-size: 13px; }
    .pw-medium { color: #fbbf24; font-weight: 600; font-size: 13px; }
    .pw-strong { color: #34d399; font-weight: 600; font-size: 13px; }

    /* ── Card base ── */
    .pn-card {
        background: #111827;
        border: 1px solid #1e293b;
        border-radius: 14px;
        padding: 24px;
    }

    /* ── Auth page centering ── */
    .auth-wrap {
        max-width: 420px;
        margin: 3rem auto;
    }

    /* ── Chat messages ── */
    div[data-testid="stChatMessage"] {
        background-color: #1e293b !important;
        border-radius: 12px !important;
        border: 1px solid #334155 !important;
        padding: 16px !important;
        margin-bottom: 16px !important;
    }

    /* ── History table ── */
    .history-table table { width: 100%; border-collapse: collapse; }
    .history-table thead th { text-align: left; padding: 10px 12px; color: #e5e7eb;
        background: #0b1220; border-bottom: 1px solid #334155; }
    .history-table tbody td { padding: 10px 12px; color: #e5e7eb; border-bottom: 1px solid #1f2937; }
    .history-table tbody tr:hover td { background: #0f172a; }
    .ai-output-cell { position: relative; }
    .ai-output-preview { display: inline-block; max-width: 360px; white-space: nowrap;
        overflow: hidden; text-overflow: ellipsis; color: #93c5fd; }
    .hover-card { display: none; position: absolute; left: 0; top: 100%;
        transform: translateY(8px); background: #0b1220; border: 1px solid #334155;
        border-radius: 10px; padding: 12px; width: 580px; max-width: 70vw;
        box-shadow: 0 12px 28px rgba(0,0,0,.45); z-index: 9999; }
    .hover-card .hover-content { color: #e5e7eb; white-space: pre-wrap;
        font-size: 0.95rem; line-height: 1.4; }
    .ai-output-cell:hover .hover-card { display: block; }
    </style>
    """, unsafe_allow_html=True)

apply_theme()

# ============================================================
# OTP CONFIG + HELPERS  (Junaid's secure OTP system)
# ============================================================
OTP_EXPIRY = 600  # 10 minutes in seconds

def generate_otp_code():
    secret = secrets.token_bytes(20)
    msg    = struct.pack(">Q", int(time.time()))
    h      = hmac.new(secret, msg, hashlib.sha1).digest()
    offset = h[19] & 0xf
    code   = ((h[offset]&0x7f)<<24|(h[offset+1]&0xff)<<16|
               (h[offset+2]&0xff)<<8|(h[offset+3]&0xff))
    return f"{code%1000000:06d}"

def send_otp_styled(to_email):
    """Junaid's branded OTP email — dark theme, indigo code box."""
    otp = generate_otp_code()
    msg             = MIMEMultipart("alternative")
    msg["Subject"]  = "PolicyNav — Your Verification Code"
    msg["From"]     = EMAIL_ID
    msg["To"]       = to_email
    html = f"""
    <html><body style="margin:0;padding:0;background:#0a0e1a;font-family:Inter,sans-serif;">
    <div style="max-width:520px;margin:40px auto;background:#111827;padding:40px;
                border-radius:16px;border:1px solid #1e293b;">
        <div style="text-align:center;margin-bottom:28px;">
            <span style="font-size:32px;">⚡</span>
            <h2 style="color:#f1f5f9;margin:8px 0 4px;font-size:22px;">PolicyNav</h2>
            <p style="color:#64748b;font-size:13px;margin:0;">Verification Code</p>
        </div>
        <p style="color:#94a3b8;font-size:15px;text-align:center;">
            Use the code below to verify your identity for
            <strong style="color:#6366f1;">{to_email}</strong>
        </p>
        <div style="background:#0a0e1a;border:1px solid #6366f1;border-radius:12px;
                    text-align:center;padding:24px;margin:24px 0;">
            <span style="font-size:36px;font-weight:700;letter-spacing:10px;color:#818cf8;">
                {otp}
            </span>
        </div>
        <p style="color:#64748b;font-size:13px;text-align:center;">
            Valid for <strong>10 minutes</strong>. Never share this code.
        </p>
        <hr style="border-color:#1e293b;margin:24px 0;">
        <p style="color:#374151;font-size:11px;text-align:center;">© 2026 PolicyNav</p>
    </div></body></html>
    """
    msg.attach(MIMEText(html, "html"))
    try:
        sv = smtplib.SMTP("smtp.gmail.com", 587)
        sv.starttls()
        sv.login(EMAIL_ID, EMAIL_APP_PASSWORD)
        sv.sendmail(EMAIL_ID, to_email, msg.as_string())
        sv.quit()
        # Store OTP + timestamp in session
        st.session_state.otp_code  = otp
        st.session_state.otp_email = to_email
        st.session_state.otp_time  = datetime.utcnow()
        return True, "Sent"
    except Exception as ex:
        return False, str(ex)

def otp_is_valid(entered, for_email):
    """Returns (bool, message). Checks expiry, email match, and code match."""
    stored_code  = st.session_state.get("otp_code")
    stored_email = st.session_state.get("otp_email")
    stored_time  = st.session_state.get("otp_time")
    if not stored_code or not stored_time:
        return False, "No OTP found. Please request a new code."
    if datetime.utcnow() - stored_time > timedelta(seconds=OTP_EXPIRY):
        return False, "OTP expired. Please request a new code."
    if stored_email != for_email:
        return False, "OTP email mismatch."
    if entered.strip() != stored_code:
        return False, "Incorrect OTP."
    return True, "Valid"

def clear_otp():
    for k in ("otp_code","otp_email","otp_time"):
        st.session_state.pop(k, None)

def otp_input_ui(label="Enter the 6-digit code sent to your email"):
    """Renders the styled OTP input box."""
    st.markdown(f"""
    <div style="background:#111827;border:1px solid #1e293b;border-radius:10px;
                padding:14px 16px;color:#94a3b8;font-size:13px;margin-bottom:12px;">
        📧 {label}
    </div>
    """, unsafe_allow_html=True)
    return st.text_input("6-digit code", max_chars=6, placeholder="000000", key="otp_input_field")

# ── Password strength helpers ──
def check_password_strength(pw):
    import re as _re
    if _re.search(r"\s", pw):  return "Weak",   ["No spaces allowed"]
    ok = (_re.search(r"[A-Za-z]", pw) and _re.search(r"\d", pw))
    if len(pw) >= 8 and ok:   return "Strong",  []
    if len(pw) >= 6 and ok:   return "Medium",  ["Add 2+ chars for Strong"]
    return "Weak", ["Too short (aim for 8+)"]

def pw_strength_html(pw):
    s, f = check_password_strength(pw)
    cls  = {"Weak":"pw-weak","Medium":"pw-medium","Strong":"pw-strong"}[s]
    icon = {"Weak":"✗","Medium":"◑","Strong":"✓"}[s]
    hint = f" — {', '.join(f)}" if f else ""
    return f"<span class='{cls}'>{icon} {s}{hint}</span>"

# ============================================================
# SHARED UI COMPONENTS
# ============================================================
def auth_header(title, subtitle="Public Policy Navigation Platform"):
    st.markdown(f"""
    <div style="text-align:center;padding:2rem 0 1.5rem;">
        <div style="font-size:40px;margin-bottom:12px;">⚡</div>
        <h1 style="font-size:1.8rem !important;color:#f1f5f9 !important;margin:0;">PolicyNav</h1>
        <p style="color:#475569;font-size:14px;margin:6px 0 0;">{subtitle}</p>
    </div>
    <div style="text-align:center;margin-bottom:1.5rem;">
        <span style="font-size:1.1rem;font-weight:600;color:#e2e8f0;">{title}</span>
    </div>
    """, unsafe_allow_html=True)

def section_header(icon, title, subtitle=""):
    st.markdown(f"""
    <div style="margin-bottom:1.5rem;">
        <div style="display:flex;align-items:center;gap:10px;">
            <span style="font-size:24px;">{icon}</span>
            <div>
                <h1 style="margin:0;font-size:1.6rem !important;">{title}</h1>
                {"<p style='margin:2px 0 0;color:#475569;font-size:13px;'>"+subtitle+"</p>" if subtitle else ""}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def card_start():
    st.markdown('<div class="pn-card">', unsafe_allow_html=True)

def card_end():
    st.markdown('</div>', unsafe_allow_html=True)

def divider_text(text):
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:12px;margin:16px 0;">
        <div style="flex:1;height:1px;background:#1e293b;"></div>
        <span style="color:#475569;font-size:12px;">{text}</span>
        <div style="flex:1;height:1px;background:#1e293b;"></div>
    </div>
    """, unsafe_allow_html=True)

def kpi_card(col, icon, label, value, accent="#6366f1"):
    col.markdown(f"""
    <div style="background:#111827;border:1px solid #1e293b;border-radius:14px;
                padding:20px;text-align:center;border-top:3px solid {accent};">
        <div style="font-size:26px;margin-bottom:6px;">{icon}</div>
        <div style="font-size:28px;font-weight:700;color:{accent};font-family:Inter;">{value}</div>
        <div style="color:#64748b;font-size:12px;margin-top:4px;">{label}</div>
    </div>
    """, unsafe_allow_html=True)

def create_gauge(value, title, min_val=0, max_val=100, color="#6366f1"):
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=value,
        title={"text": title, "font": {"color": "#94a3b8", "size": 13}},
        number={"font": {"color": color, "size": 22}},
        gauge={
            "axis":        {"range":[min_val,max_val],"tickwidth":1,"tickcolor":"#334155"},
            "bar":         {"color": color},
            "bgcolor":     "#111827",
            "borderwidth": 1,
            "bordercolor": "#1e293b",
            "steps":       [{"range":[min_val,max_val],"color":"#0f172a"}],
        }
    ))
    fig.update_layout(paper_bgcolor="#111827", font={"color":"#94a3b8","family":"Inter"},
                      height=230, margin=dict(l=10,r=10,t=40,b=10))
    return fig

# ============================================================
# INIT DB + CACHE MODELS
# ============================================================
init_db()

@st.cache_resource
def load_and_cache_models():
    nlp_engine.init_model()
    vector_store.get_embedder()
    return True

# Models load lazily on first use — login page appears instantly

# ============================================================
# SESSION DEFAULTS
# ============================================================
for k, v in [
    ("token", None), ("page", "Login"), ("reset_stage", 0),
    ("rag_chat", []), ("summary", ""), ("doc_text", ""), ("doc_answer", ""),
    ("email_otp", None), ("email_otp_time", None), ("pending_new_email", None),
    ("email_otp_sent", False),
    ("otp_code", None), ("otp_email", None), ("otp_time", None),
    ("signup_data", None), ("signup_otp_sent", False),
    ("forgot_otp_sent", False), ("forgot_otp_verified", False),
    ("pw_otp_sent", False), ("pw_otp_verified", False),
    ("forgot_stage", "email"), ("pw_change_stage", "form"), ("pending_new_pw", None),
]:
    if k not in st.session_state:
        st.session_state[k] = v

def go_to(page):
    st.session_state.page = page
    st.rerun()

# ============================================================
# AVATAR HELPERS
# ============================================================
def get_avatar_path(user):
    if not user:
        return None
    if len(user) >= 10:
        avatar_path = user[9]
        if avatar_path and os.path.exists(avatar_path):
            return avatar_path
    return None

def save_avatar(uploaded_file, email):
    ext = uploaded_file.name.split(".")[-1].lower()
    if ext not in ["png", "jpg", "jpeg"]:
        raise ValueError("Only PNG, JPG, JPEG allowed")
    safe_email = email.replace("@", "_at_").replace(".", "_")
    file_name = f"{safe_email}_{uuid.uuid4().hex[:8]}.{ext}"
    save_path = os.path.join(AVATAR_DIR, file_name)
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return save_path

# ============================================================
# FEEDBACK COMPONENT
# ============================================================
def render_feedback_ui(section_name, generated_text, unique_key):
    payload = verify_token(st.session_state.token)
    if not payload:
        return
    user_email = payload["email"]
    st.markdown("---")
    with st.expander(f"📝 Give feedback on this section"):
        col1, col2 = st.columns([1, 4])
        with col1:
            rating = st.radio("Rating (1-5)", [1,2,3,4,5], horizontal=True, key=f"r_{unique_key}")
        with col2:
            comments = st.text_input("Comments (optional)", key=f"c_{unique_key}")
        if st.button("Submit Feedback", key=f"fb_{unique_key}"):
            submit_feedback(user_email, section_name, rating, comments)
            award_points(user_email, "feedback")
            st.toast("✅ Thank you for your feedback! (+3 pts 🏆)")

# ============================================================
# SIDEBAR
# ============================================================
def render_sidebar():
    with st.sidebar:
        payload = verify_token(st.session_state.token) if st.session_state.token else None
        user = get_user_by_email(payload["email"]) if payload else None
        avatar_path = get_avatar_path(user)

        # Brand
        st.markdown(f"""
        <div style="padding:16px 8px 8px;text-align:center;">
            <div style="font-size:28px;">⚡</div>
            <div style="font-weight:700;font-size:16px;color:#f1f5f9;margin:4px 0;">PolicyNav</div>
            <div style="font-size:11px;color:#475569;">Public Policy Navigation</div>
        </div>
        <hr style="border-color:#1e293b;margin:12px 0;">
        """, unsafe_allow_html=True)

        # User chip
        if user:
            username = user[1]
            email    = user[2]
            initials = username[:2].upper()
            if avatar_path:
                st.image(avatar_path, width=60)
            else:
                st.markdown(f"""
                <div style="background:#1e293b;border-radius:12px;padding:12px 14px;
                            display:flex;align-items:center;gap:12px;margin-bottom:12px;">
                    <div style="background:#6366f1;border-radius:50%;width:36px;height:36px;
                                display:flex;align-items:center;justify-content:center;
                                font-weight:700;font-size:13px;color:white;flex-shrink:0;">
                        {initials}
                    </div>
                    <div style="overflow:hidden;">
                        <div style="font-weight:600;font-size:13px;color:#e2e8f0;
                                    white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
                            {username}
                        </div>
                        <div style="font-size:11px;color:#475569;white-space:nowrap;
                                    overflow:hidden;text-overflow:ellipsis;">{email}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        page_map = {
            "Profile": 0, "Leaderboard": 1, "Readability": 2, "RAG": 3,
            "Summarization": 4, "Graph": 5, "History": 6, "News": 7
        }
        current_index = page_map.get(st.session_state.page, 0)

        selected = option_menu(
            menu_title=None,
            options=["Profile", "Leaderboard", "Readability", "RAG Search", "Summarization",
                     "Knowledge Graph", "History", "News & Updates", "Logout"],
            icons=["person-circle", "trophy", "book", "search", "file-text",
                   "diagram-3", "clock-history", "newspaper", "box-arrow-right"],
            default_index=current_index,
            styles={
                "container":         {"padding": "0!important", "background-color": "#080c18"},
                "icon":              {"color": "#6366f1", "font-size": "15px"},
                "nav-link":          {"color": "#64748b", "font-size": "14px",
                                      "font-family": "Inter", "border-radius": "8px",
                                      "margin": "2px 0", "padding": "10px 14px"},
                "nav-link-selected": {"background-color": "#1e293b", "color": "#e2e8f0",
                                      "font-weight": "600"},
            }
        )

        if st.session_state.page == "RAG" and selected != "RAG Search":
            st.session_state.rag_chat = []
        if st.session_state.page == "Summarization" and selected != "Summarization":
            st.session_state.doc_answer = ""
            st.session_state.summary = ""

        if selected == "Profile"        and st.session_state.page != "Profile":        go_to("Profile")
        if selected == "Leaderboard"    and st.session_state.page != "Leaderboard":    go_to("Leaderboard")
        if selected == "Readability"    and st.session_state.page != "Readability":    go_to("Readability")
        if selected == "RAG Search"     and st.session_state.page != "RAG":            go_to("RAG")
        if selected == "Summarization"  and st.session_state.page != "Summarization":  go_to("Summarization")
        if selected == "Knowledge Graph" and st.session_state.page != "Graph":         go_to("Graph")
        if selected == "History"        and st.session_state.page != "History":        go_to("History")
        if selected == "News & Updates" and st.session_state.page != "News":           go_to("News")
        
        if selected == "Logout":
            try:
                payload_lo = verify_token(st.session_state.token)
                if payload_lo:
                    set_user_online(payload_lo["email"], False)
            except:
                pass
            st.session_state.token = None
            go_to("Login")

        st.markdown("<hr style='border-color:#1e293b;margin:12px 0;'>", unsafe_allow_html=True)
        st.markdown("""
        <div style="text-align:center;padding:8px 0 0;color:#1e293b;font-size:11px;">
            PolicyNav v1.0 · 2026
        </div>
        """, unsafe_allow_html=True)

# ============================================================
# PAGE: LOGIN
# ============================================================
def login_page():
    _, mid, _ = st.columns([1, 1.4, 1])
    with mid:
        auth_header("Sign in to your account")
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        email    = st.text_input("Email address", placeholder="you@example.com")
        password = st.text_input("Password", type="password", placeholder="••••••••")
        st.markdown("<br>", unsafe_allow_html=True)
        col_l, col_c, col_r = st.columns([1, 1, 1])
        login_btn  = col_l.button("Sign In →",       use_container_width=True)
        signup_btn = col_c.button("Create Account",  use_container_width=True)
        forgot_btn = col_r.button("Forgot Password", use_container_width=True)

        if login_btn:
            if not email:
                st.toast("Email required", icon="⚠️"); return
            if not password:
                st.toast("Password required", icon="⚠️"); return
            # ENV ADMIN LOGIN
            if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
                st.session_state.token = generate_token(email)
                set_user_online(email, True)
                log_activity(email, "Admin Login", "Env Admin Login", "Success")
                go_to("AdminDashboard")
                return

            user = get_user_by_email(email)
            if not user:
                st.error("No account found with that email."); return

            # Lockout logic
            failed_attempts = user[6]
            lock_until      = user[7]

            if lock_until and datetime.utcnow() < datetime.fromisoformat(lock_until):
                st.error("⛔ Account locked. Please contact administrator."); return

            if not verify_text(password, user[3]):
                failed_attempts += 1
                if failed_attempts >= MAX_LOGIN_ATTEMPTS:
                    lock_time = datetime.utcnow() + timedelta(minutes=LOCK_TIME_MINUTES)
                    update_login_attempts(email, failed_attempts, lock_time.isoformat())
                    send_admin_action_email(email,
                        f"⚠️ Your PolicyNav account has been locked after {MAX_LOGIN_ATTEMPTS} failed login attempts. Contact admin to unlock.")
                    send_admin_action_email(ADMIN_EMAIL,
                        f"⚠️ User account {email} has been locked after {MAX_LOGIN_ATTEMPTS} failed login attempts.")
                    st.error(f"🔒 Account locked. You and the admin have been notified via email.")
                else:
                    update_login_attempts(email, failed_attempts)
                    remaining = MAX_LOGIN_ATTEMPTS - failed_attempts
                    st.error(f"❌ Incorrect password. {remaining} attempt(s) remaining before lockout.")
                return

            update_login_attempts(email, 0, None)
            set_user_online(email, True)
            # Admin direct login
            if user[10] == 1:
                st.session_state.token = generate_token(email)
                log_activity(email, "Admin Login", "DB Admin Login", "Success")
                go_to("AdminDashboard")
                return
            ok, msg = send_otp_styled(email)
            if ok:
                st.session_state.pending_email = email
                go_to("OTP")
            else:
                st.error(f"Could not send OTP: {msg}")

        if signup_btn: go_to("Signup")
        if forgot_btn: go_to("Forgot")

def otp_page():
    _, mid, _ = st.columns([1, 1.4, 1])
    with mid:
        auth_header("OTP Verification", "Enter the 6-digit code sent to your email")

        entered = st.text_input("6-digit code", max_chars=6, placeholder="000000")
        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("Verify →", use_container_width=True):
            if "otp_time" not in st.session_state:
                st.toast("OTP expired. Please login again.", icon="⚠️"); go_to("Login"); return
            if datetime.utcnow() - st.session_state.otp_time > timedelta(minutes=10):
                st.toast("OTP expired.", icon="⏰"); go_to("Login"); return
            if entered == st.session_state.otp_code:
                if st.session_state.get("flow") == "forgot_otp":
                    go_to("SetNewPassword")
                else:
                    st.session_state.token = generate_token(st.session_state.pending_email)
                    set_user_online(st.session_state.pending_email, True)
                    update_login_streak(st.session_state.pending_email)
                    go_to("Dashboard")
            else:
                st.error("Invalid OTP")

        divider_text("")
        if st.button("← Back to Sign In", use_container_width=True):
            go_to("Login")

# ============================================================
# PAGE: SIGNUP
# ============================================================
def signup_page():
    _, mid, _ = st.columns([1, 1.6, 1])
    with mid:
        auth_header("Create an account", "Join PolicyNav today")

        # ── Stage 1: Registration form ──
        if not st.session_state.get("signup_otp_sent"):
            username = st.text_input("Full name / Username", placeholder="Jane Doe")
            email    = st.text_input("Email address",        placeholder="you@example.com")
            password = st.text_input("Password",             type="password", placeholder="Min. 8 characters")
            if password:
                st.markdown(pw_strength_html(password), unsafe_allow_html=True)
            confirm  = st.text_input("Confirm password",     type="password", placeholder="Re-enter password")
            question = st.selectbox("Security Question", [
                "What is your pet name?",
                "What is your mother's maiden name?",
                "What is your favourite teacher?"
            ])
            answer = st.text_input("Your answer", placeholder="Answer to security question")
            st.markdown("<br>", unsafe_allow_html=True)

            if st.button("Create Account →", use_container_width=True):
                u, e, a = username.strip(), email.strip(), answer.strip()
                if not u:                         st.error("Username required.")
                elif not e:                       st.error("Email required.")
                elif not validate_email(e):       st.error("Invalid email format.")
                elif not password:                st.error("Password required.")
                elif not confirm:                 st.error("Please confirm your password.")
                elif not a:                       st.error("Security answer required.")
                elif password != confirm:         st.error("Passwords do not match.")
                else:
                    strength, fb = check_password_strength(password)
                    if strength == "Weak":
                        st.error(f"Password too weak — {', '.join(fb)}")
                    elif email_exists(e):
                        st.error("An account with that email already exists.")
                    elif is_deleted_account(e):
                        ok = add_pending_registration(u, e, hash_text(password), question, a)
                        if ok:
                            send_admin_action_email(ADMIN_EMAIL, f"⚠️ Re-registration request from {u} ({e}) — previously deleted account. Review in Admin → Pending Registrations.")
                            st.warning("⚠️ This email was previously deleted. Your request has been sent to admin for approval.")
                        else:
                            st.error("Registration request already pending. Please wait for admin approval.")
                    else:
                        ok, msg = send_otp_styled(e)
                        if ok:
                            st.session_state.signup_data    = (u, e, password, question, a)
                            st.session_state.signup_otp_sent = True
                            st.success(f"✅ Verification code sent to {e}")
                            st.rerun()
                        else:
                            st.error(f"Could not send email: {msg}")

        # ── Stage 2: OTP verification ──
        else:
            pending_email = st.session_state.signup_data[1]
            st.markdown(f"""
            <div style="background:#111827;border:1px solid #1e293b;border-radius:10px;
                        padding:14px 16px;color:#94a3b8;font-size:13px;margin-bottom:16px;">
                📧 A verification code was sent to
                <strong style="color:#6366f1;">{pending_email}</strong>
            </div>
            """, unsafe_allow_html=True)

            divider_text("enter verification code")
            st.markdown("""
            <div style="background:#0a0e1a;border:1px solid #6366f1;border-radius:12px;
                        text-align:center;padding:16px;margin-bottom:16px;">
                <span style="color:#818cf8;font-size:13px;font-weight:600;
                             letter-spacing:1px;">CHECK YOUR INBOX</span>
            </div>
            """, unsafe_allow_html=True)

            entered = st.text_input("6-digit code", max_chars=6,
                                    placeholder="000000", key="signup_otp_field")
            st.markdown("<br>", unsafe_allow_html=True)

            if st.button("Verify & Create Account →", use_container_width=True):
                valid, vmsg = otp_is_valid(entered, pending_email)
                if valid:
                    u, e, pwd, sq, sa = st.session_state.signup_data
                    ok, msg = create_user(u, e, hash_text(pwd), sq, hash_text(sa))
                    if ok:
                        clear_otp()
                        st.session_state.signup_otp_sent = False
                        st.session_state.signup_data     = None
                        st.session_state.token           = generate_token(e)
                        log_activity(e, "Profile", "Account Created", "OTP Verified")
                        st.success("✅ Account created! Welcome to PolicyNav.")
                        time.sleep(1); go_to("Dashboard")
                    else:
                        st.error(f"Account creation failed: {msg}")
                else:
                    st.error(f"Verification failed: {vmsg}")

            divider_text("")
            if st.button("← Start Over", use_container_width=True):
                st.session_state.signup_otp_sent = False
                st.session_state.signup_data     = None
                clear_otp(); st.rerun()

        divider_text("already have an account?")
        if st.button("Back to Sign In", use_container_width=True):
            st.session_state.signup_otp_sent = False
            st.session_state.signup_data     = None
            clear_otp(); go_to("Login")

# ============================================================
# PAGE: FORGOT PASSWORD
# ============================================================
def forgot_page():
    _, mid, _ = st.columns([1, 1.4, 1])
    with mid:
        auth_header("Reset your password", "We'll verify your identity first")

        forgot_stage = st.session_state.get("forgot_stage", "email")

        # ── Stage 1: Enter email & send OTP ──
        if forgot_stage == "email":
            email = st.text_input("Registered email address", placeholder="you@example.com")
            st.markdown("<br>", unsafe_allow_html=True)

            if st.button("Send Verification Code →", use_container_width=True):
                user = get_user_by_email(email.strip())
                if not user:
                    st.error("No account found with that email.")
                else:
                    ok, msg = send_otp_styled(email.strip())
                    if ok:
                        st.session_state.pending_email = email.strip()
                        st.session_state.forgot_stage  = "otp"
                        st.success(f"✅ Verification code sent to {email.strip()}")
                        st.rerun()
                    else:
                        st.error(f"Could not send email: {msg}")

        # ── Stage 2: OTP verification ──
        elif forgot_stage == "otp":
            pending = st.session_state.get("pending_email", "")
            st.markdown(f"""
            <div style="background:#111827;border:1px solid #1e293b;border-radius:10px;
                        padding:14px 16px;color:#94a3b8;font-size:13px;margin-bottom:16px;">
                📧 A verification code was sent to
                <strong style="color:#6366f1;">{pending}</strong>
            </div>
            """, unsafe_allow_html=True)

            divider_text("enter verification code")
            st.markdown("""
            <div style="background:#0a0e1a;border:1px solid #6366f1;border-radius:12px;
                        text-align:center;padding:16px;margin-bottom:16px;">
                <span style="color:#818cf8;font-size:13px;font-weight:600;
                             letter-spacing:1px;">CHECK YOUR INBOX</span>
            </div>
            """, unsafe_allow_html=True)

            entered = st.text_input("6-digit code", max_chars=6,
                                    placeholder="000000", key="forgot_otp_field")
            st.markdown("<br>", unsafe_allow_html=True)

            if st.button("Verify Code →", use_container_width=True):
                valid, vmsg = otp_is_valid(entered, pending)
                if valid:
                    clear_otp()
                    st.session_state.forgot_stage = "reset"
                    st.rerun()
                else:
                    st.error(f"Verification failed: {vmsg}")

            divider_text("")
            if st.button("↺ Resend Code", use_container_width=True, key="forgot_resend"):
                ok, msg = send_otp_styled(pending)
                if ok:  st.success("New code sent!")
                else:   st.error(f"Failed: {msg}")

        # ── Stage 3: Set new password (inline, no separate page) ──
        elif forgot_stage == "reset":
            divider_text("set new password")
            new_pw  = st.text_input("New password", type="password",
                                    placeholder="Min. 8 characters", key="forgot_new_pw")
            if new_pw:
                st.markdown(pw_strength_html(new_pw), unsafe_allow_html=True)
            conf_pw = st.text_input("Confirm new password", type="password",
                                    placeholder="Re-enter password", key="forgot_conf_pw")
            st.markdown("<br>", unsafe_allow_html=True)

            if st.button("Update Password →", use_container_width=True, key="forgot_update_pw"):
                reset_email = st.session_state.get("pending_email")
                if new_pw != conf_pw:
                    st.error("Passwords do not match.")
                else:
                    strength, fb = check_password_strength(new_pw)
                    if strength == "Weak":
                        st.error(f"Password too weak — {', '.join(fb)}")
                    else:
                        user    = get_user_by_email(reset_email)
                        history = json.loads(user[8] or "[]")
                        reused  = any(verify_text(new_pw, h) for h in history)
                        if reused:
                            st.error("⚠️ You cannot reuse a previous password.")
                        else:
                            new_hash = hash_text(new_pw)
                            history.insert(0, new_hash)
                            history = history[:PASSWORD_HISTORY_COUNT]
                            update_password(reset_email, new_hash)
                            update_password_history(reset_email, json.dumps(history))
                            st.session_state.forgot_stage = "email"
                            st.session_state.token        = None
                            st.success("✅ Password updated! Redirecting to login...")
                            time.sleep(1.5); go_to("Login")

        divider_text("")
        if st.button("← Back to Sign In", use_container_width=True):
            st.session_state.forgot_stage = "email"
            clear_otp()
            go_to("Login")


def security_question_page():
    _, mid, _ = st.columns([1, 1.4, 1])
    with mid:
        auth_header("Security Verification", "Answer your security question")

        user = get_user_by_email(st.session_state.pending_email)
        st.markdown(f"""
        <div style="background:#111827;border:1px solid #1e293b;border-radius:10px;
                    padding:14px 16px;color:#94a3b8;font-size:14px;margin-bottom:12px;">
            🔐 {user[4]}
        </div>
        """, unsafe_allow_html=True)

        answer = st.text_input("Your answer", placeholder="Enter your answer")
        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("Verify Answer →", use_container_width=True):
            if verify_text(answer, user[5]):
                go_to("SetNewPassword")
            else:
                st.error("Incorrect answer.")

# ============================================================
# PAGE: SET NEW PASSWORD
# ============================================================
def set_new_password_page():
    _, mid, _ = st.columns([1, 1.4, 1])
    with mid:
        auth_header("Set New Password", "Choose a strong password")

        password = st.text_input("New password", type="password", placeholder="Min. 8 characters")
        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("Update Password →", use_container_width=True):
            valid, msg = validate_password(password)
            if not valid:
                st.error(msg); return

            user    = get_user_by_email(st.session_state.pending_email)
            history = json.loads(user[8] or "[]")
            for old_hash in history:
                if verify_text(password, old_hash):
                    st.error("⚠️ You cannot reuse a previous password."); return

            new_hash = hash_text(password)
            update_password(st.session_state.pending_email, new_hash)
            history.insert(0, new_hash)
            history = history[:PASSWORD_HISTORY_COUNT]
            update_password_history(st.session_state.pending_email, json.dumps(history))

            st.success("✅ Password reset! Redirecting to login...")
            st.session_state.token = None
            time.sleep(1.5); go_to("Login")

# ============================================================
# PAGE: DASHBOARD (landing after login)
# ============================================================
def dashboard_page():
    render_sidebar()
    payload = verify_token(st.session_state.token)
    if not payload:
        st.toast("Session expired", icon="❌"); go_to("Login"); return

    user         = get_user_by_email(payload["email"])
    username     = user[1]
    email        = user[2]
    avatar_path  = get_avatar_path(user)
    now_hour     = datetime.now().hour
    tod          = "Good morning" if now_hour < 12 else "Good afternoon" if now_hour < 17 else "Good evening"
    initials     = username[:2].upper()

    section_header("🏠", f"{tod}, {username}!", email)
    
    # --- CHECK FOR UNREAD NEWS ---
    latest_b = get_latest_broadcast()
    if latest_b:
        b_id, b_title, _, _ = latest_b
        last_seen = get_last_seen_broadcast(email)
        
        # If the latest broadcast ID is higher than what they've seen, show the banner!
        if b_id > last_seen:
            st.markdown(f"""
            <div style="background:linear-gradient(90deg, #1e1b4b, #312e81); border-left:4px solid #6366f1; 
                        border-radius:8px; padding:16px; margin-top:16px; display:flex; align-items:center; gap:12px;">
                <span style="font-size:24px;">📢</span>
                <div>
                    <div style="color:#818cf8; font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:1px;">New Update Available</div>
                    <div style="color:#e2e8f0; font-size:15px; font-weight:600;">{b_title}</div>
                    <div style="color:#94a3b8; font-size:13px; margin-top:4px;">Check the <b>News & Updates</b> tab in your sidebar to read the full details!</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
    if avatar_path:
        st.image(avatar_path, width=80)
    else:
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#6366f1,#818cf8);border-radius:50%;
                    width:60px;height:60px;display:flex;align-items:center;
                    justify-content:center;font-size:22px;font-weight:700;
                    color:white;margin-bottom:16px;">
            {initials}
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div style="background:#111827;border:1px solid #1e293b;border-radius:14px;
                padding:20px;margin-top:16px;text-align:center;">
        <div style="font-size:28px;margin-bottom:8px;">📖</div>
        <div style="color:#e2e8f0;font-size:14px;font-weight:600;margin-bottom:6px;">
            Ready to explore policies?
        </div>
        <div style="color:#64748b;font-size:12px;">
            Use the sidebar to navigate to RAG Search, Summarize, or the Knowledge Graph.
        </div>
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# PAGE: PROFILE
# ============================================================
def profile_page():
    render_sidebar()
    section_header("👤", "My Profile", "Manage your account details")
    st.markdown("---")

    payload = verify_token(st.session_state.token)
    if not payload:
        st.toast("Session expired", icon="❌"); go_to("Login"); return

    user        = get_user_by_email(payload["email"])
    avatar_path = get_avatar_path(user)

    # ── Hero card ──
    col1, col2 = st.columns([1, 2])
    with col1:
        if avatar_path:
            st.image(avatar_path, width=160)
        else:
            initials = user[1][:2].upper()
            st.markdown(f"""
            <div style="background:linear-gradient(135deg,#6366f1,#818cf8);border-radius:50%;
                        width:100px;height:100px;display:flex;align-items:center;
                        justify-content:center;font-size:36px;font-weight:700;color:white;">
                {initials}
            </div>
            """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="pn-card">
            <div style="color:#64748b;font-size:12px;text-transform:uppercase;
                        letter-spacing:0.5px;margin-bottom:4px;">Username</div>
            <div style="color:#f1f5f9;font-size:16px;font-weight:600;
                        margin-bottom:16px;">{user[1]}</div>
            <div style="color:#64748b;font-size:12px;text-transform:uppercase;
                        letter-spacing:0.5px;margin-bottom:4px;">Email</div>
            <div style="color:#f1f5f9;font-size:16px;font-weight:600;">{user[2]}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Tabs: Avatar | Change Email | Change Password ──
    tab_av, tab_email, tab_pw = st.tabs(["🖼️  Avatar", "✉️  Change Email", "🔒  Change Password"])

    # ──────────────────────────────────────────────────
    # TAB 1: AVATAR
    # ──────────────────────────────────────────────────
    with tab_av:
        st.markdown("<br>", unsafe_allow_html=True)
        uploaded_avatar = st.file_uploader("Choose image", type=["png","jpg","jpeg"], key="avatar_uploader")
        if st.button("Save Avatar", use_container_width=True, key="save_av"):
            if uploaded_avatar is None:
                st.error("Please choose an image file.");
            else:
                try:
                    new_avatar_path = save_avatar(uploaded_avatar, payload["email"])
                    update_avatar(payload["email"], new_avatar_path)
                    log_activity(payload["email"], "Profile", "Avatar Updated", new_avatar_path)
                    st.success("✅ Avatar updated successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Avatar upload failed: {e}")

    # ──────────────────────────────────────────────────
    # TAB 2: CHANGE EMAIL  (OTP-verified)
    # ──────────────────────────────────────────────────
    with tab_email:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div style="background:#111827;border:1px solid #1e293b;border-radius:10px;
                    padding:12px 16px;color:#94a3b8;font-size:13px;margin-bottom:16px;">
            ⚠️  A verification code will be sent to your <strong style="color:#e2e8f0;">new</strong>
            email address to confirm the change.
        </div>
        """, unsafe_allow_html=True)

        new_email = st.text_input("New email address", placeholder="newemail@example.com", key="new_email_input")

        if st.button("Send Verification Code →", use_container_width=True, key="send_email_otp"):
            new_email = new_email.strip()
            if not validate_email(new_email):
                st.error("Invalid email format.")
            elif new_email == payload["email"]:
                st.error("New email must be different from your current email.")
            elif email_exists(new_email):
                st.error("That email is already registered to another account.")
            else:
                otp = generate_otp()
                send_otp_email(new_email, otp)
                st.session_state.email_otp        = otp
                st.session_state.email_otp_time   = datetime.utcnow()
                st.session_state.pending_new_email = new_email
                st.session_state.email_otp_sent   = True
                st.success(f"✅ Verification code sent to {new_email}")
                st.rerun()

        if st.session_state.get("email_otp_sent"):
            divider_text("enter verification code")
            entered_otp = st.text_input("6-digit code", max_chars=6, placeholder="000000", key="email_otp_input")

            if st.button("Confirm Email Change →", use_container_width=True, key="confirm_email"):
                otp_time = st.session_state.get("email_otp_time")
                if not otp_time or datetime.utcnow() - otp_time > timedelta(minutes=10):
                    st.error("⏰ Verification code expired. Please request a new one.")
                    st.session_state.email_otp_sent = False
                    st.rerun()
                elif entered_otp != st.session_state.get("email_otp"):
                    st.error("Incorrect verification code.")
                else:
                    new_em = st.session_state.pending_new_email
                    old_em = payload["email"]
                    ok, msg = update_email(old_em, new_em)
                    if ok:
                        # Re-issue token with new email
                        st.session_state.token            = generate_token(new_em)
                        st.session_state.email_otp_sent   = False
                        st.session_state.email_otp        = None
                        st.session_state.pending_new_email = None
                        log_activity(new_em, "Profile", "Email Changed", f"{old_em} → {new_em}")
                        st.success("✅ Email updated! Your session has been refreshed.")
                        st.rerun()
                    else:
                        st.error(f"Update failed: {msg}")

    # ──────────────────────────────────────────────────
    # TAB 3: CHANGE PASSWORD  (OTP-verified)
    # ──────────────────────────────────────────────────
    with tab_pw:
        st.markdown("<br>", unsafe_allow_html=True)
        pw_stage = st.session_state.get("pw_change_stage", "form")

        # ── Stage 1: Current + New password entry ──
        if pw_stage == "form":
            old_password     = st.text_input("Current password",     type="password", key="prof_old_pw")
            new_password     = st.text_input("New password",         type="password",
                                             placeholder="Min. 8 chars, upper, lower, number", key="prof_new_pw")
            if new_password:
                st.markdown(pw_strength_html(new_password), unsafe_allow_html=True)
            confirm_password = st.text_input("Confirm new password", type="password", key="prof_conf_pw")
            st.markdown("<br>", unsafe_allow_html=True)

            if st.button("Send Verification Code →", use_container_width=True, key="prof_send_pw_otp"):
                current_user = get_user_by_email(payload["email"])
                error = False

                if not verify_text(old_password, current_user[3]):
                    st.error("Current password is incorrect."); error = True

                if not error:
                    strength, fb = check_password_strength(new_password)
                    if strength == "Weak":
                        st.error(f"Password too weak — {', '.join(fb)}"); error = True

                if not error and new_password != confirm_password:
                    st.error("New passwords do not match."); error = True

                if not error:
                    history = json.loads(current_user[8] or "[]")
                    for old_hash in history:
                        if verify_text(new_password, old_hash):
                            st.error("⚠️ You cannot reuse a previous password."); error = True; break

                if not error:
                    ok, msg = send_otp_styled(payload["email"])
                    if ok:
                        st.session_state.pending_new_pw    = new_password
                        st.session_state.pw_change_stage   = "otp"
                        st.success("✅ Verification code sent to " + payload["email"])
                        st.rerun()
                    else:
                        st.error(f"Could not send OTP: {msg}")

        # ── Stage 2: OTP verification ──
        elif pw_stage == "otp":
            st.markdown(f"""
            <div style="background:#111827;border:1px solid #1e293b;border-radius:10px;
                        padding:14px 16px;color:#94a3b8;font-size:13px;margin-bottom:16px;">
                📧 A verification code was sent to
                <strong style="color:#6366f1;">{payload["email"]}</strong>
            </div>
            """, unsafe_allow_html=True)

            divider_text("enter verification code")
            st.markdown("""
            <div style="background:#0a0e1a;border:1px solid #6366f1;border-radius:12px;
                        text-align:center;padding:16px;margin-bottom:16px;">
                <span style="color:#818cf8;font-size:13px;font-weight:600;
                             letter-spacing:1px;">CHECK YOUR INBOX</span>
            </div>
            """, unsafe_allow_html=True)

            entered = st.text_input("6-digit code", max_chars=6,
                                    placeholder="000000", key="pw_otp_field")
            st.markdown("<br>", unsafe_allow_html=True)

            if st.button("Confirm Password Change →", use_container_width=True, key="prof_confirm_pw"):
                valid, vmsg = otp_is_valid(entered, payload["email"])
                if valid:
                    new_password = st.session_state.get("pending_new_pw")
                    current_user = get_user_by_email(payload["email"])
                    new_hash     = hash_text(new_password)
                    history      = json.loads(current_user[8] or "[]")
                    history.insert(0, new_hash)
                    history = history[:PASSWORD_HISTORY_COUNT]
                    update_password(payload["email"], new_hash)
                    update_password_history(payload["email"], json.dumps(history))
                    log_activity(payload["email"], "Profile", "Password Changed", "OTP Verified")
                    clear_otp()
                    st.session_state.pw_change_stage = "form"
                    st.session_state.pending_new_pw  = None
                    st.session_state.token           = None
                    st.success("✅ Password updated! Please sign in again.")
                    time.sleep(1.5); go_to("Login")
                else:
                    st.error(f"Verification failed: {vmsg}")

            divider_text("")
            if st.button("← Start Over", use_container_width=True, key="pw_restart"):
                st.session_state.pw_change_stage = "form"
                st.session_state.pending_new_pw  = None
                clear_otp(); st.rerun()

# ============================================================
# PAGE: RAG SEARCH
# ============================================================
def rag_search_tab():
    render_sidebar()
    section_header("🔍", "RAG Policy Search", "Ask questions answered from your policy documents")
    st.markdown("---")

    payload = verify_token(st.session_state.token)
    if not payload:
        st.toast("Session expired", icon="❌"); go_to("Login"); return
    user_email = payload["email"]

    c1, c2 = st.columns([3, 1])
    with c1:
        target_lang = st.selectbox(
            "Response language:", 
            [
                "English", "Assamese", "Bengali", "Bhojpuri", "French", "German", 
                "Gujarati", "Hindi", "Japanese", "Kannada", "Kashmiri (Arabic)", 
                "Kashmiri (Devanagari)", "Maithili", "Malayalam", "Marathi", 
                "Meitei (Manipuri)", "Nepali", "Odia", "Punjabi", "Sanskrit", 
                "Santali", "Sindhi", "Tamil", "Telugu", "Urdu"
            ]
        )
    with c2:
        simplify = st.toggle("🧠 Simplify language")

    st.divider()

    for msg in st.session_state.rag_chat:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Ask a policy question..."):
        st.session_state.rag_chat.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Bi-Directional Vector Lookup & NLLB Extracting > Translating..."):
                t1 = time.time()
                ans, docs = nlp_engine.answer_policy_question(prompt, target_lang=target_lang, simplify=simplify)
                t2 = time.time()
                sources  = ", ".join(list(set([d["filename"] for d in docs]))) if docs else "None"
                final_txt = f"**{ans}**\n\n---\n*Inference: {round(t2-t1,2)}s | 📚 Sources: {sources}*"
                st.markdown(final_txt)
                log_activity(user_email, "RAG Search", prompt, final_txt)
                award_points(user_email, "rag_question")
                st.session_state.rag_chat.append({"role": "assistant", "content": final_txt})
                st.rerun()

    render_feedback_ui("RAG Search", "General Page Feedback", "rag_global")

# ============================================================
# PAGE: SUMMARIZATION
# ============================================================
def summarization_tab():
    render_sidebar()
    section_header("📝", "Document Summarizer", "Upload or paste a policy document to summarize")
    st.markdown("---")

    payload = verify_token(st.session_state.token)
    if not payload:
        st.toast("Session expired", icon="❌"); go_to("Login"); return
    user_email = payload["email"]

    col1, col2 = st.columns([1.4, 1])
    txt = ""

    with col1:
        uploaded_file = st.file_uploader("Upload Policy PDF or TXT", type=["pdf","txt"])
        if uploaded_file is not None:
            if uploaded_file.name.endswith(".pdf"):
                try:
                    reader = PyPDF2.PdfReader(uploaded_file)
                    for page in reader.pages:
                        txt += (page.extract_text() or "") + "\n"
                except:
                    pass
            else:
                txt = uploaded_file.read().decode("utf-8")
            st.success(f"✅ Loaded: {uploaded_file.name}")
        txt_area = st.text_area("Or paste policy text here:", value=txt, height=220)

    with col2:
        lang = st.selectbox(
            "Summary language:", 
            [
                "English", "Assamese", "Bengali", "Bhojpuri", "French", "German", 
                "Gujarati", "Hindi", "Japanese", "Kannada", "Kashmiri (Arabic)", 
                "Kashmiri (Devanagari)", "Maithili", "Malayalam", "Marathi", 
                "Meitei (Manipuri)", "Nepali", "Odia", "Punjabi", "Sanskrit", 
                "Santali", "Sindhi", "Tamil", "Telugu", "Urdu"
            ]
        )
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Generate Summary →", use_container_width=True) and txt_area.strip():
            with st.spinner("Summarizing..."):
                summary = nlp_engine.summarize_document(txt_area[:3000], target_lang=lang)
                st.session_state.summary  = summary
                st.session_state.doc_text = txt_area
                st.session_state.doc_answer = ""
                log_activity(user_email, "Summarization", f"Language:{lang}", summary)
                award_points(user_email, "summarize")

    if st.session_state.summary:
        st.markdown(f"""
        <div style="background:#111827;border:1px solid #1e293b;border-radius:12px;
                    padding:20px;margin-top:8px;">
            <div style="color:#6366f1;font-size:11px;font-weight:600;
                        text-transform:uppercase;letter-spacing:1px;margin-bottom:10px;">
                Policy Summary Breakdown
            </div>
            <div style="color:#e2e8f0;font-size:14px;line-height:1.8;white-space:pre-wrap;">
                {st.session_state.summary}
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("❓ Ask Questions About This Document")
        question = st.text_input("Ask a question from the uploaded document")
        if st.button("Get Answer", use_container_width=True) and question:
            with st.spinner("Analyzing document..."):
                context = st.session_state.doc_text[:2000]
                prompt  = f"Context:\n{context}\n\nQuestion: {question}\n\nAnswer based only on the context."
                answer  = nlp_engine.generate_english_response(prompt)
                st.session_state.doc_answer = answer

        if st.session_state.doc_answer:
            st.markdown(f"""
            <div class="pn-card" style="border-left:4px solid #6366f1;">
                <div style="color:#e2e8f0;font-size:14px;line-height:1.6;">
                    {st.session_state.doc_answer}
                </div>
            </div>
            """, unsafe_allow_html=True)

    render_feedback_ui("Summarization", "General Page Feedback", "sum_global")

# ============================================================
# PAGE: KNOWLEDGE GRAPH
# ============================================================
def graph_tab():
    render_sidebar()
    section_header("🕸️", "Knowledge Graph", "Named entity graph extracted from your policy documents")
    st.markdown("---")

    payload = verify_token(st.session_state.token)
    if not payload:
        st.toast("Session expired", icon="❌"); go_to("Login"); return
    user_email = payload["email"]

    docs = vector_store.get_all_documents()

    k1, k2, k3 = st.columns(3)
    kpi_card(k1, "📂", "Documents Indexed",    len(docs),                 "#6366f1")
    kpi_card(k2, "🕸️", "Graph Type",           "Policy Entity Network",   "#0ea5e9")
    kpi_card(k3, "🧠", "NER Engine",            "spaCy",                   "#10b981")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="background:#111827;border:1px solid #1e293b;border-radius:10px;padding:14px 18px;margin-bottom:16px;">
        <div style="color:#64748b;font-size:12px;font-weight:600;margin-bottom:8px;">Graph Legend</div>
        <div style="display:flex;gap:16px;flex-wrap:wrap;font-size:13px;color:#94a3b8;">
            <span>🟦 Document</span>
            <span>🟢 Organization</span>
            <span>🩷 Person</span>
            <span>🟠 Law / Policy</span>
            <span>🟡 Location</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if not docs:
        st.markdown("""
        <div style="background:#111827;border:1px dashed #1e293b;border-radius:14px;
                    padding:40px;text-align:center;">
            <div style="font-size:36px;margin-bottom:12px;">📂</div>
            <div style="color:#475569;font-size:14px;">No documents in the vector store yet.</div>
        </div>
        """, unsafe_allow_html=True)
        return

    if st.button("🔄 Generate Interactive Graph →", use_container_width=True):
        with st.spinner("Building knowledge graph..."):
            path = knowledge_graph.generate_interactive_graph(docs, force_rebuild=True)
            if path:
                with open(path, "r", encoding="utf-8") as f:
                    components.html(f.read(), height=650)
                log_activity(user_email, "Knowledge Graph", "Generated Graph", "Success")
            else:
                st.error("Graph generation failed — check spaCy is loaded.")

    render_feedback_ui("Knowledge Graph", "General Page Feedback", "kg_global")

# ============================================================
# PAGE: ACTIVITY HISTORY
# ============================================================
def overall_history_tab():
    render_sidebar()
    section_header("📜", "Activity History", "All your RAG searches, summaries and analyses")
    st.markdown("---")

    payload = verify_token(st.session_state.token)
    if not payload:
        st.toast("Session expired", icon="❌"); go_to("Login"); return

    activities = get_user_activity(payload["email"])
    if not activities:
        st.markdown("""
        <div style="background:#111827;border:1px dashed #1e293b;border-radius:14px;
                    padding:40px;text-align:center;">
            <div style="font-size:36px;margin-bottom:12px;">📭</div>
            <div style="color:#475569;font-size:14px;">No activity yet.</div>
            <div style="color:#334155;font-size:12px;margin-top:6px;">
                Use RAG Search or Summarize to see your history here.
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    from html import escape

    rows_html = []
    type_colors = {
        "RAG Search": "#6366f1", "Summarization": "#0ea5e9",
        "Readability": "#10b981", "Knowledge Graph": "#f59e0b",
    }
    for app, user_inp, ai_out, ts in activities:
        accent  = type_colors.get(app, "#6366f1")
        preview = str(ai_out).strip()
        trunc   = (preview[:140] + "…") if len(preview) > 140 else preview
        rows_html.append(
            f"<tr>"
            f"<td><span style='background:{accent}22;color:{accent};font-size:11px;"
            f"font-weight:600;padding:3px 10px;border-radius:20px;'>{escape(str(app))}</span></td>"
            f"<td>{escape(str(user_inp))}</td>"
            f"<td><div class='ai-output-cell'><span class='ai-output-preview'>{escape(trunc)}</span>"
            f"<div class='hover-card'><div class='hover-content'>{escape(preview)}</div></div></div></td>"
            f"<td style='color:#475569;'>{escape(str(ts))}</td>"
            f"</tr>"
        )

    table_html = (
        "<div class='history-table'>"
        "<table>"
        "<thead><tr><th>Section</th><th>Your Input</th><th>↓ AI Output</th><th>Timestamp</th></tr></thead>"
        f"<tbody>{''.join(rows_html)}</tbody>"
        "</table>"
        "</div>"
    )
    st.markdown(table_html, unsafe_allow_html=True)


# ============================================================
# PAGE: RESET PASSWORD (logged-in)
# ============================================================
def reset_page():
    render_sidebar()
    section_header("🔒", "Reset Password", "Update your account password")
    st.markdown("---")

    payload = verify_token(st.session_state.token)
    if not payload:
        st.toast("Session expired", icon="❌"); go_to("Login"); return

    user = get_user_by_email(payload["email"])

    old_password     = st.text_input("Old Password",         type="password")
    new_password     = st.text_input("New Password",         type="password")
    confirm_password = st.text_input("Confirm New Password", type="password")
    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("Update Password →", use_container_width=True):
        error = False
        if not verify_text(old_password, user[3]):
            st.error("Old password incorrect."); error = True
        if new_password != confirm_password:
            st.error("New passwords do not match."); error = True
        history = json.loads(user[8] or "[]")
        if not error:
            for old_hash in history:
                if verify_text(new_password, old_hash):
                    st.error("⚠️ Cannot reuse old password."); error = True; break
        if not error:
            new_hash = hash_text(new_password)
            history.insert(0, new_hash)
            history = history[:PASSWORD_HISTORY_COUNT]
            update_password(payload["email"], new_hash)
            update_password_history(payload["email"], json.dumps(history))
            st.success("✅ Password updated!")
            st.session_state.token = None
            time.sleep(1); go_to("Login")

# ============================================================
# PAGE: READABILITY
# ============================================================
def readability_page():
    render_sidebar()

    section_header("📖", "Readability Analyzer", "Measure how accessible your policy text is")
    st.markdown("---")

    payload = verify_token(st.session_state.token)
    if not payload:
        st.toast("Session expired", icon="❌"); go_to("Login"); return
    user_email = payload["email"]

    tab1, tab2 = st.tabs(["✍️  Paste Text", "📂  Upload File"])
    text = ""

    with tab1:
        text = st.text_area("Paste your policy text here (minimum 50 characters):", height=200)

    with tab2:
        uploaded_file = st.file_uploader("Upload TXT or PDF", type=["txt","pdf"])
        if uploaded_file:
            if uploaded_file.type == "text/plain":
                text = uploaded_file.read().decode("utf-8")
            elif uploaded_file.type == "application/pdf":
                pdf_reader = PyPDF2.PdfReader(uploaded_file)
                for page in pdf_reader.pages:
                    text += page.extract_text() or ""
            st.info(f"✅ Loaded: {uploaded_file.name}")

    if st.button("Analyze →", use_container_width=True):
        if not text.strip():
            st.error("⚠️ No text found to analyze."); return

        award_points(user_email, "readability")
        analyzer = ReadabilityAnalyzer(text)
        metrics  = analyzer.get_all_metrics()
        avg      = metrics["Overall Grade Level"]

        if   avg <= 6:  level, accent = "Beginner",        "#34d399"
        elif avg <= 10: level, accent = "Intermediate",     "#38bdf8"
        elif avg <= 14: level, accent = "Advanced",         "#fbbf24"
        else:           level, accent = "Expert/Academic",  "#f87171"

        st.markdown(f"""
        <div style="background:#111827;border:1px solid {accent};border-radius:14px;
                    padding:24px;text-align:center;margin-bottom:24px;
                    box-shadow:0 0 30px {accent}18;">
            <div style="color:{accent};font-size:13px;font-weight:600;
                        text-transform:uppercase;letter-spacing:1px;">Overall Readability Level</div>
            <div style="color:{accent};font-size:36px;font-weight:700;margin:8px 0;">{level}</div>
            <div style="color:#475569;font-size:14px;">Approximate Grade Level: {int(avg)}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("#### Text Statistics")
        c1,c2,c3,c4,c5 = st.columns(5)
        for col, label, val in [
            (c1, "Sentences",     metrics["Total Sentences"]),
            (c2, "Words",         metrics["Total Words"]),
            (c3, "Syllables",     metrics["Total Syllables"]),
            (c4, "Complex Words", metrics["Complex Words"]),
            (c5, "Characters",    metrics["Total Characters"]),
        ]:
            col.metric(label, val)

        st.markdown("#### Metric Breakdown")
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(create_gauge(metrics["Flesch Reading Ease"],  "Flesch Reading Ease",  0, 100, "#6366f1"),  use_container_width=True)
            st.plotly_chart(create_gauge(metrics["SMOG Index"],           "SMOG Index",           0, 20,  "#f59e0b"),  use_container_width=True)
            st.plotly_chart(create_gauge(metrics["Coleman-Liau"],         "Coleman-Liau Index",   0, 20,  "#ec4899"),  use_container_width=True)
        with col2:
            st.plotly_chart(create_gauge(metrics["Flesch-Kincaid Grade"], "Flesch-Kincaid Grade", 0, 20,  "#0ea5e9"),  use_container_width=True)
            st.plotly_chart(create_gauge(metrics["Gunning Fog"],          "Gunning Fog",          0, 20,  "#10b981"),  use_container_width=True)
    st.markdown("<br><br>", unsafe_allow_html=True)
    render_feedback_ui("Readability", text, "readability_feedback_key")

# ============================================================
# ADMIN DASHBOARD  — team's full logic, Junaid's styles applied
# ============================================================
def admin_dashboard():
    # ── Sidebar ──
    with st.sidebar:
        st.markdown("""
        <div style="padding:16px 8px 8px;text-align:center;">
            <div style="font-size:28px;">⚡</div>
            <div style="font-weight:700;font-size:16px;color:#f1f5f9;margin:4px 0;">PolicyNav</div>
            <div style="font-size:11px;color:#475569;">Admin Dashboard</div>
        </div>
        <hr style="border-color:#1e293b;margin:12px 0;">
        """, unsafe_allow_html=True)

        # Show admin identity chip
        payload_sb = verify_token(st.session_state.token) if st.session_state.token else None
        if payload_sb:
            adm_email = payload_sb["email"]
            adm_init  = adm_email[:2].upper()
            st.markdown(f"""
            <div style="background:#1e293b;border-radius:12px;padding:12px 14px;
                        display:flex;align-items:center;gap:12px;margin-bottom:12px;">
                <div style="background:#6366f1;border-radius:50%;width:36px;height:36px;
                            display:flex;align-items:center;justify-content:center;
                            font-weight:700;font-size:13px;color:white;flex-shrink:0;">
                    {adm_init}
                </div>
                <div style="overflow:hidden;">
                    <div style="font-weight:600;font-size:13px;color:#e2e8f0;">Admin 👑</div>
                    <div style="font-size:11px;color:#475569;white-space:nowrap;
                                overflow:hidden;text-overflow:ellipsis;">{adm_email}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        selected = option_menu(
            				menu_title=None,
            				options=["View Users", "Pending Registrations", "Security Monitor", "User Activity",
                     				"Analytics Dashboard", "Broadcasts", "Feedback Analysis", "Logout"],
           				 icons=["people", "hourglass-split", "shield-lock", "clock-history",
                   				"bar-chart", "megaphone", "chat-dots", "box-arrow-right"],
            				default_index=0,
               styles={
                  "container":         {"padding": "0!important", "background-color": "#080c18"},
                  "icon":              {"color": "#6366f1", "font-size": "15px"},
                  "nav-link":          {"color": "#64748b", "font-size": "14px",
                                      "font-family": "Inter", "border-radius": "8px",
                                      "margin": "2px 0", "padding": "10px 14px"},
                  "nav-link-selected": {"background-color": "#1e293b", "color": "#e2e8f0",
                                       "font-weight": "600"},
            }
        )
        st.markdown("<hr style='border-color:#1e293b;margin:12px 0;'>", unsafe_allow_html=True)
        st.markdown("""
        <div style="text-align:center;padding:8px 0 0;color:#1e293b;font-size:11px;">
            PolicyNav v1.0 · 2026
        </div>
        """, unsafe_allow_html=True)

        if selected == "Logout":
            st.session_state.token = None; go_to("Login")

    # ── Header + KPI row (always visible) ──
    section_header("🛡️", "Admin Control Panel", "Manage users, monitor security & activity")
    st.markdown("---")

    users = get_all_users()

    conn_kpi    = get_connection()
    cursor_kpi  = conn_kpi.cursor()
    cursor_kpi.execute("SELECT COUNT(*) FROM activity_log")
    total_acts  = cursor_kpi.fetchone()[0]
    cursor_kpi.execute("SELECT COUNT(*) FROM feedback")
    total_fb    = cursor_kpi.fetchone()[0]
    conn_kpi.close()

    locked_count = sum(
        1 for u in users
        if u[3] and datetime.utcnow() < datetime.fromisoformat(u[3])
    )

    k1,k2,k3,k4 = st.columns(4)
    kpi_card(k1, "👥", "Total Users",       len(users),    "#6366f1")
    kpi_card(k2, "🔒", "Locked Accounts",   locked_count,  "#f59e0b")
    kpi_card(k3, "📋", "Total Activities",  total_acts,    "#0ea5e9")
    kpi_card(k4, "📢", "Feedback Entries",  total_fb,      "#10b981")
    st.markdown("<br>", unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════
    # VIEW USERS
    # ════════════════════════════════════════════════════════
    if selected == "Pending Registrations":
        section_header("⏳", "Pending Registrations", "Re-registration requests from previously deleted accounts")
        st.markdown("<br>", unsafe_allow_html=True)

        pending = get_pending_registrations()
        if not pending:
            st.markdown("""
            <div style="text-align:center;padding:40px;background:#111827;
                        border:1px dashed #1e293b;border-radius:14px;">
                <div style="font-size:36px;margin-bottom:12px;">✅</div>
                <div style="color:#475569;font-size:14px;">No pending registration requests.</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info(f"⚠️ {len(pending)} pending registration request(s) need your review.")
            for row in pending:
                _, uname, uemail, _, _, _, req_at = row
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.markdown(f"""
                    <div class="pn-card" style="border-left:4px solid #f59e0b;margin-bottom:8px;">
                        <div style="display:flex;justify-content:space-between;align-items:center;">
                            <div>
                                <div style="font-weight:600;color:#e2e8f0;">{uname}</div>
                                <div style="color:#94a3b8;font-size:13px;">{uemail}</div>
                                <div style="color:#475569;font-size:11px;margin-top:4px;">Requested: {req_at[:16]}</div>
                            </div>
                            <span style="background:#451a03;color:#f59e0b;font-size:11px;
                                         padding:4px 12px;border-radius:20px;font-weight:600;">
                                🗑️ Previously Deleted
                            </span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                with col_b:
                    ap_col, re_col = st.columns(2)
                    if ap_col.button("✅ Approve", key=f"approve_{uemail}", use_container_width=True):
                        ok, msg = approve_pending_registration(uemail)
                        if ok:
                            send_admin_action_email(uemail,
                                "✅ Your PolicyNav registration has been approved by the admin. You can now sign in.")
                            st.success(f"Approved: {uemail}")
                            st.rerun()
                        else:
                            st.error(f"Error: {msg}")
                    if re_col.button("❌ Reject", key=f"reject_{uemail}", use_container_width=True):
                        reject_pending_registration(uemail)
                        send_admin_action_email(uemail,
                            "❌ Your PolicyNav re-registration request was rejected by the admin.")
                        st.warning(f"Rejected: {uemail}")
                        st.rerun()

    elif selected == "View Users":
        section_header("👥", "User Management", "All registered users")
        st.markdown("<br>", unsafe_allow_html=True)

        if not users:
            st.markdown("""
            <div style="background:#111827;border:1px dashed #1e293b;border-radius:14px;
                        padding:40px;text-align:center;">
                <div style="font-size:36px;margin-bottom:12px;">👤</div>
                <div style="color:#475569;font-size:14px;">No users found.</div>
            </div>
            """, unsafe_allow_html=True)
            return

        # Column headers
        h1,h2,h3,h4,h5,h6 = st.columns([0.4, 0.6, 1.5, 2.2, 1, 2])
        for col, lbl in zip([h1,h2,h3,h4,h5,h6], ["#","STATUS","USERNAME","EMAIL","ROLE","ACTIONS"]):
            col.markdown(
                f"<div style='font-size:11px;font-weight:600;color:#475569;text-transform:uppercase;"
                f"letter-spacing:0.5px;padding:8px 4px;background:#0f172a;border-radius:4px;'>{lbl}</div>",
                unsafe_allow_html=True
            )

        for idx, u in enumerate(users, 1):
            username, email, failed_attempts, lock_until, avatar_path, is_admin = u[0],u[1],u[2],u[3],u[4],u[5]
            is_locked_now = bool(lock_until and datetime.utcnow() < datetime.fromisoformat(lock_until))
            role_badge = (
                "<span style='background:#6366f122;color:#6366f1;font-size:11px;"
                "font-weight:600;padding:3px 10px;border-radius:20px;'>👑 Admin</span>"
                if is_admin else
                "<span style='background:#0ea5e922;color:#0ea5e9;font-size:11px;"
                "font-weight:600;padding:3px 10px;border-radius:20px;'>User</span>"
            )
            lock_badge = (
                " <span style='background:#f59e0b22;color:#f59e0b;font-size:10px;"
                "padding:2px 7px;border-radius:20px;'>🔒 Locked</span>"
                if is_locked_now else ""
            )

            is_online_now = bool(u[6]) if len(u) > 6 else False
            last_seen_str = u[7][:16].replace("T"," ") if len(u) > 7 and u[7] else "Never"
            online_dot = (
                "<span style='display:inline-block;width:10px;height:10px;background:#22c55e;"
                "border-radius:50%;margin:auto;' title='Online'></span>"
                if is_online_now else
                f"<span style='display:inline-block;width:10px;height:10px;background:#475569;"
                f"border-radius:50%;margin:auto;' title='Last seen {last_seen_str}'></span>"
            )
            # Avatar or initials
            av_path = avatar_path
            if av_path and os.path.exists(av_path):
                import base64 as _b64
                with open(av_path,"rb") as _f:
                    _b64data = _b64.b64encode(_f.read()).decode()
                _ext = av_path.split(".")[-1]
                dp_html = f"<img src='data:image/{_ext};base64,{_b64data}' style='width:32px;height:32px;border-radius:50%;object-fit:cover;'/>"
            else:
                dp_html = (f"<div style='background:#6366f1;border-radius:50%;width:32px;height:32px;"
                           f"display:flex;align-items:center;justify-content:center;font-size:12px;"
                           f"font-weight:700;color:white;'>{username[:2].upper()}</div>")

            c1,c2,c3,c4,c5,c6 = st.columns([0.4, 0.6, 1.5, 2.2, 1, 2])
            c1.markdown(f"<div style='color:#475569;padding:10px 0;font-size:13px;'>{idx}</div>", unsafe_allow_html=True)
            c2.markdown(f"<div style='padding:8px 0;text-align:center;'>{online_dot}<br>{dp_html}</div>", unsafe_allow_html=True)
            c3.markdown(f"<div style='color:#e2e8f0;font-weight:500;padding:10px 0;'>{username}</div>", unsafe_allow_html=True)
            c4.markdown(f"<div style='color:#94a3b8;padding:10px 0;font-size:13px;'>{email}{lock_badge}</div>", unsafe_allow_html=True)
            c5.markdown(f"<div style='padding:6px 0;'>{role_badge}</div>", unsafe_allow_html=True)

            with c6:
                ba, bb, bc, bd = st.columns(4)
                if is_admin:
                    if ba.button("⬇️", key=f"demote_{email}", help="Remove Admin",  use_container_width=True):
                        remove_admin_status(email)
                        send_admin_action_email(email, "Your Admin status has been removed in PolicyNav.")
                        st.toast(f"Admin removed: {email}"); st.rerun()
                else:
                    if ba.button("⬆️", key=f"promote_{email}", help="Promote to Admin", use_container_width=True):
                        promote_user_to_admin(email)
                        send_admin_action_email(email, "Your account has been promoted to Admin in PolicyNav.")
                        st.toast(f"Promoted: {email}"); st.rerun()

                if is_locked_now:
                    if bb.button("🔓", key=f"unlock_{email}", help="Unlock Account", use_container_width=True):
                        update_login_attempts(email, 0, None)
                        send_admin_action_email(email, "Your account has been unlocked by an administrator.")
                        st.toast(f"Unlocked: {email}"); st.rerun()
                else:
                    if bb.button("🔒", key=f"lock_{email}", help="Lock Account", use_container_width=True):
                        lock_time = datetime.utcnow() + timedelta(days=1)
                        update_login_attempts(email, 999, lock_time.isoformat())
                        send_admin_action_email(email, "Your account has been locked by an administrator.")
                        st.toast(f"Locked: {email}"); st.rerun()

                if bc.button("🗑️", key=f"del_{email}", help="Delete User", use_container_width=True):
                    send_admin_action_email(email, "Your PolicyNav account has been deleted by an administrator.")
                    delete_user(email)
                    st.toast(f"Deleted: {email}"); st.rerun()

            st.markdown("<div style='border-bottom:1px solid #1e293b;margin:2px 0;'></div>", unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════
    # SECURITY MONITOR
    # ════════════════════════════════════════════════════════
    elif selected == "Security Monitor":
        section_header("🔒", "Security Monitor", "Login attempts and account lock status")
        st.markdown("<br>", unsafe_allow_html=True)

        suspicious = [u for u in users if u[2] and u[2] > 0]  # failed_attempts > 0

        if not suspicious:
            st.markdown("""
            <div style="text-align:center;padding:40px;background:#111827;
                        border:1px dashed #1e293b;border-radius:14px;">
                <div style="font-size:36px;margin-bottom:12px;">✅</div>
                <div style="font-size:15px;color:#475569;">No suspicious login activity detected.</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Header
            hh1,hh2,hh3,hh4 = st.columns([2.5, 0.8, 1.5, 1.2])
            for col, lbl in zip([hh1,hh2,hh3,hh4], ["EMAIL","ATTEMPTS","LOCKED UNTIL","STATUS"]):
                col.markdown(
                    f"<div style='font-size:11px;font-weight:600;color:#475569;text-transform:uppercase;"
                    f"letter-spacing:0.5px;padding:8px 4px;background:#0f172a;border-radius:4px;'>{lbl}</div>",
                    unsafe_allow_html=True
                )

            for u in users:
                username, email, failed_attempts, lock_until, avatar_path, is_admin = u[0],u[1],u[2],u[3],u[4],u[5]
                if not failed_attempts:
                    continue
                is_locked_now = bool(lock_until and datetime.utcnow() < datetime.fromisoformat(lock_until))
                att_color     = "#f87171" if failed_attempts >= MAX_LOGIN_ATTEMPTS else "#fbbf24" if failed_attempts > 0 else "#94a3b8"
                status_html   = (
                    "<span style='background:#451a03;color:#f59e0b;font-size:11px;"
                    "padding:3px 10px;border-radius:20px;font-weight:600;'>🔒 Locked</span>"
                    if is_locked_now else
                    "<span style='background:#052e16;color:#34d399;font-size:11px;"
                    "padding:3px 10px;border-radius:20px;font-weight:600;'>✓ Active</span>"
                )
                lock_str = lock_until[:16].replace("T"," ") if lock_until else "—"

                cc1,cc2,cc3,cc4 = st.columns([2.5, 0.8, 1.5, 1.2])
                cc1.markdown(f"<div style='color:#94a3b8;padding:10px 0;font-size:13px;'>{email}</div>", unsafe_allow_html=True)
                cc2.markdown(f"<div style='color:{att_color};font-weight:700;font-size:16px;padding:8px 0;'>{failed_attempts}</div>", unsafe_allow_html=True)
                cc3.markdown(f"<div style='color:#475569;font-size:12px;padding:10px 0;'>{lock_str}</div>", unsafe_allow_html=True)
                cc4.markdown(status_html, unsafe_allow_html=True)
                st.markdown("<div style='border-bottom:1px solid #1e293b;margin:2px 0;'></div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔓  Clear All Lockouts", use_container_width=True):
            conn_cl = get_connection()
            conn_cl.cursor().execute("UPDATE users SET failed_attempts=0, lock_until=NULL")
            conn_cl.commit(); conn_cl.close()
            st.success("All lockouts cleared."); st.rerun()

    # ════════════════════════════════════════════════════════
    # USER ACTIVITY
    # ════════════════════════════════════════════════════════
    elif selected == "User Activity":
        section_header("🔍", "User Activity Log", "Per-user AI interaction history (including deleted accounts)")
        st.markdown("<br>", unsafe_allow_html=True)

        # All logs tab + per-user tab
        tab_all, tab_user = st.tabs(["📋 All Logs (incl. deleted)", "👤 Per-User Logs"])

        type_colors = {
            "RAG Search": "#6366f1", "Summarization": "#0ea5e9",
            "Readability": "#10b981", "Knowledge Graph": "#f59e0b",
            "Scheme Advisor": "#8b5cf6", "Admin Login": "#f43f5e",
        }

        with tab_all:
            all_logs = get_all_activity_logs()
            if not all_logs:
                st.info("No activity logs found.")
            else:
                import pandas as _pd
                df_all = _pd.DataFrame(all_logs,
                    columns=["Email","Section","Input","Output","Timestamp","Is Deleted"])
                df_all["Account"] = df_all["Is Deleted"].apply(
                    lambda x: "🗑️ Deleted" if x else "✅ Active")

                # Download button
                csv_all = df_all.drop(columns=["Is Deleted"]).to_csv(index=False).encode("utf-8")
                st.download_button("⬇️ Download All Logs CSV", csv_all,
                                   "all_activity_logs.csv", "text/csv", use_container_width=True)
                st.markdown("<br>", unsafe_allow_html=True)

                for row in all_logs:
                    em, sec, inp, out, ts, is_del = row
                    accent = type_colors.get(sec, "#6366f1")
                    del_badge = (" <span style='background:#450a0a;color:#f87171;font-size:10px;"
                                 "padding:2px 7px;border-radius:10px;'>🗑️ Deleted Account</span>"
                                 if is_del else "")
                    st.markdown(f"""
                    <div class="pn-card" style="margin-bottom:8px;border-left:4px solid {accent};">
                        <div style="display:flex;justify-content:space-between;margin-bottom:8px;flex-wrap:wrap;gap:4px;">
                            <div>
                                <span style="background:{accent}22;color:{accent};font-size:11px;
                                     font-weight:600;padding:3px 10px;border-radius:20px;">{sec}</span>
                                <span style="color:#64748b;font-size:12px;margin-left:8px;">{em}{del_badge}</span>
                            </div>
                            <span style="color:#475569;font-size:11px;">{ts}</span>
                        </div>
                        <div style="color:#94a3b8;font-size:12px;margin-bottom:4px;">
                            <strong style="color:#64748b;">Input:</strong> {str(inp)[:150]}
                        </div>
                        <div style="color:#94a3b8;font-size:12px;">
                            <strong style="color:#64748b;">Output:</strong> {str(out)[:200]}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

        with tab_user:
            # Include deleted account emails too
            active_emails = [u[1] for u in users]
            conn_del = get_connection()
            del_emails = [r[0] for r in conn_del.execute("SELECT email FROM deleted_accounts").fetchall()]
            conn_del.close()
            all_emails = active_emails + [f"🗑️ {e}" for e in del_emails]

            sel_raw = st.selectbox("Select user / deleted account", all_emails)
            sel_email = sel_raw.replace("🗑️ ", "")

            if st.button("Load Activity →", use_container_width=True):
                acts = get_user_activity(sel_email)
                if not acts:
                    st.markdown("""
                    <div style="text-align:center;padding:32px;background:#111827;
                                border:1px dashed #1e293b;border-radius:14px;">
                        <div style="font-size:32px;margin-bottom:10px;">📭</div>
                        <div style="color:#475569;font-size:14px;">No activity found for this user.</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    import pandas as _pd2
                    df_u = _pd2.DataFrame(acts, columns=["Section","Input","Output","Timestamp"])
                    csv_u = df_u.to_csv(index=False).encode("utf-8")
                    safe_name = sel_email.replace("@","_at_").replace(".","_")
                    st.download_button(f"⬇️ Download {sel_email} History CSV",
                                       csv_u, f"history_{safe_name}.csv",
                                       "text/csv", use_container_width=True)
                    st.markdown("<br>", unsafe_allow_html=True)

                    for app_sec, user_inp, ai_out, ts in acts:
                        accent = type_colors.get(app_sec, "#6366f1")
                        st.markdown(f"""
                        <div class="pn-card" style="margin-bottom:8px;border-left:4px solid {accent};">
                            <div style="display:flex;justify-content:space-between;margin-bottom:8px;">
                                <span style="background:{accent}22;color:{accent};font-size:11px;
                                             font-weight:600;padding:3px 10px;border-radius:20px;">{app_sec}</span>
                                <span style="color:#475569;font-size:11px;">{ts}</span>
                            </div>
                            <div style="color:#94a3b8;font-size:12px;margin-bottom:6px;">
                                <strong style="color:#64748b;">Input:</strong> {str(user_inp)[:150]}
                            </div>
                            <div style="color:#94a3b8;font-size:12px;">
                                <strong style="color:#64748b;">Output:</strong> {str(ai_out)[:250]}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════
    # ANALYTICS DASHBOARD
    # ════════════════════════════════════════════════════════
    elif selected == "Analytics Dashboard":
        section_header("📊", "Analytics Dashboard", "Live platform analytics · auto-refreshes every 20s")
        st_autorefresh(interval=20000)

        conn_an = get_connection()
        df      = pd.read_sql_query("SELECT * FROM activity_log", conn_an)
        conn_an.close()

        if df.empty:
            st.markdown("""
            <div style="text-align:center;padding:40px;background:#111827;
                        border:1px dashed #1e293b;border-radius:14px;">
                <div style="font-size:36px;margin-bottom:12px;">📊</div>
                <div style="color:#475569;font-size:14px;">No activity data available yet.</div>
            </div>
            """, unsafe_allow_html=True)
            return

        df["created_at"] = pd.to_datetime(df["created_at"])

        st.sidebar.subheader("Filter Data")
        feature_filter = st.sidebar.multiselect(
            "Select Features", df["app_section"].unique(), default=df["app_section"].unique()
        )
        df = df[df["app_section"].isin(feature_filter)]

        a1, a2, a3 = st.columns(3)
        kpi_card(a1, "📋", "Total Activities", len(df),                      "#6366f1")
        kpi_card(a2, "👥", "Unique Users",      df["user_email"].nunique(),   "#0ea5e9")
        kpi_card(a3, "🧩", "Features Used",     df["app_section"].nunique(),  "#10b981")
        st.markdown("<br>", unsafe_allow_html=True)

        # Feature popularity
        feature_counts = df["app_section"].value_counts().reset_index()
        feature_counts.columns = ["Feature","Usage"]
        fig1 = px.bar(feature_counts, x="Feature", y="Usage", text="Usage",
                      color="Feature", title="Feature Usage Distribution")
        fig1.update_layout(paper_bgcolor="#111827", plot_bgcolor="#111827",
                           font={"color":"#94a3b8","family":"Inter"})
        st.plotly_chart(fig1, use_container_width=True)

        col_l, col_r = st.columns(2)

        # Language distribution
        with col_l:
            from langdetect import detect
            SUPPORTED_LANGS = {"en","hi","ta","te","kn","mr","bn"}

            def detect_lang(text):
                try:
                    text = str(text).strip()

                    if len(text) < 10:
                        return "en"

                    detected = detect(text)

                    # allow only supported languages
                    if detected not in SUPPORTED_LANGS:
                        return "en"

                    return detected

                except:
                    return "en"
            lang_map = {
                "en": "English",
                "hi": "Hindi",
                "ta": "Tamil",
                "te": "Telugu",
                "kn": "Kannada",
                "mr": "Marathi",
                "bn": "Bengali",
                "ro": "Romanian",
                "sl": "Slovenian",
                "fr": "French",
                "de": "German",
                "es": "Spanish",
                "unknown": "Unknown"
            }
            df["language"] = df["user_input"].str.extract(r'Language:(\w+)')
            df["language"] = df["language"].fillna("English")
            # df["language"] = df["language_code"].map(lang_map).fillna(df["language_code"])
            lang_counts = df["language"].value_counts().reset_index()
            lang_counts.columns = ["Language","Count"]
            fig2 = px.pie(lang_counts, values="Count", names="Language",
                          title="User Language Distribution", hole=0.6)
            fig2.update_traces(
                textinfo="percent+label",
                textposition="inside",
                hovertemplate="<b>%{label}</b><br>Users: %{value}<extra></extra>"
            )
            fig2.update_layout(paper_bgcolor="#111827", font={"color":"#94a3b8","family":"Inter"})
            st.plotly_chart(fig2, use_container_width=True)

        # AI Model Usage
        with col_r:

            MODEL_ID = "Qwen/Qwen2.5-1.5B-Instruct"
            TRANSLATOR_ID = "facebook/nllb-200-distilled-600M"

            # Count approximate usage
            qwen_calls = df["app_section"].isin(["RAG Search","Summarization","Scheme Advisor"]).sum()

            translator_calls = df["app_section"].isin(["RAG Search"]).sum()

            model_data = pd.DataFrame({
                "Model":[MODEL_ID, TRANSLATOR_ID],
                "Calls":[qwen_calls, translator_calls]
            })

            fig3 = px.bar(
                model_data,
                x="Model",
                y="Calls",
                text="Calls",
                title="AI Model Usage"
            )

            fig3.update_layout(
                paper_bgcolor="#111827",
                plot_bgcolor="#111827",
                font={"color":"#94a3b8","family":"Inter"}
            )

            st.plotly_chart(fig3, use_container_width=True)

        # Daily activity trend
        activity = df.groupby(df["created_at"].dt.date).size().reset_index(name="count")
        fig4 = px.line(activity, x="created_at", y="count",
                       markers=True, title="Daily Platform Activity")
        fig4.update_layout(paper_bgcolor="#111827", plot_bgcolor="#111827",
                           font={"color":"#94a3b8","family":"Inter"})
        st.plotly_chart(fig4, use_container_width=True)

        # Top users
        st.markdown("""
        <div style="font-size:15px;font-weight:600;color:#e2e8f0;margin-bottom:14px;">
            🏆 Top 10 Active Users
        </div>
        """, unsafe_allow_html=True)
        user_activity = df["user_email"].value_counts().reset_index()
        user_activity.columns = ["User Email","Activity Count"]
        top_users = user_activity.head(10)
        fig5 = px.funnel(top_users, x="Activity Count", y="User Email",
                         orientation="h", text="Activity Count",
                         color="Activity Count", title="Most Active Users")
        fig5.update_traces(texttemplate="%{x}")
        fig5.update_layout(paper_bgcolor="#111827", font={"color":"#94a3b8","family":"Inter"})
        st.plotly_chart(fig5, use_container_width=True)

        # Leaderboard table
        for i, row in top_users.iterrows():
            medal = ["🥇","🥈","🥉"][i] if i < 3 else f"#{i+1}"
            st.markdown(f"""
            <div style="background:#111827;border:1px solid #1e293b;border-radius:10px;
                        padding:10px 16px;margin-bottom:6px;display:flex;
                        justify-content:space-between;align-items:center;">
                <div style="display:flex;align-items:center;gap:12px;">
                    <span style="font-size:18px;">{medal}</span>
                    <span style="color:#e2e8f0;font-size:13px;">{row["User Email"]}</span>
                </div>
                <span style="background:#6366f122;color:#6366f1;font-size:13px;font-weight:700;
                             padding:4px 14px;border-radius:20px;">{row["Activity Count"]}</span>
            </div>
            """, unsafe_allow_html=True)
# ════════════════════════════════════════════════════════
    # BROADCASTS (Admin News Tool)
    # ════════════════════════════════════════════════════════
    elif selected == "Broadcasts":
                section_header("📢", "System Broadcasts", "Publish news and changelogs to all users")
                st.markdown("<br>", unsafe_allow_html=True)
        
                st.markdown("### Create New Broadcast")
                b_title = st.text_input("Broadcast Title", placeholder="e.g., Changelog 1.1: New Search Features")
                b_desc = st.text_area("Detailed Description", height=150, placeholder="What changed? What's new?")
        
                if st.button("Publish to All Users →", use_container_width=True):
                    if not b_title or not b_desc:
                          st.error("Title and Description are required.")
                    else:
                           create_broadcast(b_title, b_desc)
                           st.success("✅ Broadcast published! Users will see it on their next login.")
    # ════════════════════════════════════════════════════════
    # FEEDBACK ANALYSIS
    # ════════════════════════════════════════════════════════
    elif selected == "Feedback Analysis":
        section_header("📢", "User Feedback", "All submitted feedback from users")
        st.markdown("<br>", unsafe_allow_html=True)

        feedback = get_all_feedback()
        if not feedback:
            st.markdown("""
            <div style="text-align:center;padding:40px;background:#111827;
                        border:1px dashed #1e293b;border-radius:14px;">
                <div style="font-size:36px;margin-bottom:12px;">📭</div>
                <div style="color:#475569;font-size:14px;">No feedback submitted yet.</div>
            </div>
            """, unsafe_allow_html=True)
            return

        # Summary KPIs
        df_fb  = pd.DataFrame(feedback, columns=["User Email","Section","Rating","Comments","Timestamp"])
        avg_r  = round(df_fb["Rating"].mean(), 1)
        fk1, fk2, fk3 = st.columns(3)
        kpi_card(fk1, "📝", "Total Responses",  len(feedback),            "#6366f1")
        kpi_card(fk2, "⭐", "Average Rating",    f"{avg_r} / 5",           "#f59e0b")
        kpi_card(fk3, "🗂️", "Sections Covered", df_fb["Section"].nunique(), "#10b981")
        st.markdown("<br>", unsafe_allow_html=True)

        # ── Setup Tabs for Organization ──
        tab_list, tab_cloud, tab_export = st.tabs(["📝 Feedback List", "☁️ Word Cloud", "⬇️ Export Data"])

        with tab_list:
            # Rating distribution chart
            fig_fb = px.histogram(df_fb, x="Rating", color="Section",
                                  title="Feedback Rating Distribution", barmode="group")
            fig_fb.update_layout(paper_bgcolor="#111827", plot_bgcolor="#111827",
                                 font={"color":"#94a3b8","family":"Inter"})
            st.plotly_chart(fig_fb, use_container_width=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # Feedback cards
            for femail, fsec, frat, fcom, fts in feedback:
                stars        = "⭐" * int(frat) + "☆" * (5 - int(frat))
                fcom_display = fcom if fcom else "<i style='color:#475569;'>No comments provided.</i>"
                st.markdown(f"""
                <div class="pn-card" style="margin-bottom:12px;border-left:4px solid #f59e0b;">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
                        <div>
                            <span style="color:#e2e8f0;font-weight:600;font-size:14px;">{femail}</span>
                            <span style="color:#64748b;font-size:12px;margin-left:8px;">· {fts}</span>
                        </div>
                        <div style="background:#1e293b;color:#94a3b8;font-size:11px;
                                    padding:3px 10px;border-radius:12px;font-weight:600;">{fsec}</div>
                    </div>
                    <div style="color:#f59e0b;font-size:16px;margin-bottom:8px;letter-spacing:3px;">{stars}</div>
                    <div style="color:#cbd5e1;font-size:13px;line-height:1.6;">{fcom_display}</div>
                </div>
                """, unsafe_allow_html=True)

        with tab_cloud:
            st.markdown("### Feedback Themes")
            # Combine all non-empty comments
            all_comments = " ".join(df_fb["Comments"].dropna().astype(str).tolist())
            if all_comments.strip():
                # Generate Word Cloud (styled to match the dark theme)
                wordcloud = WordCloud(width=800, height=400, background_color='#111827',
                                      colormap='Blues', max_words=100).generate(all_comments)

                fig, ax = plt.subplots(figsize=(10, 5), facecolor='#111827')
                ax.imshow(wordcloud, interpolation='bilinear')
                ax.axis("off")
                st.pyplot(fig)

                # Export Word Cloud Image
                buf = io.BytesIO()
                fig.savefig(buf, format="png", facecolor='#111827', bbox_inches='tight')
                st.download_button(
                    label="⬇️ Download Word Cloud Image",
                    data=buf.getvalue(),
                    file_name="feedback_wordcloud.png",
                    mime="image/png",
                    use_container_width=True
                )
            else:
                st.info("Not enough text comments available to generate a word cloud yet.")

        with tab_export:
            st.markdown("### Export Raw Data")
            st.markdown("Download all user feedback records as a CSV file for external analysis.")

            # Convert DataFrame to CSV
            csv_data = df_fb.to_csv(index=False).encode('utf-8')

            st.download_button(
                label="⬇️ Download Feedback CSV",
                data=csv_data,
                file_name="policynav_feedback_export.csv",
                mime="text/csv",
                use_container_width=True
            )




# ============================================================
# PAGE: POLICY LEADERBOARD
# ============================================================
def leaderboard_page():
    render_sidebar()
    section_header("🏆", "Policy Leaderboard", "Earn points by engaging with policies — compete with fellow citizens!")
    st.markdown("---")

    payload = verify_token(st.session_state.token)
    if not payload:
        st.toast("Session expired", icon="❌"); go_to("Login"); return
    user_email = payload["email"]

    tab_me, tab_board, tab_badges, tab_history = st.tabs([
        "⭐ My Stats", "🏆 Leaderboard", "🎖️ Badges", "📋 Points History"
    ])

    my_data     = get_user_points_data(user_email)
    my_pts      = my_data["points"]
    my_streak   = my_data["streak"]
    my_badges   = my_data["badges"]
    leaderboard = get_leaderboard(20)
    my_rank     = next((i+1 for i, r in enumerate(leaderboard) if r[1] == user_email), None)

    # ── TAB 1: MY STATS ──────────────────────────────────
    with tab_me:
        user_obj   = get_user_by_email(user_email)
        username   = user_obj[1] if user_obj else "User"
        rank_label = f"#{my_rank}" if my_rank else "Unranked"
        rank_color = "#f59e0b" if my_rank==1 else "#94a3b8" if my_rank==2 else "#cd7c32" if my_rank and my_rank<=3 else "#6366f1"
        medal      = "🥇" if my_rank==1 else "🥈" if my_rank==2 else "🥉" if my_rank and my_rank<=3 else "🏅"

        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#1e1b4b,#0f172a);border:1px solid #312e81;
                    border-radius:16px;padding:24px;margin-bottom:24px;">
            <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:16px;">
                <div>
                    <div style="font-size:20px;font-weight:700;color:#e0e7ff;">{username}</div>
                    <div style="color:#6366f1;font-size:13px;">{user_email}</div>
                    <div style="margin-top:10px;display:flex;gap:10px;flex-wrap:wrap;">
                        <span style="background:#312e81;color:#a5b4fc;font-size:12px;font-weight:700;padding:4px 14px;border-radius:20px;">{medal} Rank {rank_label}</span>
                        <span style="background:#1a2f1a;color:#4ade80;font-size:12px;font-weight:700;padding:4px 14px;border-radius:20px;">🔥 {my_streak}-day streak</span>
                        <span style="background:#1e293b;color:#94a3b8;font-size:12px;padding:4px 14px;border-radius:20px;">🎖️ {len(my_badges)} badges</span>
                    </div>
                </div>
                <div style="text-align:center;">
                    <div style="font-size:42px;font-weight:800;color:{rank_color};">{my_pts:,}</div>
                    <div style="color:#475569;font-size:12px;">Total Points</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        k1, k2, k3, k4 = st.columns(4)
        kpi_card(k1, "⭐", "My Points",    f"{my_pts:,}",        "#6366f1")
        kpi_card(k2, "🔥", "Login Streak", f"{my_streak} days",  "#f59e0b")
        kpi_card(k3, "🎖️", "Badges",       len(my_badges),       "#10b981")
        kpi_card(k4, "🏅", "Global Rank",  rank_label,            rank_color)
        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown("#### 💡 How to Earn Points")
        actions = [
            ("📂", "Upload a policy document",  "+10 pts"),
            ("🔍", "Ask a RAG Search question",  "+5 pts"),
            ("📝", "Generate a summary",         "+8 pts"),
            ("📖", "Run readability analysis",   "+4 pts"),
            ("💬", "Submit feedback",            "+3 pts"),
            ("🔥", "7-day login streak bonus",   "+20 pts"),
            ("⚡", "30-day login streak bonus",  "+50 pts"),
        ]
        cols = st.columns(2)
        for idx, (icon, action, pts) in enumerate(actions):
            cols[idx % 2].markdown(f"""
            <div style="background:#111827;border:1px solid #1e293b;border-radius:10px;
                        padding:10px 16px;margin-bottom:8px;
                        display:flex;justify-content:space-between;align-items:center;">
                <span style="color:#e2e8f0;font-size:13px;">{icon} {action}</span>
                <span style="background:#6366f122;color:#6366f1;font-size:12px;font-weight:700;
                             padding:2px 10px;border-radius:20px;">{pts}</span>
            </div>
            """, unsafe_allow_html=True)

    # ── TAB 2: LEADERBOARD ───────────────────────────────
    with tab_board:
        import json as _jj
        if not leaderboard:
            st.markdown("""
            <div style="text-align:center;padding:48px;background:#111827;
                        border:1px dashed #1e293b;border-radius:14px;">
                <div style="font-size:40px;">🏆</div>
                <div style="color:#475569;margin-top:12px;font-size:15px;">
                    No rankings yet — be the first!
                </div>
                <div style="color:#334155;font-size:13px;margin-top:6px;">
                    Start using PolicyNav features to earn points and appear here.
                </div>
            </div>""", unsafe_allow_html=True)
        else:
            # Top 3 podium
            if len(leaderboard) >= 3:
                pcols = st.columns(3)
                podium_cfg = [
                    (1, "🥈", "#94a3b8", "80px"),
                    (0, "🥇", "#f59e0b", "96px"),
                    (2, "🥉", "#cd7c32", "72px"),
                ]
                for ci, (li, p_medal, color, size) in enumerate(podium_cfg):
                    if li < len(leaderboard):
                        r      = leaderboard[li]
                        is_me  = r[1] == user_email
                        border = f"border:2px solid {color};" if is_me else ""
                        bc     = len(_jj.loads(r[4] or "[]"))
                        pcols[ci].markdown(f"""
                        <div style="background:#111827;border:1px solid #1e293b;
                                    border-radius:14px;padding:20px;text-align:center;{border}">
                            <div style="font-size:{size};">{p_medal}</div>
                            <div style="font-weight:700;color:#e2e8f0;font-size:14px;margin-top:4px;">
                                {r[0][:15]}{"  (You)" if is_me else ""}
                            </div>
                            <div style="font-size:28px;font-weight:800;color:{color};margin-top:8px;">
                                {r[2]:,}
                            </div>
                            <div style="color:#475569;font-size:11px;">points</div>
                            <div style="margin-top:8px;display:flex;justify-content:center;gap:8px;">
                                <span style="background:#1e293b;color:#94a3b8;font-size:10px;
                                             padding:2px 8px;border-radius:12px;">🔥 {r[3]}d</span>
                                <span style="background:#1e293b;color:#94a3b8;font-size:10px;
                                             padding:2px 8px;border-radius:12px;">🎖️ {bc}</span>
                            </div>
                        </div>""", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("#### 📋 Full Rankings")

            h1, h2, h3, h4, h5 = st.columns([0.5, 0.5, 2, 2, 1])
            for col, lbl in zip([h1,h2,h3,h4,h5], ["#", "", "Username", "Email", "Points"]):
                col.markdown(
                    f"<div style='font-size:11px;font-weight:600;color:#475569;"
                    f"text-transform:uppercase;padding:8px 4px;background:#0f172a;"
                    f"border-radius:4px;'>{lbl}</div>",
                    unsafe_allow_html=True
                )

            for rank, row in enumerate(leaderboard, 1):
                uname, uemail, upts, ustreak, _ = row
                is_me  = uemail == user_email
                m_icon = "🥇" if rank==1 else "🥈" if rank==2 else "🥉" if rank==3 else f"#{rank}"
                pc     = "#f59e0b" if rank==1 else "#94a3b8" if rank==2 else "#cd7c32" if rank==3 else "#6366f1"
                fw     = "700" if is_me else "400"
                you    = "  ← You" if is_me else ""
                r1,r2,r3,r4,r5 = st.columns([0.5, 0.5, 2, 2, 1])
                r1.markdown(f"<div style='color:#475569;padding:10px 0;font-size:13px;'>{rank}</div>", unsafe_allow_html=True)
                r2.markdown(f"<div style='padding:8px 0;font-size:18px;'>{m_icon}</div>", unsafe_allow_html=True)
                r3.markdown(f"<div style='color:#e2e8f0;font-weight:{fw};padding:10px 0;'>{uname}{you}</div>", unsafe_allow_html=True)
                r4.markdown(f"<div style='color:#475569;font-size:12px;padding:10px 0;'>{uemail[:25]}</div>", unsafe_allow_html=True)
                r5.markdown(f"<div style='color:{pc};font-weight:700;padding:10px 0;'>{upts:,}</div>", unsafe_allow_html=True)
                st.markdown("<div style='border-bottom:1px solid #1e293b;margin:2px 0;'></div>", unsafe_allow_html=True)

    # ── TAB 3: BADGES ────────────────────────────────────
    with tab_badges:
        st.markdown(
            f"#### 🎖️ All Badges — "
            f"<span style='color:#6366f1;'>{len(my_badges)}</span> / {len(BADGES)} earned",
            unsafe_allow_html=True
        )
        st.markdown("<br>", unsafe_allow_html=True)
        bcols = st.columns(3)
        for idx, badge in enumerate(BADGES):
            earned  = badge["id"] in my_badges
            col     = bcols[idx % 3]
            bg      = "#0f2a1a" if earned else "#111827"
            border  = "#22c55e" if earned else "#1e293b"
            opacity = "1"    if earned else "0.35"
            sc      = "#4ade80" if earned else "#475569"
            col.markdown(f"""
            <div style="background:{bg};border:1px solid {border};border-radius:12px;
                        padding:16px;text-align:center;margin-bottom:12px;opacity:{opacity};">
                <div style="font-size:36px;">{badge["icon"]}</div>
                <div style="font-weight:700;color:#e2e8f0;font-size:13px;margin-top:6px;">
                    {badge["name"]}
                </div>
                <div style="color:#64748b;font-size:11px;margin:4px 0;">{badge["desc"]}</div>
                <span style="background:{border}33;color:{sc};font-size:10px;font-weight:600;
                             padding:2px 10px;border-radius:20px;">
                    {"✅ Earned" if earned else "🔒 Locked"}
                </span>
            </div>""", unsafe_allow_html=True)

    # ── TAB 4: POINTS HISTORY ────────────────────────────
    with tab_history:
        history = get_points_history(user_email, 30)
        if not history:
            st.info("No points earned yet. Start using PolicyNav features!")
        else:
            LABELS = {
                "upload_doc":      ("📂", "Uploaded a document",       "#6366f1"),
                "rag_question":    ("🔍", "Asked a RAG question",      "#0ea5e9"),
                "summarize":       ("📝", "Generated a summary",       "#10b981"),
                "readability":     ("📖", "Ran readability analysis",  "#f59e0b"),
                "feedback":        ("💬", "Submitted feedback",        "#8b5cf6"),
                "login_streak_7":  ("🔥", "7-day streak bonus",       "#f59e0b"),
                "login_streak_30": ("⚡", "30-day streak bonus",      "#f59e0b"),
            }
            for action, pts, ts in history:
                icon, label, color = LABELS.get(action, ("⭐", action, "#6366f1"))
                st.markdown(f"""
                <div style="background:#111827;border:1px solid #1e293b;border-radius:10px;
                            padding:10px 16px;margin-bottom:6px;
                            display:flex;justify-content:space-between;align-items:center;">
                    <div style="display:flex;align-items:center;gap:10px;">
                        <span style="font-size:18px;">{icon}</span>
                        <div>
                            <div style="color:#e2e8f0;font-size:13px;">{label}</div>
                            <div style="color:#475569;font-size:11px;">{ts[:16]}</div>
                        </div>
                    </div>
                    <span style="background:{color}22;color:{color};font-size:13px;
                                 font-weight:700;padding:3px 12px;border-radius:20px;">
                        +{pts} pts
                    </span>
                </div>""", unsafe_allow_html=True)

def news_page():
    render_sidebar()
    section_header("📰", "News & Updates", "Latest changelogs, features, and platform announcements")
    st.markdown("---")

    payload = verify_token(st.session_state.token)
    if not payload:
        st.toast("Session expired", icon="❌"); go_to("Login"); return
    
    broadcasts = get_all_broadcasts()
    
    if not broadcasts:
        st.info("No news or updates yet. Check back later!")
        return

    # The user is viewing the page, so mark the latest broadcast as "seen"!
    latest_id = broadcasts[0][0]
    update_last_seen_broadcast(payload["email"], latest_id)

    # Render all broadcasts in descending order
    for b_id, title, desc, ts in broadcasts:
        st.markdown(f"""
        <div style="background:#111827; border:1px solid #1e293b; border-radius:12px; padding:24px; margin-bottom:16px;">
            <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:12px;">
                <div style="font-size:18px; font-weight:700; color:#f1f5f9;">{title}</div>
                <div style="color:#64748b; font-size:12px;">{ts[:16]}</div>
            </div>
            <div style="color:#cbd5e1; font-size:14px; line-height:1.6; white-space:pre-wrap;">{desc}</div>
        </div>
        """, unsafe_allow_html=True)
# ============================================================
# MAIN ROUTER
# ============================================================
page = st.session_state.page

if   page == "Signup":           signup_page()
elif page == "Dashboard":        dashboard_page()
elif page == "Profile":          profile_page()
elif page == "Forgot":           forgot_page()
elif page == "OTP":              otp_page()
elif page == "SecurityQuestion": security_question_page()
elif page == "SetNewPassword":   set_new_password_page()
elif page == "AdminDashboard":   admin_dashboard()
elif page == "Readability":      readability_page()
elif page == "RAG":              rag_search_tab()
elif page == "Summarization":    summarization_tab()
elif page == "Graph":            graph_tab()
elif page == "Leaderboard":      leaderboard_page()
elif page == "History":          overall_history_tab()
elif page == "News":             news_page()
else:                            login_page()
