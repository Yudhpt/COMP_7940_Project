import json
import firebase_admin
from firebase_admin import credentials, firestore
import os

# 初始化Firebase
def initialize_firebase():
    try:
        # 检查服务账号文件是否存在
        if not os.path.exists("serviceAccountKey.json"):
            raise FileNotFoundError("serviceAccountKey.json 文件不存在")
            
        # 读取并验证服务账号文件
        with open("serviceAccountKey.json", 'r') as f:
            service_account = json.load(f)
            
        # 验证必要的字段
        required_fields = ['project_id', 'private_key', 'client_email']
        for field in required_fields:
            if field not in service_account:
                raise ValueError(f"serviceAccountKey.json 缺少必要字段: {field}")
        
        # 初始化Firebase
        cred = credentials.Certificate("serviceAccountKey.json")
        firebase_admin.initialize_app(cred)
        return firestore.client()
        
    except Exception as e:
        print(f"Firebase初始化失败: {str(e)}")
        raise

# 批量上传数据
def upload_data(db, collection_name, json_file):
    try:
        # 检查集合是否存在写入权限
        test_doc = db.collection(collection_name).document('test_permission')
        test_doc.set({'test': True})
        test_doc.delete()
        
        # 读取JSON文件
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 批量写入
        batch = db.batch()
        collection_ref = db.collection(collection_name)
        
        for item in data:
            # 使用活动名称作为文档ID
            doc_ref = collection_ref.document(item['name'])
            batch.set(doc_ref, item)
        
        batch.commit()
        print(f"成功上传 {len(data)} 条数据到 {collection_name} 集合")
        
    except Exception as e:
        print(f"上传失败: {str(e)}")
        if "Missing or insufficient permissions" in str(e):
            print("请检查以下可能的原因：")
            print("1. 服务账号没有足够的权限")
            print("2. Firebase规则限制了写入操作")
            print("3. 集合名称可能不正确")
            print("4. 服务账号可能已过期或被撤销")

if __name__ == "__main__":
    try:
        db = initialize_firebase()
        upload_data(db, "Activities", "sample.json")
    except Exception as e:
        print(f"程序执行失败: {str(e)}")