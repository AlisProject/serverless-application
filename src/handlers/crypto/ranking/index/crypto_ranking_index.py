import requests
import json
import settings
from jsonschema import validate
from lambda_base import LambdaBase
from parameter_util import ParameterUtil


class CryptoRankingIndex(LambdaBase):
    def get_schema(self):
        return {
            'type': 'object',
            'properties': {
                'limit': settings.parameters['limit']
            }
        }

    def validate_params(self):
        ParameterUtil.cast_parameter_to_int(self.params, self.get_schema())
        validate(self.params, self.get_schema())

    def exec_main_proc(self):
        limit = int(self.params['limit']) if self.params.get('limit') else settings.CRYPTO_RAKING_DEFAULT_LIMIT
        try:
            response = requests.get(
                "https://api.coingecko.com/api/v3/coins/markets?vs_currency=jpy&order=market_cap_desc"
                f"&per_page={limit}"
                "&page=1&sparkline=false&price_change_percentage=24h"
            )
        except Exception as err:
            raise Exception(f'Something went wrong when call CoinGecko API: {err}')

        return {
            'statusCode': 200,
            'body': json.dumps(self.extract_crypto_info(json.loads(response.text)))
        }

    # 利用する項目のみを抽出
    @staticmethod
    def extract_crypto_info(json_array):
        return [
            {
                'symbol': crypto_info['symbol'],
                'name': crypto_info['name'],
                'image': crypto_info['image'],
                'current_price': crypto_info['current_price'],
                'market_cap': crypto_info['market_cap'],
                'price_change_percentage_24h': crypto_info['price_change_percentage_24h']
            }
            for crypto_info in json_array
        ]
