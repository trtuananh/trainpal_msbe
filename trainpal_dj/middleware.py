import re
import requests
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.conf import settings
from rest_framework_simplejwt.tokens import AccessToken
from django.middleware.csrf import CsrfViewMiddleware

class CustomCsrfMiddleware(CsrfViewMiddleware):
    def process_view(self, request, callback, callback_args, callback_kwargs):
        # Kiểm tra header để xác định request từ mobile
        if 'HTTP_X_MOBILE_APP' in request.META:
            return None
        return super().process_view(request, callback, callback_args, callback_kwargs)

@database_sync_to_async
def get_user_from_token(token):
    try:
        access_token = AccessToken(token)
        user_id = access_token['user_id']
        response = requests.get(
            f"http://localhost:8000/api/user/profile/{user_id}/",
            headers={'Authorization': f'Bearer {token}'}
        )
        if response.status_code == 200:
            return user_id
        return None
    except Exception:
        return None

class WebSocketAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        headers = dict(scope['headers'])
        token = None
        if b'authorization' in headers:
            auth_header = headers[b'authorization'].decode()
            token_match = re.match(r'Bearer\s+(\S+)', auth_header)
            if token_match:
                token = token_match.group(1)

        if token:
            user_id = await get_user_from_token(token)
            if user_id:
                scope['user_id'] = user_id
                scope['access_token'] = token
            else:
                await send({
                    "type": "websocket.close",
                    "code": 4000
                })
                return
        else:
            await send({
                "type": "websocket.close",
                "code": 4000
            })
            return

        return await super().__call__(scope, receive, send)
    