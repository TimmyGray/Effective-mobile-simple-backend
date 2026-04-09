from django.db import migrations


def seed_profile_policies(apps, schema_editor):
    AuthPolicyRule = apps.get_model("accounts", "AuthPolicyRule")
    for action in ("profile_update", "account_deactivate"):
        AuthPolicyRule.objects.update_or_create(
            resource="auth",
            action=action,
            subject_type="any",
            subject_value="",
            defaults={"is_allowed": True},
        )


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0003_authpolicyrule_subject_fields"),
    ]

    operations = [
        migrations.RunPython(seed_profile_policies, migrations.RunPython.noop),
    ]
