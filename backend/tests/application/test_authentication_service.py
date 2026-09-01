import unittest
from datetime import datetime

from app.application.services.authentication_service import AuthenticationService
from app.domain.entities.user import User, UserRole


class FakeUserRepository:
    def __init__(self, users):
        self.users = {user.email: user for user in users}

    async def create_user(self, name, email, hashed_password, role):
        user = User(
            id=f"user-{len(self.users) + 1}",
            name=name,
            email=email,
            role=role,
            created_at=datetime(2026, 1, 1),
            hashed_password=hashed_password,
        )
        self.users[email] = user
        return user

    async def get_user_by_email(self, email):
        return self.users.get(email)

    async def user_exists(self, email):
        return email in self.users

    async def list_users(self, role=None):
        users = list(self.users.values())
        return [user for user in users if role is None or user.role == role]


class FakePasswordHasher:
    def hash_password(self, password):
        return f"hashed:{password}"


class FakeTokenService:
    def create_token(self, user):
        return f"token:{user.email}"


class AuthenticationServiceTests(unittest.IsolatedAsyncioTestCase):
    def build_service(self, role=UserRole.ADMIN):
        admin = User(
            id="admin-1",
            name="Admin",
            email="admin@example.com",
            role=role,
            created_at=datetime(2026, 1, 1),
        )
        repository = FakeUserRepository([admin])
        service = AuthenticationService(
            user_repository=repository,
            password_hasher=FakePasswordHasher(),
            token_service=FakeTokenService(),
        )
        return service, repository

    async def test_candidate_registration_rejects_weak_passwords(self):
        service, repository = self.build_service()

        for password in (
            "Abcdef!",
            "12345678!",
            "Password1",
            "Abcdefg\u200d",
            "aaaaaaa\u0301",
        ):
            with self.subTest(password=password):
                with self.assertRaisesRegex(ValueError, "al menos 8 caracteres"):
                    await service.register_user(
                        name="Candidate",
                        email="candidate@example.com",
                        password=password,
                    )

        self.assertNotIn("candidate@example.com", repository.users)

    async def test_candidate_registration_accepts_exactly_eight_characters(self):
        service, repository = self.build_service()

        result = await service.register_user(
            name="Candidate",
            email="candidate@example.com",
            password="Abcdefg!",
        )

        self.assertEqual(result["user"]["role"], "candidate")
        self.assertEqual(
            repository.users["candidate@example.com"].hashed_password,
            "hashed:Abcdefg!",
        )

    async def test_admin_creation_rejects_weak_hr_password(self):
        service, repository = self.build_service()

        with self.assertRaisesRegex(ValueError, "carácter especial"):
            await service.create_user_as_admin(
                admin_email="admin@example.com",
                name="Human Resources",
                email="hr@example.com",
                password="Password1",
                role="hr",
            )

        self.assertNotIn("hr@example.com", repository.users)

    async def test_admin_creates_hr_user_and_lists_it_by_role(self):
        service, repository = self.build_service()

        result = await service.create_user_as_admin(
            admin_email="admin@example.com",
            name="Human Resources",
            email="hr@example.com",
            password="temporary-password",
            role="hr",
        )
        users = await service.list_users_as_admin("admin@example.com", "hr")

        self.assertEqual(result["user"]["role"], "hr")
        self.assertEqual(repository.users["hr@example.com"].role, UserRole.HR)
        self.assertEqual([user["email"] for user in users], ["hr@example.com"])
        self.assertNotIn("hashed_password", users[0])

    async def test_non_admin_cannot_list_users(self):
        service, _ = self.build_service(UserRole.HR)

        with self.assertRaisesRegex(ValueError, "Only admins can list users"):
            await service.list_users_as_admin("admin@example.com", "hr")


if __name__ == "__main__":
    unittest.main()