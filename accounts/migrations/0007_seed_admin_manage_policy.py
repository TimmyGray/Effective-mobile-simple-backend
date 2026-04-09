from django.db import migrations


def seed_admin_manage_policy(apps, schema_editor):
    AuthPolicyRule = apps.get_model("accounts", "AuthPolicyRule")
    for role_name in ("staff", "superuser"):
        AuthPolicyRule.objects.update_or_create(
            resource="admin",
            action="manage",
            subject_type="role",
            subject_value=role_name,
            defaults={"is_allowed": True},
        )


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0006_seed_demo_rbac_matrix"),
    ]

    operations = [
        migrations.RunPython(seed_admin_manage_policy, migrations.RunPython.noop),
    ]
