"""
MongoDB Database Connection and Helper Functions
"""
from pymongo import MongoClient, ASCENDING, DESCENDING
from django.conf import settings
from bson.objectid import ObjectId
import logging

logger = logging.getLogger(__name__)

class MongoDB:
    _client = None
    _db = None
    
    @classmethod
    def get_connection(cls):
        """Get or create MongoDB connection"""
        if cls._client is None:
            try:
                if settings.MONGODB_USER and settings.MONGODB_PASSWORD:
                    connection_string = f"mongodb://{settings.MONGODB_USER}:{settings.MONGODB_PASSWORD}@{settings.MONGODB_HOST}:{settings.MONGODB_PORT}/"
                else:
                    connection_string = f"mongodb://{settings.MONGODB_HOST}:{settings.MONGODB_PORT}/"
                
                cls._client = MongoClient(connection_string)
                cls._db = cls._client[settings.MONGODB_NAME]
                logger.info(f"Connected to MongoDB: {settings.MONGODB_NAME}")
                
                # Create indexes on first connection
                cls._create_indexes()
                
            except Exception as e:
                logger.error(f"MongoDB connection error: {e}")
                raise
        
        return cls._db
    
    @classmethod
    def _create_indexes(cls):
        """Create database indexes for performance, ensuring idempotency by naming them."""
        db = cls._db
        
        try:
            # Users collection indexes
            db.users.create_index([("email", ASCENDING)], unique=True, name="email_unique")
            db.users.create_index([("role", ASCENDING)], name="role_index")
            
            # Classes collection indexes
            db.classes.create_index([("lecturer_id", ASCENDING)], name="class_lecturer_index")
            db.classes.create_index([("name", ASCENDING)], unique=True, name="class_name_unique")
            
            # Groups collection indexes
            db.groups.create_index([("class_obj", ASCENDING)], name="group_class_index")
            db.groups.create_index([("leader", ASCENDING)], name="group_leader_index")
            db.groups.create_index([("members", ASCENDING)], name="group_members_index")
            
            # Tasks collection indexes
            db.tasks.create_index([("class_obj", ASCENDING)], name="task_class_index")
            db.tasks.create_index([("lecturer", ASCENDING)], name="task_lecturer_index")
            db.tasks.create_index([("due_date", DESCENDING)], name="task_due_date_index")
            
            # Submissions collection indexes
            db.submissions.create_index([("task", ASCENDING)], name="sub_task_index")
            db.submissions.create_index([("group", ASCENDING)], name="sub_group_index")
            db.submissions.create_index([("member", ASCENDING)], name="sub_member_index")
            db.submissions.create_index([("task", ASCENDING), ("member", ASCENDING)], unique=True, name="sub_task_member_unique")
            
            # Compiled submissions collection indexes
            db.compiled_submissions.create_index([("group", ASCENDING), ("task", ASCENDING)], unique=True, name="compiled_group_task_unique")
            
            logger.info("MongoDB indexes verified/created successfully.")
        except Exception as e:
            logger.warning(f"Could not create indexes, they may already exist: {e}")

# Initialize connection
def get_db():
    """Helper function to get database connection"""
    return MongoDB.get_connection()

# Collection helper functions
def get_collection(collection_name):
    """Get a specific collection"""
    db = get_db()
    return db[collection_name]

def to_object_id(id_string):
    """Convert string to ObjectId safely"""
    try:
        return ObjectId(id_string)
    except:
        return None

def from_object_id(obj_id):
    """Convert ObjectId to string safely"""
    return str(obj_id) if obj_id else None
