django-todo-calendar
======================

カレンダー機能、ToDoの機能を提供します。

主な機能
・スケジュール登録
・スケジュール編集
・スケジュール削除
・ToDo追加
・ToDo編集
・ToDo編集
・スケジュールとToDo同期処理
・個別のリマインダー機能
・JWT認証機能
・JSONレスポンス機能

project-root/
├── LICENSE                         # ライセンスファイル
├── Pipfile                         # pipenv用の依存管理ファイル
├── Pipfile.lock                    # Pipfileのロックファイル（バージョン固定）
├── README.md                       # プロジェクトの説明
├── manage.py                       # Djangoのエントリポイント
├── requirements.txt                # Pythonパッケージの依存定義

├── backend/                        # Djangoのバックエンドルート
│
│   ├── app/                        # メインアプリ（スケジュール・共通機能など）
│   │   ├── __init__.py             # パッケージ初期化
│   │   ├── admin.py                # 管理画面登録用
│   │   ├── apps.py                 # Djangoアプリ設定
│   │   ├── forms.py                # Djangoフォーム定義
│   │   ├── mixins.py               # 汎用Mixin（共通処理）
│   │   ├── models.py               # データベースモデル
│   │   ├── serializers.py          # DRF用のシリアライザ
│   │   ├── settings.py             # アプリ固有設定（共通設定とは別）
│   │   ├── signals.py              # モデルのシグナル処理
│   │   ├── tasks.py                # Celery非同期タスク定義
│   │   ├── templates/              # テンプレート（HTML）
│   │   ├── templatetags/           # カスタムテンプレートタグ
│   │   ├── tests.py                # 単体テスト
│   │   ├── urls.py                 # アプリルーティング
│   │   ├── views.py                # 通常のDjangoビュー
│   │   └── views_api.py            # Django REST FrameworkのAPIビュー
│
│   ├── authentication/            # 認証系（JWT処理など）
│   │   ├── authentication.py       # JWT認証などカスタムロジック
│   │   └── utils.py                # 認証周りの補助関数
│
│   ├── linker/                    # アプリ間連携の補助アプリ
│   │   ├── models.py               # 関連モデル
│   │   ├── signals.py              # シグナル処理
│   │   ├── views.py                # ビュー
│   │   └── ...                     # その他の標準ファイル
│
│   ├── project/                   # Djangoプロジェクト全体設定
│   │   ├── __init__.py            
│   │   ├── celery.py               # Celery設定（非同期実行）
│   │   ├── settings.py             # プロジェクト全体の設定ファイル
│   │   ├── urls.py                 # プロジェクト全体のURLルーティング
│   │   └── wsgi.py                 # WSGI設定（デプロイ用）
│
│   └── todo/                      # ToDoアプリ（個別アプリ構成）
│       ├── forms.py                # ToDo入力フォーム
│       ├── models.py               # ToDoモデル定義
│       ├── serializers.py          # DRFシリアライザ
│       ├── tasks.py                # ToDo関連の非同期タスク
│       ├── urls.py                 # ToDoのルーティング
│       ├── views.py                # 通常ビュー
│       ├── views_api.py            # API用ビュー
│       ├── static/                 # 静的ファイル（CSSやJSなど）
│       ├── templates/              # テンプレート（HTML）
│       ├── signals.py              # シグナル処理
│       └── tests.py                # テスト

├── frontend/                       # React + TypeScript + Viteのフロントエンド
│   ├── index.html                  # HTMLテンプレート（Viteのエントリポイント）
│   ├── package.json                # Node.js依存ファイル
│   ├── package-lock.json           # ロックファイル
│   ├── eslint.config.js            # ESLintの設定
│   ├── vite.config.ts              # Viteビルド設定
│   ├── tsconfig*.json              # TypeScript構成設定
│   ├── public/                     # 公開静的ファイル
│   │   └── vite.svg                # アイコンやfaviconなど
│   ├── src/                        # フロントエンドのソースコード
│   │   ├── App.tsx                 # ルートコンポーネント
│   │   ├── main.tsx                # エントリーポイント（ReactDOM）
│   │   ├── pages/                  # 画面ごとのページコンポーネント
│   │   ├── assets/                 # 静的画像やCSSなど
│   │   ├── App.css                 # グローバルスタイル
│   │   ├── index.css               # エントリーCSS
│   │   └── vite-env.d.ts           # Vite用型定義ファイル



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
