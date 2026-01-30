"""
MongoDB database connection and operations.

Handles connecting to MongoDB and provides helper functions
for storing and retrieving webhook events.
"""

from bson import ObjectId
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from config import MONGO_URI, MONGO_DB_NAME
from constants import EVENTS_COLLECTION

# Global MongoDB client (initialized once, reused)
_client = None
_db = None


def get_db():
    """
    Get MongoDB database instance (creates connection if needed).
    
    Returns:
        Database: MongoDB database object.
    
    Raises:
        ConnectionFailure: If MongoDB connection fails.
    """
    global _client, _db
    
    if _db is None:
        try:
            # Create MongoDB client (reuse connection)
            _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
            # Test connection
            _client.server_info()
            # Get database
            _db = _client[MONGO_DB_NAME]
            print(f"✅ Connected to MongoDB: {MONGO_DB_NAME}")
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            print(f"❌ MongoDB connection failed: {e}")
            print(f"   URI: {MONGO_URI}")
            raise
    
    return _db


def get_events_collection():
    """
    Get the events collection from MongoDB.
    
    Returns:
        Collection: MongoDB collection for storing webhook events.
    """
    db = get_db()
    return db[EVENTS_COLLECTION]


def insert_event(event_data):
    """
    Insert a webhook event document into MongoDB.
    
    Args:
        event_data (dict): Event document matching MongoDB schema:
            - request_id (str): Commit hash or PR ID
            - author (str): GitHub username
            - action (str): PUSH, PULL_REQUEST, or MERGE
            - from_branch (str): Source branch
            - to_branch (str): Target branch
            - timestamp (str): UTC datetime string
    
    Returns:
        ObjectId: MongoDB document ID of inserted event.
    
    Raises:
        ConnectionFailure: If MongoDB connection fails.
    """
    collection = get_events_collection()
    result = collection.insert_one(event_data)
    print(f"✅ Stored event: {event_data.get('action')} by {event_data.get('author')}")
    return result.inserted_id


def get_events(since_timestamp=None, after_id=None, limit=100):
    """
    Retrieve webhook events from MongoDB.
    
    Args:
        since_timestamp (str, optional): Only return events after this timestamp
                                        (UTC datetime string). Deprecated for
                                        polling; use after_id to avoid missing events.
        after_id (str, optional): MongoDB _id (string). Only return events inserted
                                  after this id. Uses insertion order so no events
                                  are missed when GitHub sends out-of-order timestamps.
        limit (int): Maximum number of events to return (default: 100).
    
    Returns:
        tuple: (events list, latest_id str or None).
               events: sorted by timestamp (newest first). Each has _id as string.
               latest_id: the _id of the newest event in the batch (for next poll).
    """
    collection = get_events_collection()
    
    if after_id:
        # Cursor-based: get events inserted after this _id (never miss events)
        try:
            query = {"_id": {"$gt": ObjectId(after_id)}}
        except Exception:
            query = {}
        cursor = collection.find(query).sort("_id", 1).limit(limit)  # insertion order
        events = list(cursor)
        # Sort by timestamp for display (newest first)
        events.sort(key=lambda e: (e.get("timestamp") or "", e["_id"]), reverse=True)
        latest_id = str(max(e["_id"] for e in events)) if events else None
    else:
        # Initial load or legacy: get most recent events by timestamp
        query = {}
        if since_timestamp:
            query["timestamp"] = {"$gt": since_timestamp}
        cursor = collection.find(query).sort([
            ("timestamp", -1),
            ("_id", -1)
        ]).limit(limit)
        events = list(cursor)
        # latest_id = max _id in batch so next poll gets only newer insertions
        latest_id = str(max(e["_id"] for e in events)) if events else None
    
    # Convert ObjectId to string for JSON
    for event in events:
        event["_id"] = str(event["_id"])
    
    return events, latest_id


def delete_all_events():
    """
    Delete all events from the collection (for testing from 0 events).
    
    Returns:
        int: Number of documents deleted.
    """
    collection = get_events_collection()
    result = collection.delete_many({})
    return result.deleted_count
