#!/bin/bash

# SalaryHelper 回滚脚本
# 使用方法: ./rollback.sh [environment] [revision]

set -e

ENVIRONMENT=${1:-production}
REVISION=${2:-1}

echo "========================================"
echo "SalaryHelper 回滚脚本"
echo "环境: $ENVIRONMENT"
echo "回滚到版本: $REVISION"
echo "========================================"

# 检查必要工具
check_requirements() {
    if ! command -v kubectl &> /dev/null; then
        echo "错误: kubectl 未安装"
        exit 1
    fi
    
    echo "✓ 环境检查通过"
}

# 获取当前部署状态
get_current_status() {
    echo "获取当前部署状态..."
    
    kubectl get deployments -n salaryhelper
    kubectl get pods -n salaryhelper
    
    echo "✓ 当前状态获取完成"
}

# 执行回滚
perform_rollback() {
    echo "执行回滚操作..."
    
    # 回滚后端服务
    echo "回滚后端服务..."
    kubectl rollout undo deployment/salaryhelper-backend -n salaryhelper --to-revision=$REVISION
    
    # 回滚前端服务
    echo "回滚前端服务..."
    kubectl rollout undo deployment/salaryhelper-frontend -n salaryhelper --to-revision=$REVISION
    
    echo "✓ 回滚操作完成"
}

# 等待回滚完成
wait_rollback() {
    echo "等待回滚完成..."
    
    kubectl rollout status deployment/salaryhelper-backend -n salaryhelper --timeout=300s
    kubectl rollout status deployment/salaryhelper-frontend -n salaryhelper --timeout=300s
    
    echo "✓ 回滚完成"
}

# 验证回滚
verify_rollback() {
    echo "验证回滚结果..."
    
    # 检查 Pod 状态
    kubectl get pods -n salaryhelper
    
    # 检查服务状态
    kubectl get services -n salaryhelper
    
    # 执行健康检查
    if command -v curl &> /dev/null; then
        echo "检查 API 健康状态..."
        curl -f https://api.salaryhelper.com/api/v1/health || echo "警告: API 健康检查失败"
    fi
    
    echo "✓ 回滚验证完成"
}

# 主函数
main() {
    echo "开始回滚流程..."
    
    check_requirements
    
    echo "确认要回滚到版本 $REVISION 吗？(y/N)"
    read -r confirm
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        echo "回滚已取消"
        exit 0
    fi
    
    get_current_status
    perform_rollback
    wait_rollback
    verify_rollback
    
    echo "========================================"
    echo "回滚完成！"
    echo "环境: $ENVIRONMENT"
    echo "回滚到版本: $REVISION"
    echo "时间: $(date)"
    echo "========================================"
}

# 执行主函数
main