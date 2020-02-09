"""
Twitterと情報をやり取りするための包括的な機能を提供する。
"""

from datetime import datetime
import json
import time
import ipaddress
from requests_oauthlib import OAuth1Session
import sys

from db import db
import const

class OAuth:
    """
    Twitter社とOAuthを用いてやり取りするためのstaticmethod群。
    """
    oauth = OAuth1Session(const.API_KEY, const.API_SECRET_KEY, const.ACCESS_TOKEN, const.ACCESS_TOKEN_SECRET)

    @staticmethod
    def get_rate_limit():
        """
        レート制限情報を取得する。

        Returns
        -------
        remaining : int
            リクエスト可能残数
        reset_sec : int
            リクエスト叶残数リセットまでの時間(秒)
        res : Responce
        """
        url = 'https://api.twitter.com/1.1/statuses/user_timeline.json'
        res = OAuth.oauth.get(url)
        remaining = int(res.headers['x-rate-limit-remaining'])
        reset_utc = int(res.headers['X-Rate-Limit-Reset']) # UTC
        reset_sec = reset_utc - time.mktime(datetime.now().timetuple()) #UTCを秒数に変換
        return remaining, reset_sec, res

    @staticmethod
    def post_tweet(message):
        """
        ツイートする。

        Parameters
        ----------
        message : str
            ツイート内容

        Returns
        -------
        Responce
            正常に成功した場合は、HTTPステータスコードが200になる。
        """
        url = 'https://api.twitter.com/1.1/statuses/update.json'
        params = {
            'status' : message
        }
        return OAuth.oauth.post(url, params=params)

    @staticmethod
    def crc():
        """
        CRCの依頼をする。

        Returns
        -------
        Responce
        """
        url = 'https://api.twitter.com/1.1/account_activity/all/%s/webhooks.json' % const.DEV_LABEL
        params = {
            'url': const.WEBHOOK_URL
        }
        return OAuth.oauth.post(url, params=params)

    @staticmethod
    def get_webhooks():
        """
        全Webhookを取得する。

        Returns
        -------
        Responce
        """
        url = 'https://api.twitter.com/1.1/account_activity/all/webhooks.json'
        return OAuth.oauth.get(url)

    @staticmethod
    def add_subscription():
        """
        サブスクリプションの追加(重複登録不可)

        Returns
        -------
        Responce
        """
        url = 'https://api.twitter.com/1.1/account_activity/all/%s/subscriptions.json' % const.DEV_LABEL
        return OAuth.oauth.post(url)

    @staticmethod
    def get_subscriptions():
        """
        サブスクリプションの確認(成功すると、HTTP 204 No Contentが返される)

        Returns
        -------
        Responce
        """
        url = 'https://api.twitter.com/1.1/account_activity/all/%s/subscriptions.json' % const.DEV_LABEL
        return OAuth.oauth.get(url)

class Parse:
    """
    Twitter社からWebhookで送られてくるJSONを解析するためのstaticmethod群。
    """

    @staticmethod
    def get_event_type(data):
        """
        イベントタイプを特定する。

        Parameters
        ----------
        data : dict

        Returns
        -------
        event_type : str
        """

        # 扱うイベントタイプの一覧
        event_types = [
            'favorite_events',
            'tweet_create_events',
        ]

        for event_type in event_types:
            if event_type in data:
                return event_type
        return None # 例外

    @staticmethod
    def parse_twitter_datetime(datetime_str):
        """
        Twitter社のdatetime文字列をdatetime型に変換する。

        Parameters
        ----------
        date_str : str

        Returns
        -------
        datetime
        """
        return datetime.strptime(datetime_str, '%a %b %d %H:%M:%S +0000 %Y')

    @staticmethod
    def is_my_tweet(tweet_object):
        """
        Tweet Objectのツイートが自分のものかを判断する。

        Returns
        -------
        bool
        """
        return tweet_object['user']['id_str'] == const.MY_ID_STR

    @staticmethod
    def is_reply_to_other(tweet_object):
        """
        Tweet Objectのツイートが他人へのリプライであるかを判断する。

        Returns
        -------
        bool
        """
        to = tweet_object.get('in_reply_to_user_id_str')
        # リプ先ユーザIDがnullであれば、それはリプライではない
        if to is None:
            return False
        # リプ先ユーザIDが存在して、それが自分なら、それは他人へのリプライではない
        elif to == const.MY_ID_STR:
            return False
        # 他人へのリプなら、それが真
        else:
            return True

    @staticmethod
    def get_original_tweet_object(tweet_object):
        """
        RTであるTweet ObjectからRT元のTweet Objectを取得(無かったらNoneを返却)
        """
        return tweet_object.get('retweeted_status')

class DB:
    """
    DB接続が必要な処理をまとめたstaticmethod群。
    """
    @staticmethod
    def send_tweet_object(tweet_object):
        """
        Tweet Objectをデータベースに反映する。
        (新ツイートならば新規追加、そうでなければ変化なし)
        """
        created_at = Parse.parse_twitter_datetime(tweet_object['created_at'])
        stmt = 'INSERT INTO my_tweets (id_str, created_at, text) VALUES (%s, %s, %s)'
        db(stmt, (tweet_object['id_str'], created_at, tweet_object['text']))

    @staticmethod
    def send_user_object(user_object):
        """
        User Objectをデータベースに反映する。
        (新ツイートならば新規追加、そうでなければ変化なし)
        """
        stmt = 'REPLACE INTO twitter_users (id_str, screen_name, name) VALUES (%s, %s, %s)'
        db(stmt, (user_object['id_str'], user_object['screen_name'], user_object['name']))

    @staticmethod
    def send_like(raw_dict_data):
        """
        いいねイベントをデータベースに反映する。
        また、それに関連したユーザとツイートもデータベースに反映する。

        Parameters
        ----------
        raw_dict_data : dict
            favorite_eventを含む生データ
        """
        favorite_event = raw_dict_data['favorite_events'][0]
        tweet_object = favorite_event['favorited_status']

        # 他人へのリプライでない自分のツイートのみが対象
        if Parse.is_my_tweet(tweet_object) and not Parse.is_reply_to_other(tweet_object):

            user_object = favorite_event['user']
            favorite_created_at =  Parse.parse_twitter_datetime(favorite_event['created_at'])

            # print('[いいね] いいねした人: ' + user_object['id_str'] + ', ' + user_object['name'], file=sys.stdout)
            # print_tweet_object(tweet_object)

            DB.send_tweet_object(tweet_object) # ツイートをデータベースに反映
            DB.send_user_object(user_object) # ユーザをデータベースに反映

            # いいねをデータベースに反映
            stmt = 'INSERT INTO favorites (user_id_str, tweet_id_str, created_at) VALUES (%s, %s, %s)'
            db(stmt, (user_object['id_str'], tweet_object['id_str'], favorite_created_at))

    @staticmethod
    def send_retweet(raw_dict_data):
        """
        tweet_create_eventを含むデータを入力し、それがRTならばRTをデータベースに反映する。
        また、それに関連したユーザとツイートもデータベースに反映する。

        Parameters
        ----------
        raw_dict_data : dict
            tweet_create_eventを含む生データ
        """
        tweet_object = raw_dict_data['tweet_create_events'][0]
        original_tweet_object = Parse.get_original_tweet_object(tweet_object)

        # RTならば
        if original_tweet_object:

            # 元ツイートが自分のもので、それが他人へのリプライでない場合のみが対象
            if Parse.is_my_tweet(original_tweet_object) and not Parse.is_reply_to_other(original_tweet_object):

                user_object = tweet_object['user']
                tweet_created_at = Parse.parse_twitter_datetime(tweet_object['created_at'])

                # print('[RT]', file=sys.stdout)
                # print_tweet_object(tweet_object)

                DB.send_tweet_object(original_tweet_object) # ツイートをデータベースに反映
                DB.send_user_object(user_object) # ユーザをデータベースに反映

                # RTをデータベースに反映
                stmt = 'INSERT INTO retweets (user_id_str, tweet_id_str, created_at) VALUES (%s, %s, %s)'
                db(stmt, (user_object['id_str'], original_tweet_object['id_str'], tweet_created_at))

    @staticmethod
    def parse_and_update_db(raw_str_data):
        """
        JSON文字列を元に、データベースを適切に更新する
        対象イベント: いいね、RT

        Parameters
        ----------
        raw_str_data : str
            JSON形式文字列の生データ
        """
        data = json.loads(raw_str_data)
        event_type = Parse.get_event_type(data)

        # いいね
        if event_type == 'favorite_events':
            DB.send_like(data)

        # RT
        if event_type == 'tweet_create_events':
            DB.send_retweet(data)

def is_from_twitter(address):
    """
    与えられたIPアドレスがTwitter社のIPアドレスであるかを検証する。

    Parameters
    ----------
    address : str
        IPアドレス

    Returns
    -------
    bool
        Twitter社のIPアドレスであるか
    """
    twitter_ipaddresses = ['199.59.148.0/22', '199.16.156.0/22']
    address = ipaddress.ip_address(address)
    for val in twitter_ipaddresses:
        val = ipaddress.ip_network(val)
        if address in val:
            return True
    return False

if __name__ == '__main__':
    """
    デバッグ用
    """

    # 全ての入力ログファイルに対して
    for fname in sys.argv:

        # 第0引数のスキップ
        if fname == sys.argv[0]:
            continue

        # ファイルの読み込み & データの抽出
        f = open(fname)
        str_data = f.read()
        f.close()

        print( 'ログファイル名: ' + fname)

        DB.parse_and_update_db(str_data) # データベース更新
