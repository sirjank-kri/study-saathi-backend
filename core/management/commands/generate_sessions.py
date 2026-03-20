from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Subject, Session, QuizAttempt
from django.utils import timezone
from datetime import timedelta
import random

class Command(BaseCommand):
    help = 'Generate dummy quiz sessions for testing analytics'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username to generate sessions for')
        parser.add_argument('--count', type=int, default=20, help='Number of sessions to generate')

    def handle(self, *args, **kwargs):
        username = kwargs['username']
        count = kwargs['count']

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User "{username}" not found'))
            return

        subjects = Subject.objects.filter(user=user, is_active=True)
        if not subjects.exists():
            self.stdout.write(self.style.ERROR('User has no subjects. Add subjects first.'))
            return

        self.stdout.write(f'Generating {count} sessions for {username}...')

        # Generate sessions over the past 30 days
        for i in range(count):
            # Random subject
            subject = random.choice(subjects)

            # Random date/time in past 30 days
            days_ago = random.randint(0, 30)
            hour = random.choice([6, 7, 8, 9, 10, 11, 14, 15, 16, 17, 18, 19, 20, 21, 22])
            minute = random.randint(0, 59)

            start_time = timezone.now() - timedelta(days=days_ago, hours=timezone.now().hour - hour, minutes=timezone.now().minute - minute)

            # Random duration (10-60 minutes)
            duration = random.choice([10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60])
            end_time = start_time + timedelta(minutes=duration)

            # Random performance (simulate patterns)
            # Morning (6-11): Higher accuracy
            # Afternoon (14-17): Medium accuracy
            # Evening (18-22): Lower accuracy
            base_accuracy = 70

            if 6 <= hour <= 11:
                accuracy = random.randint(75, 95)
            elif 14 <= hour <= 17:
                accuracy = random.randint(65, 85)
            else:
                accuracy = random.randint(50, 75)

            # Random number of questions
            total_questions = random.choice([5, 10, 15, 20])
            score = int((accuracy / 100) * total_questions)

            # Create session
            session = Session.objects.create(
                user=user,
                subject=subject,
                session_type='quiz',
                start_time=start_time,
                end_time=end_time,
                duration_minutes=duration,
            )

            # Create quiz attempt
            QuizAttempt.objects.create(
                session=session,
                score=score,
                total_questions=total_questions,
                accuracy=accuracy,
            )

        self.stdout.write(self.style.SUCCESS(f'✓ Generated {count} sessions successfully!'))