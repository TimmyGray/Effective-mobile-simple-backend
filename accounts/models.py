from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager["User"]):
    use_in_migrations = True

    def _create_user(self, email: str, password: str, **extra_fields: object) -> "User":
        """
        AI Annotation:
        - Purpose: Centralize low-level user creation for regular and superuser flows.
        - Inputs: Requires email and raw password plus model-specific extra fields.
        - Side effects: Persists a new user row and hashes password before save.
        - Failure modes: Raises ValueError when email is missing.
        """
        if not email:
            raise ValueError("Email must be set")
        normalized_email = self.normalize_email(email)
        user = self.model(email=normalized_email, username=normalized_email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email: str, password: str | None = None, **extra_fields: object) -> "User":
        """
        AI Annotation:
        - Purpose: Create a standard non-privileged account with safe defaults.
        - Inputs: Email and non-null password with optional profile fields.
        - Outputs: Returns persisted User instance with `is_staff`/`is_superuser` forced false.
        - Failure modes: Raises ValueError when password is omitted.
        """
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
        """
        AI Annotation:
        - Purpose: Create a privileged administrative account with enforced flags.
        - Inputs: Email and non-null password, with optional overriding fields.
        - Outputs: Returns persisted User instance configured for admin access.
        - Security notes: Explicitly validates `is_staff` and `is_superuser` to prevent misconfiguration.
        """
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
    middle_name = models.CharField(max_length=150, blank=True, default="")

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


class Role(models.Model):
    """
    Named security role; users are bound via `UserRole` and granted capabilities via `RolePermission`.
    Referenced by `AuthPolicyRule` subject_type=role and by the RBAC matrix.
    """

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, default="")

    def __str__(self) -> str:
        return self.name


class AccessPermission(models.Model):
    """
    Grantable capability: a (resource, action) pair evaluated by `policy.decide()` via the matrix.
    """

    resource = models.CharField(max_length=100)
    action = models.CharField(max_length=100)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["resource", "action"],
                name="uniq_access_permission_resource_action",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.resource}:{self.action}"


class RolePermission(models.Model):
    """
    Matrix entry: grants one access permission to a role.
    """

    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="role_permissions")
    access_permission = models.ForeignKey(
        AccessPermission,
        on_delete=models.CASCADE,
        related_name="role_grants",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["role", "access_permission"],
                name="uniq_role_access_permission",
            ),
        ]


class UserRole(models.Model):
    """
    Binds a user to a named role for matrix-based authorization and `AuthPolicyRule` subject_type=role.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_roles")
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="user_bindings")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "role"], name="uniq_user_role"),
        ]
