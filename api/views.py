from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Count, Q
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Company, KBEntry, QueryLog
from .permissions import IsAdminUser
from .serializers import (
    KBEntrySerializer,
    KBSearchSerializer,
    LoginSerializer,
    RegisterSerializer,
)


class RegisterView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        # Creating user fires the post_save signal which creates Company + api_key
        user = User.objects.create_user(
            username=data['username'],
            email=data['email'],
            password=data['password']
        )

        company = user.company
        company.company_name = data['company_name']
        company.save(update_fields=['company_name'])

        token = str(RefreshToken.for_user(user).access_token)

        return Response({
            "username": user.username,
            "company_name": company.company_name,
            "api_key": company.api_key,
            "access": token
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        username = serializer.validated_data['username']
        password = serializer.validated_data['password']

        user = authenticate(username=username, password=password)
        if not user:
            return Response(
                {"error": "Invalid credentials. Please verify your username and password."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        company = getattr(user, 'company', None)
        token = str(RefreshToken.for_user(user).access_token)

        return Response({
            "access": token,
            "company_name": company.company_name if company else "",
            "api_key": company.api_key if company else ""
        }, status=status.HTTP_200_OK)


class KBQueryView(APIView):
    def post(self, request):
        serializer = KBSearchSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        search_term = serializer.validated_data['search']

        try:
            company = request.user.company
        except (AttributeError, Company.DoesNotExist):
            return Response(
                {"error": "No company profile found for this user."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Atomic search and QueryLog record
        with transaction.atomic():
            entries = KBEntry.objects.filter(
                Q(question__icontains=search_term) | Q(answer__icontains=search_term)
            )
            count = entries.count()

            QueryLog.objects.create(
                company=company,
                search_term=search_term,
                results_count=count
            )

            results_data = KBEntrySerializer(entries, many=True).data

        return Response({
            "search": search_term,
            "count": count,
            "results": results_data
        }, status=status.HTTP_200_OK)


class AdminUsageSummaryView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        total_queries = QueryLog.objects.aggregate(total=Count('id'))['total'] or 0
        active_companies = QueryLog.objects.values('company').distinct().count()
        top_search_terms = list(
            QueryLog.objects.values('search_term')
            .annotate(count=Count('id'))
            .order_by('-count')[:5]
        )

        return Response({
            "total_queries": total_queries,
            "active_companies": active_companies,
            "top_search_terms": top_search_terms
        }, status=status.HTTP_200_OK)
