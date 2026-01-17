from django.db.models import Avg
from .models import LessonProgress

def update_user_rating(user):
    # rating = average best_score across all lessons attempted (progress records)
    agg = LessonProgress.objects.filter(user=user).aggregate(avg=Avg("best_score"))
    user.rating = float(agg["avg"] or 0.0)
    user.save(update_fields=["rating"])
