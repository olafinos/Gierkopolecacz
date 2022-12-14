from typing import Union

from django.contrib.auth.models import User
from django.http import Http404
from pyrebase import pyrebase

from polecacz.models import Game, SelectedGames, Recommendation, OwnedGames, ImageMetadata
from django.db.models import Count, QuerySet, Q
from gierkopolecacz.settings import storage_config


class ImageMetadataService:

    @staticmethod
    def get_image_metadata_objects_for_user_and_game(user: User, game_id: str) -> ImageMetadata:
        return ImageMetadata.objects.filter(game=game_id, user=user).all()

    @staticmethod
    def get_user_images_names_with_tokens_added_to_game(user: str, game_id: str) -> list[tuple[str, str]]:
        user_images = ImageMetadata.objects.filter(user=user, game=game_id).all()
        return [(user_image.image_name, user_image.download_token) for user_image in user_images]

    @staticmethod
    def get_game_images_with_tokens(game_id: str) -> list[tuple[str, str]]:
        game_images = ImageMetadata.objects.filter(game=game_id).all()
        return [(game_image.image_name, game_image.download_token) for game_image in game_images]

    @staticmethod
    def get_token(user: User, game_id: str, image_name: str) -> str:
        image_metadata = ImageMetadata.objects.filter(game=game_id, user=user, image_name=image_name).first()
        return image_metadata.download_token

    @staticmethod
    def get_image_metadata_object(user: User, game_id: str, image_name: str) -> ImageMetadata:
        return ImageMetadata.objects.filter(game=game_id, user=user, image_name=image_name).first()


class FirebaseStorageService:

    def __init__(self):
        self.firebase = pyrebase.initialize_app(storage_config)
        self.storage = self.firebase.storage()

    def insert_image(self, image_path: str, storage_path: str) -> dict:
        response = self.storage.child(storage_path).put(image_path)
        return response

    def get_url_for_image(self, storage_path: str, token: str) -> str:
        return self.storage.child(storage_path).get_url(token)

    def remove_image(self, storage_path: str, token: str) -> dict:
        return self.storage.child(storage_path).delete(storage_path, token)


class GameService:
    @staticmethod
    def get_all_games_ordered_by(order: str) -> QuerySet:
        return Game.objects.order_by(order)

    @staticmethod
    def find_most_similar_games(tags: list[str]) -> QuerySet:
        """
        Finds most similar games using provided tags
        :param tags: List with tags used in games
        :return: QuerySet with games ordered by similarity
        """
        similar_games = Game.objects.filter(tags__name__in=tags)
        similar_games = similar_games.annotate(same_tags=Count("tags")).order_by(
            "-same_tags", "-rating"
        )
        return similar_games

    @staticmethod
    def filter_games_which_contains_string(
        searched_string: str,
    ) -> Union[QuerySet, list]:
        """
        Get all games which has string in name
        :param user: User object
        :return: Queryset with games selected by user
        """
        return Game.objects.filter(name__icontains=searched_string).all()

    @staticmethod
    def filter_games_which_name_contains_tag(
        tag: str, object_list: Union[None, QuerySet] = None
    ) -> Union[QuerySet, list]:
        """
        Get all games which has string in name
        :param user: User object
        :param object_list: Optional QuerySet object on which operation will be performed
        :return: Queryset with games selected by user
        """
        if not object_list or len(object_list) == 0:
            games = Game.objects.filter(tags__name__contains=tag)
        else:
            games = object_list.filter(tags__name__contains=tag)
        return games.all()

    @staticmethod
    def get_game_by_id(id: str) -> QuerySet:
        """
        Get game using its id
        :param id: Game id
        :return: Queryset with game
        """
        try:
            game = Game.objects.get(id=id)
        except Game.DoesNotExist:
            raise Http404
        return game

    @staticmethod
    def get_ids_from_game_queryset(game_queryset: QuerySet) -> list[str]:
        """
        Return game ids from queryset
        :param game_queryset: QuerySet with games
        :return: List with game ids
        """
        return list(game_queryset.values_list("id", flat=True))

    @staticmethod
    def get_tag_names_list_from_game(game: Game) -> list[str]:
        """
        Return list with tag names used in game
        :param game: Game object
        :return: List with tag names
        """
        return [tag for tag in game.tags.values_list("name", flat=True)]


class SelectedGamesService:
    @staticmethod
    def get_user_selected_games(user: User) -> Union[QuerySet, list]:
        """
        Get all games which user has selected
        :param user: User object
        :return: Queryset with games selected by user
        """
        try:
            user_selected = SelectedGames.objects.get(user=user)
        except SelectedGames.DoesNotExist:
            return []
        return user_selected.selected_games.all()

    @staticmethod
    def get_selected_games_object_by_user(user: User) -> Union[QuerySet, list]:
        """
        Get all games which user has selected
        :param user: User object
        :return: Queryset with games selected by user
        """
        try:
            selected_games = SelectedGames.objects.get(user=user)
        except SelectedGames.DoesNotExist:
            return []
        return selected_games


class OwnedGamesService:
    @staticmethod
    def get_user_owned_games(user: User) -> Union[QuerySet, list]:
        """
        Get all games which user has own
        :param user: User object
        :return: Queryset with games owned by user
        """
        try:
            user_owned = OwnedGames.objects.get(user=user)
        except OwnedGames.DoesNotExist:
            return []
        return user_owned.owned_games.all()

    @staticmethod
    def get_owned_games_object_by_user(user: User) -> Union[QuerySet, list]:
        """
        Get all games which user has own
        :param user: User object
        :return: Queryset with games owned by user
        """
        try:
            owned_games = OwnedGames.objects.get(user=user)
        except OwnedGames.DoesNotExist:
            return []
        return owned_games


class RecommendationService:
    @staticmethod
    def get_recommended_games(id: str) -> Union[QuerySet, list]:
        """
        Get all games which was recommended
        :param id: Recommendation id
        :return: Queryset with recommended games
        """
        try:
            recommendation = Recommendation.objects.get(id=id)
        except Recommendation.DoesNotExist:
            return []
        return recommendation.recommended_games.all()

    @staticmethod
    def get_selected_games(id: str) -> Union[QuerySet, list]:
        """
        Get all games which was selected
        :param id: Recommendation id
        :return: Queryset with selected games
        """
        try:
            recommendation = Recommendation.objects.get(id=id)
        except Recommendation.DoesNotExist:
            return []
        return recommendation.selected_games.all()

    @staticmethod
    def get_opinion_created(id: str) -> bool:
        """
        Get information about whether opinion for given Recommendation was created
        :param id: Recommendation id
        :return: Boolean value whether opinion for given Recommendation was created
        """
        try:
            recommendation = Recommendation.objects.get(id=id)
        except Recommendation.DoesNotExist:
            return True
        return recommendation.opinion_created

    @staticmethod
    def get_all_recommendations(user: User) -> Union[QuerySet, list]:
        """
        Get all recommendations which was created for given user
        :param user: User object
        :return: QuerySet with recommendations
        """
        recommendations = Recommendation.objects.filter(user=user)
        return recommendations.all()

    @staticmethod
    def get_recommendation_by_id(id: str) -> Recommendation:
        """
        Get recommendation usign it's id
        :param id: Recommendation id
        :return: Recommendation object
        """
        try:
            recommendation = Recommendation.objects.get(id=id)
        except Recommendation.DoesNotExist:
            raise Http404
        return recommendation

    @staticmethod
    def create_recommendation(**kwargs) -> Recommendation:
        """
        Create recommendation with passed keywords
        :return: Recommendation object
        """
        try:
            recommendation = Recommendation.objects.create(**kwargs)
        except TypeError:
            raise Http404
        return recommendation
