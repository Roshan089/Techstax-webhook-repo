# Flask Backend File Structure (Quick Reference)

## 📁 Ideal Structure

```
webhook-repo/
│
├── app.py                 # 🚀 MAIN ENTRY POINT - All routes live here
├── config.py              # ⚙️  Configuration (env vars, MongoDB URI)
├── constants.py           # 📌 Constants (action types, collection names)
├── models.py              # 🗄️  Database models (optional - we use PyMongo directly)
├── utils.py                # 🔧 Helper functions (date parsing, validation)
│
├── requirements.txt       # 📦 Python packages (Flask, pymongo, etc.)
├── .env                   # 🔐 Secrets (local only, NEVER commit)
├── .env.example           # 📋 Template showing what env vars needed
├── .gitignore             # 🚫 Files to ignore (venv, .env, __pycache__)
├── README.md              # 📖 How to setup and run
│
├── templates/             # 🎨 HTML files (Flask serves these)
│   └── index.html         #    Main UI page
│
└── static/                # 🎨 CSS, JS, images (optional)
    ├── css/
    └── js/
```

---

## 📝 What Each File Does (Short)

| File/Folder | Purpose |
|------------|---------|
| **`app.py`** | **Main Flask app** - defines routes (`@app.route`), handles requests, returns responses |
| **`config.py`** | Loads environment variables (MongoDB URI, secrets) - one place for all config |
| **`constants.py`** | Stores constants like `ACTION_PUSH = "PUSH"` - avoids magic strings |
| **`models.py`** | Database schemas/models (if using ORM like SQLAlchemy) - we skip this, use PyMongo directly |
| **`utils.py`** | Helper functions (parse dates, validate data) - reusable code |
| **`requirements.txt`** | Lists Python packages - run `pip install -r requirements.txt` |
| **`.env`** | Your secrets (MongoDB URI, API keys) - **NEVER commit this** |
| **`.env.example`** | Template showing what env vars needed - **safe to commit** |
| **`.gitignore`** | Tells Git what files to ignore (venv, .env, cache files) |
| **`README.md`** | Instructions for setup and running |
| **`templates/`** | HTML files - Flask's `render_template()` looks here |
| **`static/`** | CSS, JS, images - Flask serves from `/static/` URL |

---

## 🔄 How Flask Uses These Files

1. **Start app**: `python app.py` → loads `config.py` → creates Flask app in `app.py`
2. **Request comes**: Flask checks routes in `app.py` → calls matching function
3. **Function runs**: Uses `config.py` for settings, `constants.py` for values, `utils.py` for helpers
4. **Return HTML**: Flask looks in `templates/` for HTML files
5. **Return static**: Flask serves files from `static/` folder

---

## 🎯 For Our Project (Minimal)

**Must have:**
- `app.py` - routes (webhook, API, UI)
- `config.py` - MongoDB URI
- `constants.py` - action types
- `requirements.txt` - dependencies
- `.env.example` - env template
- `.gitignore` - ignore secrets
- `templates/index.html` - UI page

**Optional:**
- `utils.py` - if we need helpers (date parsing, etc.)
- `static/` - if we want separate CSS/JS files (or inline in HTML)

---

## 💡 Key Concept

**`app.py` = The Heart**  
- All routes (`@app.route`) go here
- Each route = one function
- Function reads request → does work → returns response

Example:
```python
@app.route("/webhook", methods=["POST"])
def handle_webhook():
    data = request.json  # Read request
    # Save to MongoDB     # Do work
    return {"ok": True}  # Return response
```
