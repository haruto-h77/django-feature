from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
import jwt

SETECE_KEY = "Java側との秘密鍵"

# JWT認証の実行ファイル

class JWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        print(f"✅ authenticate() 呼び出し（todo）、request id: {id(request)}")
        # リクエストヘッダーからトークンを取得する
        auth_header = request.headers.get('Authorization')
        # トークンがない場合
        if not auth_header or not auth_header.startswith('Bearer '):
            raise AuthenticationFailed('⭐︎ JWT認証用のトークンがありません')
        
        token = auth_header.split(' ')[1]
        try:
            payload = jwt.decode(token, SETECE_KEY, algorithms=['HS256'])
            print("JWT認証用のトークン:" + payload)
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('認証期限が切れています')
        except jwt.InvalidTokenError:
            raise AuthenticationFailed('無効な認証トークンです')
        
        # DjangoのUserモデルと紐付けたい場合は、ここでuserを取得する
        user = None
        return (user, payload)
