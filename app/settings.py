# settings.py

INSTALLED_APPS = [
    'app.apps.AppConfig',  # ← 自作したカレンダーアプリ（appディレクトリの中にある）
    'django.contrib.admin',         # Djangoの管理画面
    'django.contrib.auth',          # 認証（ログイン・ユーザー管理）
    'django.contrib.contenttypes',  # モデル間の関連情報管理
    'django.contrib.sessions',      # セッション管理
    'django.contrib.messages',      # メッセージフレームワーク
    'django.contrib.staticfiles',   # CSSや画像などの静的ファイルの取り扱い
    'app',
]


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'ViZaro',  # 使用するデータベース名
        'USER': 'postgres',  # データベースユーザー名
        'PASSWORD': 'postgres',  # データベースパスワード
        'HOST': 'localhost',  # ホスト名（通常はlocalhost）
        'PORT': '5432',  # PostgreSQLのポート（デフォルトは5432）
    }
}
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
