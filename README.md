# InterKnow_Graph_Agent
云计算大作业都在这里


docker build -t interknow_graph_agent .

docker run -p 8000:8000 interknow_graph_agent

http://127.0.0.1:8000/graph.html

docker container prune

docker rm -f $(docker ps -aq)