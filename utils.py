import json
from typing import Dict, List, Any, Optional
import firebase_admin
from firebase_admin import firestore
import re

def is_recommendation_request(message: str) -> bool:
    """
    Check if the message is requesting activity recommendations
    :param message: User input message
    :return: True if the message is requesting recommendations
    """
    recommendation_keywords = [
        'recommend', 'suggest', 'find', 'look for', 'search for',
        'what activities', 'what events', 'what to do', 'what can i do',
        'interested in', 'looking for', 'want to join', 'want to participate'
    ]
    
    message_lower = message.lower()
    return any(keyword in message_lower for keyword in recommendation_keywords)

def extract_interests_from_message(message: str) -> Dict[str, Any]:
    """
    Extract interests and preferences from user message
    :param message: User input message
    :return: Dictionary containing extracted interests and preferences
    """
    # Basic keyword matching for categories
    category_keywords = {
        'gaming': ['game', 'gaming', 'play', 'player', 'gamer'],
        'vr': ['vr', 'virtual reality', 'virtual', 'metaverse'],
        'social': ['social', 'community', 'group', 'team', 'together'],
        'learning': ['learn', 'study', 'education', 'course', 'class'],
        'fitness': ['fitness', 'exercise', 'workout', 'sport', 'health'],
        'art': ['art', 'creative', 'design', 'draw', 'paint'],
        'music': ['music', 'song', 'concert', 'band', 'dance']
    }
    
    # Extract mentioned categories
    categories = []
    message_lower = message.lower()
    for category, keywords in category_keywords.items():
        if any(keyword in message_lower for keyword in keywords):
            categories.append(category)
    
    # Extract specific interests using regex
    interest_patterns = [
        r'i like (.*?)[.,!?]',
        r'i love (.*?)[.,!?]',
        r'i enjoy (.*?)[.,!?]',
        r'i want to (.*?)[.,!?]',
        r'i am interested in (.*?)[.,!?]'
    ]
    
    interests = []
    for pattern in interest_patterns:
        matches = re.findall(pattern, message_lower)
        interests.extend(matches)
    
    return {
        'categories': categories,
        'interests': interests,
        'raw_message': message
    }

def format_activity_for_db(activity: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format activity data to match database schema
    :param activity: Activity data from GPT
    :return: Formatted activity data
    """
    # Ensure all required fields are present
    required_fields = ['name', 'description', 'keywords', 'link', 'category']
    
    # If any required field is missing, return None
    if not all(field in activity for field in required_fields):
        return None
    
    # Format keywords if they're not already a list
    if isinstance(activity['keywords'], str):
        activity['keywords'] = [kw.strip() for kw in activity['keywords'].split(',')]
    
    return activity

def save_activity_to_db(db: firestore.Client, activity: Dict[str, Any]) -> bool:
    """
    Save activity to Firestore database
    :param db: Firestore database instance
    :param activity: Activity data to save
    :return: True if successful, False otherwise
    """
    try:
        # Use activity name as document ID
        doc_ref = db.collection('Activities').document(activity['name'])
        doc_ref.set(activity)
        return True
    except Exception as e:
        print(f"Error saving activity to database: {str(e)}")
        return False

def search_activities_in_db(db: firestore.Client, 
                          interests: List[str], 
                          categories: List[str] = None) -> List[Dict[str, Any]]:
    """
    Search for activities in database based on interests and categories
    :param db: Firestore database instance
    :param interests: List of user interests
    :param categories: Optional list of categories to filter by
    :return: List of matching activities
    """
    if not db:
        return []
    
    try:
        activities_ref = db.collection('Activities')
        
        # Build query
        query = activities_ref
        
        # Add category filter if provided
        if categories:
            query = query.where(filter=firestore.FieldFilter('category', 'in', categories))
        
        # Get all activities
        activities = query.stream()
        
        # Convert to list of dictionaries
        activities_list = [activity.to_dict() for activity in activities]
        
        # Filter activities based on keywords matching user interests
        matching_activities = []
        for activity in activities_list:
            # Check if any keyword matches user interests
            if any(keyword.lower() in [interest.lower() for interest in interests] 
                  for keyword in activity.get('keywords', [])):
                matching_activities.append(activity)
        
        return matching_activities
        
    except Exception as e:
        print(f"Error searching activities: {str(e)}")
        return []

def format_activities_for_response(activities: List[Dict[str, Any]]) -> str:
    """
    Format activities for response message
    :param activities: List of activities
    :return: Formatted response string
    """
    if not activities:
        return "Sorry, I couldn't find any matching activities."
    
    response = "Here are some activities that might interest you:\n\n"
    for activity in activities:
        response += f"Name: {activity['name']}\n"
        response += f"Description: {activity['description']}\n"
        response += f"Link: {activity['link']}\n\n"
    
    return response 