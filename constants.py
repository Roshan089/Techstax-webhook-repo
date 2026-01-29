"""
Constants used across the webhook-repo.

Centralizing these avoids magic strings and keeps the MongoDB schema
and display logic consistent (e.g. action types match assignment format).
"""

# MongoDB collection name for GitHub webhook events
EVENTS_COLLECTION = "events"

# Allowed action types stored in MongoDB (and displayed in UI)
# Must match assignment: PUSH, PULL_REQUEST, MERGE
ACTION_PUSH = "PUSH"
ACTION_PULL_REQUEST = "PULL_REQUEST"
ACTION_MERGE = "MERGE"

ACTION_TYPES = (ACTION_PUSH, ACTION_PULL_REQUEST, ACTION_MERGE)

# GitHub event names (from webhook payload headers / payload)
GITHUB_EVENT_PUSH = "push"
GITHUB_EVENT_PULL_REQUEST = "pull_request"
