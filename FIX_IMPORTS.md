# 修复导入问题说明

## 问题
在 Docker 容器中运行时，遇到了相对导入错误：`attempted relative import beyond top-level package`

## 解决方案
已修复所有模块的导入问题，现在所有文件都使用绝对导入，并自动添加项目根目录到 `sys.path`。

## 需要安装的依赖

在 Docker 容器内运行：

```bash
pip install python-dotenv pyyaml
```

或者重新安装所有依赖：

```bash
pip install -r requirements.txt
```

## 测试

修复后，重新运行测试：

```bash
python test_docker.py
```

应该能看到所有测试通过。
