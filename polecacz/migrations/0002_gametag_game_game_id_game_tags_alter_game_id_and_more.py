# Generated by Django 4.1 on 2022-09-01 21:38

from django.db import migrations, models
import django.db.models.deletion
import taggit.managers
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ("taggit", "0005_auto_20220424_2025"),
        ("polecacz", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="GameTag",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.AddField(
            model_name="game",
            name="game_id",
            field=models.CharField(default=10, max_length=35),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="game",
            name="tags",
            field=taggit.managers.TaggableManager(
                help_text="A comma-separated list of tags.",
                through="polecacz.GameTag",
                to="taggit.Tag",
                verbose_name="Tags",
            ),
        ),
        migrations.AlterField(
            model_name="game",
            name="id",
            field=models.UUIDField(
                default=uuid.uuid4, editable=False, primary_key=True, serialize=False
            ),
        ),
        migrations.AddField(
            model_name="gametag",
            name="content_object",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="polecacz.game"
            ),
        ),
        migrations.AddField(
            model_name="gametag",
            name="tag",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="%(app_label)s_%(class)s_items",
                to="taggit.tag",
            ),
        ),
    ]
