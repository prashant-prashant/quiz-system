from django.urls import path
from .views import (
    register, login_view, logout_view,
    quiz_list, get_questions, submit_quiz, leaderboard, export_results,
    teacher_stats, teacher_quiz_list_create, teacher_quiz_detail,
    teacher_question_list_create, teacher_question_detail, teacher_quiz_results
)

urlpatterns = [
    # Auth
    path('auth/register/', register),
    path('auth/login/', login_view),
    path('auth/logout/', logout_view),

    # Student
    path('quizzes/', quiz_list),
    path('questions/', get_questions),
    path('submit/', submit_quiz),
    path('leaderboard/', leaderboard),
    path('export/', export_results),

    # Teacher
    path('teacher/stats/', teacher_stats),
    path('teacher/quizzes/', teacher_quiz_list_create),
    path('teacher/quizzes/<int:quiz_id>/', teacher_quiz_detail),
    path('teacher/quizzes/<int:quiz_id>/questions/', teacher_question_list_create),
    path('teacher/questions/<int:question_id>/', teacher_question_detail),
    path('teacher/quizzes/<int:quiz_id>/results/', teacher_quiz_results),
]