"""
Configuration for the webhook-repo Flask application.

Loads settings from environment variables so we can use different
MongoDB instances for local dev vs deployed (e.g. MongoDB Atlas).
Never hardcode secrets; use .env (not committed) and .env.example as a template.
"""

import os
from dotenv import load_dotenv

# Load .env file if present (local development)
load_dotenv()

# MongoDB connection string (e.g. mongodb://localhost:27017 or Atlas URI)
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")

# Database name where we store webhook events
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "webhook_events")

# Optional: GitHub webhook secret for verifying payload signatures (HMAC)
# If set, we validate X-Hub-Signature-256; if empty, we skip validation (dev only)
GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET", "")
