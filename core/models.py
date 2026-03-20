from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Subject(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    weekly_goal_hours = models.IntegerField(default=5)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class Session(models.Model):
    SESSION_TYPES = [
        ('rating', 'Self Rating'),
        ('quiz', 'Quiz'),
        ('task', 'Task'),
        ('focus', 'Focus Timer'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    session_type = models.CharField(max_length=20, choices=SESSION_TYPES)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    duration_minutes = models.IntegerField()
    rating = models.IntegerField(null=True, blank=True)  # 1-5 for self-rating
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.subject.name} - {self.session_type} - {self.start_time.date()}"
    
    class Meta:
        ordering = ['-start_time']

class Question(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]
    
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, null=True, blank=True)
    topic = models.CharField(max_length=200, blank=True)
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='medium')
    question_text = models.TextField()
    option_a = models.CharField(max_length=500)
    option_b = models.CharField(max_length=500)
    option_c = models.CharField(max_length=500)
    option_d = models.CharField(max_length=500)
    correct_option = models.CharField(max_length=1)  # 'a', 'b', 'c', or 'd'
    explanation = models.TextField(blank=True)
    source = models.CharField(max_length=100, default='manual')  # 'manual', 'api', etc.
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.question_text[:50]}..."

class QuizAttempt(models.Model):
    session = models.OneToOneField(Session, on_delete=models.CASCADE)
    score = models.IntegerField()
    total_questions = models.IntegerField()
    accuracy = models.FloatField()  # percentage
    
    def __str__(self):
        return f"Quiz - {self.session.subject.name} - {self.score}/{self.total_questions}"

class QuizAnswer(models.Model):
    quiz_attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_option = models.CharField(max_length=1)
    is_correct = models.BooleanField()
    time_taken_seconds = models.IntegerField(null=True, blank=True)
    
    def __str__(self):
        return f"Answer - {'Correct' if self.is_correct else 'Wrong'}"