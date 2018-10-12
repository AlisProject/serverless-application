import json
import settings


class BlocksParserUtil:

    @staticmethod
    def get_schema(type: str) -> any:
        return {
            'type': 'object'
        }

    @staticmethod
    def validate(jsonStr: str) -> bool:
        blocks = json.load(jsonStr)
        for block in blocks:
            if block.type not in settings.ALLOWED_BLOCK_TYPES:
                return False
