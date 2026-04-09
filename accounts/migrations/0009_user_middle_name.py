from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0008_seed_demo_showcase_users"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="middle_name",
            field=models.CharField(blank=True, default="", max_length=150),
        ),
    ]
