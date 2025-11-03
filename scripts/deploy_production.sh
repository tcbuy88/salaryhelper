#!/bin/bash

# SalaryHelper 生产部署脚本
# 使用方法: ./deploy_production.sh [environment] [version]

set -e

ENVIRONMENT=${1:-production}
VERSION=${2:-latest}

echo "========================================"
echo "SalaryHelper 部署脚本"
echo "环境: $ENVIRONMENT"
echo "版本: $VERSION"
echo "========================================"

# 检查必要工具
check_requirements() {
    echo "检查部署环境..."
    
    if ! command -v kubectl &> /dev/null; then
        echo "错误: kubectl 未安装"
        exit 1
    fi
    
    if ! command -v docker &> /dev/null; then
        echo "错误: docker 未安装"
        exit 1
    fi
    
    echo "✓ 环境检查通过"
}

# 构建镜像
build_images() {
    echo "构建 Docker 镜像..."
    
    # 构建后端镜像
    cd server
    docker build -f Dockerfile.prod -t salaryhelper/backend:$VERSION .
    docker tag salaryhelper/backend:$VERSION registry.cn-hangzhou.aliyuncs.com/salaryhelper/backend:$VERSION
    
    # 构建前端镜像
    cd ../static
    docker build -t salaryhelper/frontend:$VERSION .
    docker tag salaryhelper/frontend:$VERSION registry.cn-hangzhou.aliyuncs.com/salaryhelper/frontend:$VERSION
    
    cd ..
    echo "✓ 镜像构建完成"
}

# 推送镜像
push_images() {
    echo "推送镜像到仓库..."
    
    docker push registry.cn-hangzhou.aliyuncs.com/salaryhelper/backend:$VERSION
    docker push registry.cn-hangzhou.aliyuncs.com/salaryhelper/frontend:$VERSION
    
    echo "✓ 镜像推送完成"
}

# 部署到 Kubernetes
deploy_k8s() {
    echo "部署到 Kubernetes 集群..."
    
    # 创建命名空间
    kubectl apply -f k8s/namespace.yaml
    
    # 部署配置和密钥
    kubectl apply -f k8s/configmap.yaml
    kubectl apply -f k8s/secret.yaml
    
    # 部署存储
    kubectl apply -f k8s/pvc.yaml
    
    # 部署数据库和缓存
    kubectl apply -f k8s/postgres-deployment.yaml
    kubectl apply -f k8s/redis-deployment.yaml
    
    # 等待数据库就绪
    kubectl wait --for=condition=ready pod -l app=postgres -n salaryhelper --timeout=300s
    kubectl wait --for=condition=ready pod -l app=redis -n salaryhelper --timeout=300s
    
    # 更新镜像标签
    sed -i.bak "s|image: .*backend:.*|image: registry.cn-hangzhou.aliyuncs.com/salaryhelper/backend:$VERSION|g" k8s/backend-deployment.yaml
    sed -i.bak "s|image: .*frontend:.*|image: registry.cn-hangzhou.aliyuncs.com/salaryhelper/frontend:$VERSION|g" k8s/frontend-deployment.yaml
    
    # 部署应用
    kubectl apply -f k8s/backend-deployment.yaml
    kubectl apply -f k8s/frontend-deployment.yaml
    kubectl apply -f k8s/service.yaml
    kubectl apply -f k8s/ingress.yaml
    kubectl apply -f k8s/hpa.yaml
    kubectl apply -f k8s/network-policy.yaml
    
    # 恢复原始文件
    mv k8s/backend-deployment.yaml.bak k8s/backend-deployment.yaml
    mv k8s/frontend-deployment.yaml.bak k8s/frontend-deployment.yaml
    
    echo "✓ Kubernetes 部署完成"
}

# 等待部署完成
wait_deployment() {
    echo "等待部署完成..."
    
    kubectl rollout status deployment/salaryhelper-backend -n salaryhelper --timeout=600s
    kubectl rollout status deployment/salaryhelper-frontend -n salaryhelper --timeout=600s
    
    echo "✓ 部署完成"
}

# 健康检查
health_check() {
    echo "执行健康检查..."
    
    # 检查 Pod 状态
    kubectl get pods -n salaryhelper
    
    # 检查服务状态
    kubectl get services -n salaryhelper
    
    # 检查入口状态
    kubectl get ingress -n salaryhelper
    
    # 等待服务就绪
    sleep 30
    
    # 执行 API 健康检查
    if command -v curl &> /dev/null; then
        echo "检查 API 健康状态..."
        curl -f https://api.salaryhelper.com/api/v1/health || echo "警告: API 健康检查失败"
    fi
    
    echo "✓ 健康检查完成"
}

# 运行烟雾测试
smoke_test() {
    echo "运行烟雾测试..."
    
    if [ -f "test_api.py" ]; then
        python test_api.py --env=production || echo "警告: 烟雾测试失败"
    fi
    
    echo "✓ 烟雾测试完成"
}

# 清理旧镜像
cleanup() {
    echo "清理旧镜像..."
    
    # 删除本地旧镜像
    docker images | grep salaryhelper | grep -v $VERSION | awk '{print $3}' | xargs -r docker rmi -f
    
    echo "✓ 清理完成"
}

# 主函数
main() {
    echo "开始部署流程..."
    
    check_requirements
    
    if [ "$ENVIRONMENT" = "production" ]; then
        echo "确认要部署到生产环境吗？(y/N)"
        read -r confirm
        if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
            echo "部署已取消"
            exit 0
        fi
    fi
    
    build_images
    push_images
    deploy_k8s
    wait_deployment
    health_check
    smoke_test
    cleanup
    
    echo "========================================"
    echo "部署完成！"
    echo "环境: $ENVIRONMENT"
    echo "版本: $VERSION"
    echo "时间: $(date)"
    echo "========================================"
}

# 执行主函数
main