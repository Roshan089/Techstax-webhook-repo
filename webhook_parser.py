"""
Parse GitHub webhook payloads and convert to MongoDB schema format.

Handles:
  - Push events → PUSH action
  - Pull Request events → PULL_REQUEST action
  - Merged PR events → MERGE action (brownie points)
"""

from datetime import datetime

from constants import (
    ACTION_PUSH,
    ACTION_PULL_REQUEST,
    ACTION_MERGE,
    GITHUB_EVENT_PUSH,
    GITHUB_EVENT_PULL_REQUEST,
)


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
        
        # Extract timestamp (GitHub provides ISO format, convert to UTC datetime string)
        timestamp_str = head_commit.get("timestamp", "")
        if timestamp_str:
            # Parse GitHub's ISO timestamp and format as UTC datetime string
            dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            timestamp_utc = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        else:
            # Fallback to current UTC time
            timestamp_utc = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        
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
        
        # Extract timestamp (GitHub provides ISO format)
        updated_at = pr.get("updated_at", "") or pr.get("created_at", "")
        if updated_at:
            # Parse ISO timestamp and format as UTC datetime string
            dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
            timestamp_utc = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        else:
            # Fallback to current UTC time
            timestamp_utc = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        
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
