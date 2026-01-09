#!/bin/bash
echo "2026-01-09 08:00:00 INFO - 系统启动成功" > /app/logs/app.log
echo "2026-01-09 08:01:00 INFO - 用户登录" >> /app/logs/app.log
echo "2026-01-09 08:02:00 INFO - 查询天气：北京" >> /app/logs/app.log
echo "2026-01-09 08:03:00 INFO - 查询火车票：北京到上海" >> /app/logs/app.log
cat /app/logs/app.log
