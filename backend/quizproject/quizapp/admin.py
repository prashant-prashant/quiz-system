from django.contrib import admin
from .models import Profile, Quiz, Question, Result

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role']
    list_filter = ['role']

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'difficulty', 'time_limit', 'is_active', 'created_at']
    list_filter = ['category', 'difficulty', 'is_active']
    search_fields = ['title']

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['question_text', 'quiz', 'correct_option']
    list_filter = ['quiz']

@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ['student_name', 'quiz', 'score', 'total_questions', 'completed_at']
    list_filter = ['quiz', 'completed_at']
    search_fields = ['student_name']