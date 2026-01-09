# Docker 重启后的准备脚本
# 确保所有文件都复制到容器中，并重启服务

Write-Host "等待 Docker Desktop 完全启动..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

Write-Host "检查容器状态..." -ForegroundColor Cyan
docker ps -a | Select-String "homework3-langgraph-agents-gpu"

Write-Host "`n复制所有工具文件到容器..." -ForegroundColor Cyan
docker cp tools/. homework3-langgraph-agents-gpu:/app/tools/

Write-Host "复制测试文件..." -ForegroundColor Cyan
docker cp test_date_format.py homework3-langgraph-agents-gpu:/app/ 2>$null

Write-Host "`n测试日期查询工具..." -ForegroundColor Cyan
docker exec homework3-langgraph-agents-gpu python /app/test_date_format.py

Write-Host "`n重启 Web 服务..." -ForegroundColor Cyan
docker exec homework3-langgraph-agents-gpu pkill -f "python app.py" 2>$null
Start-Sleep -Seconds 2
docker exec -d homework3-langgraph-agents-gpu python app.py

Write-Host "`n完成！Web 服务运行在 http://localhost:8000" -ForegroundColor Green
