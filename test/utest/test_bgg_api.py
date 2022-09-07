import datetime

from unittest.mock import patch, Mock, mock_open

from django.test import TestCase

from polecacz.bgg_api.api_wrapper import BGGApiWrapper

BGG_WRAPPER = BGGApiWrapper()


class BggApiTests(TestCase):
    @patch('polecacz.bgg_api.api_wrapper.requests.get')
    def test_get_games_csv_successfully(self,mocked_get):
        mocked_response = Mock()
        mocked_get.return_value = mocked_response
        mocked_response.status_code = 200
        mocked_response.content = b'test123'
        with patch('builtins.open', mock_open()) as mocked_open:
            BGG_WRAPPER._get_games_csv()

        mocked_open.assert_called_once_with(f'dump-{datetime.datetime.now().date()}.csv', 'wb')
        writer = mocked_open()
        writer.write.assert_called_once_with(b'test123')

    @patch('polecacz.bgg_api.api_wrapper.requests.get')
    def test_get_games_csv_unsuccessfully(self,mocked_get):
        mocked_response = Mock()
        mocked_get.return_value = mocked_response
        mocked_response.status_code = 404
        BGG_WRAPPER._get_games_csv()
        with patch('builtins.open', mock_open()) as mocked_open:
            BGG_WRAPPER._get_games_csv()

        assert not mocked_open.called
        writer = mocked_open()
        assert not writer.write.called

    def test_get_games_info_from_csv_file(self):
        path = 'test/utest/game_info.csv'
        info = BGG_WRAPPER._get_games_info_from_csv_file(path)
        assert len(info) == 2
        assert info[0]['id'] == '1'
        assert info[0]['rank'] == '1'
        assert info[0]['average'] == '8.475'
        assert info[0]['thumbnail'] == 'https://url1.jpg'

    @patch('polecacz.bgg_api.api_wrapper.requests.get')
    def test_get_game_information_using_id(self,mocked_get):
        mocked_response = Mock()
        mocked_get.return_value = mocked_response
        mocked_response.status_code = 200
        mocked_response.text = """  <?xml version="1.0" encoding="utf-8"?>
                                    <items>
                                    <item type="boardgame" id="1">
                                    <thumbnail>https://url.jpg</thumbnail>				
                                    <name type="primary" sortindex="1" value="Game1" />
                                    <name type="alternate" sortindex="1" value="Gra1" />
                                    <yearpublished value="2021" />
                                    <minplayers value="1" />
                                    <maxplayers value="4" />
                                    <playingtime value="120" />
                                    <minplaytime value="60" />
                                    <maxplaytime value="120" />
                                    <minage value="14" />							
                                    <link type="boardgamecategory" id="1022" value="Adventure" />
                                    <link type="boardgamecategory" id="1020" value="Exploration" />
                                    <link type="boardgamecategory" id="1010" value="Fantasy" />
                                    <link type="boardgamecategory" id="1046" value="Fighting" />
                                    <link type="boardgamecategory" id="1047" value="Miniatures" />
                                    <link type="boardgamemechanic" id="2689" value="Action Queue" />
                                    <link type="boardgamemechanic" id="2839" value="Action Retrieval" />
                                    <link type="boardgameartist" id="2839" value="artist" />
                                    <link type="boardgamedesigner" id="2839" value="designer" />
                                    </item>
                                    </items>"""
        game_info = BGG_WRAPPER._get_game_information_using_id(1)
        assert game_info['game_name'] == 'Game1'
        assert game_info['year_published'] == '2021'
        assert game_info['min_players'] == '1'
        assert game_info['max_players'] == '4'
        assert game_info['playing_time'] == '120'
        assert game_info['alternate_name'] == ['Gra1']
        assert game_info['categories'] == ['Adventure', 'Exploration', 'Fantasy', 'Fighting', 'Miniatures']
        assert game_info['mechanics'] == ['Action Queue', 'Action Retrieval']
        assert game_info['designer'] == 'designer'
        assert game_info['artist'] == 'artist'

    def test_map_fields_to_polish_equivalent(self):
        game_info = [{'mechanics': [], 'categories': []},
                      {'mechanics': ['Hand Management', 'Cooperative Game'], 'categories': ['Adventure', 'Exploration', 'Fantasy', 'Fighting', 'Miniatures']},
                      {'mechanics': ['NEW MECHANIC'], 'categories': ['Zombies']},
                      {'mechanics': ['Contracts'], 'categories': ['NEW CATEGORY']}]
        game_info = BGG_WRAPPER._map_fields_to_polish_equivalent(game_info)
        assert game_info == [{'mechanics': [], 'categories': []},
                             {'mechanics': ['Zarządzanie ręką', 'Współpraca'],
                              'categories': ['Przygodowa', 'Eksploracyjna', 'Fantasy', 'Bijatyka', 'Miniaturkowa']},
                             {'mechanics': [], 'categories': ['Zombie']},
                             {'mechanics': ['Kontrakty'], 'categories': []}]
