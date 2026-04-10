from django.contrib.auth.hashers import make_password
from django.db import migrations

# Demo-only credentials (local / recruitment showcase). Do not use in production.
DEMO_PASSWORD = "DemoShowcase2026!"

DEMO_USERS = (
    {
        "email": "demo.member@example.com",
        "first_name": "Maksim",
        "last_name": "Memberov",
        "middle_name": "Andreevich",
        "is_staff": False,
        "is_superuser": False,
        "bind_member_role": True,
    },
    {
        "email": "demo.staff@example.com",
        "first_name": "Svetlana",
        "last_name": "Staffova",
        "middle_name": "Igorevna",
        "is_staff": True,
        "is_superuser": False,
        "bind_member_role": False,
    },
    {
        "email": "demo.plain@example.com",
        "first_name": "Pavel",
        "last_name": "Plainov",
        "middle_name": "Olegovich",
        "is_staff": False,
        "is_superuser": False,
        "bind_member_role": False,
    },
    {
        "email": "demo.member2@example.com",
        "first_name": "Alina",
        "last_name": "Kuznetsova",
        "middle_name": "Sergeevna",
        "is_staff": False,
        "is_superuser": False,
        "bind_member_role": True,
    },
    {
        "email": "demo.member3@example.com",
        "first_name": "Roman",
        "last_name": "Volkov",
        "middle_name": "Nikolaevich",
        "is_staff": False,
        "is_superuser": False,
        "bind_member_role": True,
    },
    {
        "email": "demo.auditor@example.com",
        "first_name": "Elena",
        "last_name": "Auditova",
        "middle_name": "Petrovna",
        "is_staff": False,
        "is_superuser": False,
        "bind_member_role": False,
    },
)


def seed_demo_showcase_user_profiles(apps, schema_editor):
    """
    AI Annotation:
    - Purpose: Expand demo showcase accounts and populate complete profile name fields.
    - Inputs: Assumes User model already has `middle_name` and role `member` exists from prior seeds.
    - Side effects: Creates/updates demo User rows with fixed credentials and binds selected users to `member`.
    - Security notes: Uses a documented fixed demo password strictly for local/recruitment environments.
    """
    User = apps.get_model("accounts", "User")
    Role = apps.get_model("accounts", "Role")
    UserRole = apps.get_model("accounts", "UserRole")

    hashed_password = make_password(DEMO_PASSWORD)
    member_role = Role.objects.filter(name="member").first()
    if not member_role:
        raise RuntimeError("Expected 'member' role from 0006_seed_demo_rbac_matrix")

    for spec in DEMO_USERS:
        email = spec["email"]
        user, _ = User.objects.update_or_create(
            email=email,
            defaults={
                "username": email,
                "password": hashed_password,
                "is_active": True,
                "first_name": spec["first_name"],
                "last_name": spec["last_name"],
                "middle_name": spec["middle_name"],
                "is_staff": spec["is_staff"],
                "is_superuser": spec["is_superuser"],
            },
        )
        if spec["bind_member_role"]:
            UserRole.objects.get_or_create(user=user, role=member_role)


def unseed_demo_showcase_user_profiles(apps, schema_editor):
    """
    AI Annotation:
    - Purpose: Roll back the demo showcase users managed by this migration.
    - Side effects: Deletes matched demo accounts; related `UserRole` rows are removed by cascade.
    """
    User = apps.get_model("accounts", "User")
    emails = [spec["email"] for spec in DEMO_USERS]
    User.objects.filter(email__in=emails).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0009_user_middle_name"),
    ]

    operations = [
        migrations.RunPython(seed_demo_showcase_user_profiles, unseed_demo_showcase_user_profiles),
    ]
