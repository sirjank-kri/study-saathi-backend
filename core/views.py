from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Subject, Question, Session, QuizAttempt, QuizAnswer
from django.utils import timezone
from datetime import timedelta
import random
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib import messages

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password')
    return render(request, 'login.html')
def register_view(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        username = request.POST.get('username')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        
        # Validation
        if password != password2:
            messages.error(request, 'Passwords do not match')
            return render(request, 'register.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken')
            return render(request, 'register.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered')
            return render(request, 'register.html')
        
        # Create user
        user = User.objects.create_user(username=username, email=email, password=password)
        user.first_name = full_name
        user.save()
        
        login(request, user)
        return redirect('dashboard')
    
    return render(request, 'register.html')
def landing(request):
    return render(request, 'landing.html')

def settings(request):
    return render(request, 'settings.html')
def dashboard(request):
    # For now, no login required for testing
    context = {
        'total_sessions': 0,
        'total_questions': 0,
        'this_week_hours': 0,
        'streak': 0,
    }
    
    if request.user.is_authenticated:
        context['subjects'] = Subject.objects.filter(user=request.user, is_active=True)
        context['total_sessions'] = Session.objects.filter(user=request.user).count()
        
        # Calculate total questions from quiz attempts
        quiz_attempts = QuizAttempt.objects.filter(session__user=request.user)
        context['total_questions'] = sum(qa.total_questions for qa in quiz_attempts)
    
    return render(request, 'dashboard.html', context)

def practice_setup(request):
    if request.user.is_authenticated:
        subjects = Subject.objects.filter(user=request.user, is_active=True)
    else:
        subjects = Subject.objects.filter(is_active=True)[:3]  # Show first 3 for demo
    
    context = {
        'subjects': subjects
    }
    return render(request, 'practice_setup.html', context)

def start_quiz(request):
    if request.method == 'POST':
        subject_id = request.POST.get('subject')
        num_questions = int(request.POST.get('num_questions', 10))
        
        # Get random questions for this subject
        subject = get_object_or_404(Subject, id=subject_id)
        questions = list(Question.objects.filter(subject=subject))
        
        if len(questions) < num_questions:
            num_questions = len(questions)
        
        selected_questions = random.sample(questions, num_questions)
        
        # Store in session
        request.session['quiz_data'] = {
            'subject_id': subject_id,
            'question_ids': [q.id for q in selected_questions],
            'current_index': 0,
            'answers': {},
            'start_time': timezone.now().isoformat(),
        }
        
        return redirect('take_quiz')
    
    return redirect('practice_setup')

def take_quiz(request):
    quiz_data = request.session.get('quiz_data')
    
    if not quiz_data:
        return redirect('practice_setup')
    
    if request.method == 'POST':
        # Save answer
        question_id = request.POST.get('question_id')
        selected_option = request.POST.get('answer')
        
        quiz_data['answers'][question_id] = selected_option
        
        # Check if next or submit
        if 'next' in request.POST:
            quiz_data['current_index'] += 1
            request.session['quiz_data'] = quiz_data
            
            if quiz_data['current_index'] >= len(quiz_data['question_ids']):
                return redirect('quiz_result')
            
            return redirect('take_quiz')
    
    # Get current question
    current_index = quiz_data['current_index']
    question_ids = quiz_data['question_ids']
    
    if current_index >= len(question_ids):
        return redirect('quiz_result')
    
    current_question = Question.objects.get(id=question_ids[current_index])
    
    context = {
        'question': current_question,
        'current_number': current_index + 1,
        'total_questions': len(question_ids),
        'progress': ((current_index + 1) / len(question_ids)) * 100,
    }
    
    return render(request, 'take_quiz.html', context)

def quiz_result(request):
    quiz_data = request.session.get('quiz_data')
    
    if not quiz_data:
        return redirect('practice_setup')
    
    # Calculate results
    question_ids = quiz_data['question_ids']
    answers = quiz_data['answers']
    
    correct_count = 0
    results = []
    
    for q_id in question_ids:
        question = Question.objects.get(id=int(q_id))
        selected = answers.get(str(q_id), '')
        is_correct = selected == question.correct_option
        
        if is_correct:
            correct_count += 1
        
        results.append({
            'question': question,
            'selected': selected,
            'is_correct': is_correct,
        })
    
    total_questions = len(question_ids)
    accuracy = (correct_count / total_questions * 100) if total_questions > 0 else 0
    
    # Save to database if user is logged in
    if request.user.is_authenticated:
        subject = Subject.objects.get(id=quiz_data['subject_id'])
        start_time = timezone.datetime.fromisoformat(quiz_data['start_time'])
        end_time = timezone.now()
        duration = int((end_time - start_time).total_seconds() / 60)
        
        # Create session
        session = Session.objects.create(
            user=request.user,
            subject=subject,
            session_type='quiz',
            start_time=start_time,
            end_time=end_time,
            duration_minutes=duration,
        )
        
        # Create quiz attempt
        quiz_attempt = QuizAttempt.objects.create(
            session=session,
            score=correct_count,
            total_questions=total_questions,
            accuracy=accuracy,
        )
        
        # Save individual answers
        for result in results:
            QuizAnswer.objects.create(
                quiz_attempt=quiz_attempt,
                question=result['question'],
                selected_option=result['selected'],
                is_correct=result['is_correct'],
            )
    
    context = {
        'score': correct_count,
        'total': total_questions,
        'accuracy': round(accuracy, 1),
        'results': results,
    }
    
    # Clear quiz data
    del request.session['quiz_data']
    
    return render(request, 'quiz_result.html', context)
def analytics(request):
    return render(request, 'analytics.html')

def schedule(request):
    return render(request, 'schedule.html')

def history(request):
    return render(request, 'history.html')

def log_session(request):
    return render(request, 'log_session.html')