from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Subject, Session, QuizAttempt, Question, QuizAnswer

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'first_name', 'last_name']
    
    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        return user

class SubjectSerializer(serializers.ModelSerializer):
    session_count = serializers.SerializerMethodField()
    avg_accuracy = serializers.SerializerMethodField()
    
    class Meta:
        model = Subject
        fields = ['id', 'name', 'weekly_goal_hours', 'is_active', 'session_count', 'avg_accuracy']
    
    def get_session_count(self, obj):
        return Session.objects.filter(subject=obj).count()
    
    def get_avg_accuracy(self, obj):
        quiz_attempts = QuizAttempt.objects.filter(session__subject=obj)
        if not quiz_attempts.exists():
            return 0
        total_accuracy = sum([qa.accuracy for qa in quiz_attempts])
        return round(total_accuracy / quiz_attempts.count(), 1)

class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['id', 'question_text', 'option_a', 'option_b', 'option_c', 'option_d', 'difficulty']

class QuizAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizAttempt
        fields = ['id', 'session', 'score', 'total_questions', 'accuracy']

class SessionSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    accuracy = serializers.SerializerMethodField()
    
    class Meta:
        model = Session
        fields = ['id', 'subject', 'subject_name', 'session_type', 'start_time', 
                 'end_time', 'duration_minutes', 'rating', 'accuracy', 'notes']
    
    def get_accuracy(self, obj):
        try:
            return obj.quizattempt.accuracy
        except QuizAttempt.DoesNotExist:
            return None