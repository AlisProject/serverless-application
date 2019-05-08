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

    @staticmethod
    def validate_price_params(params_price):
        if params_price is not None:
            try:
                params_price = int(params_price)
            except ValueError:
                raise ValidationError('Price must be integer')

            # check price value is not decimal
            price = params_price / 10 ** 18
            if price.is_integer() is False:
                raise ValidationError('Decimal value is not allowed')
            return True
