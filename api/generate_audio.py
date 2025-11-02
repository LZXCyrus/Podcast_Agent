from flask import Flask, request, send_file
import os
import sys

# 添加父目录到路径，以便导入 tts_logic
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from tts_logic import generate_podcast

app = Flask(__name__)

@app.route('/', methods=['POST'])
def generate_audio():
    # 检查请求内容类型
    if not request.is_json:
        return {'error': 'Content-Type must be application/json'}, 400

    data = request.get_json()
    if not data or 'text' not in data:
        return {'error': 'Missing text field in JSON body'}, 400

    text = data['text']
    if not isinstance(text, str) or len(text.strip()) == 0:
        return {'error': 'Text must be a non-empty string'}, 400

    try:
        # 生成 WAV 文件
        output_path = generate_podcast(text)
        if output_path and os.path.exists(output_path):
            # 返回 WAV 文件作为响应
            return send_file(
                output_path,
                as_attachment=True,
                download_name='output.wav',
                mimetype='audio/wav'
            )
        else:
            return {'error': 'Audio generation failed'}, 500
    except Exception as e:
        return {'error': str(e)}, 500

# Vercel 需要导出 app 变量
application = app
