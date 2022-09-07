from django.core.management.base import BaseCommand

from polecacz.bgg_api.api_wrapper import BGGApiWrapper
from polecacz.models import Game


class Command(BaseCommand):
    help = 'Imports game data to database'

    def handle(self, *args, **options):
        bgg_api_wrap = BGGApiWrapper()
        data, wrong_data = bgg_api_wrap.prepare_data_to_import_to_database(10)
        counter = 0
        for game_info in data:
            try:
                game, _ = Game.objects.update_or_create(game_id=game_info['id'])
                game.rank = int(game_info['rank'])
                game.rating = float(game_info['average'])
                game.thumbnail = game_info['thumbnail']
                game.name = game_info['game_name']
                game.year_published = game_info['year_published']
                game.min_players = int(game_info['min_players'])
                game.max_players = int(game_info['max_players'])
                game.playing_time = int(game_info['playing_time'])
                game.artist = game_info['artist']
                game.designer = game_info['designer']
                game.tags.set([*game_info['categories'], *game_info['mechanics']])
                game.save()
                counter += 1
            except Exception as exception:
                self.stdout.write(self.style.WARNING(f'There was a problem with game: {game_info}, Exception: {exception.__class__.__name__}: {str(exception)}'))
        self.stdout.write(self.style.SUCCESS(f'Processed {counter} games'))
        if wrong_data:
            self.stdout.write(self.style.WARNING('There was an error with preparing data to import, affected games: '))
            for game in wrong_data:
                self.stdout.write(self.style.WARNING(game))
