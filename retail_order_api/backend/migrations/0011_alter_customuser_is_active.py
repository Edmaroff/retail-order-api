# Generated by Django 5.0.1 on 2024-01-31 10:58

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        (
            "backend",
            "0010_alter_productinfo_options_alter_customuser_username_and_more",
        ),
    ]

    operations = [
        migrations.AlterField(
            model_name="customuser",
            name="is_active",
            field=models.BooleanField(
                default=True,
                help_text="Designates whether this user should be treated as active. Unselect this instead of deleting accounts.",
                verbose_name="active",
            ),
        ),
    ]