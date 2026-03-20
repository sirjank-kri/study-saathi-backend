from django.core.management.base import BaseCommand
from core.models import Subject, Question
import requests
import html

class Command(BaseCommand):
    help = 'Import questions from Open Trivia DB API'

    def add_arguments(self, parser):
        parser.add_argument('subject_name', type=str, help='Subject name (e.g., Mathematics)')
        parser.add_argument('--count', type=int, default=10, help='Number of questions to import')

    def handle(self, *args, **kwargs):
        subject_name = kwargs['subject_name']
        count = kwargs['count']
        
        # Get or create subject (for the first user)
        try:
            subject = Subject.objects.get(name=subject_name)
        except Subject.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Subject "{subject_name}" not found. Create it first in admin.'))
            return
        
        # Map subject to Open Trivia category
        category_map = {
            'Mathematics': 19,      # Science: Mathematics
            'Programming': 18,      # Science: Computers
            'Physics': 17,          # Science & Nature
            'Computer Science': 18,
            'General Knowledge': 9,
        }
        
        category = category_map.get(subject_name, 18)  # Default to Computers
        
        # Fetch questions from API
        url = f'https://opentdb.com/api.php?amount={count}&category={category}&type=multiple'
        
        self.stdout.write(f'Fetching {count} questions for {subject_name}...')
        
        try:
            response = requests.get(url)
            data = response.json()
            
            if data['response_code'] != 0:
                self.stdout.write(self.style.ERROR('API returned an error'))
                return
            
            questions_imported = 0
            
            for item in data['results']:
                # Decode HTML entities
                question_text = html.unescape(item['question'])
                correct_answer = html.unescape(item['correct_answer'])
                incorrect_answers = [html.unescape(ans) for ans in item['incorrect_answers']]
                
                # Shuffle options
                import random
                all_options = [correct_answer] + incorrect_answers
                random.shuffle(all_options)
                
                # Find correct option letter
                correct_option = chr(97 + all_options.index(correct_answer))  # 'a', 'b', 'c', 'd'
                
                # Map difficulty
                difficulty_map = {
                    'easy': 'easy',
                    'medium': 'medium',
                    'hard': 'hard'
                }
                difficulty = difficulty_map.get(item['difficulty'], 'medium')
                
                # Create question
                Question.objects.create(
                    subject=subject,
                    topic=item['category'],
                    difficulty=difficulty,
                    question_text=question_text,
                    option_a=all_options[0] if len(all_options) > 0 else '',
                    option_b=all_options[1] if len(all_options) > 1 else '',
                    option_c=all_options[2] if len(all_options) > 2 else '',
                    option_d=all_options[3] if len(all_options) > 3 else '',
                    correct_option=correct_option,
                    source='opentdb'
                )
                
                questions_imported += 1
            
            self.stdout.write(self.style.SUCCESS(f'Successfully imported {questions_imported} questions for {subject_name}'))
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))