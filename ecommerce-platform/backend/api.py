"""
生成的 API 模块
任务：实现以下功能：[电商] 添加购物车功能
"""

from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/api/health')
def health():
    return jsonify({"status": "ok"})

# TODO: 实现具体业务逻辑

if __name__ == '__main__':
    app.run(debug=True)
