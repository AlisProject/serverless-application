from abc import ABCMeta, abstractmethod
import json
import logging
import traceback
from jsonschema import ValidationError


class LambdaBase(metaclass=ABCMeta):
    def __init__(self, event, context, dynamodb=None, s3=None):
        self.event = event
        self.context = context
        self.dynamodb = dynamodb
        self.s3 = s3

    @abstractmethod
    def get_schema(self):
        pass

    @abstractmethod
    def exec_main_proc(self):
        pass

    @abstractmethod
    def validate_params(self):
        pass

    def main(self):
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)

        try:
            # validation
            self.validate_params()

            # exec main process
            return self.exec_main_proc()
        except ValidationError as err:
            return {
                'statusCode': 400,
                'body': json.dumps({'message': "Invalid parameter: {0}".format(err)})
            }

        except Exception as err:
            logger.fatal(err)
            traceback.print_exc()

            return {
                'statusCode': 500,
                'body': json.dumps({'message': 'Internal server error'})
            }
