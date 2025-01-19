import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trainpal_dj.settings')

from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from jwt import InvalidTokenError


class WebSocketAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        # Lấy token từ query parameters
        from django.contrib.auth.models import AnonymousUser
        from rest_framework_simplejwt.tokens import AccessToken, TokenError

        query_string = scope.get('query_string', b'').decode()
        query_params = dict(param.split('=') for param in query_string.split('&') if param)
        token = query_params.get('token', None)

        scope['user'] = AnonymousUser()

        if token:
            try:
                # Verify token
                access_token = AccessToken(token)
                user_id = access_token.payload.get('user_id')
                
                if user_id:
                    user = await self.get_user(user_id)
                    scope['user'] = user
            except TokenError as e:
                print("TokenError in middleware")
                pass
                
        return await super().__call__(scope, receive, send)

    @database_sync_to_async
    def get_user(self, user_id):
        from base.models import User
        from django.contrib.auth.models import AnonymousUser
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return AnonymousUser()