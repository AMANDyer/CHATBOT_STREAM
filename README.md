# QUERY BOT - Smart Caching Chat Application

A intelligent chat application that provides detailed answers on first query and ultra-short cached summaries for repeat questions, powered by Groq's LLM and Redis caching.

## ✨ Features

- **🔐 Simple Authentication** - Basic login system with predefined users
- **🤖 Groq-Powered Responses** - Uses Llama-3.3-70b-versatile model for fast, accurate answers
- **💾 Smart Redis Caching** 
  - First time: Full detailed answer
  - Repeat questions: Ultra-short summary (cached for 30 minutes)
- **📜 Conversation History** - Stores last 50 conversations per user (7-day retention)
- **⚡ Lightning Fast** - Cached responses for repeated queries
- **👤 Multi-User Support** - Separate history and cache per user

## 🛠️ Technology Stack

- **Frontend**: Streamlit
- **LLM Provider**: Groq (Llama-3.3-70b-versatile)
- **Caching Layer**: Redis
- **Language**: Python 3.8+

## 📋 Prerequisites

- Python 3.8 or higher
- Redis server (local or remote)
- Groq API key

## 🚀 Installation

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd query-bot
```

2. **Install dependencies**
```bash
pip install streamlit groq redis python-dotenv
```

3. **Set up environment variables**
Create a `.env` file in the root directory:
```env
GROQ_API_KEY=your_groq_api_key_here
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

4. **Start Redis server**
```bash
# On Linux/Mac
redis-server

# On Windows (with Redis installed)
redis-server
```

5. **Run the application**
```bash
streamlit run app.py
```

## 🔧 Configuration

The application has several configurable parameters at the top of `app.py`:

```python
GROQ_MODEL = "llama-3.3-70b-versatile"  # Change model if needed
CACHE_TTL_SECONDS = 30 * 60              # Summary cache duration (30 min)
SEEN_TTL_SECONDS = 24 * 60 * 60          # "First-time" marker duration (24h)
HISTORY_TTL_SECONDS = 7 * 24 * 60 * 60   # History retention (7 days)
```

## 👥 Default Users

The application comes with two predefined users:
- **aman** / pass123
- **demo** / demo2025

*For production, replace the authentication logic in `VALID_USERS` with a proper auth system.*

## 🎯 How It Works

1. **First Time Asking a Question**
   - Gets full detailed answer from Groq
   - Generates a concise summary
   - Caches the summary for 30 minutes
   - Marks question as "seen" for 24 hours

2. **Asking the Same Question Again**
   - Detects cached summary
   - Shows only the brief summary
   - Much faster response time

3. **Conversation History**
   - All Q&A pairs saved to Redis
   - Viewable in expandable section
   - Auto-expires after 7 days

## 📁 Project Structure

```
query-bot/
├── app.py              # Main application file
├── .env                # Environment variables (create this)
├── README.md           # This file
└── requirements.txt    # Python dependencies
```

## 💡 Usage Tips

- First-time questions get comprehensive answers
- Repeat the same question to get quick summaries
- Use "Clear my history" button to delete your conversation history
- Each user has their own cache and history

## ⚠️ Important Notes

- Redis must be running before starting the application
- Groq API key is required for LLM responses
- Authentication is basic - replace with production-ready auth for public deployment
- Cache keys are user-specific, ensuring privacy between users

## 🔒 Security Considerations

For production deployment, consider:
- Implementing proper authentication (Auth0, OAuth, database)
- Using environment variables for all secrets
- Adding rate limiting
- Encrypting sensitive data in Redis
- Using Redis with password authentication
- Adding HTTPS/SSL

## 🐛 Troubleshooting

**Redis connection error:**
- Ensure Redis server is running: `redis-cli ping` (should return PONG)
- Check Redis host/port in `.env` file
- Verify firewall isn't blocking Redis port

**Groq API errors:**
- Verify your API key is correct in `.env`
- Check your Groq account has available credits
- Ensure internet connectivity

## 📝 License

[MIT License](LICENSE)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 🙏 Acknowledgments

- [Groq](https://groq.com) for their lightning-fast LLM inference
- [Streamlit](https://streamlit.io) for the amazing web framework
- [Redis](https://redis.io) for reliable caching

---

**Built with ❤️ using Streamlit, Groq, and Redis**