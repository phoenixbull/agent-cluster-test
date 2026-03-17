FROM python:3.9-slim

WORKDIR /app

# 复制代码
COPY /test /app/

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt || true

# 暴露端口
EXPOSE 8080

# 启动命令
CMD ["python", "app.py"]
