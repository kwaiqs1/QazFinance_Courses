from functools import wraps
from django.conf import settings
from django.shortcuts import redirect
from django.contrib import messages

def verified_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(settings.LOGIN_URL)
        if settings.REQUIRE_EMAIL_VERIFICATION and not getattr(request.user, "email_verified", False):
            messages.warning(request, "Подтвердите email, чтобы открыть курсы.")
            return redirect("accounts:verify_notice")
        return view_func(request, *args, **kwargs)
    return _wrapped
