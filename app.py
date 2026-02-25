import streamlit as st
import os
from dotenv import load_dotenv
import google.generativeai as genai
import redis
import json
import hashlib
import time

load_dotenv()

# ──── Gemini setup ───────────────────────────────────────
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")   # ← changed to 1.5-flash (usually faster & cheaper)

# ──── Redis connection ───────────────────────────────────
@st.cache_resource
def get_redis_client():
    host = os.getenv("REDIS_HOST", "localhost")
    port = int(os.getenv("REDIS_PORT", 6379))
    db   = int(os.getenv("REDIS_DB", 0))

    client = redis.Redis(
        host=host,
        port=port,
        db=db,
        decode_responses=True
    )

    # Test connection right away
    try:
        client.ping()
        return client
    except Exception as e:
        st.error(f"Redis connection failed: {e}")
        st.stop()   # stop app if Redis is down

redis_client = get_redis_client()

# Show connection status once
if "redis_ok_shown" not in st.session_state:
    st.success("Redis connected successfully ✓")
    st.session_state.redis_ok_shown = True

# ──── Cache key helper ───────────────────────────────────
def make_safe_key(question: str) -> str:
    # Normalize + hash → same question = same key
    cleaned = " ".join(question.strip().lower().split())
    hash_val = hashlib.sha256(cleaned.encode("utf-8")).hexdigest()
    return f"gemini:cache:{hash_val}"

# ──── Cache get / set ────────────────────────────────────
def get_from_cache(question: str):
    key = make_safe_key(question)
    value = redis_client.get(key)
    if value:
        try:
            data = json.loads(value)
            return data.get("answer")
        except:
            return None
    return None

def save_to_cache(question: str, answer: str, ttl_seconds: int = 3600):  # 1 hour
    key = make_safe_key(question)
    payload = {"answer": answer, "when": time.time()}
    redis_client.setex(key, ttl_seconds, json.dumps(payload))

# ──── UI ─────────────────────────────────────────────────
st.set_page_config(page_title="QUERY BOT - Cached", layout="wide")
st.title("QUERY BOT (with Redis cache)")

question = st.text_input("Ask anything:", key="question_input")
btn = st.button("Send")

if btn and question.strip():
    start_time = time.time()

    cached = get_from_cache(question)

    if cached:
        st.success(f"Cache HIT! ({time.time() - start_time:.3f} seconds)")
        st.markdown("**Answer:**")
        st.write(cached)
    else:
        with st.spinner("Calling Gemini (this may take 3–15 seconds the first time)..."):
            try:
                response = model.generate_content(question)
                answer = response.text.strip()

                save_to_cache(question, answer, ttl_seconds=3600)

                st.success(f"Cache MISS → saved! ({time.time() - start_time:.3f} seconds)")
                st.markdown("**Answer:**")
                st.write(answer)

            except Exception as e:
                st.error(f"Gemini failed: {e}")

# Debug area
with st.expander("Debug info"):
    st.write("Current question hash example:")
    if question.strip():
        st.code(make_safe_key(question))
    st.write(f"Redis keys count: {redis_client.dbsize()}")
    if st.button("Clear ALL cache (for testing)"):
        redis_client.flushdb()
        st.success("Cache cleared")
        st.rerun()