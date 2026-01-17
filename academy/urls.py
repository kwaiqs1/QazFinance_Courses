from django.urls import path
from . import views

app_name = "academy"

urlpatterns = [
    path("", views.courses_view, name="courses"),
    path("course/<slug:slug>/", views.course_detail_view, name="course_detail"),
    path("course/<slug:slug>/enroll/", views.enroll_view, name="enroll"),
    path("course/<slug:slug>/lesson/<int:lesson_id>/", views.lesson_detail_view, name="lesson_detail"),
]
