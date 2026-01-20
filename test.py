import pymongo
client = pymongo.MongoClient("mongodb://ecnu10235501426:ECNU10235501426@dds-uf6800965d405e14-pub.mongodb.rds.aliyuncs.com:3717/admin")
print(client.list_database_names())
db = client['ecnu10235501426']
print(client.list_database_names())
users_col = db['users']
users_col.delete_many({})