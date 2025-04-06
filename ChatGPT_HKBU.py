# Import necessary libraries
import os  # For reading environment variables
import requests  # For sending HTTP requests
import json  # For handling JSON data
from configparser import RawConfigParser  # For reading configuration files
from pathlib import Path  # For handling file paths
import firebase_admin  # For Firebase
from firebase_admin import credentials, firestore  # For Firestore
from typing import List, Dict, Any

class HKBU_ChatGPT():
    def __init__(self, db=None):
        """
        Initialize ChatGPT class
        Get configuration from environment variables or config file
        :param db: Firestore database instance (optional)
        """
        # Load configuration
        config = self._load_config()
        
        # Set ChatGPT configuration
        self.basic_url = config['basic_url']
        self.model_name = config['model_name']
        self.api_version = config['api_version']
        self.access_token = config['access_token']
        
        # Set Firestore database instance
        self.db = db
        
        # Validate required configurations
        required_configs = [
            'basic_url',
            'model_name',
            'api_version',
            'access_token'
        ]
        
        missing_configs = [config for config in required_configs if not getattr(self, config)]
        if missing_configs:
            raise ValueError(f"Missing required configurations: {', '.join(missing_configs)}")
    
    def _load_config(self):
        """
        Load configuration, prioritize environment variables, fall back to config file
        """
        config = RawConfigParser()
        config_path = Path('config.ini')
        
        if config_path.exists():
            config.read('config.ini')
        
        # Get configuration, prioritize environment variables
        return {
            'basic_url': os.getenv('CHATGPT_BASIC_URL') or config.get('CHATGPT', 'BASICURL', fallback=None),
            'model_name': os.getenv('CHATGPT_MODEL_NAME') or config.get('CHATGPT', 'MODELNAME', fallback=None),
            'api_version': os.getenv('CHATGPT_API_VERSION') or config.get('CHATGPT', 'APIVERSION', fallback=None),
            'access_token': os.getenv('CHATGPT_ACCESS_TOKEN') or config.get('CHATGPT', 'ACCESS_TOKEN', fallback=None)
        }
            
    def submit(self, message):
        """
        Submit message to ChatGPT API and get reply
        :param message: User input message
        :return: ChatGPT reply or error message
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
        ChatGPT_test = HKBU_ChatGPT(test_db)
        
        # Test basic conversation
        test_message = "Hello, how are you?"
        print("Testing basic conversation:")
        response = ChatGPT_test.submit(test_message)
        print(f"User: {test_message}")
        print(f"ChatGPT: {response}")
        
        # Test activity search
        print("\nTesting activity search:")
        activities = ChatGPT_test.search_similar_activities(["gaming", "VR"])
        print(f"Found {len(activities)} matching activities")
        for activity in activities[:2]:  # Print first 2 activities
            print(f"- {activity['name']}")
        
        # Test activity recommendations
        print("\nTesting activity recommendations:")
        test_interests = {
            "name": "John",
            "age": 25,
            "interests": ["gaming", "VR", "social"],
            "preferences": {
                "online_activities": True,
                "group_activities": True
            }
        }
        recommendations = ChatGPT_test.get_activity_recommendations(json.dumps(test_interests))
        print(recommendations)
        
    except Exception as e:
        print(f"Test failed: {str(e)}")