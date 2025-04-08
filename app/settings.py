# settings.py

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'your_db_name',  # 使用するデータベース名
        'USER': 'your_db_user',  # データベースユーザー名
        'PASSWORD': 'your_db_password',  # データベースパスワード
        'HOST': 'localhost',  # ホスト名（通常はlocalhost）
        'PORT': '5432',  # PostgreSQLのポート（デフォルトは5432）
    }
}
