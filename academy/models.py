from django.db import models
from django.conf import settings

class Course(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    is_published = models.BooleanField(default=True)

    def __str__(self):
        return self.title

class Unit(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="units")
    title = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["order", "id"]
        unique_together = [("course", "order")]

    def __str__(self):
        return f"{self.course.title}: {self.title}"

class Lesson(models.Model):
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=1)

    objectives = models.TextField(blank=True, help_text="Можно использовать базовый HTML")
    theory = models.TextField(blank=True, help_text="Можно использовать базовый HTML")
    numbers = models.TextField(blank=True, help_text="Опционально: формулы/цифры/опоры (HTML допускается)")
    case = models.TextField(blank=True, help_text="Кейс (HTML допускается)")
    summary = models.TextField(blank=True, help_text="Итоги (HTML допускается)")

    class Meta:
        ordering = ["order", "id"]
        unique_together = [("unit", "order")]

    def __str__(self):
        return f"{self.unit.title}: {self.title}"

class Enrollment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="enrollments")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrollments")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("user", "course")]

    def __str__(self):
        return f"{self.user.email} -> {self.course.title}"

class Question(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="questions")
    text = models.TextField()
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["order", "id"]
        unique_together = [("lesson", "order")]

    def __str__(self):
        return f"Q{self.order} ({self.lesson.title})"

class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="choices")
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"Choice ({'correct' if self.is_correct else 'wrong'}): {self.text[:40]}"

class LessonAttempt(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="lesson_attempts")
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="attempts")
    score = models.FloatField(default=0.0)  # percent
    submitted_at = models.DateTimeField(auto_now_add=True)
    answers = models.JSONField(default=dict, blank=True)  # {question_id: choice_id}

    class Meta:
        ordering = ["-submitted_at"]

class LessonProgress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="lesson_progress")
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="progress_records")

    best_score = models.FloatField(default=0.0)
    last_score = models.FloatField(default=0.0)
    completed = models.BooleanField(default=False)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("user", "lesson")]
