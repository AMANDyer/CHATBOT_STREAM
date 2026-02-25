import streamlit as st
import os
from dotenv import load_dotenv
from groq import Groq
import redis
import json
import time
import uuid
from datetime import datetime
import hashlib

load_dotenv()

# ──── CONFIG ────────────────────────────────────────────────────────────────
GROQ_MODEL         = "llama-3.3-70b-versatile"   # or "llama-3.1-70b-versatile"
CACHE_TTL_SECONDS  = 30 * 60          # 30 min
SEEN_TTL_SECONDS   = 24 * 60 * 60     # 24 h
HISTORY_TTL_SECONDS = 7 * 24 * 60 * 60  # 7 days — feel free to adjust

# ──── Groq Client ───────────────────────────────────────────────────────────
@st.cache_resource
def get_groq_client():
    return Groq(api_key=os.getenv("GROQ_API_KEY"))

groq_client = get_groq_client()

# ──── Redis Client ──────────────────────────────────────────────────────────
@st.cache_resource
def get_redis_client():
    client = redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        db=int(os.getenv("REDIS_DB", 0)),
        decode_responses=True
    )
    try:
        client.ping()
        return client
    except Exception as e:
        st.error(f"Redis connection failed: {e}\nIs Redis running?")
        st.stop()

redis_client = get_redis_client()

# ──── Hash Helpers ──────────────────────────────────────────────────────────
def make_query_hash(q: str) -> str:
    cleaned = " ".join(q.strip().lower().split())
    return hashlib.sha256(cleaned.encode()).hexdigest()[:16]

def summary_cache_key(username: str, q_hash: str) -> str:
    return f"cache:{username}:summary:{q_hash}"

def seen_key(username: str, q_hash: str) -> str:
    return f"cache:{username}:seen:{q_hash}"

def history_key(username: str) -> str:
    return f"history:{username}"

# ──── History Helpers ───────────────────────────────────────────────────────
def save_to_history(username: str, question: str, summary: str):
    key = history_key(username)
    ts = time.time()
    msg = {
        "ts": ts,
        "time": datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M"),
        "question": question,
        "summary": summary,
    }
    redis_client.zadd(key, {json.dumps(msg): -ts})   # negative for DESC order
    redis_client.expire(key, HISTORY_TTL_SECONDS)

def load_history(username: str):
    key = history_key(username)
    items = redis_client.zrevrange(key, 0, 49)  # last 50 items max
    return [json.loads(item) for item in items if item]

def clear_history(username: str):
    redis_client.delete(history_key(username))

# ──── Session state initialization ──────────────────────────────────────────
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.username = None

# ──── Simple dummy auth (replace with real auth in production) ──────────────
VALID_USERS = {
    "aman": "pass123",
    "demo": "demo2025",
    # Add more users here or connect to database / auth0 / etc.
}

def authenticate(username, password):
    return VALID_USERS.get(username.strip().lower()) == password

# ──── SIDEBAR – Controls ────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### QUERY BOT Controls")

    if st.session_state.authenticated:
        st.success(f"Logged in as **{st.session_state.username}**")
        
        if st.button("🚪 Logout", use_container_width=True, type="primary"):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

        if st.button("🗑️ Clear my history", use_container_width=True):
            clear_history(st.session_state.username)
            st.success("History cleared")
            time.sleep(0.8)
            st.rerun()

    else:
        st.info("Please sign in")

# ──── MAIN UI ───────────────────────────────────────────────────────────────
st.markdown("""
    <div style="
        background: linear-gradient(90deg, #0d47a1, #1976d2);
        padding: 2.2rem 1.8rem;
        border-radius: 12px;
        margin-bottom: 1.8rem;
        color: white;
        text-align: center;
        box-shadow: 0 6px 12px rgba(0,0,0,0.25);
    ">
        <h1 style="margin:0; font-size: 2.6rem;">QUERY BOT</h1>
        <p style="margin: 0.6rem 0 0; font-size: 1.15rem; opacity: 0.92;">
            Lightning-fast answers • Powered by Groq • Smart caching
        </p>
    </div>
""", unsafe_allow_html=True)

st.caption("Ask once → detailed answer • Ask again → ultra-short cached summary")

# ──── LOGIN SCREEN ──────────────────────────────────────────────────────────
if not st.session_state.authenticated:
    st.title("Sign In")
    with st.form("login", clear_on_submit=False):
        col1, col2 = st.columns([5,4])
        with col1:
            username = st.text_input("Username", placeholder="aman / demo")
        with col2:
            password = st.text_input("Password", type="password")
        
        if st.form_submit_button("Sign In", use_container_width=True, type="primary"):
            if authenticate(username, password):
                st.session_state.username = username.strip().lower()
                st.session_state.authenticated = True
                st.success(f"Welcome back, {st.session_state.username}!")
                time.sleep(0.6)
                st.rerun()
            else:
                st.error("Invalid username or password")
    st.stop()

# ──────────────────────────────────────────────────────────────────────────────
# ── Authenticated user area ─────────────────────────────────────────────────
USERNAME = st.session_state.username

st.subheader(f"Hi {USERNAME.capitalize()}, ask anything…")

# Show recent history
history = load_history(USERNAME)
if history:
    with st.expander("Recent conversations (latest first)", expanded=False):
        for item in history:
            with st.chat_message("user", avatar="🧑‍💻"):
                st.caption(item["time"])
                st.markdown(item["question"])
            with st.chat_message("assistant", avatar="🤖"):
                st.caption(item["time"] + " • Summary")
                st.markdown(item["summary"])

# ── Main chat input ─────────────────────────────────────────────────────────
question = st.chat_input("Your question…")

if question:
    question = question.strip()
    if not question:
        st.rerun()

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with st.chat_message("user"):
        st.caption(current_time)
        st.markdown(question)

    q_hash = make_query_hash(question)
    summary_key = f"cache:{USERNAME}:summary:{q_hash}"
    seen_key   = f"cache:{USERNAME}:seen:{q_hash}"

    cached_summary = redis_client.get(summary_key)
    has_seen_full  = redis_client.exists(seen_key)  # exists → already saw full once

    if cached_summary and has_seen_full:
        # ── Repeat ask → show only cached summary ───────────────────────
        with st.chat_message("assistant"):
            st.caption(f"{current_time} • Short summary (repeat)")
            st.info("→ Same question asked before → showing concise summary")
            st.markdown(cached_summary)

        # Still log to history (only summary)
        save_to_history(USERNAME, question, cached_summary)

    else:
        # ── First time this question → generate & show full answer ───────
        with st.spinner("Generating full detailed answer..."):
            try:
                full_resp = groq_client.chat.completions.create(
                    model=GROQ_MODEL,
                    messages=[{"role": "user", "content": question}],
                    temperature=0.7,
                    max_tokens=2048,
                )
                full_text = full_resp.choices[0].message.content.strip()

                # Create very short summary
                summary_prompt = (
                    "Create an extremely concise summary in **1–3 short sentences maximum**. "
                    "No examples, no lists, no code blocks, be as brief as possible:\n\n" + full_text
                )
                summary_resp = groq_client.chat.completions.create(
                    model=GROQ_MODEL,
                    messages=[{"role": "user", "content": summary_prompt}],
                    temperature=0.4,
                    max_tokens=140,
                )
                summary_text = summary_resp.choices[0].message.content.strip()

                # Cache **only** the summary + mark that full was shown
                redis_client.setex(summary_key, CACHE_TTL_SECONDS, summary_text)
                redis_client.setex(seen_key, SEEN_TTL_SECONDS, "1")

            except Exception as e:
                st.error(f"Groq error: {e}")
                st.rerun()

        # Show **full** answer (only this time)
        with st.chat_message("assistant"):
            st.caption(f"{current_time} • Full detailed answer")
            st.markdown(full_text)
            st.caption("↑ This full version is shown only once — next time you'll see only summary")

        # Log summary to history (consistent with repeat case)
        save_to_history(USERNAME, question, summary_text)

    #st.rerun()