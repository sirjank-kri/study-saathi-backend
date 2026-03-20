from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
from dateutil import parser

from .models import Subject, Session, Question, QuizAttempt, QuizAnswer
from .serializers import (
    UserSerializer, RegisterSerializer, SubjectSerializer, 
    SessionSerializer, QuestionSerializer, QuizAttemptSerializer
)

# ========== AUTH ENDPOINTS ==========

@api_view(['POST'])
@permission_classes([AllowAny])
def register_api(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def login_api(request):
    username = request.data.get('username')
    password = request.data.get('password')
    
    user = authenticate(username=username, password=password)
    if user:
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        })
    return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    return Response(UserSerializer(request.user).data)

# ========== DASHBOARD ==========

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    user = request.user
    
    total_sessions = Session.objects.filter(user=user).count()
    
    total_questions = QuizAttempt.objects.filter(
        session__user=user
    ).aggregate(total=Sum('total_questions'))['total'] or 0
    
    week_ago = timezone.now() - timedelta(days=7)
    this_week_minutes = Session.objects.filter(
        user=user, 
        start_time__gte=week_ago
    ).aggregate(total=Sum('duration_minutes'))['total'] or 0
    this_week_hours = round(this_week_minutes / 60, 1)
    
    streak = 0  # TODO: Implement streak logic
    
    return Response({
        'totalSessions': total_sessions,
        'totalQuestions': total_questions,
        'thisWeek': this_week_hours,
        'streak': streak
    })

# ========== SUBJECTS ==========

class SubjectViewSet(viewsets.ModelViewSet):
    serializer_class = SubjectSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Subject.objects.filter(user=self.request.user, is_active=True)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

# ========== QUIZ ==========

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_quiz_api(request):
    """This is kept for reference but we're using external API now"""
    return Response({'message': 'Use Open Trivia DB directly'})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_quiz_api(request):
    """This is kept for reference but we're using save_quiz_api now"""
    return Response({'message': 'Use save_quiz_api instead'})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_quiz_api(request):
    """Save quiz results from external API questions"""
    try:
        subject_id = request.data.get('subject_id')
        score = request.data.get('score')
        total_questions = request.data.get('total_questions')
        accuracy = request.data.get('accuracy')
        duration_minutes = request.data.get('duration_minutes', 0)
        start_time_str = request.data.get('start_time')
        end_time_str = request.data.get('end_time')
        
        # Parse timestamps
        start_time = parser.parse(start_time_str)
        end_time = parser.parse(end_time_str)
        
        # Get subject
        subject = Subject.objects.get(id=subject_id, user=request.user, is_active=True)
        
        # Create session
        session = Session.objects.create(
            user=request.user,
            subject=subject,
            session_type='quiz',
            start_time=start_time,
            end_time=end_time,
            duration_minutes=duration_minutes,
        )
        
        # Create quiz attempt
        quiz_attempt = QuizAttempt.objects.create(
            session=session,
            score=score,
            total_questions=total_questions,
            accuracy=accuracy,
        )
        
        return Response({
            'message': 'Quiz saved successfully',
            'session_id': session.id,
            'quiz_attempt_id': quiz_attempt.id,
        }, status=status.HTTP_201_CREATED)
        
    except Subject.DoesNotExist:
        return Response({'error': 'Subject not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

# ========== HISTORY ==========

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def session_history_api(request):
    try:
        sessions = Session.objects.filter(user=request.user).order_by('-start_time')
        serializer = SessionSerializer(sessions, many=True)
        return Response(serializer.data)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def analytics_data_api(request):
    """Get analytics data for charts"""
    user = request.user
    
    # Get all quiz sessions
    sessions = Session.objects.filter(
        user=user, 
        session_type='quiz',
        quizattempt__isnull=False
    ).select_related('quizattempt')
    
    if sessions.count() < 5:
        return Response({
            'error': 'Not enough data',
            'sessions_count': sessions.count(),
            'min_required': 15
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # 1. Performance by Time of Day
    time_of_day_data = {
        'Morning (6-11)': [],
        'Afternoon (12-17)': [],
        'Evening (18-21)': [],
        'Night (22-5)': []
    }
    
    for session in sessions:
        hour = session.start_time.hour
        accuracy = session.quizattempt.accuracy
        
        if 6 <= hour < 12:
            time_of_day_data['Morning (6-11)'].append(accuracy)
        elif 12 <= hour < 18:
            time_of_day_data['Afternoon (12-17)'].append(accuracy)
        elif 18 <= hour < 22:
            time_of_day_data['Evening (18-21)'].append(accuracy)
        else:
            time_of_day_data['Night (22-5)'].append(accuracy)
    
    time_of_day_avg = {
        key: round(sum(values) / len(values), 1) if values else 0
        for key, values in time_of_day_data.items()
    }
    
    # 2. Performance by Duration
    duration_data = {
        '10-20 min': [],
        '20-30 min': [],
        '30-45 min': [],
        '45-60 min': []
    }
    
    for session in sessions:
        duration = session.duration_minutes
        accuracy = session.quizattempt.accuracy
        
        if 10 <= duration < 20:
            duration_data['10-20 min'].append(accuracy)
        elif 20 <= duration < 30:
            duration_data['20-30 min'].append(accuracy)
        elif 30 <= duration < 45:
            duration_data['30-45 min'].append(accuracy)
        elif 45 <= duration <= 60:
            duration_data['45-60 min'].append(accuracy)
    
    duration_avg = {
        key: round(sum(values) / len(values), 1) if values else 0
        for key, values in duration_data.items()
    }
    
    # 3. Performance by Day of Week
    day_data = {
        'Monday': [], 'Tuesday': [], 'Wednesday': [], 
        'Thursday': [], 'Friday': [], 'Saturday': [], 'Sunday': []
    }
    
    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    for session in sessions:
        day_index = session.start_time.weekday()
        day_name = day_names[day_index]
        accuracy = session.quizattempt.accuracy
        day_data[day_name].append(accuracy)
    
    day_avg = {
        day: round(sum(values) / len(values), 1) if values else 0
        for day, values in day_data.items()
    }
    
    # 4. Accuracy Trend Over Time
    trend_data = []
    for session in sessions.order_by('start_time'):
        trend_data.append({
            'date': session.start_time.strftime('%b %d'),
            'accuracy': session.quizattempt.accuracy
        })
    
    # 5. Overall Stats
    total_sessions = sessions.count()
    avg_accuracy = round(sum([s.quizattempt.accuracy for s in sessions]) / total_sessions, 1)
    avg_duration = round(sum([s.duration_minutes for s in sessions]) / total_sessions, 1)
    
    # Find best time
    best_time = max(time_of_day_avg.items(), key=lambda x: x[1])[0] if any(time_of_day_avg.values()) else 'N/A'
    
    # Find best duration
    best_duration = max(duration_avg.items(), key=lambda x: x[1])[0] if any(duration_avg.values()) else 'N/A'
    
    return Response({
        'total_sessions': total_sessions,
        'avg_accuracy': avg_accuracy,
        'avg_duration': avg_duration,
        'best_time': best_time,
        'best_duration': best_duration,
        'time_of_day': time_of_day_avg,
        'duration': duration_avg,
        'day_of_week': day_avg,
        'trend': trend_data,
    })
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def generate_schedule_api(request):
    """Generate personalized weekly study schedule"""
    user = request.user
    
    # Get all quiz sessions
    sessions = Session.objects.filter(
        user=user, 
        session_type='quiz',
        quizattempt__isnull=False
    ).select_related('quizattempt', 'subject')
    
    if sessions.count() < 10:
        return Response({
            'error': 'Not enough data',
            'sessions_count': sessions.count(),
            'min_required': 10
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Get user's subjects
    subjects = Subject.objects.filter(user=user, is_active=True)
    
    if not subjects.exists():
        return Response({'error': 'No subjects found'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Analyze performance by hour
    hour_performance = {}
    for hour in range(6, 23):  # 6 AM to 10 PM
        hour_sessions = sessions.filter(start_time__hour=hour)
        if hour_sessions.exists():
            avg_accuracy = sum([s.quizattempt.accuracy for s in hour_sessions]) / hour_sessions.count()
            confidence = min(hour_sessions.count(), 5)  # Max 5 stars
            hour_performance[hour] = {
                'accuracy': round(avg_accuracy, 1),
                'confidence': confidence,
                'sessions': hour_sessions.count()
            }
    
    # Find best hours (top performing)
    best_hours = sorted(
        hour_performance.items(), 
        key=lambda x: (x[1]['accuracy'], x[1]['sessions']), 
        reverse=True
    )[:10]  # Top 10 hours
    
    # Generate weekly schedule
    schedule = {}
    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    for day_index, day_name in enumerate(day_names):
        schedule[day_name] = []
        
        # Analyze performance on this day
        day_sessions = sessions.filter(start_time__week_day=day_index + 2)  # Django: 1=Sunday, 2=Monday
        
        if day_sessions.exists():
            # Get best hours for this day
            day_hours = {}
            for session in day_sessions:
                hour = session.start_time.hour
                if hour not in day_hours:
                    day_hours[hour] = []
                day_hours[hour].append(session.quizattempt.accuracy)
            
            # Calculate average for each hour
            day_hour_avg = {
                hour: round(sum(accuracies) / len(accuracies), 1)
                for hour, accuracies in day_hours.items()
            }
            
            # Sort by performance
            sorted_hours = sorted(day_hour_avg.items(), key=lambda x: x[1], reverse=True)
            
            # Assign subjects to top 2-3 hours
            for i, (hour, accuracy) in enumerate(sorted_hours[:3]):
                if hour < 6 or hour > 22:  # Skip unrealistic hours
                    continue
                    
                # Round-robin subject assignment
                subject = list(subjects)[i % subjects.count()]
                
                # Calculate confidence based on data points
                sessions_at_hour = len(day_hours[hour])
                confidence = min(sessions_at_hour, 5)
                
                schedule[day_name].append({
                    'hour': hour,
                    'subject': subject.name,
                    'subject_id': subject.id,
                    'expected_accuracy': accuracy,
                    'confidence': confidence,
                    'duration': 45  # Recommended duration in minutes
                })
    
    # Overall recommendations
    recommendations = {
        'best_time': f"{best_hours[0][0]}:00" if best_hours else "N/A",
        'best_accuracy': best_hours[0][1]['accuracy'] if best_hours else 0,
        'optimal_duration': '30-45 minutes',  # Based on common patterns
        'total_study_hours': sum([len(slots) * 0.75 for slots in schedule.values()]),
    }
    
    return Response({
        'schedule': schedule,
        'recommendations': recommendations,
        'data_quality': {
            'total_sessions': sessions.count(),
            'subjects_tracked': subjects.count(),
            'hours_analyzed': len(hour_performance),
        }
    })  
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def log_session_api(request):
    """Manually log a study session"""
    try:
        subject_id = request.data.get('subject_id')
        session_type = request.data.get('session_type', 'manual')
        start_time_str = request.data.get('start_time')
        duration_minutes = request.data.get('duration_minutes')
        rating = request.data.get('rating')  # 1-5 stars
        notes = request.data.get('notes', '')
        
        # Validate
        if not all([subject_id, start_time_str, duration_minutes]):
            return Response({
                'error': 'Missing required fields'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get subject
        subject = Subject.objects.get(id=subject_id, user=request.user, is_active=True)
        
        # Parse start time
        start_time = parser.parse(start_time_str)
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        # Create session
        session = Session.objects.create(
            user=request.user,
            subject=subject,
            session_type=session_type,
            start_time=start_time,
            end_time=end_time,
            duration_minutes=duration_minutes,
            rating=rating,
            notes=notes,
        )
        
        return Response({
            'message': 'Session logged successfully',
            'session_id': session.id,
        }, status=status.HTTP_201_CREATED)
        
    except Subject.DoesNotExist:
        return Response({'error': 'Subject not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)