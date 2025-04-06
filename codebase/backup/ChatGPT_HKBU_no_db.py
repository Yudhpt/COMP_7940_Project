# Import necessary libraries
import os  # For reading environment variables
import requests  # For sending HTTP requests
import json  # For handling JSON data
from configparser import RawConfigParser  # For reading configuration files
from pathlib import Path  # For handling file paths
from typing import Dict, Any

class HKBU_ChatGPT():
    def __init__(self):
        """
        Initialize ChatGPT class
        Get configuration from environment variables or config file
        """
        # Load configuration
        config = self._load_config()
        
        # Set ChatGPT configuration
        self.basic_url = config['basic_url']
        self.model_name = config['model_name']
        self.api_version = config['api_version']
        self.access_token = config['access_token']
        
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
    
    def _load_config(self) -> Dict[str, Any]:
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
            
    def submit(self, message: str) -> str:
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
        
if __name__ == '__main__':
    # Test code
    ChatGPT_test = HKBU_ChatGPT()
    
    # Test basic conversation
    test_message = "Hello, how are you?"
    print("Testing basic conversation:")
    response = ChatGPT_test.submit(test_message)
    print(f"User: {test_message}")
    print(f"ChatGPT: {response}") 