# Twitter-API-Test
TwitterのWebhookを受け取って、頂いたいいねやRTを集計する
2020/01/14現在、開発中である。

## Dependency
- CentOS
- Python3系
- Nginx
- uWSGI
- Flask

## Usage
- サーバを構築し、必要なものをインストールする。
- Let's Encrypt等を用いてSSLを導入する。
- uwsgi --ini myapp.ini で起動する。
- TwitterサーバにCRCを依頼して認証を済ませる。
- Account Activityが発生する度に、そのJSONデータが ./log/ に蓄積される。
- python3 twitter_log_parser.py ./log/* でいいねやRTを抽出する。スクリプトは対話型である。

## Author
御福宏佑
