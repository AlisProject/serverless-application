from unittest import TestCase

from array_unique_validator import ArrayUniqueValidator
from jsonschema import ValidationError


class TestArrayUniqueValidator(TestCase):
    def test_validate_ok(self):
        target_items = ["FOO", "BAR", "foo"]

        try:
            ArrayUniqueValidator.validate(target_items, 'tags')
        except ValidationError:
            self.fail('expected no error is raised')

    def test_validate_ok_with_case_insensitive(self):
        target_items = ["FOO", "BAR", "BAZ"]

        try:
            ArrayUniqueValidator.validate(target_items, 'tags', case_insensitive=True)
        except ValidationError:
            self.fail('expected no error is raised')

    def test_validate_with_not_unique(self):
        target_items = ["FOO", "BAR", "FOO"]

        with self.assertRaises(ValidationError):
            ArrayUniqueValidator.validate(target_items, 'tags')

    def test_validate_with_not_unique_case_insensitive(self):
        target_items = ["FOO", "BAR", "foo"]

        with self.assertRaises(ValidationError):
            ArrayUniqueValidator.validate(target_items, 'tags', case_insensitive=True)
