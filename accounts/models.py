from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager["User"]):
    use_in_migrations = True

    def _create_user(self, email: str, password: str, **extra_fields: object) -> "User":
        if not email:
            raise ValueError("Email must be set")
        normalized_email = self.normalize_email(email)
        user = self.model(email=normalized_email, username=normalized_email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email: str, password: str | None = None, **extra_fields: object) -> "User":
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        if password is None:
            raise ValueError("Password must be set")
        return self._create_user(email, password, **extra_fields)

    def create_superuser(
        self,
        email: str,
        password: str | None = None,
        **extra_fields: object,
    ) -> "User":
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        if password is None:
            raise ValueError("Password must be set")
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    username = models.CharField(max_length=150, blank=True)
    email = models.EmailField(unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    objects = UserManager()


class AuthPolicyRule(models.Model):
    SUBJECT_ANY = "any"
    SUBJECT_USER = "user"
    SUBJECT_ROLE = "role"
    SUBJECT_CHOICES = (
        (SUBJECT_ANY, "Any authenticated user"),
        (SUBJECT_USER, "Specific user"),
        (SUBJECT_ROLE, "Role"),
    )

    resource = models.CharField(max_length=100)
    action = models.CharField(max_length=100)
    subject_type = models.CharField(max_length=20, choices=SUBJECT_CHOICES, default=SUBJECT_ANY)
    subject_value = models.CharField(max_length=150, blank=True, default="")
    is_allowed = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["resource", "action", "subject_type", "subject_value"],
                name="uniq_auth_policy_rule_subject",
            ),
        ]
