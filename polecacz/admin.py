from django.contrib import admin
from polecacz.models import Game, GameTag, Opinion, Recommendation, SelectedGames

# Register your models here.
admin.site.register(Game)
admin.site.register(GameTag)
admin.site.register(Opinion)
admin.site.register(Recommendation)
admin.site.register(SelectedGames)
