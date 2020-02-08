Twitter-App
===========
TwitterからWebhookを受け取る。
頂いた いいね・RT・リプライを集計し、表示する。
2020/02/09現在、開発進行中である。

## Dependency
- CentOS
- Python3系
- Nginx
- uWSGI
- Flask
- MariaDB

## Usage
- サーバを構築し、必要なものをインストールおよび設定する。
  - default.confを用意し、/etc/nginx/conf.d/に置く。
- Let's Encryptを用いてSSLを導入する。
- ./start_server で起動する。
- tw.pyを用いて、TwitterサーバにCRCを依頼し、認証を済ませる。
- Account Activityが発生する度に、
  - その生JSONデータが ./log/ に蓄積される。
  - いいねとRTの情報がデータベースに記録される。

## Author
[御福宏佑 GofukuKosuke](https://github.com/GofukuKosuke)
