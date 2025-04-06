# Import necessary libraries
from telegram import Update  # Telegram Bot API
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
CallbackContext)  # Telegram Bot extensions
import os  # For reading environment variables
import logging  # For logging
import firebase_admin  # Firebase management
from firebase_admin import credentials, firestore  # Firebase authentication and database
from configparser import RawConfigParser  # For reading configuration files
from pathlib import Path  # For handling file paths

from ChatGPT_HKBU import HKBU_ChatGPT  # Import custom ChatGPT class

def load_config():
    """
    Load configuration, prioritize environment variables, fall back to config file
    """
    config = RawConfigParser()
    config_path = Path('config.ini')
    
    if config_path.exists():
        config.read('config.ini')
    
    # Get configuration, prioritize environment variables
    telegram_token = os.getenv('TELEGRAM_ACCESS_TOKEN') or config.get('TELEGRAM', 'ACCESS_TOKEN', fallback=None)
    
    # Firebase configuration
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
    
    # Logging configuration
    log_level = os.getenv('LOG_LEVEL') or config.get('LOGGING', 'LEVEL', fallback='INFO')
    log_format = os.getenv('LOG_FORMAT') or config.get('LOGGING', 'FORMAT', 
                      fallback='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    log_file = os.getenv('LOG_FILE') or config.get('LOGGING', 'FILE', fallback='logs/app.log')
    
    return {
        'telegram_token': telegram_token,
        'firebase_config': firebase_config,
        'log_level': log_level,
        'log_format': log_format,
        'log_file': log_file
    }

def setup_logging(config):
    """
    Configure logging settings
    """
    # Ensure log directory exists
    log_dir = Path(config['log_file']).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, config['log_level']),
        format=config['log_format'],
        handlers=[
            logging.FileHandler(config['log_file']),
            logging.StreamHandler()
        ]
    )

def main():
    # Load configuration
    config = load_config()
    
    # Setup logging
    setup_logging(config)
    
    # Validate required configuration
    if not config['telegram_token']:
        raise ValueError("Telegram access token not configured")
    
    # Initialize Firebase
    try:
        # Check if Firebase app is already initialized
        if not firebase_admin._apps:
            # Initialize Firebase app
            cred = credentials.Certificate(config['firebase_config'])
            firebase_admin.initialize_app(cred)
            logging.info("Firebase initialized successfully")
        
        # Get Firestore database instance
        db = firestore.client()
        logging.info("Successfully connected to Firestore")
        
    except Exception as e:
        logging.error(f"Firebase initialization failed: {str(e)}")
        # Continue without Firebase if initialization fails
        db = None
        logging.warning("Continuing without Firebase support")
    
    # Create Telegram Bot updater
    updater = Updater(token=config['telegram_token'], use_context=True)
    dispatcher = updater.dispatcher
    
    # Initialize ChatGPT handler with db instance
    global chatgpt
    chatgpt = HKBU_ChatGPT(db)
    chatgpt_handler = MessageHandler(Filters.text & (~Filters.command), equiped_chatgpt)
    dispatcher.add_handler(chatgpt_handler)
    
    # Start bot
    logging.info("Bot started successfully")
    updater.start_polling()
    updater.idle()

# ChatGPT message handler
def equiped_chatgpt(update, context):
    global chatgpt
    
    # Get user message
    user_message = update.message.text
    user_id = str(update.effective_user.id)
    
    try:
        # Get ChatGPT reply
        reply_message = chatgpt.submit(user_message)
        
        # Log the interaction
        logging.info(f"User {user_id} sent message: {user_message}")
        logging.info(f"ChatGPT reply: {reply_message}")
        
        # Send reply to user
        context.bot.send_message(chat_id=update.effective_chat.id, text=reply_message)
        
    except Exception as e:
        logging.error(f"Error processing message: {str(e)}")
        context.bot.send_message(chat_id=update.effective_chat.id, 
                                text="Sorry, an error occurred while processing your message. Please try again later.")
        
if __name__ == '__main__':
    main()
