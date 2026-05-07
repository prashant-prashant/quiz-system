from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    ROLE_CHOICES = [('student', 'Student'), ('teacher', 'Teacher')]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')

    def __str__(self):
        return f"{self.user.username} ({self.role})"


class Quiz(models.Model):
    CATEGORY_CHOICES = [
        ('general', 'General Knowledge'),
        ('science', 'Science'),
        ('math', 'Mathematics'),
        ('history', 'History'),
        ('technology', 'Technology'),
        ('english', 'English'),
        ('other', 'Other'),
    ]
    DIFFICULTY_CHOICES = [('easy', 'Easy'), ('medium', 'Medium'), ('hard', 'Hard')]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='general')
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='medium')
    time_limit = models.IntegerField(default=60, help_text="Time limit in seconds")
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='quizzes')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

    def question_count(self):
        return self.question_set.count()


class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    option1 = models.CharField(max_length=200)
    option2 = models.CharField(max_length=200)
    option3 = models.CharField(max_length=200)
    option4 = models.CharField(max_length=200)
    correct_option = models.IntegerField()
    explanation = models.TextField(blank=True, default='')

    def __str__(self):
        return self.question_text[:60]


class Result(models.Model):
    student_name = models.CharField(max_length=100)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='results')
    quiz = models.ForeignKey(Quiz, null=True, blank=True, on_delete=models.SET_NULL, related_name='results')
    score = models.IntegerField()
    total_questions = models.IntegerField(default=10)
    time_taken = models.IntegerField(default=0, help_text="Time taken in seconds")
    completed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student_name}: {self.score}"

    def percentage(self):
        if self.total_questions > 0:
            return round((self.score / self.total_questions) * 100, 1)
        return 0

    class Meta:
        ordering = ['-completed_at']