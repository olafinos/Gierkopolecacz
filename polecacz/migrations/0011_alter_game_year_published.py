# Generated by Django 4.1 on 2022-09-11 17:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("polecacz", "0010_remove_opinion_recommendation_id_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="game",
            name="year_published",
            field=models.CharField(max_length=5),
        ),
    ]
