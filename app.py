"""
Flaskアプリのメイン部分である。
"""

import base64
from datetime import datetime
import hashlib
import hmac
import json
import secrets
import sys

from flask import Flask, render_template, request, jsonify
from flask_httpauth import HTTPDigestAuth

import tw

# adminページのユーザ名 & パスワード
admin_users = {
    '': ''
}

# 必要なflaskのインスタンスを作成
app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)
auth = HTTPDigestAuth()

# ユーザ名を入力し、パスワードを返す
@auth.get_password
def get_pw(username):
    if username in admin_users:
        return admin_users[username]
    return None

@app.route('/')
def page_index():
    return render_template('index.html')

# Rate Limitの取得(セキュリティがまだ良くない)
@app.route('/get-rate-limit', methods=['POST'])
def page_get_rate_limit():
    remaining, reset_sec, _ = tw.OAuth.get_rate_limit()
    json_result = {
        'remaining': remaining,
        'reset_sec': reset_sec,
    }
    return jsonify(ResultSet=json.dumps(json_result))

# TwitterのCRC(GET)
@app.route('/webhooks/twitter', methods=['GET'])
def twitter_crc():
    if 'crc_token' in request.args and tw.is_from_twitter(request.remote_addr):

        # レスポンスの生成
        crc_token = request.args.get('crc_token')
        sha256_hash_digest = hmac.new(tw.api_secret_key.encode(), msg = crc_token.encode(), digestmod = hashlib.sha256).digest()
        response_token = 'sha256=' + base64.b64encode(sha256_hash_digest).decode()
        response = {'response_token': response_token}

        return json.dumps(response), 200, {'Content-Type': 'application/json'}

    return 'No Content', 200, {'Content-Type': 'text/plain'}

# TwitterからAccount Activityのデータ受信(POST)
@app.route('/webhooks/twitter', methods=['POST'])
def twitter_activity():

    # Twitter社からのPOST
    if tw.is_from_twitter(request.remote_addr):
        print('Got data from Twitter!', file=sys.stdout)
        str_data = request.data.decode('utf-8')

        # ログファイルの書き込み
        file = open( './log/' + datetime.now().strftime("%Y-%m-%d_%H-%M-%S.%f") + '.log' , 'a')
        file.write(str_data)
        file.close()

        # データベースの更新
        tw.DB.parse_and_update_db(str_data)

    # Twitter社以外からのPOST(攻撃の可能性あり)
    else:
        print('[!] Got attack from ' + request.remote_addr, file=sys.stdout)

    return 'No Content', 200, {'Content-Type': 'text/plain'}

if __name__ == '__main__':
    app.run()
