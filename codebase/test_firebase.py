import firebase_admin
from firebase_admin import credentials, firestore
import os
import json

def initialize_firebase():
    """Initialize Firebase connection"""
    try:
        if not firebase_admin._apps:
            # Check if service account file exists
            if not os.path.exists("serviceAccountKey.json"):
                raise FileNotFoundError("serviceAccountKey.json file does not exist")
            
            # Initialize Firebase with service account
            cred = credentials.Certificate("serviceAccountKey.json")
            firebase_admin.initialize_app(cred)
        
        # Get Firestore client
        db = firestore.client()
        print("Successfully connected to Firebase.")
        return db
        
    except Exception as e:
        print(f"Firebase initialization failed: {str(e)}")
        raise

def test_connection(db):
    """Test basic connection to Firestore"""
    try:
        # Try to get a document
        test_doc = db.collection('test').document('test')
        test_doc.set({'test': True})
        test_doc.delete()
        print("Connection test successful!")
    except Exception as e:
        print(f"Connection test failed: {str(e)}")

def get_all_activities(db):
    """Get all activities from the database"""
    try:
        activities = []
        docs = db.collection('Activities').stream()
        
        for doc in docs:
            activity = doc.to_dict()
            activity['id'] = doc.id
            activities.append(activity)
        
        print(f"Successfully retrieved {len(activities)} activities")
        return activities
    except Exception as e:
        print(f"Failed to get activities: {str(e)}")
        return []

def get_activities_by_category(db, category):
    """Get activities by category"""
    try:
        activities = []
        docs = db.collection('Activities').where('category', '==', category).stream()
        
        for doc in docs:
            activity = doc.to_dict()
            activity['id'] = doc.id
            activities.append(activity)
        
        print(f"Successfully retrieved {len(activities)} activities in category: {category}")
        return activities
    except Exception as e:
        print(f"Failed to get activities by category: {str(e)}")
        return []

def get_activity_by_name(db, name):
    """Get a specific activity by name"""
    try:
        doc = db.collection('Activities').document(name).get()
        if doc.exists:
            activity = doc.to_dict()
            activity['id'] = doc.id
            print(f"Successfully retrieved activity: {name}")
            return activity
        else:
            print(f"Activity not found: {name}")
            return None
    except Exception as e:
        print(f"Failed to get activity: {str(e)}")
        return None

def main():
    try:
        # Initialize Firebase
        db = initialize_firebase()
        
        # Test connection
        test_connection(db)
        
        # Get all activities
        print("\nGetting all activities:")
        all_activities = get_all_activities(db)
        print(json.dumps(all_activities, indent=2, ensure_ascii=False))
        
        # Get activities by category
        print("\nGetting activities by category (Online Gaming):")
        gaming_activities = get_activities_by_category(db, "Online Gaming")
        print(json.dumps(gaming_activities, indent=2, ensure_ascii=False))
        
        # Get specific activity
        print("\nGetting specific activity (League of Legends Beginner Bootcamp):")
        specific_activity = get_activity_by_name(db, "League of Legends Beginner Bootcamp")
        print(json.dumps(specific_activity, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"Test failed: {str(e)}")

if __name__ == "__main__":
    main() 