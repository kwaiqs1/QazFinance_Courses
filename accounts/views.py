import logging
import threading

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.csrf import ensure_csrf_cookie

from .forms import SignUpForm, LoginForm, ProfileEditForm
from .models import User
from .tokens import make_token, verify_token

logger = logging.getLogger(__name__)


def _build_verify_url(user: User) -> str:
    token = make_token(user.id)
    base = (settings.SITE_URL or "").rstrip("/")
    return base + reverse("accounts:verify_email", args=[token])


def _send_verification_email_sync(user: User) -> None:
    verify_url = _build_verify_url(user)
    subject = "QazFinance — подтверждение email"
    body = (
        f"Здравствуйте, {user.full_name}!\n\n"
        f"Подтвердите email по ссылке:\n{verify_url}\n\n"
        "Если вы не регистрировались, просто проигнорируйте это письмо."
    )

    try:
        msg = EmailMessage(
            subject=subject,
            body=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        sent = msg.send(fail_silently=False)
        logger.info("SMTP email send result=%s to=%s (user_id=%s)", sent, user.email, user.id)
    except Exception as e:
        logger.exception("Verification email FAILED for %s (user_id=%s). Reason: %r", user.email, user.id, e)


def _send_verification_email_async(user: User) -> None:
    t = threading.Thread(target=_send_verification_email_sync, args=(user,), daemon=True)
    t.start()


@ensure_csrf_cookie
def signup_view(request):
    if request.user.is_authenticated:
        return redirect("academy:courses")

    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)

            _send_verification_email_async(user)

            messages.success(
                request,
                "Аккаунт создан. Мы отправили письмо для подтверждения email. "
                "Если письмо не пришло — проверьте Spam/Promotions."
            )
            return redirect("accounts:verify_notice")
    else:
        form = SignUpForm()

    return render(request, "accounts/signup.html", {"form": form})


@ensure_csrf_cookie
def login_view(request):
    if request.user.is_authenticated:
        return redirect("academy:courses")

    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data["user"]
            login(request, user)
            return redirect("academy:courses")
    else:
        form = LoginForm()

    return render(request, "accounts/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("home")


@login_required
def verify_notice_view(request):
    return render(request, "accounts/verify_notice.html")


@login_required
def resend_verification_view(request):
    user = request.user
    if user.email_verified:
        messages.info(request, "Email уже подтверждён.")
        return redirect("academy:courses")

    _send_verification_email_async(user)
    messages.success(request, "Письмо отправлено повторно. Проверьте почту и папку Spam.")
    return redirect("accounts:verify_notice")


def verify_email_view(request, token: str):
    user_id = verify_token(token)
    if not user_id:
        return render(request, "accounts/verify_email.html", {"status": "invalid"})

    user = get_object_or_404(User, id=user_id)
    user.email_verified = True
    user.save(update_fields=["email_verified"])
    messages.success(request, "Email подтверждён. Добро пожаловать в QazFinance Academy.")
    return render(request, "accounts/verify_email.html", {"status": "ok"})


@login_required
def profile_view(request):
    return render(request, "accounts/profile.html", {"profile_user": request.user})


@login_required
def profile_edit_view(request):
    if request.method == "POST":
        form = ProfileEditForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Профиль обновлён.")
            return redirect("accounts:profile")
    else:
        form = ProfileEditForm(instance=request.user)

    return render(request, "accounts/profile_edit.html", {"form": form})


@login_required
def people_search_view(request):
    q = request.GET.get("q", "").strip()
    users = []
    if q:
        users = User.objects.filter(
            Q(full_name__icontains=q) | Q(nickname__icontains=q) | Q(email__icontains=q)
        ).order_by("-rating")[:50]
    return render(request, "accounts/people_search.html", {"q": q, "users": users})


@login_required
def person_detail_view(request, user_id: int):
    person = get_object_or_404(User, id=user_id)
    return render(request, "accounts/person_detail.html", {"person": person})
