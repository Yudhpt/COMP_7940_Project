import json
import firebase_admin
from firebase_admin import credentials, firestore
from typing import List, Dict, Any, Optional
import os
from datetime import datetime
from configparser import RawConfigParser
from pathlib import Path

class DatabaseManager:
    def __init__(self, config_path: str = "config.ini"):
        """
        初始化数据库管理器
        :param config_path: 配置文件路径
        """
        self.config_path = config_path
        self.db = None
        self._initialize_firebase()

    def _initialize_firebase(self):
        """
        初始化 Firebase 连接
        """
        try:
            if not firebase_admin._apps:
                config = self._load_config()
                cred = credentials.Certificate(config['firebase_config'])
                firebase_admin.initialize_app(cred)
                print("Firebase initialized successfully")
            
            self.db = firestore.client()
            print("Successfully connected to Firestore")
            
        except Exception as e:
            print(f"Firebase initialization failed: {str(e)}")
            raise

    def _load_config(self) -> Dict[str, Any]:
        """
        加载配置，优先从环境变量读取，其次从配置文件读取
        """
        config = {}
        config_parser = RawConfigParser()
        
        # 如果配置文件存在，读取配置
        if os.path.exists(self.config_path):
            config_parser.read(self.config_path)
        
        # 从环境变量或配置文件获取 Firebase 配置
        firebase_config = {
            "type": "service_account",
            "project_id": os.getenv('FIREBASE_PROJECT_ID') or config_parser.get('FIREBASE', 'PROJECT_ID', fallback=None),
            "private_key_id": os.getenv('FIREBASE_PRIVATE_KEY_ID') or config_parser.get('FIREBASE', 'PRIVATE_KEY_ID', fallback=None),
            "private_key": (os.getenv('FIREBASE_PRIVATE_KEY') or config_parser.get('FIREBASE', 'PRIVATE_KEY', fallback=None)).replace('\\n', '\n'),
            "client_email": os.getenv('FIREBASE_CLIENT_EMAIL') or config_parser.get('FIREBASE', 'CLIENT_EMAIL', fallback=None),
            "client_id": os.getenv('FIREBASE_CLIENT_ID') or config_parser.get('FIREBASE', 'CLIENT_ID', fallback=None),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": os.getenv('FIREBASE_CLIENT_CERT_URL') or config_parser.get('FIREBASE', 'CLIENT_CERT_URL', fallback=None)
        }
        
        # 验证必要的配置是否存在
        required_fields = ['project_id', 'private_key', 'client_email']
        missing_fields = [field for field in required_fields if not firebase_config.get(field)]
        
        if missing_fields:
            raise ValueError(f"Missing required Firebase configuration: {', '.join(missing_fields)}")
        
        return {'firebase_config': firebase_config}

    def create_activity(self, activity: Dict[str, Any]) -> bool:
        """
        创建新活动
        :param activity: 活动数据
        :return: 是否成功
        """
        try:
            # 数据清洗
            cleaned_activity = self._clean_activity_data(activity)
            
            # 使用活动名称作为文档ID
            doc_ref = self.db.collection('Activities').document(cleaned_activity['name'])
            doc_ref.set(cleaned_activity)
            return True
        except Exception as e:
            print(f"Error creating activity: {str(e)}")
            return False

    def read_activity(self, activity_name: str) -> Optional[Dict[str, Any]]:
        """
        读取活动信息
        :param activity_name: 活动名称
        :return: 活动数据或None
        """
        try:
            doc_ref = self.db.collection('Activities').document(activity_name)
            doc = doc_ref.get()
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            print(f"Error reading activity: {str(e)}")
            return None

    def update_activity(self, activity_name: str, updates: Dict[str, Any]) -> bool:
        """
        更新活动信息
        :param activity_name: 活动名称
        :param updates: 要更新的字段
        :return: 是否成功
        """
        try:
            # 数据清洗
            cleaned_updates = self._clean_activity_data(updates)
            
            doc_ref = self.db.collection('Activities').document(activity_name)
            doc_ref.update(cleaned_updates)
            return True
        except Exception as e:
            print(f"Error updating activity: {str(e)}")
            return False

    def delete_activity(self, activity_name: str) -> bool:
        """
        删除活动
        :param activity_name: 活动名称
        :return: 是否成功
        """
        try:
            doc_ref = self.db.collection('Activities').document(activity_name)
            doc_ref.delete()
            return True
        except Exception as e:
            print(f"Error deleting activity: {str(e)}")
            return False

    def merge_activities(self, activities: List[Dict[str, Any]], merge_strategy: str = 'update') -> Dict[str, int]:
        """
        合并活动数据
        :param activities: 活动列表
        :param merge_strategy: 合并策略 ('update' 或 'skip')
        :return: 统计信息
        """
        stats = {'created': 0, 'updated': 0, 'skipped': 0, 'failed': 0}
        
        for activity in activities:
            try:
                # 数据清洗
                cleaned_activity = self._clean_activity_data(activity)
                
                doc_ref = self.db.collection('Activities').document(cleaned_activity['name'])
                doc = doc_ref.get()
                
                if doc.exists and merge_strategy == 'skip':
                    stats['skipped'] += 1
                    continue
                
                if doc.exists:
                    doc_ref.update(cleaned_activity)
                    stats['updated'] += 1
                else:
                    doc_ref.set(cleaned_activity)
                    stats['created'] += 1
                    
            except Exception as e:
                print(f"Error merging activity {activity.get('name', 'unknown')}: {str(e)}")
                stats['failed'] += 1
                
        return stats

    def _clean_activity_data(self, activity: Dict[str, Any]) -> Dict[str, Any]:
        """
        清洗活动数据
        :param activity: 原始活动数据
        :return: 清洗后的活动数据
        """
        cleaned = activity.copy()
        
        # 确保必需字段存在
        required_fields = ['name', 'description', 'keywords', 'link', 'category']
        for field in required_fields:
            if field not in cleaned:
                cleaned[field] = ''
        
        # 清理名称
        cleaned['name'] = cleaned['name'].strip()
        
        # 清理描述
        cleaned['description'] = cleaned['description'].strip()
        
        # 清理关键词
        if isinstance(cleaned['keywords'], str):
            cleaned['keywords'] = [kw.strip() for kw in cleaned['keywords'].split(',')]
        elif isinstance(cleaned['keywords'], list):
            cleaned['keywords'] = [kw.strip() for kw in cleaned['keywords']]
        else:
            cleaned['keywords'] = []
        
        # 清理链接
        cleaned['link'] = cleaned['link'].strip()
        
        # 清理类别
        cleaned['category'] = cleaned['category'].strip()
        
        # 添加时间戳
        cleaned['last_updated'] = datetime.now().isoformat()
        
        return cleaned

    def search_activities(self, 
                         interests: List[str] = None, 
                         categories: List[str] = None,
                         limit: int = 10) -> List[Dict[str, Any]]:
        """
        搜索活动
        :param interests: 兴趣关键词列表
        :param categories: 类别列表
        :param limit: 返回结果数量限制
        :return: 匹配的活动列表
        """
        try:
            query = self.db.collection('Activities')
            
            # 添加类别过滤
            if categories:
                query = query.where(filter=firestore.FieldFilter('category', 'in', categories))
            
            # 获取结果
            results = query.limit(limit).stream()
            activities = [doc.to_dict() for doc in results]
            
            # 如果提供了兴趣关键词，进行过滤
            if interests:
                activities = [
                    activity for activity in activities
                    if any(keyword.lower() in [interest.lower() for interest in interests]
                          for keyword in activity.get('keywords', []))
                ]
            
            return activities
            
        except Exception as e:
            print(f"Error searching activities: {str(e)}")
            return []

    def export_activities(self, output_file: str) -> bool:
        """
        导出所有活动数据
        :param output_file: 输出文件路径
        :return: 是否成功
        """
        try:
            activities = []
            docs = self.db.collection('Activities').stream()
            
            for doc in docs:
                activities.append(doc.to_dict())
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(activities, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"Error exporting activities: {str(e)}")
            return False

    def import_activities(self, input_file: str, merge_strategy: str = 'update') -> Dict[str, int]:
        """
        导入活动数据
        :param input_file: 输入文件路径
        :param merge_strategy: 合并策略
        :return: 统计信息
        """
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                activities = json.load(f)
            
            return self.merge_activities(activities, merge_strategy)
        except Exception as e:
            print(f"Error importing activities: {str(e)}")
            return {'created': 0, 'updated': 0, 'skipped': 0, 'failed': 0}

if __name__ == "__main__":
    # 测试代码
    try:
        # 初始化数据库管理器
        db_manager = DatabaseManager()
        
        # 测试创建活动
        test_activity = {
            "name": "Test Activity",
            "description": "This is a test activity",
            "keywords": ["test", "example"],
            "link": "https://example.com",
            "category": "Test"
        }
        
        if db_manager.create_activity(test_activity):
            print("Activity created successfully")
        
        # 测试读取活动
        activity = db_manager.read_activity("Test Activity")
        if activity:
            print("Activity found:", activity)
        
        # 测试更新活动
        updates = {
            "description": "Updated description",
            "keywords": ["test", "example", "updated"]
        }
        if db_manager.update_activity("Test Activity", updates):
            print("Activity updated successfully")
        
        # 测试搜索活动
        results = db_manager.search_activities(
            interests=["test"],
            categories=["Test"],
            limit=5
        )
        print(f"Found {len(results)} matching activities")
        
        # 测试导出活动
        if db_manager.export_activities("activities_export.json"):
            print("Activities exported successfully")
        
        # 测试导入活动
        stats = db_manager.import_activities("sample.json", merge_strategy='update')
        print("Import statistics:", stats)
        
        # 测试删除活动
        if db_manager.delete_activity("Test Activity"):
            print("Activity deleted successfully")
            
    except Exception as e:
        print(f"Test failed: {str(e)}") 