import base64
import datetime
import hashlib
import hmac
import ipaddress
import json
import secrets
import sys

from flask import Flask, render_template, request
from flask_httpauth import HTTPDigestAuth

import twitter_config

# adminページのユーザ名 & パスワード
admin_users = {
    'User': 'Password'
}

def check_ipaddress(address, allow_networks):
    """ 第一引数が第二引数のネットワークの範囲に入っているか検証し、T/Fを返す

    Args:
        address (str): IPアドレス文字列
        allow_networks (list[str]): IPアドレス文字列のリスト
    """
    address = ipaddress.ip_address(address)
    for val in allow_networks:
        val = ipaddress.ip_network(val)
        if address in val:
            return True
    return False

# 必要なflaskのインスタンスを作成
app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)
auth = HTTPDigestAuth()

# ユーザ名を入力し、パスワードを返す
@auth.get_password
def get_pw(username):
    if username in users:
        return users.get(username)
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin')
@auth.login_required
def admin():
    return 'ログイン成功！'

# TwitterのCRC(GET)
@app.route('/webhooks/twitter', methods=['GET'])
def twitter_crc():
    if 'crc_token' in request.args and check_ipaddress(request.remote_addr, twitter_config.twitter_ipaddresses):
        crc_token = request.args.get('crc_token')
        sha256_hash_digest = hmac.new(twitter_config.CONSUMER_SECRET.encode(), msg = crc_token.encode(), digestmod = hashlib.sha256).digest()

        response_token = 'sha256=' + base64.b64encode(sha256_hash_digest).decode()
        response = {'response_token': response_token}

        return json.dumps(response), 200, {'Content-Type': 'application/json'}

    return 'No Content', 200, {'Content-Type': 'text/plain'}

# TwitterからAccount Activityのデータ受信(POST)
@app.route('/webhooks/twitter', methods=['POST'])
def twitter_activity():

    # Twitter社からのPOST
    if check_ipaddress(request.remote_addr, twitter_config.twitter_ipaddresses):
        print('Got data from Twitter!', file=sys.stdout)
        file = open( './log/' + datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S.%f") + '.log' , 'a')
        file.write( request.data.decode('utf-8') )
        file.close()

    # Twitter社以外からのPOST(攻撃の可能性あり)
    else:
        print('Got attack from ' + request.remote_addr, file=sys.stdout)

    return 'No Content'

if __name__ == '__main__':
    app.run()
