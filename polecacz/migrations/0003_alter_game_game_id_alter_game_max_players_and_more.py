# Generated by Django 4.1 on 2022-09-02 15:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polecacz', '0002_gametag_game_game_id_game_tags_alter_game_id_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='game',
            name='game_id',
            field=models.CharField(blank=True, max_length=35),
        ),
        migrations.AlterField(
            model_name='game',
            name='max_players',
            field=models.IntegerField(blank=True),
        ),
        migrations.AlterField(
            model_name='game',
            name='min_players',
            field=models.IntegerField(blank=True),
        ),
        migrations.AlterField(
            model_name='game',
            name='playing_time',
            field=models.IntegerField(blank=True),
        ),
        migrations.AlterField(
            model_name='game',
            name='rank',
            field=models.IntegerField(blank=True),
        ),
        migrations.AlterField(
            model_name='game',
            name='rating',
            field=models.FloatField(blank=True),
        ),
    ]
