# Generated by Django 4.1 on 2022-09-07 14:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("polecacz", "0005_game_artist_game_designer"),
    ]

    operations = [
        migrations.AlterField(
            model_name="game",
            name="designer",
            field=models.CharField(max_length=900, null=True),
        ),
    ]
