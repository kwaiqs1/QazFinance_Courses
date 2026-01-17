from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from django.views.decorators.csrf import ensure_csrf_cookie

from .forms import SignUpForm, LoginForm, ProfileEditForm
from .models import User
from .tokens import make_token, verify_token

def _send_verification_email(request, user: User):
    token = make_token(user.id)
    verify_url = settings.SITE_URL + reverse("accounts:verify_email", args=[token])
    subject = "QazFinance — подтверждение email"
    body = f"Здравствуйте, {user.full_name}!\n\nПодтвердите email по ссылке:\n{verify_url}\n\nЕсли вы не регистрировались, просто проигнорируйте это письмо."
    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)


@ensure_csrf_cookie
def signup_view(request):
    if request.user.is_authenticated:
        return redirect("academy:courses")

    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            _send_verification_email(request, user)
            messages.success(request, "Аккаунт создан. Мы отправили письмо для подтверждения email.")
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
    _send_verification_email(request, user)
    messages.success(request, "Письмо отправлено повторно.")
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
