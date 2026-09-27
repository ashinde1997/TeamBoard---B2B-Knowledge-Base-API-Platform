from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from api.models import Company, KBEntry, QueryLog


class TeamBoardAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Seed KB entries for query testing
        self.kb1 = KBEntry.objects.create(
            category=KBEntry.Category.DATABASE,
            question="What is select_related in Django ORM?",
            answer="select_related performs a SQL JOIN and fetches related single-valued relationships."
        )
        self.kb2 = KBEntry.objects.create(
            category=KBEntry.Category.DATABASE,
            question="How does transaction.atomic() work in Django?",
            answer="transaction.atomic() guarantees atomicity for a series of database operations."
        )
        self.kb3 = KBEntry.objects.create(
            category=KBEntry.Category.API,
            question="What is a JWT token?",
            answer="A JSON Web Token used for stateless authentication."
        )

        # Create a Client company user
        self.client_user = User.objects.create_user(
            username="clientuser",
            password="clientpassword123",
            email="client@example.com"
        )
        # Note: Company is auto-created by signal on User creation
        self.client_company = self.client_user.company
        self.client_company.company_name = "Client Corp"
        self.client_company.save()

        # Generate tokens for client user
        self.client_token = str(RefreshToken.for_user(self.client_user).access_token)

        # Create an Admin company user
        self.admin_user = User.objects.create_user(
            username="adminuser",
            password="adminpassword123",
            email="admin@example.com"
        )
        self.admin_company = self.admin_user.company
        self.admin_company.company_name = "Admin Corp"
        self.admin_company.role = Company.Role.ADMIN
        self.admin_company.save()

        # Generate tokens for admin user
        self.admin_token = str(RefreshToken.for_user(self.admin_user).access_token)

    # Scenario 1: Register a new company
    def test_01_register_new_company_success(self):
        url = reverse('auth-register')
        payload = {
            "username": "newcompany",
            "password": "strongpassword123",
            "company_name": "New Innovations Inc",
            "email": "contact@newinnovations.com"
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertEqual(data["username"], "newcompany")
        self.assertEqual(data["company_name"], "New Innovations Inc")
        self.assertIn("api_key", data)
        self.assertTrue(len(data["api_key"]) > 0)
        self.assertIn("access", data)
        self.assertTrue(len(data["access"]) > 0)

        # Verify company in DB
        created_user = User.objects.get(username="newcompany")
        self.assertTrue(hasattr(created_user, 'company'))
        self.assertEqual(created_user.company.role, Company.Role.CLIENT)
        self.assertEqual(created_user.company.company_name, "New Innovations Inc")

    # Scenario 2: Register with duplicate username
    def test_02_register_duplicate_username_fails(self):
        url = reverse('auth-register')
        payload = {
            "username": "clientuser",  # Already exists
            "password": "anotherpassword123",
            "company_name": "Another Corp",
            "email": "another@example.com"
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # Scenario 3: Login with valid credentials
    def test_03_login_valid_credentials_success(self):
        url = reverse('auth-login')
        payload = {
            "username": "clientuser",
            "password": "clientpassword123"
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn("access", data)
        self.assertEqual(data["company_name"], "Client Corp")
        self.assertEqual(data["api_key"], self.client_company.api_key)

    # Scenario 4: Login with wrong password
    def test_04_login_wrong_password_fails(self):
        url = reverse('auth-login')
        payload = {
            "username": "clientuser",
            "password": "wrongpassword_incorrect"
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        data = response.json()
        self.assertIn("error", data)

    # Scenario 5: Query KB - no token
    def test_05_query_kb_no_token_unauthorized(self):
        url = reverse('kb-query')
        payload = {"search": "select_related"}
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # Scenario 6: Query KB - valid token, keyword with results
    def test_06_query_kb_valid_token_with_results(self):
        url = reverse('kb-query')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.client_token}')
        payload = {"search": "select_related"}
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["search"], "select_related")
        self.assertGreaterEqual(data["count"], 1)
        self.assertEqual(len(data["results"]), data["count"])
        self.assertEqual(data["results"][0]["question"], self.kb1.question)

    # Scenario 7: Query KB - valid token, no matching results
    def test_07_query_kb_valid_token_no_results(self):
        url = reverse('kb-query')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.client_token}')
        payload = {"search": "nonexistent_term_xyz_123"}
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["search"], "nonexistent_term_xyz_123")
        self.assertEqual(data["count"], 0)
        self.assertEqual(data["results"], [])

    # Scenario 8: Query KB - missing search field
    def test_08_query_kb_missing_search_field(self):
        url = reverse('kb-query')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.client_token}')
        payload = {}
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Blank string test
        payload_blank = {"search": "   "}
        response_blank = self.client.post(url, payload_blank, format='json')
        self.assertEqual(response_blank.status_code, status.HTTP_400_BAD_REQUEST)

    # Scenario 9: Usage summary - CLIENT token
    def test_09_usage_summary_client_token_forbidden(self):
        url = reverse('admin-usage-summary')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.client_token}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # Scenario 10: Usage summary - Admin token
    def test_10_usage_summary_admin_token_success(self):
        # Create some query logs
        QueryLog.objects.create(company=self.client_company, search_term="select_related", results_count=1)
        QueryLog.objects.create(company=self.client_company, search_term="select_related", results_count=1)
        QueryLog.objects.create(company=self.admin_company, search_term="transaction atomic", results_count=2)

        url = reverse('admin-usage-summary')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["total_queries"], 3)
        self.assertEqual(data["active_companies"], 2)
        self.assertTrue(len(data["top_search_terms"]) > 0)
        # Check top search term is select_related with count 2
        self.assertEqual(data["top_search_terms"][0]["search_term"], "select_related")
        self.assertEqual(data["top_search_terms"][0]["count"], 2)

    # Scenario 11: Verify QueryLog created after queries
    def test_11_verify_query_log_created_in_database(self):
        initial_log_count = QueryLog.objects.count()

        url = reverse('kb-query')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.client_token}')

        # Scenario 6 type query
        self.client.post(url, {"search": "select_related"}, format='json')
        # Scenario 7 type query (zero results)
        self.client.post(url, {"search": "nothingmatcheshere"}, format='json')

        self.assertEqual(QueryLog.objects.count(), initial_log_count + 2)

        latest_logs = QueryLog.objects.filter(company=self.client_company).order_by('-queried_at')[:2]
        terms = [log.search_term for log in latest_logs]
        self.assertIn("select_related", terms)
        self.assertIn("nothingmatcheshere", terms)

        # Check zero results log still recorded results_count = 0
        zero_log = QueryLog.objects.get(search_term="nothingmatcheshere")
        self.assertEqual(zero_log.results_count, 0)
        self.assertEqual(zero_log.company, self.client_company)

    # Security check: User cannot register as admin by sending role in payload
    def test_register_role_tampering_prevented(self):
        url = reverse('auth-register')
        payload = {
            "username": "hackercompany",
            "password": "password123",
            "company_name": "Hacker Corp",
            "email": "hacker@example.com",
            "role": "admin"  # Malicious attempt
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user = User.objects.get(username="hackercompany")
        self.assertEqual(user.company.role, Company.Role.CLIENT)
