# 快速开始指南

## 使用 Docker 运行（推荐）

### 1. 准备工作

确保已安装：
- Docker Desktop（已启用 GPU 支持）
- Git

### 2. 配置环境变量

```bash
# 创建 .env 文件
cd homework3-langgraph-agents
cp .env.example .env

# 编辑 .env 文件，填入你的 API 密钥
# DEEPSEEK_API_KEY=your_api_key_here
# 或
# OPENAI_API_KEY=your_api_key_here
```

### 3. 启动 Docker 容器

```bash
# 构建并启动容器（支持 GPU）
docker-compose -f docker-compose.gpu.yml up -d

# 查看容器状态
docker-compose -f docker-compose.gpu.yml ps

# 查看日志
docker logs homework3-langgraph-agents-gpu
```

### 4. 测试系统

```bash
# 进入容器
docker exec -it homework3-langgraph-agents-gpu bash

# 在容器内运行测试
python test_docker.py

# 如果测试通过，可以运行系统
python main.py
```

### 5. 启动 FastAPI 服务

```bash
# 在容器内启动服务（后台运行）
docker exec -d homework3-langgraph-agents-gpu python app.py

# 或者在前台运行（可以看到日志）
docker exec -it homework3-langgraph-agents-gpu python app.py
```

服务启动后，可以通过以下方式访问：
- API 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/api/health

### 6. 测试 API

```bash
# 使用 curl 测试
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "message": "我的订单什么时候能到？"
  }'
```

## 本地运行（不使用 Docker）

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
# Windows PowerShell
$env:DEEPSEEK_API_KEY="your_api_key_here"

# Linux/Mac
export DEEPSEEK_API_KEY="your_api_key_here"
```

### 3. 运行测试

```bash
python test_docker.py
```

### 4. 运行系统

```bash
# 命令行模式
python main.py

# 或 FastAPI 服务
python app.py
```

## 常见问题

### Q: Docker 容器无法启动 GPU？

A: 确保：
1. Docker Desktop 已启用 GPU 支持
2. 已安装 NVIDIA Container Toolkit
3. 在 Docker Desktop 设置中启用 GPU 支持

### Q: 提示缺少模块？

A: 在容器内运行：
```bash
docker exec -it homework3-langgraph-agents-gpu pip install -r requirements.txt
```

### Q: API 密钥在哪里配置？

A: 在 `.env` 文件中配置，或通过环境变量设置。

### Q: 如何查看日志？

A: 
```bash
# Docker 日志
docker logs homework3-langgraph-agents-gpu

# 本地日志文件
cat logs/app.log
```

## 下一步

- 查看 [README.md](./README.md) 了解详细功能
- 查看 [ARCHITECTURE.md](./ARCHITECTURE.md) 了解系统架构
- 运行示例对话测试系统功能
