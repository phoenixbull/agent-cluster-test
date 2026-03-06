"""
生成的 API 模块
任务：实现以下功能：使用 LayaAir 3.3.8(2D) 引擎复刻一款微信小游戏：跳一跳
要求核心玩法、关卡跟原游戏基本一致。
"""

from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/api/health')
def health():
    return jsonify({"status": "ok"})

# TODO: 实现具体业务逻辑

if __name__ == '__main__':
    app.run(debug=True)
