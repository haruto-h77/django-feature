# backend/app/utils.py
import jwt
from datetime import datetime, timedelta, timezone

# jwd検証トークンを生成した時のキー
SECRET_KEY = "your-java-secret-key"

# jwd検証トークンを作成
def generate_jwt_token(user_id):
    # user情報
    payload = {
        'user_id': user_id,
        'exp': datetime.now(timezone.utc) + timedelta(hours=1),  # 有効期限を1時間
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    return token
