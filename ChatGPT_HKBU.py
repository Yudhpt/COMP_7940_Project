# 导入必要的库
import os  # 用于读取环境变量
import requests  # 用于发送HTTP请求
import json  # 用于处理JSON数据
import configparser  # 用于读取配置文件
from pathlib import Path  # 用于处理文件路径

class HKBU_ChatGPT():
    def __init__(self):
        """
        初始化ChatGPT类
        从环境变量或配置文件获取配置信息
        """
        # 加载配置
        config = self._load_config()
        
        # 设置ChatGPT配置
        self.basic_url = config['basic_url']
        self.model_name = config['model_name']
        self.api_version = config['api_version']
        self.access_token = config['access_token']
        
        # 验证必要的配置是否已设置
        required_configs = [
            'basic_url',
            'model_name',
            'api_version',
            'access_token'
        ]
        
        missing_configs = [config for config in required_configs if not getattr(self, config)]
        if missing_configs:
            raise ValueError(f"缺少必要的配置: {', '.join(missing_configs)}")
    
    def _load_config(self):
        """
        加载配置，优先使用环境变量，如果环境变量不存在则使用配置文件
        """
        config = configparser.ConfigParser()
        config_path = Path('config.ini')
        
        if config_path.exists():
            config.read('config.ini')
        
        # 获取配置，优先使用环境变量
        return {
            'basic_url': os.getenv('CHATGPT_BASIC_URL') or config.get('CHATGPT', 'BASICURL', fallback=None),
            'model_name': os.getenv('CHATGPT_MODEL_NAME') or config.get('CHATGPT', 'MODELNAME', fallback=None),
            'api_version': os.getenv('CHATGPT_API_VERSION') or config.get('CHATGPT', 'APIVERSION', fallback=None),
            'access_token': os.getenv('CHATGPT_ACCESS_TOKEN') or config.get('CHATGPT', 'ACCESS_TOKEN', fallback=None)
        }
            
    def submit(self, message):
        """
        向ChatGPT API提交消息并获取回复
        :param message: 用户输入的消息
        :return: ChatGPT的回复或错误信息
        """
        # 构建对话内容
        conversation = [{"role": "user", "content": message}]
        
        # 构建API请求URL
        url = f"{self.basic_url}/deployments/{self.model_name}/chat/completions/?api-version={self.api_version}"
                
        # 设置请求头
        headers = {
            'Content-Type': 'application/json',
            'api-key': self.access_token
        }
        
        # 设置请求体
        payload = { 'messages': conversation }
        
        # 发送POST请求
        response = requests.post(url, json=payload, headers=headers)
        
        # 处理响应
        if response.status_code == 200:
            # 如果请求成功，返回ChatGPT的回复
            data = response.json()
            return data['choices'][0]['message']['content']
        else:
            # 如果请求失败，返回错误信息
            return f'错误: {response.status_code} - {response.text}'
    
    def analyze_user_interests(self, user_data):
        """
        分析用户兴趣
        :param user_data: 用户数据字典
        :return: 分析结果
        """
        prompt = f"""
        请分析以下用户数据，提取用户的主要兴趣和偏好：
        {json.dumps(user_data, ensure_ascii=False, indent=2)}
        
        请以JSON格式返回分析结果，包含以下字段：
        - main_interests: 主要兴趣列表
        - preferences: 偏好描述
        - potential_activities: 可能感兴趣的活动列表
        """
        
        response = self.submit(prompt)
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                "main_interests": [],
                "preferences": "无法解析兴趣分析结果",
                "potential_activities": []
            }
    
    def generate_recommendations(self, user_interests, available_activities):
        """
        生成活动推荐
        :param user_interests: 用户兴趣分析结果
        :param available_activities: 可用活动列表
        :return: 推荐活动列表
        """
        prompt = f"""
        基于以下用户兴趣和可用活动，生成个性化推荐：
        
        用户兴趣分析：
        {json.dumps(user_interests, ensure_ascii=False, indent=2)}
        
        可用活动：
        {json.dumps(available_activities, ensure_ascii=False, indent=2)}
        
        请返回一个JSON格式的推荐列表，每个推荐包含：
        - activity_name: 活动名称
        - match_score: 匹配度（0-100）
        - reason: 推荐理由
        """
        
        response = self.submit(prompt)
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return []
        
if __name__ == '__main__':
    # 测试代码
    ChatGPT_test = HKBU_ChatGPT()
    
    # 测试用户兴趣分析
    test_user_data = {
        "name": "张三",
        "age": 25,
        "interests": ["编程", "摄影", "旅行"],
        "recent_activities": ["参加编程比赛", "摄影展览"],
        "preferences": {
            "outdoor_activities": True,
            "group_activities": True,
            "learning_new_skills": True
        }
    }
    
    print("测试用户兴趣分析：")
    interests = ChatGPT_test.analyze_user_interests(test_user_data)
    print(json.dumps(interests, ensure_ascii=False, indent=2))
    
    # 测试活动推荐
    test_activities = [
        {"name": "编程工作坊", "type": "学习", "difficulty": "中级"},
        {"name": "摄影比赛", "type": "艺术", "difficulty": "初级"},
        {"name": "户外徒步", "type": "运动", "difficulty": "初级"}
    ]
    
    print("\n测试活动推荐：")
    recommendations = ChatGPT_test.generate_recommendations(interests, test_activities)
    print(json.dumps(recommendations, ensure_ascii=False, indent=2))