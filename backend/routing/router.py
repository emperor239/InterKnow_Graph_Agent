from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import Response
from backend.models.llm_graph_builder import build_knowledge_graph
from backend.models.bloom_filter import BloomFilter
from pymongo import MongoClient    
import asyncio
import os
import time

app = FastAPI()
mongodb_client = None
users_col = None
templates = Jinja2Templates(directory="frontend/templates")
app.mount("/frontend/static", StaticFiles(directory="frontend/static"), name="frontend/static")
bf = BloomFilter(expected_elements=100, false_positive_rate=0.001)

# 开关服务器
@app.on_event("startup")
async def startup_event():
    global mongodb_client, users_col
    while True:
        try:
            mongodb_client = MongoClient(
                "mongodb://ecnu10235501426:ECNU10235501426@dds-uf6800965d405e14-pub.mongodb.rds.aliyuncs.com:3717/admin",
                serverSelectionTimeoutMS=10000,
                connectTimeoutMS=10000,
            )
            db = mongodb_client['ecnu10235501426']
            users_col = db['users']
            await asyncio.to_thread(users_col.delete_many, {})
            await asyncio.to_thread(
                users_col.insert_one, 
                {
                    "total_tokens": 50,
                    "total_counts": 250
                }
            )

            # 删除所有索引
            indexes = await asyncio.to_thread(users_col.list_indexes)
            for idx in indexes:
                if idx["name"] != "_id_":
                    await asyncio.to_thread(users_col.drop_index, idx["name"])
            
            # 给name建非唯一索引
            await asyncio.to_thread(users_col.create_index, "name")
            
            print(f"进程 {os.getpid()} 的 MongoDB 初始化成功")
            break
        except Exception as e:
            print(f"进程 {os.getpid()} 的 MongoDB 初始化失败：{str(e)}")


@app.on_event("shutdown")
async def shutdown_event():
    if mongodb_client:
        await asyncio.to_thread(mongodb_client.close)
        print(f"进程 {os.getpid()} 的MongoDB 连接已关闭")

# 功能路由
@app.post("/api/graph")
async def build_graph(request: Request):
    try:
        data = await request.json()
        concept = (data.get("concept") or "").strip()
        if not concept:
            return {"error": "empty concept", "nodes": [], "links": []}
        
        original_data = None

        global bf

        print("start")
        start = time.time()
        if bf.contains(concept):
            doct = dict(await asyncio.to_thread(
                lambda: users_col.find_one({"concept": concept}, {"_id": 0})  
            ))
            original_data = doct["graph"]
            print("Bloom Filter 热查询命中")
        else: 
            original_data = await asyncio.to_thread(build_knowledge_graph, concept)
            await asyncio.to_thread(users_col.insert_one, {"concept": concept, "graph": original_data})
            bf.add(concept)
        end = time.time()
        print("end")
        print(f"{end-start}")
        
        await asyncio.to_thread(
            users_col.update_one, 
            {
                "total_tokens": {"$exists": True},
                "total_counts": {"$exists": True},
                "$expr": {"$eq": [{"$size": {"$objectToArray": "$$ROOT"}}, 3]}
            }, 
            {
                "$inc": {
                    "total_tokens": int(original_data.get("tokens", 0)/1000), 
                    "total_counts": 1
                }
            }
        )
        
        nodes=[]
        links=[]
        for node in original_data["nodes"]:
            nodes.append({"id":node["id"],"name":node["name"],"discipline":node["discipline"],"value":node["value"],"description":node["description"]})
        for link in original_data["links"]:
            sourseName = [node["name"] for node in original_data["nodes"] if node["id"] == link["source"]]
            targetName = [node["name"] for node in original_data["nodes"] if node["id"] == link["target"]]
            links.append({"source":link["source"],"target":link["target"],"sourseName":sourseName,"targetName":targetName,"relation":link["relation"],"description":link["description"]})
        graph={"nodes":nodes, "links":links}
        return graph

    except Exception as e:
        return {"error": str(e), "nodes": [], "links": []}

@app.post("/api/counts_and_tokens")
async def counts_and_tokens(request: Request):
    try:
        docs = dict(await asyncio.to_thread(
            lambda: users_col.find_one({"total_tokens": {"$exists": True}, "total_counts": {"$exists": True}}, {"_id": 0})  
        ))
        return {
            "total_counts": docs.get("total_counts",0),
            "total_tokens": docs.get("total_tokens",0)
        }

    except Exception as e:
        return {"error": str(e)}


# 页面路由
@app.get("/index.html", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/favicon.ico")
async def favicon():
    return Response(status_code=200)

@app.get("/graph.html", response_class=HTMLResponse)
async def calculator2(request: Request):
    return templates.TemplateResponse("graph.html", {"request": request})

@app.get("/technologies.html", response_class=HTMLResponse)
async def calculator2(request: Request):
    return templates.TemplateResponse("technologies.html", {"request": request})