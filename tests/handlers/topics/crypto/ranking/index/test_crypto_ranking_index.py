from unittest import TestCase
from unittest.mock import patch, MagicMock
from topics_crypto_ranking_index import TopicsCryptoRankingIndex

import requests
import responses
import json
import settings


class TestTopicsCryptoRankingIndex(TestCase):
    def assert_bad_request(self, params):
        function = TopicsCryptoRankingIndex(params, {})
        response = function.main()

        self.assertEqual(response['statusCode'], 400)

    @responses.activate
    def test_main_ok(self):
        test_desc = [
          {
            "id": "bitcoin",
            "symbol": "btc",
            "name": "Bitcoin",
            "image": "https://assets.coingecko.com/coins/images/1/large/bitcoin.png?1547033579",
            "current_price": 5931175,
            "market_cap": 110482945958109,
            "market_cap_rank": 1,
            "fully_diluted_valuation": 124115855126296,
            "total_volume": 5247451090387,
            "high_24h": 6062537,
            "low_24h": 5884134,
            "price_change_24h": -294.1148347,
            "price_change_percentage_24h": -0.00496,
            "market_cap_change_24h": -214713277132.76562,
            "market_cap_change_percentage_24h": -0.19396,
            "circulating_supply": 18693356,
            "total_supply": 21000000,
            "max_supply": 21000000,
            "ath": 7058952,
            "ath_change_percentage": -16.40148,
            "ath_date": "2021-04-14T11:54:46.763Z",
            "atl": 6641.83,
            "atl_change_percentage": 88748.66169,
            "atl_date": "2013-07-05T00:00:00.000Z",
            "roi": None,
            "last_updated": "2021-04-28T07:13:46.139Z",
            "price_change_percentage_24h_in_currency": -0.004958549480891654
          },
          {
            "id": "ethereum",
            "symbol": "eth",
            "name": "Ethereum",
            "image": "https://assets.coingecko.com/coins/images/279/large/ethereum.png?1595348880",
            "current_price": 283867,
            "market_cap": 32749883550536,
            "market_cap_rank": 2,
            "fully_diluted_valuation": None,
            "total_volume": 4145441249110,
            "high_24h": 295016,
            "low_24h": 274914,
            "price_change_24h": 6090.14,
            "price_change_percentage_24h": 2.19245,
            "market_cap_change_24h": 680330753525,
            "market_cap_change_percentage_24h": 2.12142,
            "circulating_supply": 115651156.5615,
            "total_supply": None,
            "max_supply": None,
            "ath": 295016,
            "ath_change_percentage": -4.44847,
            "ath_date": "2021-04-28T01:58:15.864Z",
            "atl": 51.85,
            "atl_change_percentage": 543618.50987,
            "atl_date": "2015-10-20T00:00:00.000Z",
            "roi": {
              "times": 63.102283755994826,
              "currency": "btc",
              "percentage": 6310.228375599482
            },
            "last_updated": "2021-04-28T07:13:22.846Z",
            "price_change_percentage_24h_in_currency": 2.1924546377374696
          }]

        responses.add(responses.GET,
                      "https://api.coingecko.com/api/v3/coins/markets?vs_currency=jpy&order=market_cap_desc"
                      "&per_page=3"
                      "&page=1&sparkline=false&price_change_percentage=24h",
                      json=test_desc,
                      status=200)

        expected_json = [
            {
                'symbol': test_desc[0]['symbol'],
                'name': test_desc[0]['name'],
                'image': test_desc[0]['image'],
                'current_price': test_desc[0]['current_price'],
                'market_cap': test_desc[0]['market_cap'],
                'price_change_percentage_24h': test_desc[0]['price_change_percentage_24h']
            },
            {
                'symbol': test_desc[1]['symbol'],
                'name': test_desc[1]['name'],
                'image': test_desc[1]['image'],
                'current_price': test_desc[1]['current_price'],
                'market_cap': test_desc[1]['market_cap'],
                'price_change_percentage_24h': test_desc[1]['price_change_percentage_24h']
            },
        ]

        response = TopicsCryptoRankingIndex({}, {}).main()
        self.assertEqual(200, response['statusCode'])
        self.assertEqual(json.dumps(expected_json), response['body'])

    def test_main_ok_call_default_limit(self):
        magic_mock = MagicMock()
        with patch('topics_crypto_ranking_index.requests', magic_mock):
            TopicsCryptoRankingIndex({}, {}).main()
            args, _ = magic_mock.get.call_args
            self.assertTrue(magic_mock.get.called)
            self.assertEqual(args[0],
                             "https://api.coingecko.com/api/v3/coins/markets?vs_currency=jpy&order=market_cap_desc"
                             f"&per_page={settings.CRYPTO_RAKING_DEFAULT_LIMIT}"
                             "&page=1&sparkline=false&price_change_percentage=24h")

    def test_main_ok_call_specified_limit(self):
        params = {
            'queryStringParameters': {
                'limit': '100'
            }
        }
        magic_mock = MagicMock()
        with patch('topics_crypto_ranking_index.requests', magic_mock):
            TopicsCryptoRankingIndex(params, {}).main()
            args, _ = magic_mock.get.call_args
            self.assertTrue(magic_mock.get.called)
            self.assertEqual(args[0],
                             "https://api.coingecko.com/api/v3/coins/markets?vs_currency=jpy&order=market_cap_desc"
                             "&per_page=100"
                             "&page=1&sparkline=false&price_change_percentage=24h")

    def test_validation_limit_max(self):
        params = {
            'queryStringParameters': {
                'limit': '101'
            }
        }

        self.assert_bad_request(params)

    def test_validation_limit_min(self):
        params = {
            'queryStringParameters': {
                'limit': '0'
            }
        }

        self.assert_bad_request(params)

    @patch('requests.get', MagicMock(side_effect=requests.exceptions.RequestException()))
    def test_main_with_exception(self):
        response = TopicsCryptoRankingIndex({}, {}).main()
        self.assertEqual(500, response['statusCode'])
