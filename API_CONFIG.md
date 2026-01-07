# API 配置说明

## 支持的 LLM 提供商

系统支持两种 LLM API：
1. **DeepSeek**（默认）
2. **OpenAI**

## 配置方式

### 方式一：环境变量（推荐）

在 `.env` 文件中配置：

#### 使用 DeepSeek（默认）

```bash
# 设置提供商
LLM_PROVIDER=deepseek

# 设置 API 密钥
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# 可选：自定义模型和参数
LLM_MODEL=deepseek-chat
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2000
```

#### 使用 OpenAI

```bash
# 设置提供商
LLM_PROVIDER=openai

# 设置 API 密钥
OPENAI_API_KEY=your_openai_api_key_here

# 可选：自定义模型和参数
LLM_MODEL=gpt-3.5-turbo  # 或 gpt-4, gpt-4-turbo 等
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2000
```

### 方式二：Docker Compose 环境变量

在 `docker-compose.gpu.yml` 中已经配置了环境变量传递：

```yaml
environment:
  - LLM_PROVIDER=${LLM_PROVIDER:-deepseek}
  - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY:-}
  - OPENAI_API_KEY=${OPENAI_API_KEY:-}
  - LLM_MODEL=${LLM_MODEL:-deepseek-chat}
  - LLM_TEMPERATURE=${LLM_TEMPERATURE:-0.7}
  - LLM_MAX_TOKENS=${LLM_MAX_TOKENS:-2000}
```

### 方式三：config.yaml

在 `config.yaml` 中配置：

```yaml
llm:
  provider: "deepseek"  # 或 "openai"
  model: "deepseek-chat"  # 或 "gpt-3.5-turbo"
  temperature: 0.7
  max_tokens: 2000
```

**注意**：目前代码优先使用环境变量，`config.yaml` 中的配置需要代码支持才能生效。

## 切换 API 提供商

### 在 Docker 容器中

1. **编辑 `.env` 文件**（在项目根目录）：
   ```bash
   LLM_PROVIDER=openai  # 或 deepseek
   OPENAI_API_KEY=your_key_here
   ```

2. **重启容器**：
   ```bash
   docker-compose -f docker-compose.gpu.yml restart
   ```

### 在本地运行

1. **设置环境变量**：
   ```bash
   # Windows PowerShell
   $env:LLM_PROVIDER="openai"
   $env:OPENAI_API_KEY="your_key_here"
   
   # Linux/Mac
   export LLM_PROVIDER="openai"
   export OPENAI_API_KEY="your_key_here"
   ```

2. **运行程序**：
   ```bash
   python main.py
   ```

## API 密钥优先级

系统按以下顺序查找 API 密钥：

1. 如果 `LLM_PROVIDER=deepseek`：
   - 优先使用 `DEEPSEEK_API_KEY`
   - 如果没有，尝试使用 `OPENAI_API_KEY`（作为 fallback）

2. 如果 `LLM_PROVIDER=openai`：
   - 优先使用 `OPENAI_API_KEY`
   - 如果没有，尝试使用 `DEEPSEEK_API_KEY`（作为 fallback）

**建议**：明确设置对应的 API 密钥，避免混淆。

## 支持的模型

### DeepSeek
- `deepseek-chat`（默认）
- `deepseek-coder`
- 其他 DeepSeek 模型

### OpenAI
- `gpt-3.5-turbo`（默认）
- `gpt-4`
- `gpt-4-turbo`
- `gpt-4o`
- 其他 OpenAI 模型

## 验证配置

运行测试脚本验证配置：

```bash
python test_docker.py
```

如果配置正确，系统会正常初始化并显示：
```
✅ 所有模块导入成功！
```

## 常见问题

### Q: 如何知道当前使用的是哪个 API？

A: 查看日志输出，系统启动时会显示使用的提供商和模型。

### Q: 可以同时配置两个 API 密钥吗？

A: 可以，但系统会根据 `LLM_PROVIDER` 选择使用哪个。建议只配置当前使用的 API 密钥。

### Q: 切换 API 需要重启吗？

A: 是的，需要重启容器或重新运行程序。

### Q: 如何测试不同的 API？

A: 
1. 修改 `.env` 文件中的 `LLM_PROVIDER`
2. 设置对应的 API 密钥
3. 重启系统
4. 运行测试对话
