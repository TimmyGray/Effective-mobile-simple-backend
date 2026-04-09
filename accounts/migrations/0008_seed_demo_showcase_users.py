from django.contrib.auth.hashers import make_password
from django.db import migrations

# Demo-only credentials (local / recruitment showcase). Do not use in production.
DEMO_PASSWORD = "DemoShowcase2026!"

DEMO_USERS = (
    {
        "email": "demo.member@example.com",
        "is_staff": False,
        "is_superuser": False,
        "bind_member_role": True,
    },
    {
        "email": "demo.staff@example.com",
        "is_staff": True,
        "is_superuser": False,
        "bind_member_role": False,
    },
    {
        "email": "demo.plain@example.com",
        "is_staff": False,
        "is_superuser": False,
        "bind_member_role": False,
    },
)


def seed_demo_users(apps, schema_editor):
    """
    AI Annotation:
    - Purpose: Populate showcase accounts so RBAC and admin flows are demonstrable without manual setup.
    - Inputs: Assumes `member` role and `widgets:list` matrix from prior migrations.
    - Side effects: Creates or updates `User` rows and `UserRole` for the member demo account.
    - Security notes: Password is a fixed demo string; documented in ARCHITECTURE.md; not for production.
    """
    User = apps.get_model("accounts", "User")
    Role = apps.get_model("accounts", "Role")
    UserRole = apps.get_model("accounts", "UserRole")

    hashed = make_password(DEMO_PASSWORD)
    member_role = Role.objects.filter(name="member").first()
    if not member_role:
        raise RuntimeError("Expected 'member' role from 0006_seed_demo_rbac_matrix")

    for spec in DEMO_USERS:
        email = spec["email"]
        user, _ = User.objects.update_or_create(
            email=email,
            defaults={
                "username": email,
                "password": hashed,
                "is_active": True,
                "is_staff": spec["is_staff"],
                "is_superuser": spec["is_superuser"],
            },
        )
        if spec["bind_member_role"]:
            UserRole.objects.get_or_create(user=user, role=member_role)


def unseed_demo_users(apps, schema_editor):
    """
    AI Annotation:
    - Purpose: Remove showcase users created by `seed_demo_users` for migration reversal.
    - Side effects: Deletes matching users; `UserRole` rows cascade.
    """
    User = apps.get_model("accounts", "User")
    emails = [s["email"] for s in DEMO_USERS]
    User.objects.filter(email__in=emails).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0007_seed_admin_manage_policy"),
    ]

    operations = [
        migrations.RunPython(seed_demo_users, unseed_demo_users),
    ]
