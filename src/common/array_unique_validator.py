from jsonschema import ValidationError


class ArrayUniqueValidator:

    @staticmethod
    def validate(items, key, case_insensitive=False):
        if len(items) != len(set(items)):
            raise ValidationError("{key} must be unique".format(key=key))

        if case_insensitive:
            lower_items = [item.lower() for item in items]

            if len(lower_items) != len(set(lower_items)):
                raise ValidationError("{key} must be unique(case-insensitive)".format(key=key))
