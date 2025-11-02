#!/bin/bash

echo "=== SalaryHelper Demo 启动脚本 ==="

# 检查是否在正确的目录
if [ ! -f "server/app/main.py" ]; then
    echo "错误: 请在项目根目录运行此脚本"
    exit 1
fi

# 启动后端服务
echo "1. 启动后端服务..."
cd server
source .venv/bin/activate
python app/main.py &
SERVER_PID=$!
cd ..

# 等待服务启动
echo "2. 等待服务启动..."
sleep 3

# 测试API
echo "3. 测试API连接..."
cd server
source .venv/bin/activate
cd ..
python test_api.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 后端服务启动成功！"
    echo ""
    echo "🌐 前端页面访问地址："
    echo "   主页: file://$(pwd)/static/index.html"
    echo "   登录: file://$(pwd)/static/login.html"
    echo "   会话: file://$(pwd)/static/conversations.html"
    echo ""
    echo "🔧 后端API地址: http://localhost:8000"
    echo "📊 API文档: http://localhost:8000/docs"
    echo ""
    echo "💡 测试账号:"
    echo "   手机号: 13800000000"
    echo "   验证码: 123456"
    echo ""
    echo "按 Ctrl+C 停止服务"
    
    # 保持脚本运行，等待用户中断
    trap "echo ''; echo '停止服务...'; kill $SERVER_PID; exit" INT
    wait $SERVER_PID
else
    echo "❌ 后端服务启动失败"
    kill $SERVER_PID 2>/dev/null
    exit 1
fi