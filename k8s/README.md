# Kubernetes 部署文件

本目录包含 SalaryHelper 应用的 Kubernetes 部署配置文件。

## 文件说明

- `namespace.yaml` - 命名空间配置
- `configmap.yaml` - 配置映射
- `secret.yaml` - 密钥配置
- `backend-deployment.yaml` - 后端服务部署
- `frontend-deployment.yaml` - 前端服务部署
- `postgres-deployment.yaml` - PostgreSQL 数据库部署
- `redis-deployment.yaml` - Redis 缓存部署
- `service.yaml` - 服务配置
- `ingress.yaml` - 入口配置
- `hpa.yaml` - 水平自动扩缩容
- `pvc.yaml` - 持久卷声明
- `network-policy.yaml` - 网络策略

## 部署步骤

1. 创建命名空间：
   ```bash
   kubectl apply -f namespace.yaml
   ```

2. 部署配置和密钥：
   ```bash
   kubectl apply -f configmap.yaml
   kubectl apply -f secret.yaml
   ```

3. 部署数据库和缓存：
   ```bash
   kubectl apply -f postgres-deployment.yaml
   kubectl apply -f redis-deployment.yaml
   ```

4. 部署应用服务：
   ```bash
   kubectl apply -f backend-deployment.yaml
   kubectl apply -f frontend-deployment.yaml
   kubectl apply -f service.yaml
   ```

5. 配置入口和自动扩缩容：
   ```bash
   kubectl apply -f ingress.yaml
   kubectl apply -f hpa.yaml
   ```

6. 应用网络策略：
   ```bash
   kubectl apply -f network-policy.yaml
   ```

## 注意事项

- 部署前请确保 Kubernetes 集群已正确配置
- 需要提前创建 PVC 或配置存储类
- 密钥文件中的敏感信息需要替换为实际值
- Ingress 控制器需要提前安装和配置