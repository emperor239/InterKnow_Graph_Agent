import pymongo
client = pymongo.MongoClient("mongodb://ecnu10235501426:ECNU10235501426@dds-uf6800965d405e14-pub.mongodb.rds.aliyuncs.com:3717/admin")
db = client['ecnu10235501426']
users_col = db['users']
result = users_col.find({}, {"_id": 0})
print(list(result))

