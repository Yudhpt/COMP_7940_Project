import json
import firebase_admin
from firebase_admin import credentials, firestore
import os

# Initialize Firebase
def initialize_firebase():
    try:
        # Check if service account file exists
        if not os.path.exists("serviceAccountKey.json"):
            raise FileNotFoundError("serviceAccountKey.json file does not exist")
            
        # Read and validate service account file
        with open("serviceAccountKey.json", 'r') as f:
            service_account = json.load(f)
            
        # Validate required fields
        required_fields = ['project_id', 'private_key', 'client_email']
        for field in required_fields:
            if field not in service_account:
                raise ValueError(f"serviceAccountKey.json is missing required field: {field}")
        
        # Initialize Firebase
        cred = credentials.Certificate("serviceAccountKey.json")
        firebase_admin.initialize_app(cred)
        return firestore.client()
        
    except Exception as e:
        print(f"Firebase initialization failed: {str(e)}")
        raise

# Batch upload data
def upload_data(db, collection_name, json_file):
    try:
        # Check write permissions for collection
        test_doc = db.collection(collection_name).document('test_permission')
        test_doc.set({'test': True})
        test_doc.delete()
        
        # Read JSON file
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Batch write
        batch = db.batch()
        collection_ref = db.collection(collection_name)
        
        for item in data:
            # Use activity name as document ID
            doc_ref = collection_ref.document(item['name'])
            batch.set(doc_ref, item)
        
        batch.commit()
        print(f"Successfully uploaded {len(data)} records to {collection_name} collection")
        
    except Exception as e:
        print(f"Upload failed: {str(e)}")
        if "Missing or insufficient permissions" in str(e):
            print("Please check the following possible causes:")
            print("1. Service account does not have sufficient permissions")
            print("2. Firebase rules restrict write operations")
            print("3. Collection name may be incorrect")
            print("4. Service account may be expired or revoked")

if __name__ == "__main__":
    try:
        db = initialize_firebase()
        upload_data(db, "Activities", "sample.json")
    except Exception as e:
        print(f"Program execution failed: {str(e)}")