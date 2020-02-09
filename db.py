"""
DBに簡単に接続する関数dbを提供する。
from db import db でインポートしよう。
"""

import MySQLdb

import const

def db(*args, **kwargs):
    """
    mysqlclientの接続・操作・切断を一纏めにラッピングした関数。

    Parameters
    ----------
    mysqlclientのcursor.execute()と同様

    Returns
    -------
    mysqlclientのcursor.fetchall()と同様のもの もしくは MySQLdb.Error
    """

    # MariaDBに接続
    conn = MySQLdb.connect(
        user = const.DB['USER'],
        password = const.DB['PASSWORD'],
        host = const.DB['HOST'],
        db = const.DB['DB'],
        charset = 'utf8mb4',
    )
    cursor = conn.cursor(MySQLdb.cursors.DictCursor)

    result = None

    # DB操作
    try:
        cursor.execute(*args, **kwargs)
        conn.commit()
        result = cursor.fetchall()
    except MySQLdb.Error as e:
        result = e

    # MariaDBとの接続を終了
    cursor.close()
    conn.close()

    return result
