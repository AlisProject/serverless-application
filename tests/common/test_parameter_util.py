from unittest import TestCase
from parameter_util import ParameterUtil


class TestParameterToInt(TestCase):
    def test_cast_parameter_to_int(self):
        schema = {
            'properties': {
                'limit': {'type': 'integer'},
                'article_id': {'type': 'string'},
                'sort_key': {'type': 'integer'}
            }
        }

        params = {
            'limit': '100',
            'article_id': '150',
            'sort_key': 'ALIS',
            'other_key': '150'
        }

        ParameterUtil.cast_parameter_to_int(params, schema)

        expected_params = {
            'limit': 100,
            'article_id': '150',
            'sort_key': 'ALIS',
            'other_key': '150'
        }

        self.assertEqual(params, expected_params)
