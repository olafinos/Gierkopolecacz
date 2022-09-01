import pytest

from unittest.mock import patch, Mock

from gierkopolecacz.bgg_api.api_wrapper import BGGApiWrapper

class TestBGGApi:

    def __int__(self):
        self.bgg_wrapper = BGGApiWrapper()

    @patch('bgg_api.api_wrapper.requests.get')
    def test_get_games_csv_succesfull(self, mocked_get):
        mocked_response = Mock()
        mocked_get.return_value = mocked_response
        mocked_response.status_code = 200
        mocked_response.content = 'test123'


