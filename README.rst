======================
django-simple-calendar
======================

月間カレンダー、週間カレンダーなどの機能を提供します。

`解説ブログ <https://narito.ninja/detail/11/>`_

======================

Web上でサンプルプロジェクトとして見つけました。（カレンダー機能の）

以下が、基本的なプロジェクト構成になるっぽいです。

<img width="646" alt="スクリーンショット 2025-04-08 11 28 20" src="https://github.com/user-attachments/assets/6de940f5-bdfd-40ec-bce4-b244231518d7" />

実行する際は、仮想環境（今回だと.venv）に入る必要があります。

### 仮想環境の入り方
- **Windowsの場合**  
  ```bash
  .\.venv\Scripts\activate
- **Macの場合**  
  ```bash
  source .venv/bin/activate

### 起動
- **サーバー起動**
  ```bash
  python manage.py runserver

- **マイグレーションが変更されている場合**
  ```bash
  python manage.py migrate
  python manage.py runserver

### 停止
- **サーバー停止**
  Ctrl + C

### 仮想環境の出方
- **出方
  ```bash
  deactivate

