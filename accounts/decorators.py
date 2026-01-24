from functools import wraps
from django.conf import settings
from django.shortcuts import redirect

def verified_required(view_func):
    """
    Backward-compatible decorator.
    Раньше он блокировал доступ до подтверждения email.
    Теперь email-верификации нет — просто требуем логин.
    """
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(settings.LOGIN_URL)
        return view_func(request, *args, **kwargs)
    return _wrapped
