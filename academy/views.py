from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
from django.shortcuts import render, get_object_or_404, redirect

from accounts.decorators import verified_required
from .models import Course, Unit, Lesson, Enrollment, Question, Choice, LessonAttempt, LessonProgress
from .services import update_user_rating

@verified_required
def courses_view(request):
    courses = Course.objects.filter(is_published=True).order_by("title")
    # optional: show enrollment + simple progress
    enrollments = {e.course_id: e for e in Enrollment.objects.filter(user=request.user)}
    return render(request, "academy/course_list.html", {"courses": courses, "enrollments": enrollments})

@verified_required
def course_detail_view(request, slug: str):
    course = get_object_or_404(Course, slug=slug, is_published=True)
    units = Unit.objects.filter(course=course).prefetch_related("lessons").order_by("order")

    enrolled = Enrollment.objects.filter(user=request.user, course=course).exists()
    progress_map = {
        p.lesson_id: p for p in LessonProgress.objects.filter(user=request.user, lesson__unit__course=course)
    }
    return render(request, "academy/course_detail.html", {
        "course": course,
        "units": units,
        "enrolled": enrolled,
        "progress_map": progress_map,
    })

@verified_required
def enroll_view(request, slug: str):
    course = get_object_or_404(Course, slug=slug, is_published=True)
    Enrollment.objects.get_or_create(user=request.user, course=course)
    messages.success(request, "Вы записались на курс.")
    return redirect("academy:course_detail", slug=slug)

def _build_sidebar(course, progress_map):
    units = Unit.objects.filter(course=course).prefetch_related("lessons").order_by("order")
    sidebar = []
    for u in units:
        lessons = []
        for l in u.lessons.all().order_by("order"):
            p = progress_map.get(l.id)
            lessons.append({"lesson": l, "progress": p})
        sidebar.append({"unit": u, "lessons": lessons})
    return sidebar

@verified_required
def lesson_detail_view(request, slug: str, lesson_id: int):
    course = get_object_or_404(Course, slug=slug, is_published=True)
    lesson = get_object_or_404(Lesson, id=lesson_id, unit__course=course)

    # ensure enrollment
    if not Enrollment.objects.filter(user=request.user, course=course).exists():
        messages.info(request, "Сначала запишитесь на курс, чтобы отслеживать прогресс.")
        return redirect("academy:course_detail", slug=slug)

    questions = Question.objects.filter(lesson=lesson).prefetch_related("choices").order_by("order")

    progress_map = {
        p.lesson_id: p for p in LessonProgress.objects.filter(user=request.user, lesson__unit__course=course)
    }
    progress = progress_map.get(lesson.id)

    result = None
    selected_answers = {}

    if request.method == "POST":
        # Process quiz submission
        if not questions.exists():
            messages.warning(request, "Для этого урока ещё не добавлены вопросы.")
            return redirect("academy:lesson_detail", slug=slug, lesson_id=lesson_id)

        correct = 0
        total = questions.count()

        for q in questions:
            key = f"q_{q.id}"
            choice_id = request.POST.get(key)
            if choice_id:
                selected_answers[str(q.id)] = int(choice_id)

            correct_choice = q.choices.filter(is_correct=True).first()
            if choice_id and correct_choice and int(choice_id) == correct_choice.id:
                correct += 1

        score = round((correct / total) * 100, 1) if total else 0.0

        LessonAttempt.objects.create(
            user=request.user,
            lesson=lesson,
            score=score,
            answers=selected_answers
        )

        prog, _ = LessonProgress.objects.get_or_create(user=request.user, lesson=lesson)
        prog.last_score = score
        if score > prog.best_score:
            prog.best_score = score
        prog.completed = prog.best_score >= 70.0
        prog.save()

        update_user_rating(request.user)

        progress = prog
        result = {
            "correct": correct,
            "total": total,
            "score": score,
        }
        messages.success(request, f"Результат сохранён: {score}% ({correct}/{total})")

    sidebar = _build_sidebar(course, progress_map={**progress_map, **({lesson.id: progress} if progress else {})})

    # compute next / prev within course ordering
    ordered_lessons = list(Lesson.objects.filter(unit__course=course).select_related("unit").order_by("unit__order", "order", "id"))
    idx = next((i for i, l in enumerate(ordered_lessons) if l.id == lesson.id), None)
    prev_l = ordered_lessons[idx - 1] if idx is not None and idx > 0 else None
    next_l = ordered_lessons[idx + 1] if idx is not None and idx < len(ordered_lessons) - 1 else None

    return render(request, "academy/lesson_detail.html", {
        "course": course,
        "lesson": lesson,
        "questions": questions,
        "progress": progress,
        "sidebar": sidebar,
        "result": result,
        "selected_answers": selected_answers,
        "prev_lesson": prev_l,
        "next_lesson": next_l,
    })
