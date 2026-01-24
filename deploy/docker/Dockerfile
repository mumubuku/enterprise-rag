FROM ccr.ccs.tencentyun.com/library/python:3.10

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 使用清华镜像源安装Python包
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

COPY . .

RUN mkdir -p /app/uploads /app/temp /app/data/chroma /app/logs

EXPOSE 8000

CMD ["python", "-m", "src.api.main"]