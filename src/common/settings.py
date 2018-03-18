parameters = {
    'limit': {
        'type': 'integer',
        'minimum': 1,
        'maximum': 100
    },
    'article_id': {
        'type': 'string',
        "minLength": 12,
        "maxLength": 12
    },
    'sort_key': {
        'type': 'integer',
        "minimum": 1,
        "maximum": 2147483647000000
    }
}

article_recent_default_limit = 20

LIKED_RETRY_COUNT = 3
