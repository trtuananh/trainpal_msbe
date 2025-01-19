from django.middleware.csrf import CsrfViewMiddleware

class CustomCsrfMiddleware(CsrfViewMiddleware):
    def process_view(self, request, callback, callback_args, callback_kwargs):
        # Kiểm tra header để xác định request từ mobile
        if 'HTTP_X_MOBILE_APP' in request.META:
            return None
        return super().process_view(request, callback, callback_args, callback_kwargs)
    