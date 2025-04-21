from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
import jwt
from .utils import generate_jwt_token  # utils.pyの関数をインポート
import json

# Java側の認証キー
SETECE_KEY = "3a79c0e3f01f4ba8a4bc6ef0df8fa7c1a7c6506a2d3901fbe8e9ce7a6d9a7a89"

# JWT認証の実行ファイル（検証用）

class JWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        #auth_header = request.headers.get('Authorization') #本番環境
        auth_header = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJleHAiOjE3NDUyMTk0MTR9.m-GFERA4XherttIzVFOSGiqhViohDgQAY-8iLOKLj_A"    # テスト用トークン

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
            print("JWT認証用のトークン:" + json.dumps(payload))
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('トークンの有効期限が切れています')
        except jwt.InvalidTokenError:
            raise AuthenticationFailed('無効なトークンです')

        user = None  # 本番ではここで User モデルと紐付ける
        return (user, payload)
