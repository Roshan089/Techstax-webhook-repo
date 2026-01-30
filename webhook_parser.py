"""
Parse GitHub webhook payloads and convert to MongoDB schema format.

Handles:
  - Push events → PUSH action
  - Pull Request events → PULL_REQUEST action
  - Merged PR events → MERGE action (brownie points)
"""

from datetime import datetime, timezone

from constants import (
    ACTION_PUSH,
    ACTION_PULL_REQUEST,
    ACTION_MERGE,
    GITHUB_EVENT_PUSH,
    GITHUB_EVENT_PULL_REQUEST,
)


def _timestamp_to_utc_str(timestamp_str):
    """
    Parse GitHub timestamp (ISO 8601) and return a single pattern: UTC string.
    Ensures push and pull_request times are stored in the same UTC pattern.
    """
    if not timestamp_str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    # Handle Z and +00:00, and any other offset (e.g. +05:30)
    s = timestamp_str.strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is not None:
            dt = dt.astimezone(timezone.utc)
        else:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    except Exception:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def parse_github_webhook(payload, event_type):
    """
    Parse GitHub webhook payload and convert to MongoDB schema format.
    
    Args:
        payload (dict): GitHub webhook JSON payload.
        event_type (str): GitHub event type from X-GitHub-Event header
                         (e.g., "push", "pull_request").
    
    Returns:
        dict: Event document matching MongoDB schema:
            {
                "request_id": str,      # Commit hash or PR ID
                "author": str,          # GitHub username
                "action": str,          # PUSH, PULL_REQUEST, or MERGE
                "from_branch": str,     # Source branch
                "to_branch": str,       # Target branch
                "timestamp": str        # UTC datetime string
            }
    
    Returns None if event type is not supported.
    """
    if event_type == GITHUB_EVENT_PUSH:
        return _parse_push_event(payload)
    elif event_type == GITHUB_EVENT_PULL_REQUEST:
        return _parse_pull_request_event(payload)
    else:
        # Unknown event type (e.g., "ping", "issues", etc.) - ignore
        return None


def _parse_push_event(payload):
    """
    Parse GitHub push event and convert to MongoDB schema.
    
    Push event structure:
        - payload["commits"][0]["id"] → commit hash (request_id)
        - payload["pusher"]["name"] → author
        - payload["ref"] → "refs/heads/{branch_name}" (to_branch)
        - payload["head_commit"]["timestamp"] → timestamp
        - payload["before"] → previous commit (from_branch is implicit)
    
    For push: from_branch = to_branch (pushed to same branch).
    """
    try:
        # Extract commit hash (use head_commit.id or first commit)
        head_commit = payload.get("head_commit", {})
        commit_id = head_commit.get("id") or payload.get("after", "")
        
        # Extract author (pusher name or commit author)
        author = payload.get("pusher", {}).get("name", "")
        if not author:
            author = head_commit.get("author", {}).get("name", "")
        
        # Extract branch name from ref (e.g., "refs/heads/staging" → "staging")
        ref = payload.get("ref", "")
        branch_name = ref.replace("refs/heads/", "") if ref.startswith("refs/heads/") else ref
        
        # Extract timestamp: same UTC pattern for all event types
        timestamp_utc = _timestamp_to_utc_str(head_commit.get("timestamp", ""))
        
        return {
            "request_id": commit_id[:40] if commit_id else "",  # Commit hash (40 chars)
            "author": author,
            "action": ACTION_PUSH,
            "from_branch": branch_name,  # For push, same as to_branch
            "to_branch": branch_name,
            "timestamp": timestamp_utc,
        }
    except Exception as e:
        print(f"❌ Error parsing push event: {e}")
        return None


def _parse_pull_request_event(payload):
    """
    Parse GitHub pull_request event and convert to MongoDB schema.
    
    Pull Request event structure:
        - payload["action"] → "opened", "closed", "synchronize", etc.
        - payload["pull_request"]["number"] → PR ID (request_id)
        - payload["pull_request"]["user"]["login"] → author
        - payload["pull_request"]["head"]["ref"] → from_branch (PR source)
        - payload["pull_request"]["base"]["ref"] → to_branch (PR target)
        - payload["pull_request"]["merged"] → True if merged (MERGE action)
        - payload["pull_request"]["updated_at"] → timestamp
    
    If merged=True and action="closed" → MERGE action
    If action="opened" → PULL_REQUEST action
    """
    try:
        pr = payload.get("pull_request", {})
        action = payload.get("action", "")
        merged = pr.get("merged", False)
        
        # Determine our action type
        if merged and action == "closed":
            # PR was merged → MERGE action (brownie points!)
            our_action = ACTION_MERGE
        elif action == "opened":
            # PR was opened → PULL_REQUEST action
            our_action = ACTION_PULL_REQUEST
        else:
            # Other PR actions (synchronize, closed without merge, etc.) → ignore or treat as PULL_REQUEST
            # For assignment, we'll treat "opened" as the main event
            if action not in ["opened", "closed"]:
                return None  # Ignore synchronize, labeled, etc.
            our_action = ACTION_PULL_REQUEST
        
        # Extract PR number (request_id for PRs)
        pr_number = pr.get("number", "")
        request_id = str(pr_number) if pr_number else ""
        
        # Extract author
        author = pr.get("user", {}).get("login", "")
        
        # Extract branches
        from_branch = pr.get("head", {}).get("ref", "")  # PR source branch
        to_branch = pr.get("base", {}).get("ref", "")    # PR target branch
        
        # Extract timestamp: same UTC pattern as push (always normalized to UTC)
        updated_at = pr.get("updated_at", "") or pr.get("created_at", "")
        timestamp_utc = _timestamp_to_utc_str(updated_at)
        
        return {
            "request_id": request_id,
            "author": author,
            "action": our_action,
            "from_branch": from_branch,
            "to_branch": to_branch,
            "timestamp": timestamp_utc,
        }
    except Exception as e:
        print(f"❌ Error parsing pull_request event: {e}")
        return None
