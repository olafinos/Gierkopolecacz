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
    game_id = models.CharField(max_length=35)
    rank = models.IntegerField()
    rating = models.FloatField()
    thumbnail = models.CharField(max_length=200)
    name = models.CharField(max_length=200)
    year_published = models.CharField(max_length=4)
    min_players = models.IntegerField()
    max_players = models.IntegerField()
    playing_time = models.IntegerField()
    tags = TaggableManager(through=GameTag)


class Opinion(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    rating = models.FloatField()
    description = models.TextField(max_length=500)
    recommendation_id = models.IntegerField()
