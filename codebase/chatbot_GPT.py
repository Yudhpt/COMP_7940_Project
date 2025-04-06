# Import necessary libraries
from telegram import Update  # Telegram Bot API
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
CallbackContext)  # Telegram Bot extensions
import os  # For reading environment variables
import logging  # For logging
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
    
    # Logging configuration
    log_level = os.getenv('LOG_LEVEL') or config.get('LOGGING', 'LEVEL', fallback='INFO')
    log_format = os.getenv('LOG_FORMAT') or config.get('LOGGING', 'FORMAT', 
                      fallback='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    log_file = os.getenv('LOG_FILE') or config.get('LOGGING', 'FILE', fallback='logs/app.log')
    
    return {
        'telegram_token': telegram_token,
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
    
    # Create Telegram Bot updater
    updater = Updater(token=config['telegram_token'], use_context=True)
    dispatcher = updater.dispatcher
    
    # Initialize ChatGPT handler
    global chatgpt
    chatgpt = HKBU_ChatGPT(use_database=True)  # Enable database support
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
