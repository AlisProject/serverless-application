import json
from decimal_encoder import DecimalEncoder


class ResponseBuilder:
    @staticmethod
    def response(status_code, body):
        return {
            'statusCode': status_code,
            'body': json.dumps(body, cls=DecimalEncoder)
        }
