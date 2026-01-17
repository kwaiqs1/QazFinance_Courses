from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("signup/", views.signup_view, name="signup"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    path("verify/", views.verify_notice_view, name="verify_notice"),
    path("verify/resend/", views.resend_verification_view, name="resend_verification"),
    path("verify/<str:token>/", views.verify_email_view, name="verify_email"),

    path("profile/", views.profile_view, name="profile"),
    path("profile/edit/", views.profile_edit_view, name="profile_edit"),

    path("people/", views.people_search_view, name="people_search"),
    path("people/<int:user_id>/", views.person_detail_view, name="person_detail"),
]
