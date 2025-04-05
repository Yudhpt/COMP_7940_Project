# 导入必要的库
from telegram import Update  # Telegram Bot API
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
CallbackContext)  # Telegram Bot 扩展功能
import os  # 用于读取环境变量
import logging  # 用于日志记录
import firebase_admin  # Firebase管理
from firebase_admin import credentials, firestore  # Firebase认证和数据库
import configparser  # 用于读取配置文件
from pathlib import Path  # 用于处理文件路径

from ChatGPT_HKBU import HKBU_ChatGPT  # 导入自定义的ChatGPT类

def load_config():
    """
    加载配置，优先使用环境变量，如果环境变量不存在则使用配置文件
    """
    config = configparser.ConfigParser()
    config_path = Path('config.ini')
    
    if config_path.exists():
        config.read('config.ini')
    
    # 获取配置，优先使用环境变量
    telegram_token = os.getenv('TELEGRAM_ACCESS_TOKEN') or config.get('TELEGRAM', 'ACCESS_TOKEN', fallback=None)
    
    # Firebase配置
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
    
    # 日志配置
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
    设置日志配置
    """
    # 确保日志目录存在
    log_dir = Path(config['log_file']).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 配置日志
    logging.basicConfig(
        level=getattr(logging, config['log_level']),
        format=config['log_format'],
        handlers=[
            logging.FileHandler(config['log_file']),
            logging.StreamHandler()
        ]
    )

def main():
    # 加载配置
    config = load_config()
    
    # 设置日志
    setup_logging(config)
    
    # 验证必要的配置
    if not config['telegram_token']:
        raise ValueError("Telegram访问令牌未配置")
    
    # 初始化Firebase
    try:
        # 初始化Firebase应用
        cred = credentials.Certificate(config['firebase_config'])
        firebase_admin.initialize_app(cred)
        
        # 获取Firestore数据库实例
        global db
        db = firestore.client()
        logging.info("成功连接到Firebase。")
        
    except Exception as e:
        logging.error(f"Firebase初始化失败: {str(e)}")
        raise
    
    # 创建Telegram Bot更新器
    updater = Updater(token=config['telegram_token'], use_context=True)
    dispatcher = updater.dispatcher
    
    # 初始化ChatGPT处理器
    global chatgpt
    chatgpt = HKBU_ChatGPT()
    chatgpt_handler = MessageHandler(Filters.text & (~Filters.command), equiped_chatgpt)
    dispatcher.add_handler(chatgpt_handler)
    
    # 启动机器人
    logging.info("机器人启动成功")
    updater.start_polling()
    updater.idle()

# ChatGPT消息处理函数
def equiped_chatgpt(update, context):
    global chatgpt
    global db
    
    # 获取用户消息
    user_message = update.message.text
    user_id = str(update.effective_user.id)
    
    try:
        # 获取用户对话历史
        user_ref = db.collection('users').document(user_id)
        user_doc = user_ref.get()
        
        if user_doc.exists:
            conversation_history = user_doc.to_dict().get('conversation', [])
        else:
            conversation_history = []
        
        # 添加新消息到历史
        conversation_history.append({
            'role': 'user',
            'content': user_message,
            'timestamp': firestore.SERVER_TIMESTAMP
        })
        
        # 获取ChatGPT回复
        reply_message = chatgpt.submit(user_message)
        
        # 添加ChatGPT回复到历史
        conversation_history.append({
            'role': 'assistant',
            'content': reply_message,
            'timestamp': firestore.SERVER_TIMESTAMP
        })
        
        # 更新用户对话历史
        user_ref.set({
            'conversation': conversation_history,
            'last_updated': firestore.SERVER_TIMESTAMP
        }, merge=True)
        
        # 记录日志
        logging.info(f"用户 {user_id} 发送消息: {user_message}")
        logging.info(f"ChatGPT回复: {reply_message}")
        
        # 发送回复消息给用户
        context.bot.send_message(chat_id=update.effective_chat.id, text=reply_message)
        
    except Exception as e:
        logging.error(f"处理消息时出错: {str(e)}")
        context.bot.send_message(chat_id=update.effective_chat.id, 
                                text="抱歉，处理消息时出现错误。请稍后再试。")
        
if __name__ == '__main__':
    main()
