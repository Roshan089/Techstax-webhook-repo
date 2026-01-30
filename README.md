# webhook-repo — Techstax Assignment

Flask app that receives GitHub webhooks from **action-repo**, stores events in MongoDB, and serves a minimal UI that polls every 15 seconds.

## Setup (local)

1. **Clone / open this repo**

2. **Create virtual environment and install dependencies**
   ```bash
   python -m venv venv
   venv\Scripts\activate   # Windows
   pip install -r requirements.txt
   ```

3. **Configure environment**
   - Copy `.env.example` to `.env`
   - Set `MONGO_URI` (e.g. `mongodb://localhost:27017` or MongoDB Atlas URI)
   - Optionally set `GITHUB_WEBHOOK_SECRET` for production

4. **Run the app**
   ```bash
   flask run
   ```
   Or: `python app.py` — app runs at http://127.0.0.1:5000

## Project structure

- `app.py` — Flask app, webhook route (`POST /webhook`), API route, serves UI
- `config.py` — Loads env vars (MongoDB URI, etc.)
- `constants.py` — Action types, collection name
- `db.py` — MongoDB connection and database operations
- `webhook_parser.py` — Parse GitHub webhooks and convert to MongoDB schema
- `requirements.txt` — Dependencies
- `templates/` — HTML for minimal UI (added in Step 4)
- `static/` — CSS/JS if needed (optional)

## Routes

- `GET /` — Main UI page (minimal frontend, polls `/api/events` every 15s)
- `GET /health` — Health check (for deployment platforms)
- `GET /api/events` — API for UI polling (optional `?since=<timestamp>` to avoid duplicates)
- `POST /webhook` — GitHub webhook receiver (push, pull_request → PUSH, PULL_REQUEST, MERGE)
- `GET /test-db` — MongoDB connection test (local testing only)

## Submission (Techstax Assignment)

1. **Create webhook-repo on GitHub**
   - Go to https://github.com/new
   - Repository name: `webhook-repo` (or `webhook-repo-Techstax`)
   - Public, do not initialize with README
   - Create repository

2. **Push this code to webhook-repo**
   ```bash
   cd "c:\Users\csp\Desktop\New folder\webhook-repo"
   git init
   git add .
   git commit -m "Techstax assignment - Flask webhook receiver"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/webhook-repo.git
   git push -u origin main
   ```
   Replace `YOUR_USERNAME` with your GitHub username.

3. **Submit both repo links in the form**
   - Assignment form: https://forms.gle/qkdB1GVVkjq7ytc7
   - **action-repo:** https://github.com/Roshan089/action-repo-Techstax-
   - **webhook-repo:** https://github.com/YOUR_USERNAME/webhook-repo
   - Due: 30 Jan 2026 23:59:59

## Deployment (when ready)

- Set `MONGO_URI` (e.g. MongoDB Atlas URI) and `GITHUB_WEBHOOK_SECRET` in your host's environment.
- Point GitHub webhook (action-repo) to your deployed URL, e.g. `https://your-app.onrender.com/webhook`.
- Hosts like Render/Railway use the `Procfile` and `gunicorn` for production.