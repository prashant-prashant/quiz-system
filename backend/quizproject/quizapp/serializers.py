from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Profile, Quiz, Question, Result


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    role = serializers.ChoiceField(choices=['student', 'teacher'])
    teacher_code = serializers.CharField(required=False, allow_blank=True, write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'role', 'teacher_code']

    def validate(self, data):
        if data.get('role') == 'teacher':
            if data.get('teacher_code') != 'TEACH2024':
                raise serializers.ValidationError({'teacher_code': 'Invalid teacher access code.'})
        return data

    def create(self, validated_data):
        role = validated_data.pop('role')
        validated_data.pop('teacher_code', None)
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password']
        )
        Profile.objects.create(user=user, role=role)
        return user


class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username')
    email = serializers.CharField(source='user.email')

    class Meta:
        model = Profile
        fields = ['username', 'email', 'role']


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['id', 'quiz', 'question_text', 'option1', 'option2', 'option3', 'option4', 'correct_option', 'explanation']


class QuestionReadSerializer(serializers.ModelSerializer):
    """Serializer for students - does NOT expose correct_option"""
    class Meta:
        model = Question
        fields = ['id', 'quiz', 'question_text', 'option1', 'option2', 'option3', 'option4']


class QuizSerializer(serializers.ModelSerializer):
    question_count = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Quiz
        fields = ['id', 'title', 'description', 'category', 'difficulty', 'time_limit',
                  'is_active', 'created_at', 'question_count', 'created_by_name']

    def get_question_count(self, obj):
        return obj.questions.count()

    def get_created_by_name(self, obj):
        if obj.created_by:
            return obj.created_by.username
        return 'Admin'


class QuizCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quiz
        fields = ['id', 'title', 'description', 'category', 'difficulty', 'time_limit', 'is_active']


class ResultSerializer(serializers.ModelSerializer):
    quiz_title = serializers.SerializerMethodField()
    percentage = serializers.SerializerMethodField()

    class Meta:
        model = Result
        fields = ['id', 'student_name', 'quiz', 'quiz_title', 'score', 'total_questions',
                  'percentage', 'time_taken', 'completed_at']

    def get_quiz_title(self, obj):
        if obj.quiz:
            return obj.quiz.title
        return 'Unknown Quiz'

    def get_percentage(self, obj):
        return obj.percentage()