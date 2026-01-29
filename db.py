"""
MongoDB database connection and operations.

Handles connecting to MongoDB and provides helper functions
for storing and retrieving webhook events.
"""

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


def get_events(since_timestamp=None, limit=100):
    """
    Retrieve webhook events from MongoDB.
    
    Args:
        since_timestamp (str, optional): Only return events after this timestamp
                                        (UTC datetime string). Used to avoid
                                        showing duplicate events in UI refresh.
        limit (int): Maximum number of events to return (default: 100).
    
    Returns:
        list: List of event documents, sorted by timestamp (newest first).
              Each document includes all MongoDB schema fields plus _id.
    
    Raises:
        ConnectionFailure: If MongoDB connection fails.
    """
    collection = get_events_collection()
    
    # Build query: if since_timestamp provided, filter by timestamp
    query = {}
    if since_timestamp:
        # MongoDB string comparison works for ISO-like datetime strings
        # We store as "YYYY-MM-DD HH:MM:SS UTC", so we can compare strings
        query["timestamp"] = {"$gt": since_timestamp}
    
    # Sort by timestamp descending (newest first), then by _id as tiebreaker
    cursor = collection.find(query).sort([
        ("timestamp", -1),  # Newest first
        ("_id", -1)         # Tiebreaker for same timestamp
    ]).limit(limit)
    
    # Convert cursor to list of dictionaries
    events = list(cursor)
    
    # Convert ObjectId to string for JSON serialization
    for event in events:
        event["_id"] = str(event["_id"])
    
    return events
