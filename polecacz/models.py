import uuid

from django.conf import settings
from django.db import models
from taggit.managers import TaggableManager
from taggit.models import TaggedItemBase
# Create your models here.


class GameTag(TaggedItemBase):
    content_object = models.ForeignKey('Game', on_delete=models.CASCADE)


class Game(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    game_id = models.CharField(max_length=35, null=True)
    artist = models.CharField(max_length=350, null=True)
    designer = models.CharField(max_length=350, null=True)
    rank = models.IntegerField(null=True)
    rating = models.FloatField(null=True)
    thumbnail = models.CharField(max_length=200)
    name = models.CharField(max_length=200)
    year_published = models.CharField(max_length=4)
    min_players = models.IntegerField(null=True)
    max_players = models.IntegerField(null=True)
    playing_time = models.IntegerField(null=True)
    tags = TaggableManager(through=GameTag)

    def __str__(self):
        return f'{self.name}, Tags: {self.tags.names()}'


class Opinion(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    rating = models.FloatField()
    description = models.TextField(max_length=500)
    recommendation_id = models.IntegerField()


class SelectedGames(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    selected_games = models.ManyToManyField(Game)
