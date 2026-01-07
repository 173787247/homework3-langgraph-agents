# 作业3：基于 LangGraph 的多角色协作智能体系统

## 项目概述

本项目实现了一个基于 LangGraph 的多角色协作智能客服系统，包含三个专业化智能体：
- **接待员 (Receptionist Agent)**: 负责用户接待、问题初步分类和引导
- **问题分析师 (Analyst Agent)**: 深入分析用户问题，提取关键信息
- **解决方案专家 (Solution Expert Agent)**: 基于分析结果提供专业解决方案

## 功能特性

✅ **多角色智能体协作**：三个不同角色的智能体协同工作  
✅ **状态管理和数据传递**：基于 LangGraph 的状态管理机制  
✅ **外部工具集成**：集成 MCP 工具（知识库查询、订单查询）  
✅ **记忆持久化**：支持多轮对话，记忆持久化存储  
✅ **条件路由和动态决策**：根据问题类型智能路由到不同智能体  
✅ **人机协同交互**：支持人工介入和确认机制  

## 技术栈

- **框架**: LangGraph, LangChain
- **LLM**: DeepSeek / OpenAI（支持切换，详见 [API_CONFIG.md](./API_CONFIG.md)）
- **记忆存储**: SQLite / PostgreSQL
- **工具集成**: MCP (Model Context Protocol)
- **API**: FastAPI
- **部署**: Docker + GPU 支持

## 项目结构

```
homework3-langgraph-agents/
├── README.md                    # 项目说明
├── ARCHITECTURE.md              # 系统架构设计文档
├── requirements.txt             # Python 依赖
├── config.yaml                  # 配置文件
├── .env.example                 # 环境变量示例
├── main.py                      # 主入口文件
├── app.py                       # FastAPI 应用
├── agents/                      # 智能体实现
│   ├── __init__.py
│   ├── base_agent.py            # 智能体基类
│   ├── receptionist_agent.py    # 接待员智能体
│   ├── analyst_agent.py         # 问题分析师智能体
│   └── solution_expert_agent.py # 解决方案专家智能体
├── workflow/                    # LangGraph 工作流
│   ├── __init__.py
│   ├── state.py                 # 状态定义
│   └── customer_service_graph.py # 客服工作流图
├── tools/                       # 外部工具
│   ├── __init__.py
│   ├── mcp_tools.py             # MCP 工具集成
│   ├── knowledge_base_tool.py   # 知识库查询工具
│   └── order_query_tool.py      # 订单查询工具
├── memory/                      # 记忆管理
│   ├── __init__.py
│   ├── memory_store.py          # 记忆存储
│   └── conversation_manager.py  # 对话管理
├── utils/                       # 工具函数
│   ├── __init__.py
│   └── logger.py                # 日志工具
└── tests/                       # 测试文件
    ├── __init__.py
    └── test_workflow.py         # 工作流测试
```

## 安装和运行

### 方式一：Docker 运行（推荐，支持 GPU）

**前提条件：**
- 已安装 Docker Desktop
- 已启用 GPU 支持（NVIDIA GPU）
- 已创建 `.env` 文件并配置 API 密钥

```bash
# 1. 创建 .env 文件（如果还没有）
cp .env.example .env
# 编辑 .env 文件，填入 DEEPSEEK_API_KEY 或 OPENAI_API_KEY

# 2. 使用 Docker Compose 启动
docker-compose -f docker-compose.gpu.yml up -d

# 3. 查看容器状态
docker-compose -f docker-compose.gpu.yml ps

# 4. 进入容器
docker exec -it homework3-langgraph-agents-gpu bash

# 5. 在容器内运行测试
docker exec -it homework3-langgraph-agents-gpu python test_docker.py

# 6. 在容器内运行命令行模式
docker exec -it homework3-langgraph-agents-gpu python main.py

# 7. 在容器内启动 FastAPI 服务（后台运行）
docker exec -d homework3-langgraph-agents-gpu python app.py

# 8. 查看日志
docker logs homework3-langgraph-agents-gpu

# 9. 停止容器
docker-compose -f docker-compose.gpu.yml down
```

### 方式二：本地运行

```bash
# 1. 克隆项目
git clone <repository-url>
cd homework3-langgraph-agents

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入 API 密钥等配置

# 4. 运行测试
python test_docker.py

# 5. 运行示例
# 命令行交互模式
python main.py

# 或启动 FastAPI 服务
python app.py
```

### 3. Docker 运行（推荐，支持 GPU）

```bash
# 使用 Docker Compose 启动（支持 GPU）
docker-compose -f docker-compose.gpu.yml up -d

# 查看容器状态
docker-compose -f docker-compose.gpu.yml ps

# 进入容器
docker exec -it homework3-langgraph-agents-gpu bash

# 在容器内运行命令行模式
docker exec -it homework3-langgraph-agents-gpu python main.py

# 在容器内启动 FastAPI 服务
docker exec -it homework3-langgraph-agents-gpu python app.py

# 查看日志
docker logs homework3-langgraph-agents-gpu

# 停止容器
docker-compose -f docker-compose.gpu.yml down
```

**注意**：使用 Docker 前，请确保：
1. 已安装 Docker Desktop 并启用 GPU 支持
2. 已创建 `.env` 文件并配置了 API 密钥
3. 确保 Docker Desktop 已分配足够的资源（建议至少 4GB 内存）

## 使用示例

### 命令行交互

```python
from workflow.customer_service_graph import CustomerServiceGraph

# 初始化工作流
graph = CustomerServiceGraph()

# 开始对话
response = graph.process_message(
    user_id="user123",
    message="我的订单什么时候能到？"
)
print(response)
```

### API 调用

```bash
# 发送消息
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "message": "我的订单什么时候能到？"
  }'
```

## 系统架构

详见 [ARCHITECTURE.md](./ARCHITECTURE.md)

## 演示视频

[待上传] 演示视频将展示：
1. 系统启动和初始化
2. 多轮对话示例
3. 智能体协作流程
4. 工具调用演示
5. 记忆持久化验证

## 评分标准对照

| 评分项 | 实现情况 |
|--------|---------|
| 功能完整性（40%）| ✅ 3个智能体、状态管理、工具集成、记忆持久化、条件路由 |
| 代码质量（20%）| ✅ 模块化设计、类型注解、错误处理、日志记录 |
| 架构设计（20%）| ✅ LangGraph 工作流、MCP 工具集成、记忆管理 |
| 创新性（10%）| ✅ 智能路由决策、人机协同机制 |
| 文档完善度（10%）| ✅ README、架构文档、代码注释 |

## 参考文献

- LangGraph 官方文档: https://langchain-ai.github.io/langgraph/
- MCP 协议文档: https://modelcontextprotocol.io/
- LangChain 文档: https://python.langchain.com/

## 许可证

MIT License
