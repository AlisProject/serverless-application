parameters = {
    'limit': {
        'type': 'integer',
        'minimum': 1,
        'maximum': 100
    },
    'article_id': {
        'type': 'string',
        'minLength': 12,
        'maxLength': 12
    },
    'user_id': {
        'type': 'string',
        'minLength': 1,
        'maxLength': 255
    },
    'sort_key': {
        'type': 'integer',
        'minimum': 1,
        'maximum': 2147483647000000
    },
    'title': {
        'type': 'string',
        'maxLength': 255,
    },
    'body': {
        'type': 'string',
        'maxLength': 65535
    },
    'eye_catch_url': {
        'type': 'string',
        'format': 'uri',
        'maxLength': 2048
    },
    'overview': {
        'type': 'string',
        'maxLength': 100
    }
}

article_recent_default_limit = 20
users_articles_public_default_limit = 10

article_id_length = 12

html_allowed_tags = ['a', 'b', 'blockquote', 'br', 'h2', 'h3', 'i', 'p', 'u', 'img']
html_allowed_attributes = {'a': ['href'], 'img': ['src', 'alt']}

LIKED_RETRY_COUNT = 3
