from abc import ABCMeta, abstractmethod
import logging
import traceback
from jsonschema import ValidationError


class CognitoTriggerBase(metaclass=ABCMeta):
    def __init__(self, event, context, dynamodb=None, s3=None, cognito=None, elasticsearch=None):
        self.event = event
        self.context = context
        self.dynamodb = dynamodb
        self.s3 = s3
        self.cognito = cognito
        self.elasticsearch = elasticsearch
        self.params = None
        self.headers = None

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
            # params validation
            self.validate_params()

            # exec main process
            return self.exec_main_proc()
        except ValidationError as err:
            logger.fatal(err)
            logger.info(self.event)
            raise Exception(err.message)

        except Exception as err:
            logger.fatal(err)
            logger.info(self.event)
            traceback.print_exc()
            raise Exception('Internal server error')
