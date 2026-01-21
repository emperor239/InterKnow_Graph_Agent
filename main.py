import uvicorn 
import os
import shutil
import time
import threading
from pymongo import MongoClient
import random 

# 清理__pycache__
def clean_pycache():
    for dirpath, dirnames, filenames in os.walk(os.getcwd()):
        if "__pycache__" in dirnames:
            pycache_path = os.path.join(dirpath, "__pycache__")
            shutil.rmtree(pycache_path)            

# 模拟其他用户在更新使用
def simulation_other_users():
    while True:
        mongodb_client = MongoClient(
            "mongodb://ecnu10235501426:ECNU10235501426@dds-uf6800965d405e14-pub.mongodb.rds.aliyuncs.com:3717/admin",
            serverSelectionTimeoutMS=10000,
            connectTimeoutMS=10000,
        )
        db = mongodb_client['ecnu10235501426']
        users_col = db['users']
        counts = random.randint(20, 40)
        users_col.update_one( 
            {
                "total_tokens": {"$exists": True},
                "total_counts": {"$exists": True},
                "$expr": {"$eq": [{"$size": {"$objectToArray": "$$ROOT"}}, 3]}
            }, 
            {
                "$inc": {
                    "total_tokens": int(counts * random.randint(3000, 8000) /1000), 
                    "total_counts": counts
                }
        })
        time.sleep(2)

if __name__ == "__main__":
    threading.Thread(target=simulation_other_users, daemon=True).start()
    uvicorn.run(
        "backend.routing.router:app",
        host="0.0.0.0",
        port=8000,
        workers=2
    )
    clean_pycache()