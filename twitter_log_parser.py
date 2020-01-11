import json
import sys

# 自分のid_str
my_id_str = ''

# 扱うイベントタイプの一覧
event_types = [ \
    'favorite_events', \
    'tweet_create_events', \
]

# 罫線を出力する
def print_line():
    print('-------------------------------------------------------------------')

# event_typeを特定する
def get_event_type(data):
    for event_type in event_types:
        if event_type in data:
            return event_type
    return None # 例外

# Tweet Objectから必要な情報を抜粋して出力する
def print_tweet_object(tweet_object):
    print( tweet_object['user']['name'] + ': ' + tweet_object['text'] )

# Tweet Objectのツイートが自分のものかを判断する
def is_my_tweet(tweet_object):
    return tweet_object['user']['id_str'] == my_id_str

# Tweet Objectのツイートが他人へのリプライであるかを判断する
def is_reply_to_other(tweet_object):
    to = tweet_object.get('in_reply_to_user_id_str')
    # リプ先ユーザIDがnullであれば、それはリプライではない
    if to is None:
        return False
    # リプ先ユーザIDが存在して、それが自分なら、それは他人へのリプライではない
    elif to == my_id_str:
        return False
    # 他人へのリプなら、それが真
    else:
        return True

# Tweet ObjectからRetweet Objectを取得(無かったらNoneを返却)
def get_retweet_object(tweet_object):
    return tweet_object.get('retweeted_status')

if __name__ == '__main__':
    print('# 何をしますか？')
    print(' * 1: 自分の通常ツイートに対するいいねをピックアップ')
    print(' * 2: 自分の通常ツイートに対するRTをピックアップ')
    command = int(input('>> '), 10)

    # 全ての入力ログファイルに対して
    for fname in sys.argv:

        # 第0引数のスキップ
        if fname == sys.argv[0]:
            continue

        # ファイルの読み込み & データの抽出
        f = open(fname)
        str_data = f.read()
        dict_data = json.loads(str_data)
        event_type = get_event_type(dict_data)
        f.close()

        # コマンド1: 自分の通常ツイートに対するいいねをピックアップ
        if command == 1 and event_type == 'favorite_events':
            tweet_object = dict_data['favorite_events'][0]['favorited_status']
            user = dict_data['favorite_events'][0]['user']
            if is_my_tweet(tweet_object) and not is_reply_to_other(tweet_object):
                print( fname + ': ' + event_type )
                print('いいねした人: ' + user['id_str'] + ', ' + user['name'])
                print_tweet_object( tweet_object )
                print_line()

        # コマンド2: 自分の通常ツイートに対するRTをピックアップ
        if command == 2 and event_type == 'tweet_create_events':
            tweet_object = dict_data['tweet_create_events'][0]
            retweet_object = get_retweet_object(tweet_object)
            if retweet_object:
                if is_my_tweet(retweet_object) and not is_reply_to_other(retweet_object):
                    print( fname + ': ' + event_type )
                    print_tweet_object( tweet_object )
                    print_line()
