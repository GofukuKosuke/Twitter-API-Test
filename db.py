"""
DBに簡単に接続する関数dbを提供する。
from db import db でインポートしよう。
"""

import MySQLdb

def db(*args):

    # MariaDBに接続
    conn = MySQLdb.connect(
        user = '',
        password = '',
        host = '',
        db = '',
        charset = '',
    )
    cursor = conn.cursor(MySQLdb.cursors.DictCursor)

    result = None

    # DB操作
    try:
        cursor.execute(*args)
        conn.commit()
        result = cursor.fetchall()
    except MySQLdb.Error as e:
        result = e

    # MariaDBとの接続を終了
    cursor.close()
    conn.close()

    return result
