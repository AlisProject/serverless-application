from jsonschema import ValidationError


class ParameterUtil:
    @staticmethod
    def cast_parameter_to_int(params, schema):
        properties = schema['properties']

        for key, value in params.items():
            if properties.get(key) is None:
                continue

            if properties[key]['type'] == 'integer' and value.isdigit():
                params[key] = int(value)

    @staticmethod
    def validate_array_unique(items, key, case_insensitive=False):
        if len(items) != len(set(items)):
            raise ValidationError("{key} must be unique".format(key=key))

        if case_insensitive:
            lower_items = [item.lower() for item in items]

            if len(lower_items) != len(set(lower_items)):
                raise ValidationError("{key} must be unique(case-insensitive)".format(key=key))
