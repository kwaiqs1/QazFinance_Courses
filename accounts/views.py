import logging

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import ensure_csrf_cookie

from .forms import SignUpForm, LoginForm, ProfileEditForm
from .models import User

logger = logging.getLogger(__name__)


@ensure_csrf_cookie
def signup_view(request):
    if request.user.is_authenticated:
        return redirect("academy:courses")

    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()

            # сразу логиним
            login(request, user)

            messages.success(request, "Аккаунт создан. Добро пожаловать в QazFinance Academy.")
            return redirect("academy:courses")
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
