class ParameterUtil:
    @staticmethod
    def cast_parameter_to_int(params, schema):
        properties = schema['properties']

        for key, value in params.items():
            if properties.get(key) is None:
                continue

            if properties[key]['type'] == 'integer' and value.isdigit():
                params[key] = int(value)
