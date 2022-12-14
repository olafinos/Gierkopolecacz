from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.db.models import QuerySet
from django.http import JsonResponse, HttpRequest
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils.datastructures import MultiValueDictKeyError
from django.views import generic

from gierkopolecacz.settings import MEDIA_ROOT
from polecacz.bgg_api import CATEGORIES_MAP, MECHANICS_MAP
from polecacz.forms import OpinionForm
from polecacz.models import Game, Opinion, SelectedGames, Recommendation, OwnedGames, ImageMetadata
from polecacz.service import SelectedGamesService, RecommendationService, GameService, OwnedGamesService, \
    FirebaseStorageService, ImageMetadataService
from polecacz.validators import validate_file_extension, validate_file_size, TooBigFileException

ORDER_MAPPING = {
    "rank": "Ranking rosnąco",
    "-rank": "Ranking malejąco",
    "name": "Alfabetycznie A-Z",
    "-name": "Alfabetycznie Z-A",
    "rating": "Średnia ocen rosnąco",
    "-rating": "Średnia ocen malejąco",
}


class IndexView(generic.ListView):
    """
    Main view, which greets the user.
    """

    template_name = "polecacz/index.html"
    context_object_name = "top_games"

    def get_queryset(self):
        """
        Return the list of items for this view.
        """
        return GameService.get_all_games_ordered_by("rank")[:12]


class GameDetailView(LoginRequiredMixin, generic.DetailView):
    """
    View responsible for retrieving Game details. Requires to be logged in
    """

    model = Game
    template_name = "polecacz/game_detail.html"
    login_url = "/login/"

    def get_context_data(self, **kwargs):
        """
        Get the context for this view.
        """
        firebase_storage = FirebaseStorageService()
        context = super(GameDetailView, self).get_context_data(**kwargs)
        user = self.request.user
        game = GameService.get_game_by_id(self.kwargs["pk"])
        user_images = ImageMetadataService.get_image_metadata_objects_for_user_and_game(user=user, game_id=game.id)
        urls_to_user_images = [(firebase_storage.get_url_for_image(storage_path=f"images/{game.id}/{user.username}/{user_image.image_name}",
                                                                   token=user_image.download_token), user_image) for user_image in user_images]
        game_images = ImageMetadataService.get_game_images_with_tokens(game_id=game.id)
        urls_to_game_images = [firebase_storage.get_url_for_image(storage_path=f"images/{game.id}/{user.username}/{game_image[0]}",
                                                                  token=game_image[1]) for game_image in game_images]
        try:
            context['urls_to_user_images'] = urls_to_user_images
            context['urls_to_game_images'] = urls_to_game_images
            context["selected_game"] = game in SelectedGamesService.get_user_selected_games(user=user)
            context["owned_game"] = game in OwnedGamesService.get_user_owned_games(user=user)
        except SelectedGames.DoesNotExist:
            context["selected_game"] = False
        except OwnedGames.DoesNotExist:
            context["owned_game"] = False
        return context


class AddImageView(LoginRequiredMixin, generic.View):

    def post(self, request, *args, **kwargs):
        firebase_service = FirebaseStorageService()
        try:
            file = request.FILES['uploaded_file']
            validate_file_extension(file.name)
            validate_file_size(file.size)
            file_save = default_storage.save(file.name, file)
            path_to_file = f"{MEDIA_ROOT}/{file.name}"
            path_on_storage = f'images/{self.kwargs["game_id"]}/{self.request.user.username}/{file.name}'
            response = firebase_service.insert_image(path_to_file, path_on_storage)
            image_metadata = ImageMetadata.objects.update_or_create(user=self.request.user,
                                                                    game_id=self.kwargs['game_id'],
                                                                    image_name=file.name,
                                                                    defaults={'download_token': response['downloadTokens']})
            image_metadata[0].save()
            messages.success(request, "Zdjęcie zostało zapisane")
            delete = default_storage.delete(file.name)
        except TooBigFileException as e:
            messages.error(request, "Za duży rozmiar pliku. Maksymalna akceptowalna wartość to 6MB")
        except ValidationError as e:
            messages.error(request, "Niepoprawny typ pliku. Akceptowalne typy to: .jpg oraz .png")
        except Exception as e:
            messages.error(request, "Nastąpił błąd w trakcie dodawania zdjęcia")
        return redirect("polecacz:game_detail", self.kwargs["game_id"])


class RemoveImageView(LoginRequiredMixin, generic.View):

    def get(self, request, *args, **kwargs):
        firebase_service = FirebaseStorageService()
        image_name = request.GET.get('image_name', '')
        try:
            token = ImageMetadataService.get_token(user=request.user, game_id=self.kwargs["game_id"], image_name=image_name)
            path_on_storage = f'images/{self.kwargs["game_id"]}/{self.request.user.username}/{image_name}'
            firebase_service.remove_image(path_on_storage, token)
            image_metadata = ImageMetadataService.get_image_metadata_object(user=request.user, game_id=self.kwargs["game_id"], image_name=image_name)
            image_metadata.delete()
            messages.success(request, "Zdjęcie zostało usunięte")
        except Exception as e:
            messages.error(request, "Zdjęcie nie zostało usunięte")
        return redirect("polecacz:game_detail", self.kwargs["game_id"])


class GameListView(LoginRequiredMixin, generic.ListView):
    """
    View responsible for retrieving Game list. Allows to change by user ordering and filtering. Also allows to use
    search bar.
    """

    model = Game
    template_name = "polecacz/game_list.html"
    login_url = "/login/"
    context_object_name = "games_list"
    paginate_by = 10
    ordering = ["rank"]
    order_mapping = ORDER_MAPPING
    categories = list(CATEGORIES_MAP.values())
    mechanics = list(MECHANICS_MAP.values())

    def get_ordering(self):
        """
        Return the field or fields to use for ordering the queryset.
        """
        ordering = self.request.GET.get("ordering", "rank")
        return ordering

    def get_context_data(self, **kwargs):
        """
        Get the context for this view.
        """
        context = super(GameListView, self).get_context_data(**kwargs)
        context = self._prepare_context(context)
        return context

    def _prepare_context(self, context: dict) -> dict:
        """Retrives user information about ordering, selected games, searched game, selected categories and mechanics
        from request and set it to context dictionary
        :param context: Dictionary with response context
        """
        order_name, ordering = self._get_ordering_options()
        context["selected_games"] = SelectedGamesService().get_user_selected_games(
            self.request.user
        )
        context["owned_games"] = OwnedGamesService.get_user_owned_games(self.request.user)
        context["ordering"] = ordering
        context["order_name"] = order_name
        context["mechanics"] = self.mechanics
        context["categories"] = self.categories
        context["selected_categories"] = self.request.GET.getlist(
            "selected_categories", []
        )
        context["selected_mechanics"] = self.request.GET.getlist(
            "selected_mechanics", []
        )
        context["game_name"] = self.request.GET.get("game_name", "")
        return context

    def _get_ordering_options(self) -> tuple[str, str]:
        """
        Retrieves information about used ordering
        """
        ordering = self.request.GET.get("ordering", "rank")
        order_name = self.order_mapping[ordering]
        return order_name, ordering

    def get_queryset(self):
        """
        Return the list of items for this view.
        """
        game = self.request.GET.get("game_name", "")
        tags = self.request.GET.getlist("selected_categories", [])
        tags.extend(self.request.GET.getlist("selected_mechanics", []))
        if game or tags:
            object_list = GameService.filter_games_which_contains_string(game)
            for tag in tags:
                object_list = GameService.filter_games_which_name_contains_tag(
                    tag, object_list
                )
            return object_list.order_by(self.request.GET.get("ordering", "rank"))
        else:
            return super(GameListView, self).get_queryset()


class SelectedGamesListView(LoginRequiredMixin, generic.ListView):
    """
    View responsible for retrieving SelectedGames list
    """

    model = SelectedGames
    template_name = "polecacz/selected_games.html"
    login_url = "/login/"
    context_object_name = "games_list"

    def get_queryset(self):
        """
        Return the list of items for this view.
        """
        selected_games_object, _ = SelectedGames.objects.get_or_create(
            user=self.request.user
        )
        return SelectedGamesService.get_user_selected_games(self.request.user)


class OwnedGamesListView(LoginRequiredMixin, generic.ListView):
    """
    View responsible for retrieving OwnedGames list
    """

    model = OwnedGames
    template_name = "polecacz/owned_games.html"
    login_url = "/login/"
    context_object_name = "games_list"

    def get_queryset(self):
        """
        Return the list of items for this view.
        """
        selected_games_object, _ = OwnedGames.objects.get_or_create(
            user=self.request.user
        )
        return OwnedGamesService.get_user_owned_games(self.request.user)


class RecommendationDetailView(LoginRequiredMixin, generic.DetailView):
    """
    View responsible for retrieving Recommendation details
    """

    model = Recommendation
    template_name = "polecacz/recommendation_detail.html"
    login_url = "/login/"
    context_object_name = "games"

    def get_context_data(self, **kwargs):
        """
        Get the context for this view.
        """
        context = super(RecommendationDetailView, self).get_context_data(**kwargs)
        id = self.kwargs["pk"]
        context["recommended_games"] = RecommendationService().get_recommended_games(id)
        context["selected_games"] = RecommendationService().get_selected_games(id)[:4]
        context["opinion_created"] = RecommendationService().get_opinion_created(id)
        context["id"] = id
        return context


class RecommendationListView(LoginRequiredMixin, generic.ListView):
    """
    View responsible for retrieving Recommendation list
    """

    model = Recommendation
    template_name = "polecacz/recommendation_list.html"
    login_url = "/login/"
    context_object_name = "recommendations"
    paginate_by = 20

    def get_queryset(self):
        """
        Return the list of items for this view.
        """
        recommendation_objects = RecommendationService.get_all_recommendations(
            self.request.user
        )
        return recommendation_objects.order_by('-creation_date')


class OpinionFormView(LoginRequiredMixin, SuccessMessageMixin, generic.FormView):
    """
    View responsible for Opinion form processing
    """

    model = Opinion
    template_name = "polecacz/create_opinion.html"
    context_object_name = "context"
    form_class = OpinionForm
    success_url = "/polecacz/recommendation_list"
    success_message = "Dziękujemy za zostawienie opinii."

    def get_context_data(self, **kwargs):
        """
        Get the context for this view.
        """
        context = super(OpinionFormView, self).get_context_data(**kwargs)
        recommendation = RecommendationService().get_recommendation_by_id(
            id=self.kwargs["pk"]
        )
        context["id"] = recommendation.id
        return context


class AddOpinionView(LoginRequiredMixin, generic.View):

    name_map = {"Description": "Uwagi do rekomendacji", "Rating": "Ocena"}

    def post(self, request: HttpRequest, pk: str):
        """
        Function responsible for adding opinion. Accepts only POST requests
        :param request: Incoming HttpRequest with all data
        :param pk: Recommendation id
        """
        form = OpinionForm(request.POST)
        if form.is_valid():
            recommendation = RecommendationService.get_recommendation_by_id(id=pk)
            opinion = form.save(commit=False)
            opinion.recommendation = recommendation
            opinion.user = request.user
            opinion.save()
            recommendation.opinion_created = True
            recommendation.save()
            return redirect("polecacz:recommendation_list")
        else:
            return render(
                request=request,
                template_name="./polecacz/create_opinion.html",
                context={"form": form, "id": pk, "name_map": self.name_map},
            )

    def get(self, request: HttpRequest, pk: str):
        form = OpinionForm()
        return render(
            request=request,
            template_name="./polecacz/create_opinion.html",
            context={"form": form, "id": pk, "name_map": self.name_map},
        )


class GameSearchView(LoginRequiredMixin, generic.View):

    def get(self, request: HttpRequest, *args, **kwargs) -> JsonResponse:
        """
        Method responsible for autocompletion feature in searchbar
        :param request: Incoming HttpRequest with all data
        """
        game = request.GET.get("game_name")
        payload = []
        if game:
            games_objs = GameService.filter_games_which_contains_string(
                searched_string=game
            )[:10]

            for game_obj in games_objs:
                payload.append(game_obj.name)

        return JsonResponse({"status": 200, "data": payload})


def _build_url_with_pagination_and_order(url: str, request: HttpRequest) -> str:
    """
    Builds url with all attributes like pagination, ordering, searched games,
    selected categories and selected mechanics
    :param url: Base URL
    :param request: Incoming HttpRequest with all data
    :return: URL with included all attributes
    """
    url = url + "?"
    (
        game,
        ordering,
        page,
        selected_categories,
        selected_mechanics,
    ) = _retrieve_attributes_from_request(request)

    if ordering:
        url += f"&ordering={ordering}"
    if page:
        url += f"&page={page}"
    if game:
        url += f"&game_name={game}"
    if selected_categories:
        for category in selected_categories:
            url += f"&selected_categories={category}"
    if selected_mechanics:
        for mechanics in selected_mechanics:
            url += f"&selected_mechanics={mechanics}"
    return url


def _retrieve_attributes_from_request(
    request: HttpRequest,
) -> tuple[str, str, str, list, list]:
    """
    Retrieves information about pagination, ordering, searched games,
    selected categories and selected mechanics
    :param request: Incoming HttpRequest with all data
    """
    ordering = request.GET.get("ordering", "")
    page = request.GET.get("page", "")
    game = request.GET.get("game_name", "")
    selected_categories = request.GET.getlist("selected_categories", [])
    selected_mechanics = request.GET.getlist("selected_mechanics", [])
    return game, ordering, page, selected_categories, selected_mechanics


class AddGameToSelectedGamesView(LoginRequiredMixin, generic.View):

    def get(self, request: HttpRequest, game_id: str, *args, **kwargs):
        """
        Adds game to user selected games
        :param request: Incoming HttpRequest with all data
        :param game_id: Game id
        """
        game = GameService.get_game_by_id(id=game_id)
        selected_games_object, _ = SelectedGames.objects.get_or_create(
            user=request.user
        )
        selected_games_object.selected_games.add(game)
        selected_games_object.save()

        if request.GET.get("redirect") == "game_detail":
            return redirect("polecacz:game_detail", game_id)

        return redirect(
            _build_url_with_pagination_and_order(
                reverse_lazy("polecacz:game_list"), request
            )
        )


class AddGameToOwnedGamesView(LoginRequiredMixin, generic.View):

    def get(self, request: HttpRequest, game_id: str, *args, **kwargs):
        """
        Adds game to user owned games
        :param request: Incoming HttpRequest with all data
        :param game_id: Game id
        """
        game = GameService.get_game_by_id(id=game_id)
        owned_games_object, _ = OwnedGames.objects.get_or_create(
            user=request.user
        )
        owned_games_object.owned_games.add(game)
        owned_games_object.save()

        if request.GET.get("redirect") == "game_detail":
            return redirect("polecacz:game_detail", game_id)

        return redirect(
            _build_url_with_pagination_and_order(
                reverse_lazy("polecacz:game_list"), request
            )
        )


class RemoveFromOwnedGamesView(LoginRequiredMixin, generic.View):

    def get(self, request: HttpRequest, game_id: str):
        """
        Removes game from user owned games
        :param request: Incoming HttpRequest with all data
        :param game_id: Game id
        """
        game = GameService.get_game_by_id(id=game_id)
        owned_games_object, _ = OwnedGames.objects.get_or_create(
            user=request.user
        )
        owned_games_object.owned_games.remove(game)
        owned_games_object.save()

        if request.GET.get("redirect") == "owned_games":
            return redirect("polecacz:owned_games")

        if request.GET.get("redirect") == "game_detail":
            return redirect("polecacz:game_detail", game_id)

        return redirect(
            _build_url_with_pagination_and_order(
                reverse_lazy("polecacz:game_list"), request
            )
        )


class RemoveFromSelectedGamesView(LoginRequiredMixin, generic.View):

    def get(self, request: HttpRequest, game_id: str):
        """
        Removes game from user selected games
        :param request: Incoming HttpRequest with all data
        :param game_id: Game id
        """
        game = GameService.get_game_by_id(id=game_id)
        selected_games_object, _ = SelectedGames.objects.get_or_create(
            user=request.user
        )
        selected_games_object.selected_games.remove(game)
        selected_games_object.save()

        if request.GET.get("redirect") == "selected_games":
            return redirect("polecacz:selected_games")

        if request.GET.get("redirect") == "game_detail":
            return redirect("polecacz:game_detail", game_id)

        return redirect(
            _build_url_with_pagination_and_order(
                reverse_lazy("polecacz:game_list"), request
            )
        )


class CreateRecommendationView(LoginRequiredMixin, generic.View):
    def post(self, request: HttpRequest):
        """
        Creates Recommendation object based on user selected games
        :param request: Incoming HttpRequest with all data
        """
        selected_games_obj = SelectedGamesService.get_selected_games_object_by_user(
            user=request.user
        )
        games = selected_games_obj.selected_games.all()
        if not games:
            return redirect("polecacz:selected_games")
        owned_games_obj = OwnedGamesService.get_owned_games_object_by_user(user=request.user)
        if owned_games_obj:
            owned_games = owned_games_obj.owned_games.all()
            owned_games_ids = GameService.get_ids_from_game_queryset(owned_games) if owned_games else []
        else:
            owned_games_ids = []

        recommendation_object = RecommendationService.create_recommendation(
            user=request.user
        )
        games_ids = GameService.get_ids_from_game_queryset(games)
        tag_list = []
        for game in games:
            recommendation_object.selected_games.add(game)
            tag_list.extend(GameService.get_tag_names_list_from_game(game))

        recommended_games_query = self._create_recommendation_using_tags(games_ids, tag_list, owned_games_ids)
        for game in recommended_games_query[:10]:
            recommendation_object.recommended_games.add(game)
        recommendation_object.save()
        selected_games_obj.selected_games.clear()
        selected_games_obj.save()
        return redirect("polecacz:recommendation_detail", recommendation_object.id)

    def _create_recommendation_using_tags(self,
        used_games_ids: list[str], tag_list: list[str], owned_games_ids: list[str]
    ) -> QuerySet:
        """
        Returns games in which were used similar mechanics and game categories
        :param used_games_ids: List with game ids which were used to create recommendations
        :param tag_list: List with tags used in games which were used to create recommendations
        :return: QuerySet with games in which were used similar mechanics and game categories
        """
        recommended_games_query = GameService.find_most_similar_games(list(set(tag_list)))
        recommended_games_query = recommended_games_query.exclude(id__in=used_games_ids+owned_games_ids)
        return recommended_games_query
