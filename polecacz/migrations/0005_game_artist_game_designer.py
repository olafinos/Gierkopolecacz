# Generated by Django 4.1 on 2022-09-07 14:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polecacz', '0004_alter_game_game_id_alter_game_max_players_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='game',
            name='artist',
            field=models.CharField(max_length=350, null=True),
        ),
        migrations.AddField(
            model_name='game',
            name='designer',
            field=models.CharField(max_length=350, null=True),
        ),
    ]