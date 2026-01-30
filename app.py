"""
Techstax Webhook Receiver — Flask application entry point.

This app:
  1. Receives GitHub webhooks (push, pull_request) from action-repo.
  2. Stores events in MongoDB with the required schema.
  3. Exposes an API for the UI to poll events every 15 seconds.
  4. Serves the minimal UI (single HTML page).

Run locally: flask run  (or: python app.py)
Deploy: use the same app; set MONGO_URI and GITHUB_WEBHOOK_SECRET in env.
"""

from flask import Flask, request, jsonify, render_template

from config import MONGO_URI, MONGO_DB_NAME
from db import insert_event, get_db, get_events, delete_all_events
from webhook_parser import parse_github_webhook

# -----------------------------------------------------------------------------
# App factory pattern: create Flask app and attach config
# -----------------------------------------------------------------------------
app = Flask(__name__)

# We will add routes in the next steps:
#  - POST /webhook          → receive GitHub webhook, save to MongoDB
#  - GET  /api/events       → return events for UI (polling)
#  - GET  /                 → serve the minimal UI page

@app.route("/")
def index():
    """Serve the main UI page (minimal frontend)."""
    return render_template("index.html")


@app.route("/health")
def health():
    """Simple health check for deployment platforms (e.g. Render, Railway)."""
    return {"status": "ok"}, 200


@app.route("/clear-events")
def clear_events():
    """
    Delete all events from MongoDB (for testing from 0 events).
    Visit: http://127.0.0.1:5000/clear-events
    """
    try:
        deleted = delete_all_events()
        return jsonify({
            "status": "success",
            "message": f"Deleted {deleted} event(s). UI will show 0 events after refresh.",
            "deleted_count": deleted,
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/test-db")
def test_db():
    """
    Test MongoDB connection (for local testing).
    
    Visit: http://127.0.0.1:5000/test-db
    Should return connection status and database info.
    """
    try:
        # Try to connect to MongoDB
        db = get_db()
        # Get database stats
        stats = db.command("dbStats")
        
        return jsonify({
            "status": "success",
            "message": "MongoDB connection successful!",
            "database": MONGO_DB_NAME,
            "uri": MONGO_URI.split("@")[-1] if "@" in MONGO_URI else MONGO_URI,  # Hide credentials
            "collections": stats.get("collections", 0),
            "dataSize": f"{stats.get('dataSize', 0) / 1024:.2f} KB"
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": "MongoDB connection failed",
            "error": str(e),
            "uri": MONGO_URI.split("@")[-1] if "@" in MONGO_URI else MONGO_URI
        }), 500


@app.route("/webhook", methods=["POST"])
def handle_webhook():
    """
    Receive GitHub webhook from action-repo.
    
    GitHub sends:
      - Header: X-GitHub-Event (event type: "push", "pull_request", etc.)
      - Body: JSON payload with event details
    
    Process:
      1. Read event type from header
      2. Parse JSON payload
      3. Convert to MongoDB schema format
      4. Store in MongoDB
      5. Return success response
    """
    try:
        # Get event type from GitHub header (e.g., "push", "pull_request")
        event_type = request.headers.get("X-GitHub-Event", "")
        
        if not event_type:
            return jsonify({"error": "Missing X-GitHub-Event header"}), 400
        
        # Get JSON payload
        payload = request.get_json()
        if not payload:
            return jsonify({"error": "Missing JSON payload"}), 400
        
        # Handle GitHub ping event (webhook test)
        if event_type == "ping":
            return jsonify({"message": "Webhook endpoint is active"}), 200
        
        # Parse webhook payload and convert to MongoDB schema
        event_data = parse_github_webhook(payload, event_type)
        
        if not event_data:
            # Event type not supported (e.g., "issues", "star", etc.)
            return jsonify({"message": f"Event type '{event_type}' not supported"}), 200
        
        # Store event in MongoDB
        insert_event(event_data)
        
        return jsonify({
            "status": "success",
            "event": event_data.get("action"),
            "author": event_data.get("author"),
        }), 200
        
    except Exception as e:
        # Log error and return 500 (don't expose internal errors to GitHub)
        print(f"❌ Webhook error: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/api/events", methods=["GET"])
def api_events():
    """
    API endpoint for UI to poll events from MongoDB.
    
    Query parameters:
        - after_id (optional): MongoDB _id (string). Return only events inserted
                               after this id. Uses insertion order so no events
                               are missed when GitHub sends out-of-order timestamps.
        - since (optional): Legacy; UTC timestamp. Prefer after_id for polling.
        - limit (optional): Maximum number of events to return (default: 100).
    
    Returns:
        JSON: events, count, latest_id (for next poll; use after_id=latest_id).
    """
    try:
        after_id = request.args.get("after_id", None)
        since_timestamp = request.args.get("since", None)
        limit = int(request.args.get("limit", 100))
        
        # Prefer after_id (cursor-based) so we never miss events
        events, latest_id = get_events(
            after_id=after_id,
            since_timestamp=since_timestamp if not after_id else None,
            limit=limit,
        )
        
        return jsonify({
            "status": "success",
            "events": events,
            "count": len(events),
            "latest_id": latest_id,
        }), 200
        
    except Exception as e:
        print(f"❌ API error: {e}")
        return jsonify({
            "status": "error",
            "message": "Failed to retrieve events",
            "error": str(e)
        }), 500


# -----------------------------------------------------------------------------
# Run with: flask run  or  python app.py
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
