import random
import pandas as pd

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.http import HttpResponse

from .models import Question, Result, Quiz, Profile
from .serializers import (
    QuestionSerializer, QuestionReadSerializer, ResultSerializer,
    QuizSerializer, QuizCreateSerializer,
    UserRegisterSerializer, UserLoginSerializer
)


# ─────────────────────────────────────────────
# AUTH ENDPOINTS
# ─────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    serializer = UserRegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        profile = user.profile
        return Response({
            'token': token.key,
            'role': profile.role,
            'username': user.username,
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(username=username, password=password)
    if user:
        token, _ = Token.objects.get_or_create(user=user)
        try:
            role = user.profile.role
        except Exception:
            role = 'student'
        return Response({
            'token': token.key,
            'role': role,
            'username': user.username,
        })
    return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    request.user.auth_token.delete()
    return Response({'message': 'Logged out successfully'})


# ─────────────────────────────────────────────
# QUIZ LIST (Students)
# ─────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([AllowAny])
def quiz_list(request):
    quizzes = Quiz.objects.filter(is_active=True).order_by('-created_at')
    serializer = QuizSerializer(quizzes, many=True)
    return Response(serializer.data)


# ─────────────────────────────────────────────
# QUESTIONS (Students – random, no correct answer)
# ─────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([AllowAny])
def get_questions(request):
    quiz_id = request.query_params.get('quiz_id')
    if quiz_id:
        questions = list(Question.objects.filter(quiz_id=quiz_id))
    else:
        questions = list(Question.objects.all())

    random.shuffle(questions)
    qs_subset = questions[:10]

    try:
        time_limit = qs_subset[0].quiz.time_limit
        quiz_title = qs_subset[0].quiz.title
        quiz_id_val = qs_subset[0].quiz.id
    except Exception:
        time_limit = 60
        quiz_title = 'Quiz'
        quiz_id_val = None

    serializer = QuestionReadSerializer(qs_subset, many=True)
    return Response({
        "time_limit": time_limit,
        "quiz_title": quiz_title,
        "quiz_id": quiz_id_val,
        "total": len(qs_subset),
        "questions": serializer.data
    })


# ─────────────────────────────────────────────
# SUBMIT QUIZ (Students)
# ─────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([AllowAny])
def submit_quiz(request):
    answers = request.data.get('answers', [])
    name = request.data.get('name', 'Anonymous')
    quiz_id = request.data.get('quiz_id')
    time_taken = request.data.get('time_taken', 0)

    score = 0
    total = len(answers)

    for ans in answers:
        try:
            question = Question.objects.get(id=ans['question_id'])
            if question.correct_option == ans['answer']:
                score += 1
        except Question.DoesNotExist:
            pass

    quiz = None
    if quiz_id:
        try:
            quiz = Quiz.objects.get(id=quiz_id)
        except Quiz.DoesNotExist:
            pass

    user = request.user if request.user.is_authenticated else None

    Result.objects.create(
        student_name=name,
        user=user,
        quiz=quiz,
        score=score,
        total_questions=total if total > 0 else 10,
        time_taken=time_taken,
    )

    percentage = round((score / (total if total > 0 else 10)) * 100, 1)

    return Response({
        "score": score,
        "total": total if total > 0 else 10,
        "percentage": percentage,
    })


# ─────────────────────────────────────────────
# LEADERBOARD
# ─────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([AllowAny])
def leaderboard(request):
    results = Result.objects.all().order_by('-score', 'time_taken')[:20]
    serializer = ResultSerializer(results, many=True)
    return Response(serializer.data)


# ─────────────────────────────────────────────
# CSV EXPORT
# ─────────────────────────────────────────────

def export_results(request):
    results = Result.objects.all().values(
        'id', 'student_name', 'quiz__title', 'score', 'total_questions', 'time_taken', 'completed_at'
    )
    df = pd.DataFrame(results)
    if not df.empty:
        df.rename(columns={'quiz__title': 'quiz_title'}, inplace=True)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="quiz_results.csv"'
    df.to_csv(path_or_buf=response, index=False)
    return response


# ─────────────────────────────────────────────
# TEACHER – DASHBOARD STATS
# ─────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([AllowAny])
def teacher_stats(request):
    from django.contrib.auth.models import User
    total_quizzes = Quiz.objects.count()
    total_results = Result.objects.count()
    total_students = Profile.objects.filter(role='student').count()

    scores = list(Result.objects.values_list('score', 'total_questions'))
    avg_score = 0
    pass_count = 0
    if scores:
        percentages = [(s / t * 100) if t > 0 else 0 for s, t in scores]
        avg_score = round(sum(percentages) / len(percentages), 1)
        pass_count = sum(1 for p in percentages if p >= 50)

    pass_rate = round((pass_count / len(scores)) * 100, 1) if scores else 0

    return Response({
        'total_quizzes': total_quizzes,
        'total_results': total_results,
        'total_students': total_students,
        'avg_score': avg_score,
        'pass_rate': pass_rate,
    })


# ─────────────────────────────────────────────
# TEACHER – QUIZ CRUD
# ─────────────────────────────────────────────

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def teacher_quiz_list_create(request):
    if request.method == 'GET':
        quizzes = Quiz.objects.all().order_by('-created_at')
        serializer = QuizSerializer(quizzes, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = QuizCreateSerializer(data=request.data)
        if serializer.is_valid():
            quiz = serializer.save(
                created_by=request.user if request.user.is_authenticated else None
            )
            return Response(QuizSerializer(quiz).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([AllowAny])
def teacher_quiz_detail(request, quiz_id):
    try:
        quiz = Quiz.objects.get(id=quiz_id)
    except Quiz.DoesNotExist:
        return Response({'error': 'Quiz not found'}, status=404)

    if request.method == 'GET':
        serializer = QuizSerializer(quiz)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = QuizCreateSerializer(quiz, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(QuizSerializer(quiz).data)
        return Response(serializer.errors, status=400)

    elif request.method == 'DELETE':
        quiz.delete()
        return Response({'message': 'Quiz deleted'}, status=204)


# ─────────────────────────────────────────────
# TEACHER – QUESTION CRUD
# ─────────────────────────────────────────────

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def teacher_question_list_create(request, quiz_id):
    try:
        quiz = Quiz.objects.get(id=quiz_id)
    except Quiz.DoesNotExist:
        return Response({'error': 'Quiz not found'}, status=404)

    if request.method == 'GET':
        questions = quiz.questions.all()
        serializer = QuestionSerializer(questions, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        data = request.data.copy()
        data['quiz'] = quiz_id
        serializer = QuestionSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


@api_view(['PUT', 'DELETE'])
@permission_classes([AllowAny])
def teacher_question_detail(request, question_id):
    try:
        question = Question.objects.get(id=question_id)
    except Question.DoesNotExist:
        return Response({'error': 'Question not found'}, status=404)

    if request.method == 'PUT':
        serializer = QuestionSerializer(question, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    elif request.method == 'DELETE':
        question.delete()
        return Response({'message': 'Question deleted'}, status=204)


# ─────────────────────────────────────────────
# TEACHER – VIEW STUDENT RESULTS PER QUIZ
# ─────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([AllowAny])
def teacher_quiz_results(request, quiz_id):
    results = Result.objects.filter(quiz_id=quiz_id).order_by('-completed_at')
    serializer = ResultSerializer(results, many=True)
    return Response(serializer.data)