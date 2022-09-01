import datetime
import csv
import time
from typing import Union

import requests
from bs4 import BeautifulSoup

from bgg_api import MECHANICS_MAP,CATEGORIES_MAP



class BGGApiWrapper:

    def __init__(self):
        self.api_url = 'https://boardgamegeek.com/xmlapi2/'
        self.bgg_games_url = 'https://raw.githubusercontent.com/beefsack/bgg-ranking-historicals/master/'

    def import_data_to_database(self, number_of_games: int = None):
        result = []
        games_with_errors = []
        counter = 1
        dump_filename = self._get_games_csv()

        if not dump_filename:
            return

        games_info = BGGApiWrapper._get_games_info_from_csv_file(dump_filename)

        if number_of_games:
            games_info = games_info[:number_of_games]
        for game in games_info:
            print(f'Processing game number: {counter}')
            counter += 1
            extended_info = self._get_game_information_using_id(game['id'])

            if 'error' in extended_info.keys():
                games_with_errors.append({**game, **extended_info})
            else:
                result.append({**game, **extended_info})

        result = BGGApiWrapper._map_fields_to_polish_equivalent(result)
        return result, games_with_errors

    def _get_games_csv(self) -> Union[str, None]:
        """
        Get csv file with BGG games dump
        :return: list with game ids from BoardGameGeek page
        """
        number_of_retries = 0
        current_date = datetime.datetime.now()
        while number_of_retries < 3:
            dump_name = str(current_date.date())+'.csv'
            response = requests.get(self.bgg_games_url+dump_name)
            if response.status_code == 200:
                dump_filename = f'dump-{dump_name}'
                with open(dump_filename, 'wb') as file:
                    file.write(response.content)
                return dump_filename
            else:
                current_date = current_date - datetime.timedelta(days=1)
                number_of_retries += 1
                time.sleep(0.5)
        print("There was an error while downloading dump")

    @staticmethod
    def _get_games_info_from_csv_file(dump_filename: str) -> list[dict[str, str]]:
        """
        Retrieve game ids and their names from csv file
        :param dump_filename: csv filename
        :return: list with dictionaries containing name and id
        """
        result = []
        with open(dump_filename, newline='\n', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            for row in reader:
                result.append(
                    {'id': row[0], 'rank': row[3], 'average': row[5], 'thumbnail': row[8]})
        return result[1:]

    def _get_game_information_using_id(self, game_id: str) -> dict:
        """
        Retrieve information about game using its ID
        :param game_id: Game ID
        :return: Dictionary with game information
        """

        def _get_tag_value(tag_name: str, soup: BeautifulSoup,  **kwargs) -> str:
            """
            Get tag value from XML object
            :return: XML tag value
            """
            tag = soup.items.item.find(tag_name, kwargs)
            return tag.get('value')

        def _get_tag_list_values(tag_name: str, soup: BeautifulSoup, **kwargs) -> list[str]:
            """
            Get list with tag values from XML object
            :return: XML tag value
            """
            tags = soup.items.item.find_all(tag_name, kwargs)
            return [tag.get('value') for tag in tags]

        def _process_game_info(game_info: str) -> dict:
            """
            Processes xml object with game info into form of dictionary
            :param game_info: XML object with game info
            :return: Dictionary with game info
            """
            result = {}
            soup = BeautifulSoup(game_info, features='xml')
            result['game_name'] = _get_tag_value(tag_name="name", soup=soup, **{"type": "primary"})
            result['year_published'] = _get_tag_value(tag_name="yearpublished", soup=soup)
            result['min_players'] = _get_tag_value(tag_name="minplayers", soup=soup)
            result['max_players'] = _get_tag_value(tag_name="maxplayers", soup=soup)
            result['playing_time'] = _get_tag_value(tag_name="playingtime", soup=soup)
            result['alternate_name'] = _get_tag_list_values(tag_name='name', soup=soup, **{"type": "alternate"})
            result['categories'] = _get_tag_list_values(tag_name='link', soup=soup, **{"type": "boardgamecategory"})
            result['mechanics'] = _get_tag_list_values(tag_name='link', soup=soup, **{"type": "boardgamemechanic"})
            return result

        game_info = self._request_game_info_using_api(game_id)
        print(game_info)
        if isinstance(game_info, dict):
            return game_info
        processed_game_info = _process_game_info(game_info)
        return processed_game_info

    def _request_game_info_using_api(self, game_id: str) -> Union[str, dict]:
        """
        Requests information about game using XMLAPI2. If game information was returned succesfully returns XML in
        string form, if not returns dictionary with game id and response content
        :param game_id: Game ID
        :return: XML with game info if request was accepted or dicitonary with game id and response content.
        """
        request_url = self.api_url + f'thing?id={game_id}'
        try:
            number_of_retries = 0
            response = requests.get(request_url)
            while response.status_code != 200:
                time.sleep(0.5)
                number_of_retries += 1
                response = requests.get(request_url)
                if number_of_retries >= 3 and response.status_code != 200:
                    raise requests.exceptions.ConnectionError
            return response.text
        except requests.exceptions.ConnectionError:
            print(f"There was an error with retriving information about game with id: {game_id}")
            return {'game_id': game_id, 'error': response.content}

    @staticmethod
    def _map_fields_to_polish_equivalent(result: list[dict]) -> list[dict]:
        """
        Maps english name of categories and mechanics to polish equivalent using predefined map
        :param result: List with games in dictionary form
        :return: List with games, which mechanics and categories fields are mapped to polish equivalent.
        """
        for game in result:
            game['mechanics'] = [MECHANICS_MAP.get(mechanic, '') for mechanic in game['mechanics']]
            while '' in game['mechanics']:
                game['mechanics'].remove('')
            game['categories'] = [CATEGORIES_MAP.get(category, '') for category in game['categories']]
            while '' in game['categories']:
                game['categories'].remove('')
        return result
