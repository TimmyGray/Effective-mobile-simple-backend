from django.db import migrations, models


def populate_existing_rules(apps, schema_editor):
    AuthPolicyRule = apps.get_model("accounts", "AuthPolicyRule")
    for rule in AuthPolicyRule.objects.all():
        rule.subject_type = "any"
        rule.subject_value = ""
        rule.save(update_fields=["subject_type", "subject_value"])


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0002_authpolicyrule_and_seed"),
    ]

    operations = [
        migrations.AddField(
            model_name="authpolicyrule",
            name="subject_type",
            field=models.CharField(
                choices=[
                    ("any", "Any authenticated user"),
                    ("user", "Specific user"),
                    ("role", "Role"),
                ],
                default="any",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="authpolicyrule",
            name="subject_value",
            field=models.CharField(blank=True, default="", max_length=150),
        ),
        migrations.RunPython(populate_existing_rules, migrations.RunPython.noop),
        migrations.RemoveConstraint(
            model_name="authpolicyrule",
            name="uniq_auth_policy_rule",
        ),
        migrations.AddConstraint(
            model_name="authpolicyrule",
            constraint=models.UniqueConstraint(
                fields=("resource", "action", "subject_type", "subject_value"),
                name="uniq_auth_policy_rule_subject",
            ),
        ),
    ]
