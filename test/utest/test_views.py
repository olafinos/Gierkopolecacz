from django.test import TestCase
from  django.test.client import RequestFactory
from polecacz.views import _retrieve_attributes_from_request, _build_url_with_pagination_and_order



class TestPolecaczViews(TestCase):

    def test_retrieve_attributes_from_request(self):
        factory = RequestFactory()
        request = factory.get('/some_path/?ordering=rank&page=1&game_name=name&selected_categories=abc&selected_mechanics=ef')
        game, ordering, page, selected_categories, selected_mechanics = _retrieve_attributes_from_request(request)
        self.assertEqual(game, 'name')
        self.assertEqual(ordering, 'rank')
        self.assertEqual(page, '1')
        self.assertEqual(selected_categories, ['abc'])
        self.assertEqual(selected_mechanics, ['ef'])


    def test_build_url_with_pagination_and_order(self):
        factory = RequestFactory()
        request = factory.get(
            '/some_path/?ordering=rank&page=1&game_name=name&selected_categories=abc&selected_mechanics=ef')
        url = 'some_other_path'
        self.assertEqual(_build_url_with_pagination_and_order(url, request),
                         'some_other_path?&ordering=rank&page=1&game_name=name&selected_categories=abc&selected_categories=ef')