# SalaryHelper 部署方案

## 概述

本文档提供 SalaryHelper 应用的完整部署蓝图，涵盖前端、后端、数据库、容器化、CI/CD、安全监控等各个方面的生产环境部署指南。

---

## 1. 前端部署方案

### 1.1 静态资源打包与版本控制

#### 构建优化
```bash
# 资源压缩与版本化
#!/bin/bash
# package_static.sh 改进版
VERSION=$(git rev-parse --short HEAD)
TIMESTAMP=$(date +%Y%m%d%H%M%S)

# 创建版本化目录
mkdir -p dist/v${VERSION}_${TIMESTAMP}

# 复制并压缩静态资源
cp -r static/* dist/v${VERSION}_${TIMESTAMP}/

# 压缩 JS/CSS
find dist/v${VERSION}_${TIMESTAMP} -name "*.js" -exec uglifyjs -o {} {} \;
find dist/v${VERSION}_${TIMESTAMP} -name "*.css" -exec cleancss -o {} {} \;

# 生成版本映射文件
echo "{\"version\": \"v${VERSION}_${TIMESTAMP}\", \"path\": \"/v${VERSION}_${TIMESTAMP}/\"}" > dist/version.json
```

#### 文件版本策略
- 使用 Git commit hash + 时间戳作为版本号
- 静态资源路径包含版本信息：`/static/v1.2.3_abc123/styles.css`
- HTML 文件引用版本化资源，支持缓存控制

### 1.2 对象存储 + CDN 架构

#### 推荐方案
```yaml
# 阿里云 OSS + CDN 配置
oss_config:
  bucket: salaryhelper-static
  region: oss-cn-hangzhou
  endpoint: https://salaryhelper-static.oss-cn-hangzhou.aliyuncs.com
  
cdn_config:
  domain: cdn.salaryhelper.com
  cache_rules:
    - pattern: "*.js"
      ttl: 31536000  # 1年
    - pattern: "*.css"
      ttl: 2592000   # 30天
    - pattern: "*.png,*.jpg,*.svg"
      ttl: 604800    # 7天
    - pattern: "*.html"
      ttl: 3600      # 1小时
```

#### 部署脚本
```bash
#!/bin/bash
# deploy_static.sh
ossutil cp -r dist/ oss://salaryhelper-static/
# 刷新 CDN 缓存
curl -X POST "https://cdn.aliyuncs.com/refresh" \
  -d "{\"ObjectPath\": [\"https://cdn.salaryhelper.com/*\"]}"
```

### 1.3 生产级 Nginx 配置

```nginx
# /etc/nginx/sites-available/salaryhelper
server {
    listen 443 ssl http2;
    server_name www.salaryhelper.com salaryhelper.com;
    
    # SSL 配置
    ssl_certificate /etc/ssl/certs/salaryhelper.com.crt;
    ssl_certificate_key /etc/ssl/private/salaryhelper.com.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    
    # 安全头
    add_header Strict-Transport-Security "max-age=63072000" always;
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self';";
    
    # Gzip/Brotli 压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
    
    brotli on;
    brotli_comp_level 6;
    brotli_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
    
    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }
    
    # HTML 文件缓存
    location ~* \.html$ {
        expires 1h;
        add_header Cache-Control "public, must-revalidate";
    }
    
    # API 代理
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时配置
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
    
    # SPA 路由支持
    location / {
        try_files $uri $uri/ /index.html;
        root /var/www/salaryhelper;
    }
    
    # 健康检查
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}

# HTTP 重定向到 HTTPS
server {
    listen 80;
    server_name www.salaryhelper.com salaryhelper.com;
    return 301 https://$server_name$request_uri;
}
```

### 1.4 域名管理与 SSL/TLS

#### 域名配置
- 主域名：`salaryhelper.com`
- CDN 域名：`cdn.salaryhelper.com`
- API 域名：`api.salaryhelper.com`

#### SSL/TLS 自动化
```bash
# Let's Encrypt 自动续期
#!/bin/bash
# ssl_renew.sh
certbot renew --quiet --no-self-upgrade
nginx -s reload

# 添加到 crontab
0 2 * * * /opt/scripts/ssl_renew.sh
```

---

## 2. 后端部署方案

### 2.1 FastAPI 生产配置

#### Gunicorn + Uvicorn 配置
```python
# gunicorn_conf.py
import multiprocessing

bind = "0.0.0.0:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 30
keepalive = 2
preload_app = True

# 日志配置
accesslog = "/var/log/salaryhelper/access.log"
errorlog = "/var/log/salaryhelper/error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# 进程管理
daemon = False
pidfile = "/var/run/salaryhelper/gunicorn.pid"
user = "salaryhelper"
group = "salaryhelper"
```

#### 启动命令
```bash
# 生产环境启动
gunicorn -c gunicorn_conf.py app.main:app

# 开发环境启动
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2.2 反向代理与 API 网关

#### Nginx API 网关配置
```nginx
upstream backend {
    least_conn;
    server backend1:8000 weight=1 max_fails=3 fail_timeout=30s;
    server backend2:8000 weight=1 max_fails=3 fail_timeout=30s;
    keepalive 32;
}

server {
    listen 443 ssl http2;
    server_name api.salaryhelper.com;
    
    # 限流配置
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;
    
    location / {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 连接池优化
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        
        # 超时配置
        proxy_connect_timeout 5s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # 健康检查
    location /api/v1/health {
        proxy_pass http://backend;
        access_log off;
    }
}
```

### 2.3 环境变量与密钥管理

#### 环境配置
```bash
# /etc/environment/salaryhelper.prod
export DATABASE_URL="postgresql://user:pass@db:5432/salaryhelper"
export REDIS_URL="redis://redis:6379/0"
export SECRET_KEY="your-production-secret-key"
export JWT_SECRET_KEY="your-jwt-secret-key"
export ALGORITHM="HS256"
export ACCESS_TOKEN_EXPIRE_MINUTES=30

# 第三方服务
export SMS_PROVIDER="aliyun"
export SMS_ACCESS_KEY="your-sms-key"
export SMS_SECRET_KEY="your-sms-secret"

# 文件存储
export STORAGE_TYPE="oss"
export OSS_BUCKET="salaryhelper-uploads"
export OSS_REGION="oss-cn-hangzhou"
export OSS_ACCESS_KEY="your-oss-key"
export OSS_SECRET_KEY="your-oss-secret"

# 监控配置
export SENTRY_DSN="https://your-sentry-dsn"
export LOG_LEVEL="INFO"
```

#### 密钥管理（使用 HashiCorp Vault）
```bash
# Vault 配置示例
vault kv put secret/salaryhelper/database \
  username=salaryhelper \
  password=$(openssl rand -base64 32)

vault kv put secret/salaryhelper/jwt \
  secret_key=$(openssl rand -base64 64)
```

### 2.4 配置分离

#### 配置文件结构
```
config/
├── base.py           # 基础配置
├── development.py    # 开发环境
├── testing.py        # 测试环境
├── staging.py        # 预发布环境
└── production.py     # 生产环境
```

#### 配置加载
```python
# config/base.py
from pydantic import BaseSettings

class BaseSettings(BaseSettings):
    app_name: str = "SalaryHelper"
    debug: bool = False
    database_url: str
    redis_url: str
    secret_key: str
    
    class Config:
        env_file = ".env"

# config/production.py
from .base import BaseSettings

class ProductionSettings(BaseSettings):
    debug: bool = False
    log_level: str = "INFO"
    workers: int = 4
```

### 2.5 日志策略

#### 结构化日志配置
```python
# logging_config.py
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
            
        return json.dumps(log_entry)

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": JSONFormatter,
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
            "level": "INFO",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "/var/log/salaryhelper/app.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "formatter": "json",
            "level": "INFO",
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["console", "file"],
    },
}
```

### 2.6 监控集成

#### Prometheus 指标
```python
# monitoring.py
from prometheus_client import Counter, Histogram, Gauge
import time
from functools import wraps

# 指标定义
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')
ACTIVE_USERS = Gauge('active_users_total', 'Number of active users')
DATABASE_CONNECTIONS = Gauge('database_connections_active', 'Active database connections')

def monitor_request(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            REQUEST_COUNT.labels(method='GET', endpoint=func.__name__, status='200').inc()
            return result
        except Exception as e:
            REQUEST_COUNT.labels(method='GET', endpoint=func.__name__, status='500').inc()
            raise
        finally:
            REQUEST_DURATION.observe(time.time() - start_time)
    return wrapper
```

---

## 3. 数据库部署方案

### 3.1 生产数据库选择

#### 推荐方案：PostgreSQL (云数据库)
```yaml
# 阿里云 RDS PostgreSQL 配置
rds_config:
  engine: PostgreSQL
  version: 13.7
  instance_type: pg.n2.small.1  # 2核4GB
  storage: 100GB
  storage_type: cloud_essd
  zone: cn-hangzhou-i
  
  # 高可用配置
  high_availability: true
  backup_retention: 7  # 天
  maintenance_window: "02:00-03:00"
  
  # 安全配置
  network_type: VPC
  vpc_id: vpc-xxxx
  security_group_id: sg-xxxx
```

#### 数据库连接池配置
```python
# database.py
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool
import psycopg2

# 生产环境连接池
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False
)

# pgBouncer 配置
# /etc/pgbouncer/pgbouncer.ini
[databases]
salaryhelper = host=pg-rds-xxxx.aliyuncs.com port=5432 dbname=salaryhelper

[pgbouncer]
listen_port = 6432
listen_addr = 127.0.0.1
pool_mode = transaction
max_client_conn = 100
default_pool_size = 20
min_pool_size = 10
reserve_pool_size = 5
reserve_pool_timeout = 5
server_reset_query = DISCARD ALL
```

### 3.2 数据库迁移方案

#### SQLite 到 PostgreSQL 迁移脚本
```python
# migrate_to_postgres.py
import sqlite3
import psycopg2
from psycopg2.extras import execute_values

def migrate_sqlite_to_postgres():
    # 连接源数据库
    sqlite_conn = sqlite3.connect('/tmp/salaryhelper.db')
    sqlite_cursor = sqlite_conn.cursor()
    
    # 连接目标数据库
    pg_conn = psycopg2.connect(DATABASE_URL)
    pg_cursor = pg_conn.cursor()
    
    # 创建表结构
    with open('schema_postgres.sql', 'r') as f:
        schema_sql = f.read()
    pg_cursor.execute(schema_sql)
    
    # 迁移数据
    tables = ['users', 'conversations', 'messages', 'attachments', 'templates', 'documents', 'orders']
    
    for table in tables:
        sqlite_cursor.execute(f"SELECT * FROM {table}")
        rows = sqlite_cursor.fetchall()
        columns = [desc[0] for desc in sqlite_cursor.description]
        
        # 构建插入语句
        insert_sql = f"INSERT INTO {table} ({','.join(columns)}) VALUES %s"
        execute_values(pg_cursor, insert_sql, rows)
    
    pg_conn.commit()
    pg_conn.close()
    sqlite_conn.close()

if __name__ == "__main__":
    migrate_sqlite_to_postgres()
```

#### PostgreSQL 表结构
```sql
-- schema_postgres.sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 用户表
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phone VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 会话表
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 消息表
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    sender VARCHAR(20) NOT NULL,
    sender_id UUID,
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 附件表
CREATE TABLE attachments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    file_name VARCHAR(255) NOT NULL,
    content_type VARCHAR(100),
    size_bytes BIGINT,
    storage_url TEXT,
    preview_url TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 模板表
CREATE TABLE templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    category VARCHAR(50),
    content TEXT NOT NULL,
    fields JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 文档表
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    template_id UUID REFERENCES templates(id),
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'draft',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 订单表
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    product_type VARCHAR(50) NOT NULL,
    product_id UUID,
    amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    payment_method VARCHAR(20),
    transaction_id VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    paid_at TIMESTAMP WITH TIME ZONE
);

-- 索引
CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_documents_user_id ON documents(user_id);
CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_attachments_created_at ON attachments(created_at);
```

### 3.3 备份与恢复策略

#### 自动备份脚本
```bash
#!/bin/bash
# backup_database.sh
BACKUP_DIR="/backup/postgresql"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="salaryhelper"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 全量备份
pg_dump -h $PG_HOST -U $PG_USER -d $DB_NAME -f $BACKUP_DIR/salaryhelper_full_$DATE.sql

# 压缩备份
gzip $BACKUP_DIR/salaryhelper_full_$DATE.sql

# 上传到对象存储
ossutil cp $BACKUP_DIR/salaryhelper_full_$DATE.sql.gz oss://salaryhelper-backups/database/

# 清理本地旧备份（保留7天）
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete

# 记录备份日志
echo "$(date): Database backup completed" >> /var/log/backup.log
```

#### 定时备份配置
```bash
# crontab 配置
# 每天凌晨2点全量备份
0 2 * * * /opt/scripts/backup_database.sh

# 每小时增量备份（WAL归档）
0 * * * * /opt/scripts/backup_wal.sh
```

#### 恢复流程
```bash
#!/bin/bash
# restore_database.sh
BACKUP_FILE=$1
DB_NAME="salaryhelper"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    exit 1
fi

# 下载备份文件
ossutil cp oss://salaryhelper-backups/database/$BACKUP_FILE ./

# 解压
gunzip $BACKUP_FILE

# 恢复数据库
psql -h $PG_HOST -U $PG_USER -d $DB_NAME < ${BACKUP_FILE%.gz}

echo "Database restored from $BACKUP_FILE"
```

### 3.4 数据库监控

#### 性能监控配置
```sql
-- 创建监控用户
CREATE USER monitoring WITH PASSWORD 'monitor_pass';
GRANT SELECT ON ALL TABLES IN SCHEMA public TO monitoring;
GRANT SELECT ON pg_stat_activity TO monitoring;

-- 慢查询监控
ALTER SYSTEM SET log_min_duration_statement = 1000;  # 1秒
ALTER SYSTEM SET log_statement = 'all';
SELECT pg_reload_conf();
```

---

## 4. 容器化与编排

### 4.1 生产级 Dockerfile

#### 多阶段构建 Dockerfile
```dockerfile
# server/Dockerfile.prod
# 构建阶段
FROM python:3.11-slim as builder

WORKDIR /app

# 安装构建依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 创建虚拟环境并安装依赖
RUN python -m venv /opt/venv
RUN . /opt/venv/bin/activate && pip install --no-cache-dir -r requirements.txt

# 生产阶段
FROM python:3.11-slim as production

# 创建非root用户
RUN groupadd -r salaryhelper && useradd -r -g salaryhelper salaryhelper

# 安装运行时依赖
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制虚拟环境
COPY --from=builder /opt/venv /opt/venv

# 设置工作目录
WORKDIR /app

# 复制应用代码
COPY --chown=salaryhelper:salaryhelper . .

# 创建必要目录
RUN mkdir -p /tmp/salaryhelper_uploads /var/log/salaryhelper && \
    chown -R salaryhelper:salaryhelper /tmp/salaryhelper_uploads /var/log/salaryhelper

# 切换到非root用户
USER salaryhelper

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# 暴露端口
EXPOSE 8000

# 启动命令
ENV PATH="/opt/venv/bin:$PATH"
CMD ["gunicorn", "-c", "gunicorn_conf.py", "app.main:app"]
```

#### 前端 Dockerfile
```dockerfile
# static/Dockerfile
FROM node:18-alpine as builder

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

FROM nginx:alpine as production

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### 4.2 Docker Compose 生产配置

#### docker-compose.prod.yml
```yaml
version: "3.8"

services:
  # 前端服务
  frontend:
    build:
      context: ./static
      dockerfile: Dockerfile
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./ssl:/etc/ssl/certs:ro
      - ./logs/nginx:/var/log/nginx
    depends_on:
      - backend
    restart: unless-stopped
    networks:
      - salaryhelper-network

  # 后端服务
  backend:
    build:
      context: ./server
      dockerfile: Dockerfile.prod
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - SECRET_KEY=${SECRET_KEY}
      - LOG_LEVEL=INFO
    volumes:
      - ./logs/app:/var/log/salaryhelper
      - uploads:/tmp/salaryhelper_uploads
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
    networks:
      - salaryhelper-network

  # PostgreSQL 数据库
  postgres:
    image: postgres:13
    environment:
      - POSTGRES_DB=salaryhelper
      - POSTGRES_USER=salaryhelper
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backup:/backup
    ports:
      - "5432:5432"
    restart: unless-stopped
    networks:
      - salaryhelper-network

  # Redis 缓存
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    restart: unless-stopped
    networks:
      - salaryhelper-network

  # pgBouncer 连接池
  pgbouncer:
    image: bitnami/pgbouncer:latest
    environment:
      - DATABASE_HOST=postgres
      - DATABASE_PORT_NUMBER=5432
      - DATABASE_NAME=salaryhelper
      - DATABASE_USER=salaryhelper
      - DATABASE_PASSWORD=${POSTGRES_PASSWORD}
      - PGBOUNCER_POOL_MODE=transaction
      - PGBOUNCER_MAX_CLIENT_CONN=100
      - PGBOUNCER_DEFAULT_POOL_SIZE=20
    ports:
      - "6432:6432"
    depends_on:
      - postgres
    restart: unless-stopped
    networks:
      - salaryhelper-network

volumes:
  postgres_data:
  redis_data:
  uploads:

networks:
  salaryhelper-network:
    driver: bridge
```

#### 环境变量文件
```bash
# .env.prod
DATABASE_URL=postgresql://salaryhelper:your_password@postgres:5432/salaryhelper
REDIS_URL=redis://:your_password@redis:6379/0
SECRET_KEY=your-production-secret-key
POSTGRES_PASSWORD=your_postgres_password
REDIS_PASSWORD=your_redis_password
```

### 4.3 Kubernetes 部署

#### Namespace
```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: salaryhelper
```

#### ConfigMap
```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: salaryhelper-config
  namespace: salaryhelper
data:
  DATABASE_HOST: "postgres-service"
  DATABASE_PORT: "5432"
  DATABASE_NAME: "salaryhelper"
  REDIS_HOST: "redis-service"
  REDIS_PORT: "6379"
  LOG_LEVEL: "INFO"
```

#### Secret
```yaml
# k8s/secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: salaryhelper-secrets
  namespace: salaryhelper
type: Opaque
data:
  DATABASE_PASSWORD: <base64-encoded-password>
  REDIS_PASSWORD: <base64-encoded-password>
  SECRET_KEY: <base64-encoded-secret>
  JWT_SECRET_KEY: <base64-encoded-jwt-secret>
```

#### Backend Deployment
```yaml
# k8s/backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: salaryhelper-backend
  namespace: salaryhelper
spec:
  replicas: 3
  selector:
    matchLabels:
      app: salaryhelper-backend
  template:
    metadata:
      labels:
        app: salaryhelper-backend
    spec:
      containers:
      - name: backend
        image: salaryhelper/backend:v1.0.0
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          value: "postgresql://salaryhelper:$(DATABASE_PASSWORD)@$(DATABASE_HOST):$(DATABASE_PORT)/$(DATABASE_NAME)"
        - name: REDIS_URL
          value: "redis://:$(REDIS_PASSWORD)@$(REDIS_HOST):$(REDIS_PORT)/0"
        envFrom:
        - configMapRef:
            name: salaryhelper-config
        - secretRef:
            name: salaryhelper-secrets
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /api/v1/health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/v1/health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        volumeMounts:
        - name: uploads
          mountPath: /tmp/salaryhelper_uploads
      volumes:
      - name: uploads
        persistentVolumeClaim:
          claimName: uploads-pvc
```

#### Service
```yaml
# k8s/backend-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: salaryhelper-backend-service
  namespace: salaryhelper
spec:
  selector:
    app: salaryhelper-backend
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: ClusterIP
```

#### Ingress
```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: salaryhelper-ingress
  namespace: salaryhelper
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/rate-limit-window: "1m"
spec:
  tls:
  - hosts:
    - api.salaryhelper.com
    secretName: salaryhelper-tls
  rules:
  - host: api.salaryhelper.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: salaryhelper-backend-service
            port:
              number: 80
```

#### PersistentVolumeClaim
```yaml
# k8s/pvc.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: uploads-pvc
  namespace: salaryhelper
spec:
  accessModes:
  - ReadWriteMany
  resources:
    requests:
      storage: 100Gi
  storageClassName: nfs
```

#### HorizontalPodAutoscaler
```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: salaryhelper-backend-hpa
  namespace: salaryhelper
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: salaryhelper-backend
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### 4.4 网络与安全

#### NetworkPolicy
```yaml
# k8s/network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: salaryhelper-network-policy
  namespace: salaryhelper
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: postgres
    ports:
    - protocol: TCP
      port: 5432
  - to:
    - podSelector:
        matchLabels:
          app: redis
    ports:
    - protocol: TCP
      port: 6379
```

---

## 5. CI/CD 流程

### 5.1 GitHub Actions 工作流

#### 主工作流文件
```yaml
# .github/workflows/deploy.yml
name: Deploy SalaryHelper

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

env:
  REGISTRY: registry.cn-hangzhou.aliyuncs.com
  NAMESPACE: salaryhelper

jobs:
  # 代码质量检查
  lint-and-test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        cd server
        pip install -r requirements.txt
        pip install pytest flake8 black mypy
    
    - name: Lint with flake8
      run: |
        cd server
        flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
        flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
    
    - name: Check formatting with black
      run: |
        cd server
        black --check .
    
    - name: Type check with mypy
      run: |
        cd server
        mypy app/
    
    - name: Run tests
      run: |
        cd server
        pytest tests/ -v --cov=app --cov-report=xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./server/coverage.xml

  # 构建和推送镜像
  build-and-push:
    needs: lint-and-test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    outputs:
      backend-image: ${{ steps.backend-meta.outputs.tags }}
      frontend-image: ${{ steps.frontend-meta.outputs.tags }}
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2
    
    - name: Log in to Container Registry
      uses: docker/login-action@v2
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ secrets.REGISTRY_USERNAME }}
        password: ${{ secrets.REGISTRY_PASSWORD }}
    
    - name: Extract metadata for backend
      id: backend-meta
      uses: docker/metadata-action@v4
      with:
        images: ${{ env.REGISTRY }}/${{ env.NAMESPACE }}/backend
        tags: |
          type=ref,event=branch
          type=ref,event=pr
          type=sha,prefix={{branch}}-
    
    - name: Build and push backend image
      uses: docker/build-push-action@v4
      with:
        context: ./server
        file: ./server/Dockerfile.prod
        push: true
        tags: ${{ steps.backend-meta.outputs.tags }}
        labels: ${{ steps.backend-meta.outputs.labels }}
        cache-from: type=gha
        cache-to: type=gha,mode=max
    
    - name: Extract metadata for frontend
      id: frontend-meta
      uses: docker/metadata-action@v4
      with:
        images: ${{ env.REGISTRY }}/${{ env.NAMESPACE }}/frontend
        tags: |
          type=ref,event=branch
          type=ref,event=pr
          type=sha,prefix={{branch}}-
    
    - name: Build and push frontend image
      uses: docker/build-push-action@v4
      with:
        context: ./static
        file: ./static/Dockerfile
        push: true
        tags: ${{ steps.frontend-meta.outputs.tags }}
        labels: ${{ steps.frontend-meta.outputs.labels }}
        cache-from: type=gha
        cache-to: type=gha,mode=max

  # 安全扫描
  security-scan:
    needs: build-and-push
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Run Trivy vulnerability scanner
      uses: aquasecurity/trivy-action@master
      with:
        image-ref: ${{ needs.build-and-push.outputs.backend-image }}
        format: 'sarif'
        output: 'trivy-results.sarif'
    
    - name: Upload Trivy scan results to GitHub Security tab
      uses: github/codeql-action/upload-sarif@v2
      with:
        sarif_file: 'trivy-results.sarif'

  # 部署到预发布环境
  deploy-staging:
    needs: [build-and-push, security-scan]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/develop'
    environment: staging
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Configure kubectl
      uses: azure/k8s-set-context@v1
      with:
        method: kubeconfig
        kubeconfig: ${{ secrets.KUBE_CONFIG_STAGING }}
    
    - name: Deploy to staging
      run: |
        sed -i 's|image: .*backend:.*|image: ${{ needs.build-and-push.outputs.backend-image }}|' k8s/backend-deployment.yaml
        sed -i 's|image: .*frontend:.*|image: ${{ needs.build-and-push.outputs.frontend-image }}|' k8s/frontend-deployment.yaml
        kubectl apply -f k8s/ -n salaryhelper-staging
        kubectl rollout status deployment/salaryhelper-backend -n salaryhelper-staging
        kubectl rollout status deployment/salaryhelper-frontend -n salaryhelper-staging

  # 部署到生产环境
  deploy-production:
    needs: [build-and-push, security-scan]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    environment: production
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Configure kubectl
      uses: azure/k8s-set-context@v1
      with:
        method: kubeconfig
        kubeconfig: ${{ secrets.KUBE_CONFIG_PRODUCTION }}
    
    - name: Deploy to production
      run: |
        sed -i 's|image: .*backend:.*|image: ${{ needs.build-and-push.outputs.backend-image }}|' k8s/backend-deployment.yaml
        sed -i 's|image: .*frontend:.*|image: ${{ needs.build-and-push.outputs.frontend-image }}|' k8s/frontend-deployment.yaml
        kubectl apply -f k8s/ -n salaryhelper
        kubectl rollout status deployment/salaryhelper-backend -n salaryhelper
        kubectl rollout status deployment/salaryhelper-frontend -n salaryhelper
    
    - name: Run smoke tests
      run: |
        python test_api.py --env=production
    
    - name: Notify deployment
      uses: 8398a7/action-slack@v3
      with:
        status: ${{ job.status }}
        channel: '#deployments'
        webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

### 5.2 部署脚本

#### 生产部署脚本
```bash
#!/bin/bash
# deploy_production.sh

set -e

ENVIRONMENT=${1:-production}
VERSION=${2:-latest}

echo "Deploying SalaryHelper to $ENVIRONMENT with version $VERSION"

# 检查环境
if [ "$ENVIRONMENT" != "staging" ] && [ "$ENVIRONMENT" != "production" ]; then
    echo "Error: Environment must be staging or production"
    exit 1
fi

# 备份当前版本
echo "Creating backup..."
kubectl get deployment salaryhelper-backend -n salaryhelper-$ENVIRONMENT -o yaml > backup-deployment-$(date +%Y%m%d%H%M%S).yaml

# 更新镜像
echo "Updating container images..."
kubectl set image deployment/salaryhelper-backend backend=registry.cn-hangzhou.aliyuncs.com/salaryhelper/backend:$VERSION -n salaryhelper-$ENVIRONMENT
kubectl set image deployment/salaryhelper-frontend frontend=registry.cn-hangzhou.aliyuncs.com/salaryhelper/frontend:$VERSION -n salaryhelper-$ENVIRONMENT

# 等待部署完成
echo "Waiting for rollout to complete..."
kubectl rollout status deployment/salaryhelper-backend -n salaryhelper-$ENVIRONMENT --timeout=300s
kubectl rollout status deployment/salaryhelper-frontend -n salaryhelper-$ENVIRONMENT --timeout=300s

# 健康检查
echo "Running health checks..."
kubectl wait --for=condition=ready pod -l app=salaryhelper-backend -n salaryhelper-$ENVIRONMENT --timeout=60s

# 运行烟雾测试
echo "Running smoke tests..."
python test_api.py --env=$ENVIRONMENT

echo "Deployment completed successfully!"
```

#### 回滚脚本
```bash
#!/bin/bash
# rollback.sh

set -e

ENVIRONMENT=${1:-production}
REVISION=${2:-1}

echo "Rolling back SalaryHelper in $ENVIRONMENT to revision $REVISION"

# 回滚部署
kubectl rollout undo deployment/salaryhelper-backend -n salaryhelper-$ENVIRONMENT --to-revision=$REVISION
kubectl rollout undo deployment/salaryhelper-frontend -n salaryhelper-$ENVIRONMENT --to-revision=$REVISION

# 等待回滚完成
kubectl rollout status deployment/salaryhelper-backend -n salaryhelper-$ENVIRONMENT --timeout=300s
kubectl rollout status deployment/salaryhelper-frontend -n salaryhelper-$ENVIRONMENT --timeout=300s

echo "Rollback completed successfully!"
```

---

## 6. 安全与性能

### 6.1 HTTPS 强制与安全配置

#### SSL/TLS 配置
```nginx
# 强制 HTTPS
server {
    listen 80;
    server_name .salaryhelper.com;
    return 301 https://$host$request_uri;
}

# HSTS 配置
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;

# 其他安全头
add_header X-Frame-Options DENY always;
add_header X-Content-Type-Options nosniff always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;
```

#### CSP 策略
```nginx
add_header Content-Security-Policy "
    default-src 'self';
    script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net;
    style-src 'self' 'unsafe-inline' https://fonts.googleapis.com;
    font-src 'self' https://fonts.gstatic.com;
    img-src 'self' data: https:;
    connect-src 'self' https://api.salaryhelper.com;
    frame-ancestors 'none';
    base-uri 'self';
    form-action 'self';
" always;
```

### 6.2 密钥轮换策略

#### 自动密钥轮换
```python
# scripts/rotate_secrets.py
import os
import secrets
import subprocess
from datetime import datetime

def rotate_jwt_secret():
    """轮换 JWT 密钥"""
    new_secret = secrets.token_urlsafe(64)
    
    # 更新环境变量
    os.environ['JWT_SECRET_KEY'] = new_secret
    
    # 更新 Vault
    subprocess.run([
        'vault', 'kv', 'put', 'secret/salaryhelper/jwt',
        f'secret_key={new_secret}'
    ])
    
    # 记录轮换日志
    print(f"JWT secret rotated at {datetime.now()}")

def rotate_database_password():
    """轮换数据库密码"""
    new_password = secrets.token_urlsafe(32)
    
    # 更新数据库用户密码
    subprocess.run([
        'psql', '-h', '$DB_HOST', '-U', 'postgres', '-d', 'salaryhelper',
        '-c', f"ALTER USER salaryhelper PASSWORD '{new_password}';"
    ])
    
    # 更新应用配置
    update_application_config('DATABASE_PASSWORD', new_password)

if __name__ == "__main__":
    rotate_jwt_secret()
    rotate_database_password()
```

### 6.3 依赖与镜像安全扫描

#### 安全扫描工作流
```yaml
# .github/workflows/security.yml
name: Security Scan

on:
  schedule:
    - cron: '0 2 * * *'  # 每天凌晨2点
  workflow_dispatch:

jobs:
  dependency-scan:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Run safety check
      run: |
        pip install safety
        safety check --json --output safety-report.json || true
    
    - name: Run bandit security scan
      run: |
        pip install bandit
        bandit -r server/ -f json -o bandit-report.json || true
    
    - name: Upload security reports
      uses: actions/upload-artifact@v3
      with:
        name: security-reports
        path: "*.json"

  image-scan:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Build image for scanning
      run: |
        docker build -t salaryhelper/backend:scan ./server
    
    - name: Run Trivy scanner
      uses: aquasecurity/trivy-action@master
      with:
        image-ref: 'salaryhelper/backend:scan'
        format: 'sarif'
        output: 'trivy-results.sarif'
    
    - name: Upload Trivy results
      uses: github/codeql-action/upload-sarif@v2
      with:
        sarif_file: 'trivy-results.sarif'
```

### 6.4 WAF 与限流配置

#### WAF 规则（ModSecurity）
```nginx
# /etc/nginx/modsecurity/main.conf
SecRuleEngine On
SecRequestBodyAccess On
SecResponseBodyAccess On

# 基础规则
SecRule REQUEST_HEADERS:User-Agent "@streq bad-bot" \
    "id:1001,phase:1,deny,status:403,msg:'Bad bot blocked'"

# SQL 注入防护
SecRule ARGS "@detectSQLi" \
    "id:1002,phase:2,block,msg:'SQL Injection Attack Detected'"

# XSS 防护
SecRule ARGS "@detectXSS" \
    "id:1003,phase:2,block,msg:'XSS Attack Detected'"

# 限流规则
SecRule IP:@pmFromFile /etc/nginx/modsecurity/blacklist.txt \
    "id:1004,phase:1,deny,status:403,msg:'IP blocked'"
```

#### API 限流
```nginx
# 限流配置
http {
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=auth_limit:10m rate=5r/m;
    limit_conn_zone $binary_remote_addr zone=conn_limit:10m;
    
    server {
        # API 限流
        location /api/ {
            limit_req zone=api_limit burst=20 nodelay;
            limit_conn conn_limit 10;
        }
        
        # 认证接口严格限流
        location /api/v1/auth/ {
            limit_req zone=auth_limit burst=2 nodelay;
        }
    }
}
```

### 6.5 性能优化

#### 应用层优化
```python
# performance.py
import asyncio
import aioredis
from fastapi import FastAPI
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

app = FastAPI()

# Redis 缓存配置
@app.on_event("startup")
async def startup():
    redis = aioredis.from_url("redis://redis:6379/0")
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")

# 缓存装饰器
from fastapi_cache.decorator import cache

@app.get("/api/v1/templates")
@cache(expire=3600)  # 缓存1小时
async def get_templates():
    # 模板数据查询
    pass

# 异步任务队列
from celery import Celery

celery_app = Celery("salaryhelper", broker="redis://redis:6379/1")

@celery_app.task
async def process_document_generation(doc_id: str, template_id: str, data: dict):
    # 异步处理文档生成
    pass
```

#### 数据库优化
```sql
-- 性能优化索引
CREATE INDEX CONCURRENTLY idx_messages_conversation_created 
ON messages(conversation_id, created_at);

CREATE INDEX CONCURRENTLY idx_users_phone_active 
ON users(phone) WHERE created_at > NOW() - INTERVAL '1 year';

-- 分区表（如果数据量大）
CREATE TABLE messages_2024 PARTITION OF messages
FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');

-- 查询优化
EXPLAIN (ANALYZE, BUFFERS) 
SELECT * FROM conversations c
JOIN messages m ON c.id = m.conversation_id
WHERE c.user_id = $1
ORDER BY m.created_at DESC
LIMIT 50;
```

#### 缓存策略
```python
# cache.py
from functools import wraps
import redis
import json
import hashlib

redis_client = redis.Redis(host='redis', port=6379, db=0)

def cache_result(expire=3600, key_prefix=""):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = f"{key_prefix}:{func.__name__}:{hashlib.md5(str(args).encode()).hexdigest()}"
            
            # 尝试从缓存获取
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            # 执行函数并缓存结果
            result = await func(*args, **kwargs)
            redis_client.setex(cache_key, expire, json.dumps(result, default=str))
            
            return result
        return wrapper
    return decorator

# 使用示例
@cache_result(expire=1800, key_prefix="user")
async def get_user_conversations(user_id: str):
    # 数据库查询
    pass
```

### 6.6 资源限制与自动扩缩容

#### 资源限制配置
```yaml
# 资源限制示例
resources:
  requests:
    memory: "256Mi"
    cpu: "100m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

#### 自动扩缩容策略
```yaml
# HPA 配置
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: salaryhelper-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: salaryhelper-backend
  minReplicas: 2
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 60
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 70
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
```

---

## 7. 运维与监控

### 7.1 健康检查

#### 应用健康检查端点
```python
# health.py
from fastapi import APIRouter, Depends
from sqlalchemy import text
import redis
import asyncio

router = APIRouter()

@router.get("/api/v1/health")
async def health_check():
    """基础健康检查"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@router.get("/api/v1/health/detailed")
async def detailed_health_check():
    """详细健康检查"""
    checks = {
        "database": await check_database(),
        "redis": await check_redis(),
        "storage": await check_storage(),
        "external_services": await check_external_services()
    }
    
    overall_status = "healthy" if all(check["status"] == "healthy" for check in checks.values()) else "unhealthy"
    
    return {
        "status": overall_status,
        "checks": checks,
        "timestamp": datetime.utcnow()
    }

async def check_database():
    """检查数据库连接"""
    try:
        conn = get_db_connection()
        result = conn.execute(text("SELECT 1"))
        conn.close()
        return {"status": "healthy", "response_time": "< 10ms"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

async def check_redis():
    """检查 Redis 连接"""
    try:
        redis_client.ping()
        return {"status": "healthy", "response_time": "< 5ms"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```

#### 容器健康检查
```yaml
# Kubernetes 健康检查
livenessProbe:
  httpGet:
    path: /api/v1/health
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3

readinessProbe:
  httpGet:
    path: /api/v1/health/detailed
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 3
```

### 7.2 集中化日志

#### EFK 栈配置
```yaml
# elasticsearch.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: elasticsearch
spec:
  serviceName: elasticsearch
  replicas: 3
  selector:
    matchLabels:
      app: elasticsearch
  template:
    metadata:
      labels:
        app: elasticsearch
    spec:
      containers:
      - name: elasticsearch
        image: docker.elastic.co/elasticsearch/elasticsearch:7.15.0
        env:
        - name: discovery.type
          value: single-node
        - name: ES_JAVA_OPTS
          value: "-Xms512m -Xmx512m"
        ports:
        - containerPort: 9200
        volumeMounts:
        - name: data
          mountPath: /usr/share/elasticsearch/data
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 10Gi

# fluentd.yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: fluentd
spec:
  selector:
    matchLabels:
      name: fluentd
  template:
    metadata:
      labels:
        name: fluentd
    spec:
      containers:
      - name: fluentd
        image: fluent/fluentd-kubernetes-daemonset:v1-debian-elasticsearch
        env:
        - name: FLUENT_ELASTICSEARCH_HOST
          value: "elasticsearch"
        - name: FLUENT_ELASTICSEARCH_PORT
          value: "9200"
        volumeMounts:
        - name: varlog
          mountPath: /var/log
        - name: varlibdockercontainers
          mountPath: /var/lib/docker/containers
          readOnly: true
      volumes:
      - name: varlog
        hostPath:
          path: /var/log
      - name: varlibdockercontainers
        hostPath:
          path: /var/lib/docker/containers

# kibana.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kibana
spec:
  replicas: 1
  selector:
    matchLabels:
      app: kibana
  template:
    metadata:
      labels:
        app: kibana
    spec:
      containers:
      - name: kibana
        image: docker.elastic.co/kibana/kibana:7.15.0
        env:
        - name: ELASTICSEARCH_HOSTS
          value: "http://elasticsearch:9200"
        ports:
        - containerPort: 5601
```

#### 日志收集配置
```yaml
# fluentd.conf
<source>
  @type tail
  path /var/log/containers/*salaryhelper*.log
  pos_file /var/log/fluentd-containers.log.pos
  tag kubernetes.*
  format json
  time_format %Y-%m-%dT%H:%M:%S.%NZ
</source>

<filter kubernetes.**>
  @type kubernetes_metadata
</filter>

<match kubernetes.var.log.containers.**salaryhelper**.log>
  @type elasticsearch
  host elasticsearch
  port 9200
  index_name salaryhelper
  type_name _doc
  <buffer>
    @type file
    path /var/log/fluentd-buffers/kubernetes.system.buffer
    flush_mode interval
    retry_type exponential_backoff
    flush_thread_count 2
    flush_interval 5s
    retry_forever
    retry_max_interval 30
    chunk_limit_size 2M
    queue_limit_length 8
    overflow_action block
  </buffer>
</match>
```

### 7.3 指标收集与告警

#### Prometheus 配置
```yaml
# prometheus.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
      evaluation_interval: 15s
    
    rule_files:
      - "/etc/prometheus/rules/*.yml"
    
    scrape_configs:
      - job_name: 'kubernetes-pods'
        kubernetes_sd_configs:
          - role: pod
        relabel_configs:
          - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
            action: keep
            regex: true
          - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
            action: replace
            target_label: __metrics_path__
            regex: (.+)
          - source_labels: [__address__, __meta_kubernetes_pod_annotation_prometheus_io_port]
            action: replace
            regex: ([^:]+)(?::\d+)?;(\d+)
            replacement: $1:$2
            target_label: __address__
          - action: labelmap
            regex: __meta_kubernetes_pod_label_(.+)
          - source_labels: [__meta_kubernetes_namespace]
            action: replace
            target_label: kubernetes_namespace
          - source_labels: [__meta_kubernetes_pod_name]
            action: replace
            target_label: kubernetes_pod_name

      - job_name: 'node-exporter'
        kubernetes_sd_configs:
          - role: endpoints
        relabel_configs:
          - source_labels: [__meta_kubernetes_service_name]
            regex: node-exporter
            action: keep

      - job_name: 'postgres-exporter'
        kubernetes_sd_configs:
          - role: endpoints
        relabel_configs:
          - source_labels: [__meta_kubernetes_service_name]
            regex: postgres-exporter
            action: keep
```

#### 告警规则
```yaml
# alerts.yml
groups:
- name: salaryhelper.rules
  rules:
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "High error rate detected"
      description: "Error rate is {{ $value }} errors per second"

  - alert: HighResponseTime
    expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High response time detected"
      description: "95th percentile response time is {{ $value }} seconds"

  - alert: DatabaseConnectionsHigh
    expr: pg_stat_activity_count > 80
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High database connections"
      description: "Database has {{ $value }} active connections"

  - alert: PodCrashLooping
    expr: rate(kube_pod_container_status_restarts_total[15m]) > 0
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "Pod is crash looping"
      description: "Pod {{ $labels.pod }} is restarting frequently"

  - alert: MemoryUsageHigh
    expr: container_memory_usage_bytes / container_spec_memory_limit_bytes > 0.9
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High memory usage"
      description: "Memory usage is {{ $value | humanizePercentage }}"
```

#### Grafana 仪表板
```json
{
  "dashboard": {
    "title": "SalaryHelper Monitoring",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{ method }} {{ endpoint }}"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          },
          {
            "expr": "histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "50th percentile"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total{status=~\"5..\"}[5m])",
            "legendFormat": "5xx errors"
          }
        ]
      },
      {
        "title": "Database Connections",
        "type": "singlestat",
        "targets": [
          {
            "expr": "pg_stat_activity_count",
            "legendFormat": "Active connections"
          }
        ]
      }
    ]
  }
}
```

### 7.4 告警通知

#### Alertmanager 配置
```yaml
# alertmanager.yaml
global:
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_from: 'alerts@salaryhelper.com'

route:
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'default-receiver'
  routes:
  - match:
      severity: critical
    receiver: 'critical-alerts'
  - match:
      severity: warning
    receiver: 'warning-alerts'

receivers:
- name: 'default-receiver'
  email_configs:
  - to: 'team@salaryhelper.com'
    subject: '[SalaryHelper] {{ .GroupLabels.alertname }}'
    body: |
      {{ range .Alerts }}
      Alert: {{ .Annotations.summary }}
      Description: {{ .Annotations.description }}
      {{ end }}

- name: 'critical-alerts'
  email_configs:
  - to: 'oncall@salaryhelper.com'
    subject: '[CRITICAL] SalaryHelper Alert'
    body: |
      CRITICAL ALERT:
      {{ range .Alerts }}
      {{ .Annotations.summary }}
      {{ .Annotations.description }}
      {{ end }}
  slack_configs:
  - api_url: 'https://hooks.slack.com/services/...'
    channel: '#alerts'
    title: 'Critical Alert'
    text: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'

- name: 'warning-alerts'
  email_configs:
  - to: 'team@salaryhelper.com'
    subject: '[WARNING] SalaryHelper Alert'
```

### 7.5 运维手册

#### 常见故障处理
```bash
#!/bin/bash
# troubleshooting.sh

# 1. 检查 Pod 状态
echo "=== Pod Status ==="
kubectl get pods -n salaryhelper

# 2. 检查服务状态
echo "=== Service Status ==="
kubectl get svc -n salaryhelper

# 3. 检查最近的事件
echo "=== Recent Events ==="
kubectl get events -n salaryhelper --sort-by='.lastTimestamp' | tail -20

# 4. 检查资源使用
echo "=== Resource Usage ==="
kubectl top pods -n salaryhelper

# 5. 检查日志
echo "=== Recent Logs ==="
kubectl logs -n salaryhelper -l app=salaryhelper-backend --tail=50

# 6. 检查数据库连接
echo "=== Database Connection ==="
kubectl exec -n salaryhelper deployment/salaryhelper-backend -- python -c "
import psycopg2
try:
    conn = psycopg2.connect('$DATABASE_URL')
    print('Database connection: OK')
    conn.close()
except Exception as e:
    print(f'Database connection failed: {e}')
"

# 7. 检查 Redis 连接
echo "=== Redis Connection ==="
kubectl exec -n salaryhelper deployment/salaryhelper-backend -- python -c "
import redis
try:
    r = redis.Redis(host='redis', port=6379)
    r.ping()
    print('Redis connection: OK')
except Exception as e:
    print(f'Redis connection failed: {e}')
"
```

#### 紧急响应流程
```markdown
## 紧急响应流程

### 1. 服务不可用
- **症状**: 5xx 错误率 > 50%
- **响应时间**: 5分钟内
- **处理步骤**:
  1. 检查 Pod 状态
  2. 查看最近的部署
  3. 如有必要，执行回滚
  4. 通知团队

### 2. 数据库问题
- **症状**: 数据库连接失败或响应慢
- **响应时间**: 10分钟内
- **处理步骤**:
  1. 检查数据库服务状态
  2. 查看慢查询日志
  3. 必要时重启数据库服务
  4. 联系 DBA 团队

### 3. 高负载
- **症状**: CPU/内存使用率 > 90%
- **响应时间**: 15分钟内
- **处理步骤**:
  1. 检查资源使用情况
  2. 扩展 Pod 数量
  3. 分析性能瓶颈
  4. 优化查询或增加资源
```

### 7.6 灾难恢复

#### 备份策略
```bash
#!/bin/bash
# disaster_recovery.sh

# 全量备份
create_full_backup() {
    DATE=$(date +%Y%m%d_%H%M%S)
    
    # 数据库备份
    pg_dump -h $PG_HOST -U $PG_USER salaryhelper > backup_db_$DATE.sql
    
    # 文件备份
    tar -czf backup_files_$DATE.tar.gz /tmp/salaryhelper_uploads/
    
    # 配置备份
    kubectl get all -n salaryhelper -o yaml > backup_k8s_$DATE.yaml
    
    # 上传到云存储
    upload_to_cloud backup_db_$DATE.sql
    upload_to_cloud backup_files_$DATE.tar.gz
    upload_to_cloud backup_k8s_$DATE.yaml
}

# 恢复流程
restore_from_backup() {
    BACKUP_DATE=$1
    
    # 恢复数据库
    psql -h $PG_HOST -U $PG_USER salaryhelper < backup_db_$BACKUP_DATE.sql
    
    # 恢复文件
    tar -xzf backup_files_$BACKUP_DATE.tar.gz -C /
    
    # 恢复 Kubernetes 配置
    kubectl apply -f backup_k8s_$BACKUP_DATE.yaml
}
```

#### 恢复测试
```bash
#!/bin/bash
# recovery_test.sh

# 模拟灾难
simulate_disaster() {
    echo "Simulating disaster..."
    kubectl delete namespace salaryhelper
    kubectl create namespace salaryhelper
}

# 执行恢复
execute_recovery() {
    echo "Executing recovery..."
    LATEST_BACKUP=$(get_latest_backup)
    restore_from_backup $LATEST_BACKUP
    
    # 验证恢复
    verify_recovery
}

# 验证恢复
verify_recovery() {
    echo "Verifying recovery..."
    
    # 检查服务状态
    kubectl wait --for=condition=ready pod -l app=salaryhelper-backend -n salaryhelper --timeout=300s
    
    # 运行健康检查
    curl -f http://api.salaryhelper.com/api/v1/health
    
    # 运行 smoke tests
    python test_api.py --env=production
    
    echo "Recovery verification completed successfully!"
}
```

---

## 8. 部署检查清单

### 8.1 部署前检查

- [ ] 代码审查通过
- [ ] 所有测试通过
- [ ] 安全扫描无高危漏洞
- [ ] 性能测试通过
- [ ] 数据库迁移脚本准备就绪
- [ ] 配置文件检查完成
- [ ] 备份策略确认
- [ ] 回滚方案准备就绪

### 8.2 部署后验证

- [ ] 服务启动正常
- [ ] 健康检查通过
- [ ] API 功能测试通过
- [ ] 数据库连接正常
- [ ] 缓存服务正常
- [ ] 日志收集正常
- [ ] 监控指标正常
- [ ] 告警配置生效

### 8.3 生产环境就绪检查

- [ ] SSL 证书配置正确
- [ ] 域名解析正确
- [ ] CDN 配置生效
- [ ] 防火墙规则配置
- [ ] 备份计划运行
- [ ] 监控告警测试
- [ ] 性能基准测试
- [ ] 安全渗透测试

---

## 9. 总结

本部署方案提供了 SalaryHelper 应用从开发到生产的完整部署指南，涵盖了：

1. **前端部署**：静态资源优化、CDN 加速、HTTPS 配置
2. **后端部署**：FastAPI 生产优化、负载均衡、配置管理
3. **数据库部署**：PostgreSQL 生产配置、备份恢复、性能优化
4. **容器化编排**：Docker 优化、Kubernetes 部署、自动扩缩容
5. **CI/CD 流程**：自动化测试、安全扫描、分环境部署
6. **安全性能**：HTTPS 强制、WAF 防护、性能调优
7. **运维监控**：健康检查、日志收集、指标告警

通过遵循本方案，可以确保 SalaryHelper 应用在生产环境中稳定、安全、高效地运行。