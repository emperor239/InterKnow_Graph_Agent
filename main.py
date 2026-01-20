import uvicorn 
import os
import shutil

# 清理__pycache__
def clean_pycache():
    for dirpath, dirnames, filenames in os.walk(os.getcwd()):
        if "__pycache__" in dirnames:
            pycache_path = os.path.join(dirpath, "__pycache__")
            shutil.rmtree(pycache_path)            

if __name__ == "__main__":
    uvicorn.run(
        "backend.routing.router:router",
        host="127.0.0.1",
        port=8000,
        workers=4
    )
    clean_pycache()