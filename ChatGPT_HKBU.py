# Import necessary libraries
import os  # For reading environment variables
import requests  # For sending HTTP requests
import json  # For handling JSON data
from configparser import RawConfigParser  # For reading configuration files
from pathlib import Path  # For handling file paths
import firebase_admin  # For Firebase
from firebase_admin import credentials, firestore  # For Firestore
from typing import List, Dict, Any

from recommend import (
    is_recommendation_request,
    extract_interests_from_message,
    search_activities_in_db,
    get_activity_recommendations_from_gpt,
    format_activities_for_response
)

class HKBU_ChatGPT():
    def __init__(self, use_database: bool = True):
        """
        Initialize ChatGPT class
        :param use_database: Whether to use Firebase database (default: True)
        """
        # Load configuration
        config = self._load_config()
        
        # Set ChatGPT configuration
        self.basic_url = config['basic_url']
        self.model_name = config['model_name']
        self.api_version = config['api_version']
        self.access_token = config['access_token']
        
        # Initialize database if needed
        self.db = None
        if use_database:
            try:
                # Check if Firebase app is already initialized
                if not firebase_admin._apps:
                    # Initialize Firebase app
                    cred = credentials.Certificate(config['firebase_config'])
                    firebase_admin.initialize_app(cred)
                    print("Firebase initialized successfully")
                
                # Get Firestore database instance
                self.db = firestore.client()
                print("Successfully connected to Firestore")
                
            except Exception as e:
                print(f"Firebase initialization failed: {str(e)}")
                print("Continuing without database support")
                self.db = None
    
    def _load_config(self):
        """
        Load configuration, prioritize environment variables, fall back to config file
        """
        config = RawConfigParser()
        config_path = Path('config.ini')
        
        if config_path.exists():
            config.read('config.ini')
        
        # Get configuration, prioritize environment variables
        firebase_config = {
            "type": "service_account",
            "project_id": os.getenv('FIREBASE_PROJECT_ID') or config.get('FIREBASE', 'PROJECT_ID', fallback=None),
            "private_key_id": os.getenv('FIREBASE_PRIVATE_KEY_ID') or config.get('FIREBASE', 'PRIVATE_KEY_ID', fallback=None),
            "private_key": (os.getenv('FIREBASE_PRIVATE_KEY') or config.get('FIREBASE', 'PRIVATE_KEY', fallback=None)).replace('\\n', '\n'),
            "client_email": os.getenv('FIREBASE_CLIENT_EMAIL') or config.get('FIREBASE', 'CLIENT_EMAIL', fallback=None),
            "client_id": os.getenv('FIREBASE_CLIENT_ID') or config.get('FIREBASE', 'CLIENT_ID', fallback=None),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": os.getenv('FIREBASE_CLIENT_CERT_URL') or config.get('FIREBASE', 'CLIENT_CERT_URL', fallback=None)
        }
        
        return {
            'basic_url': os.getenv('CHATGPT_BASIC_URL') or config.get('CHATGPT', 'BASICURL', fallback=None),
            'model_name': os.getenv('CHATGPT_MODEL_NAME') or config.get('CHATGPT', 'MODELNAME', fallback=None),
            'api_version': os.getenv('CHATGPT_API_VERSION') or config.get('CHATGPT', 'APIVERSION', fallback=None),
            'access_token': os.getenv('CHATGPT_ACCESS_TOKEN') or config.get('CHATGPT', 'ACCESS_TOKEN', fallback=None),
            'firebase_config': firebase_config
        }
            
    def submit(self, message):
        """
        Submit message to ChatGPT API and get reply
        :param message: User input message
        :return: ChatGPT reply or error message
        """
        # Check if this is a recommendation request
        if is_recommendation_request(message):
            return self.handle_recommendation_request(message)
        
        # Regular ChatGPT response
        return self._get_chatgpt_response(message)
    
    def handle_recommendation_request(self, message: str) -> str:
        """
        Handle activity recommendation requests
        :param message: User input message
        :return: Response with activity recommendations
        """
        try:
            # Extract interests from message
            interests_data = extract_interests_from_message(message)
            
            # First try to find matching activities in database
            if self.db:
                matching_activities = search_activities_in_db(
                    self.db,
                    interests_data['interests'],
                    interests_data['categories']
                )
                
                if matching_activities:
                    return format_activities_for_response(matching_activities)
            
            # If no matches found in database, use ChatGPT
            return get_activity_recommendations_from_gpt(self, interests_data)
        except Exception as e:
            print(f"Error handling recommendation request: {str(e)}")
            return "Sorry, there was an error processing your request. Please try again later."
    
    def _get_chatgpt_response(self, message: str) -> str:
        """
        Get response from ChatGPT API
        :param message: User input message
        :return: ChatGPT response
        """
        # Build conversation content
        conversation = [{"role": "user", "content": message}]
        
        # Build API request URL
        url = f"{self.basic_url}/deployments/{self.model_name}/chat/completions/?api-version={self.api_version}"
                
        # Set request headers
        headers = {
            'Content-Type': 'application/json',
            'api-key': self.access_token
        }
        
        # Set request body
        payload = { 'messages': conversation }
        
        # Send POST request
        response = requests.post(url, json=payload, headers=headers)
        
        # Handle response
        if response.status_code == 200:
            # If request successful, return ChatGPT reply
            data = response.json()
            return data['choices'][0]['message']['content']
        else:
            # If request failed, return error message
            return f'Error: {response.status_code} - {response.text}'
    
    def search_similar_activities(self, user_interests: List[str], category: str = None) -> List[Dict[str, Any]]:
        """
        Search for similar activities in Firestore based on user interests
        :param user_interests: List of user interests
        :param category: Optional category filter
        :return: List of matching activities
        """
        if not self.db:
            print("Firestore database not initialized")
            return []
            
        try:
            activities_ref = self.db.collection('Activities')
            
            # Build query
            query = activities_ref
            
            # Add category filter if provided
            if category:
                query = query.where('category', '==', category)
            
            # Get all activities
            activities = query.stream()
            
            # Convert to list of dictionaries
            activities_list = [activity.to_dict() for activity in activities]
            
            # Filter activities based on keywords matching user interests
            matching_activities = []
            for activity in activities_list:
                # Check if any keyword matches user interests
                if any(keyword.lower() in [interest.lower() for interest in user_interests] 
                      for keyword in activity.get('keywords', [])):
                    matching_activities.append(activity)
            
            return matching_activities
            
        except Exception as e:
            print(f"Error searching activities: {str(e)}")
            return []
    
    def get_activity_recommendations(self, user_message: str) -> str:
        """
        Get activity recommendations based on user message
        :param user_message: User's message about activities they're interested in
        :return: Formatted response with recommendations
        """
        if not self.db:
            return "Sorry, I cannot access the activity database at the moment."
            
        try:
            # First, analyze user interests from the message
            user_interests = self.analyze_user_interests({"message": user_message})
            
            # Extract interests and category if mentioned
            interests = user_interests.get("main_interests", [])
            category = None
            if "category" in user_interests:
                category = user_interests["category"]
            
            # Search for similar activities in Firestore
            matching_activities = self.search_similar_activities(interests, category)
            
            if matching_activities:
                # Format the response with matching activities
                response = "Here are some activities that might interest you:\n\n"
                for activity in matching_activities:
                    response += f"📌 {activity['name']}\n"
                    response += f"📝 {activity['description']}\n"
                    response += f"🔗 {activity['link']}\n\n"
                return response
            else:
                # If no matches found, use ChatGPT to generate recommendations
                prompt = f"""
                Based on the following user interests, suggest some activities:
                Interests: {', '.join(interests)}
                Category: {category if category else 'Any'}
                
                Please provide a list of suggested activities with descriptions and links.
                """
                return self.submit(prompt)
                
        except Exception as e:
            print(f"Error getting recommendations: {str(e)}")
            return "I apologize, but I encountered an error while processing your request. Please try again later."
    
    def analyze_user_interests(self, user_data):
        """
        Analyze user interests
        :param user_data: User data dictionary
        :return: Analysis results
        """
        prompt = f"""
        Please analyze the following user data and extract main interests and preferences:
        {json.dumps(user_data, ensure_ascii=False, indent=2)}
        
        Please return the analysis results in JSON format with the following fields:
        - main_interests: List of main interests
        - preferences: Description of preferences
        - category: Activity category if mentioned (e.g., "Online Gaming", "Virtual Reality", "Social Media")
        - potential_activities: List of potentially interesting activities
        """
        
        response = self.submit(prompt)
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                "main_interests": [],
                "preferences": "Unable to parse interest analysis results",
                "category": None,
                "potential_activities": []
            }
    
    def generate_recommendations(self, user_interests, available_activities):
        """
        Generate activity recommendations
        :param user_interests: User interest analysis results
        :param available_activities: List of available activities
        :return: List of recommended activities
        """
        prompt = f"""
        Based on the following user interests and available activities, generate personalized recommendations:
        
        User interest analysis:
        {json.dumps(user_interests, ensure_ascii=False, indent=2)}
        
        Available activities:
        {json.dumps(available_activities, ensure_ascii=False, indent=2)}
        
        Please return a JSON list of recommendations, each containing:
        - activity_name: Activity name
        - match_score: Match score (0-100)
        - reason: Recommendation reason
        """
        
        response = self.submit(prompt)
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return []
        
if __name__ == '__main__':
    # Test code
    try:
        # Initialize Firebase for testing
        if not firebase_admin._apps:
            cred = credentials.Certificate("serviceAccountKey.json")
            firebase_admin.initialize_app(cred)
        test_db = firestore.client()
        
        # Initialize ChatGPT with database
        ChatGPT_test = HKBU_ChatGPT(True)
        
        # Test basic conversation
        test_message = "Hello, how are you?"
        print("Testing basic conversation:")
        response = ChatGPT_test.submit(test_message)
        print(f"User: {test_message}")
        print(f"ChatGPT: {response}")
        
        # Test activity recommendations
        print("\nTesting activity recommendations:")
        test_recommendation = "I'm interested in gaming and VR. Can you recommend some activities?"
        response = ChatGPT_test.submit(test_recommendation)
        print(f"User: {test_recommendation}")
        print(f"ChatGPT: {response}")
        
    except Exception as e:
        print(f"Test failed: {str(e)}")