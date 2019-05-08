from unittest import TestCase

from jsonschema import ValidationError
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

    def test_validate_array_unique_ok(self):
        target_items = ["FOO", "BAR", "foo"]

        try:
            ParameterUtil.validate_array_unique(target_items, 'tags')
        except ValidationError:
            self.fail('expected no error is raised')

    def test_validate_array_unique_ok_with_case_insensitive(self):
        target_items = ["FOO", "BAR", "BAZ"]

        try:
            ParameterUtil.validate_array_unique(target_items, 'tags', case_insensitive=True)
        except ValidationError:
            self.fail('expected no error is raised')

    def test_validate_array_unique_with_not_unique(self):
        target_items = ["FOO", "BAR", "FOO"]

        with self.assertRaises(ValidationError):
            ParameterUtil.validate_array_unique(target_items, 'tags')

    def test_validate_array_unique_with_not_unique_case_insensitive(self):
        target_items = ["FOO", "BAR", "foo"]

        with self.assertRaises(ValidationError):
            ParameterUtil.validate_array_unique(target_items, 'tags', case_insensitive=True)

    def test_validate_price_params_ng_string(self):
        price = 'AAAA'
        with self.assertRaises(ValidationError):
            ParameterUtil.validate_price_params(price)

    def test_validate_price_params_ng_decimal(self):
        price = 1 * (10 ** 18) + 1 * (10 ** 17)
        with self.assertRaises(ValidationError):
            ParameterUtil.validate_price_params(price)

    def test_validate_price_through(self):
        price = 1 * (10 ** 18)
        self.assertTrue(ParameterUtil.validate_price_params(price))
