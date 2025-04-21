from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
import jwt
from .utils import generate_jwt_token  # utils.pyの関数をインポート
from django.utils.timezone import now

SETECE_KEY = "your-java-secret-key"

# JWT認証の実行ファイル（検証用）

class JWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        #auth_header = request.headers.get('Authorization') #本番環境
        auth_header = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJleHAiOjE3NDUyMDU2MjB9.zZxga0b91SwVqwmc6xDh4MTy4axpPaDLovv3_CH5XH8"    # テスト用トークン

        # トークンがない場合 or Bearer形式ではない場合
        if not auth_header or not auth_header.startswith('Bearer '):
            print("トークンが見つかりません。テスト用に新しいトークンを生成します。")
            test_token = generate_jwt_token(user_id=1)
            print(f"テスト用トークンを以下のようにリクエストヘッダーにセットしてください：\nAuthorization: Bearer {test_token}")
            raise AuthenticationFailed('トークンがありません（デバッグメッセージ出力済）')

        # トークンを検証（Bearerは不要なので）
        token = auth_header.split(' ')[1]
        try:
            payload = jwt.decode(token, SETECE_KEY, algorithms=['HS256'])
            print("JWTトークンの中身:", payload)
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('トークンの有効期限が切れています')
        except jwt.InvalidTokenError:
            raise AuthenticationFailed('無効なトークンです')

        user = None  # 本番ではここで User モデルと紐付ける
        return (user, payload)
