from django.contrib import admin
from .models import Subject, Session, Question, QuizAttempt, QuizAnswer

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'weekly_goal_hours', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name']

@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ['subject', 'session_type', 'start_time', 'duration_minutes', 'rating']
    list_filter = ['session_type', 'start_time', 'subject']
    search_fields = ['subject__name', 'notes']
    date_hierarchy = 'start_time'

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['question_text', 'subject', 'topic', 'difficulty', 'correct_option']
    list_filter = ['difficulty', 'subject', 'created_at']
    search_fields = ['question_text', 'topic']

@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ['session', 'score', 'total_questions', 'accuracy']
    list_filter = ['session__start_time']

@admin.register(QuizAnswer)
class QuizAnswerAdmin(admin.ModelAdmin):
    list_display = ['quiz_attempt', 'question', 'selected_option', 'is_correct']
    list_filter = ['is_correct']