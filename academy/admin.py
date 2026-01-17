from django.contrib import admin
from .models import Course, Unit, Lesson, Question, Choice, Enrollment, LessonAttempt, LessonProgress

class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 3

class QuestionAdmin(admin.ModelAdmin):
    list_display = ("lesson", "order", "short_text")
    list_filter = ("lesson__unit__course",)
    search_fields = ("text", "lesson__title")
    inlines = [ChoiceInline]

    def short_text(self, obj):
        return (obj.text[:60] + "…") if len(obj.text) > 60 else obj.text

class LessonAdmin(admin.ModelAdmin):
    list_display = ("title", "unit", "order")
    list_filter = ("unit__course", "unit")
    search_fields = ("title", "unit__title", "unit__course__title")

class UnitAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "order")
    list_filter = ("course",)
    search_fields = ("title", "course__title")

class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "is_published")
    search_fields = ("title", "slug")

admin.site.register(Course, CourseAdmin)
admin.site.register(Unit, UnitAdmin)
admin.site.register(Lesson, LessonAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Enrollment)
admin.site.register(LessonAttempt)
admin.site.register(LessonProgress)
