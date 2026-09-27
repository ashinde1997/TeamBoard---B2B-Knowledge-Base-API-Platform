from django.core.management.base import BaseCommand
from api.models import KBEntry


class Command(BaseCommand):
    help = 'Seeds the Knowledge Base with initial Q&A entries across various categories'

    def handle(self, *args, **options):
        entries = [
            {
                "category": KBEntry.Category.DATABASE,
                "question": "What is select_related in Django ORM?",
                "answer": "select_related performs a SQL JOIN and fetches related single-valued relationships (ForeignKey, OneToOneField) in a single query to reduce database hits."
            },
            {
                "category": KBEntry.Category.DATABASE,
                "question": "When should I use select_related vs prefetch_related?",
                "answer": "Use select_related for single-valued relationships (ForeignKey, OneToOne) using SQL JOINs, and prefetch_related for multi-valued relationships (ManyToMany, reverse ForeignKey) using separate batch queries."
            },
            {
                "category": KBEntry.Category.DATABASE,
                "question": "How does transaction.atomic() work in Django?",
                "answer": "transaction.atomic() creates an atomic transaction block using SQL BEGIN and COMMIT/ROLLBACK or SAVEPOINTs. If an unhandled exception occurs inside the block, all database operations within it are rolled back."
            },
            {
                "category": KBEntry.Category.DATABASE,
                "question": "When should I use Q objects in Django queries?",
                "answer": "Q objects allow complex database lookups with logical operators like OR (|), AND (&), and NOT (~). For example: Q(question__icontains=term) | Q(answer__icontains=term)."
            },
            {
                "category": KBEntry.Category.DATABASE,
                "question": "Why should database credentials be stored in environment variables?",
                "answer": "Storing database credentials in environment variables keeps sensitive secrets out of source code, allows distinct configurations per environment, and follows Twelve-Factor App principles."
            },
            {
                "category": KBEntry.Category.API,
                "question": "What is a JWT token and how is it structured?",
                "answer": "A JWT (JSON Web Token) is a compact, URL-safe means of representing claims between two parties. It consists of three parts separated by dots: header, payload, and signature."
            },
            {
                "category": KBEntry.Category.API,
                "question": "How does JWT authentication work in Django REST Framework?",
                "answer": "DRF uses libraries like SimpleJWT to authenticate incoming HTTP requests via Authorization Bearer headers containing a signed JWT token."
            },
            {
                "category": KBEntry.Category.API,
                "question": "What is the difference between an API key and a JWT token?",
                "answer": "An API key is typically a long-lived credential identifying a project or client application, while a JWT token is short-lived, digitally signed, and encapsulates verified user identity and permissions."
            },
            {
                "category": KBEntry.Category.FRAMEWORK,
                "question": "How do Django signals work and when should you use post_save?",
                "answer": "Django signals allow decoupled components to get notified when actions occur elsewhere in the framework. A post_save signal on User is commonly used to auto-create related profile models."
            },
            {
                "category": KBEntry.Category.FRAMEWORK,
                "question": "How do custom permissions work in Django REST Framework?",
                "answer": "Custom permissions extend BasePermission and override has_permission() or has_object_permission() to enforce fine-grained role-based access control."
            },
            {
                "category": KBEntry.Category.CLOUD,
                "question": "How does Docker containerization benefit backend services?",
                "answer": "Docker packages applications and dependencies into isolated containers, ensuring reproducible environments across development, testing, and production."
            },
            {
                "category": KBEntry.Category.CLOUD,
                "question": "How do you run PostgreSQL in a Docker container?",
                "answer": "You run PostgreSQL in Docker using official postgres images, mapping port 5432, defining environment variables for DB credentials, and persisting data with Docker volumes."
            },
            {
                "category": KBEntry.Category.GENERAL,
                "question": "What are the core principles of RESTful API design?",
                "answer": "Core REST principles include stateless communication, standard HTTP methods (GET, POST, PUT, DELETE), uniform resource identifiers (URIs), and standard HTTP status codes."
            }
        ]

        created_count = 0
        for data in entries:
            entry, created = KBEntry.objects.get_or_create(
                question=data["question"],
                defaults={
                    "answer": data["answer"],
                    "category": data["category"]
                }
            )
            if created:
                created_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"Successfully seeded knowledge base. {created_count} entries created ({len(entries)} total in seed set)."
        ))
