from django.db import migrations


def seed_demo_rbac_matrix(apps, schema_editor):
    """
    Minimal demo data for recruitment-task RBAC: role + matrix row so the schema is visibly populated.
    Demo user bindings are created in migration `0008_seed_demo_showcase_users` (B-H3).
    """
    Role = apps.get_model("accounts", "Role")
    AccessPermission = apps.get_model("accounts", "AccessPermission")
    RolePermission = apps.get_model("accounts", "RolePermission")

    member, _ = Role.objects.get_or_create(
        name="member",
        defaults={"description": "Demo role for mock business resources"},
    )
    ap, _ = AccessPermission.objects.get_or_create(
        resource="widgets",
        action="list",
        defaults={},
    )
    RolePermission.objects.get_or_create(role=member, access_permission=ap)


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0005_role_matrix"),
    ]

    operations = [
        migrations.RunPython(seed_demo_rbac_matrix, migrations.RunPython.noop),
    ]
