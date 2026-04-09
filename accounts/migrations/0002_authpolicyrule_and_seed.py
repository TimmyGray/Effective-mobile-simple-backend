from django.db import migrations, models


def seed_auth_policy_rules(apps, schema_editor):
    AuthPolicyRule = apps.get_model("accounts", "AuthPolicyRule")
    AuthPolicyRule.objects.update_or_create(
        resource="auth",
        action="logout",
        defaults={"is_allowed": True},
    )
    AuthPolicyRule.objects.update_or_create(
        resource="auth",
        action="me",
        defaults={"is_allowed": True},
    )


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="AuthPolicyRule",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("resource", models.CharField(max_length=100)),
                ("action", models.CharField(max_length=100)),
                ("is_allowed", models.BooleanField(default=True)),
            ],
            options={
                "constraints": [
                    models.UniqueConstraint(fields=("resource", "action"), name="uniq_auth_policy_rule"),
                ],
            },
        ),
        migrations.RunPython(seed_auth_policy_rules, migrations.RunPython.noop),
    ]
