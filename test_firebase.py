import firebase_admin
from firebase_admin import credentials, firestore
import json
import os

def test_firebase_connection():
    try:
        # 检查服务账号文件
        if not os.path.exists("serviceAccountKey.json"):
            print("错误: serviceAccountKey.json 文件不存在")
            return False
            
        # 读取并验证服务账号文件
        with open("serviceAccountKey.json", 'r') as f:
            service_account = json.load(f)
            
        # 验证必要的字段
        required_fields = ['project_id', 'private_key', 'client_email']
        for field in required_fields:
            if field not in service_account:
                print(f"错误: serviceAccountKey.json 缺少必要字段: {field}")
                return False
        
        # 打印项目信息
        print(f"项目ID: {service_account['project_id']}")
        print(f"客户端邮箱: {service_account['client_email']}")
        
        # 初始化Firebase
        cred = credentials.Certificate("serviceAccountKey.json")
        firebase_admin.initialize_app(cred)
        
        # 获取Firestore实例
        db = firestore.client()
        
        # 测试读取权限
        print("\n测试读取权限...")
        collections = db.collections()
        for collection in collections:
            print(f"找到集合: {collection.id}")
        
        # 测试写入权限
        print("\n测试写入权限...")
        test_collection = db.collection("test_collection")
        test_doc = test_collection.document("test_doc")
        test_doc.set({"test": "success"})
        print("写入测试成功")
        
        # 清理测试数据
        test_doc.delete()
        print("清理测试数据成功")
        
        return True
        
    except Exception as e:
        print(f"错误: {str(e)}")
        if "Missing or insufficient permissions" in str(e):
            print("\n权限错误，请检查：")
            print("1. 确保服务账号具有正确的权限")
            print("2. 检查Firestore规则")
            print("3. 确认服务账号未过期")
        return False

if __name__ == "__main__":
    print("开始测试Firebase连接...")
    success = test_firebase_connection()
    if success:
        print("\nFirebase连接测试成功！")
    else:
        print("\nFirebase连接测试失败！") 