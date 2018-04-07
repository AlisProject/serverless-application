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
        'minLength': 3,
        'maxLength': 30
    },
    'icon_image': {
        'type': 'string',
        'maxLength': 8388608
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
    'article_image': {
        'type': 'string',
        'maxLength': 8388608
    },
    'eye_catch_url': {
        'type': 'string',
        'format': 'uri',
        'maxLength': 2048
    },
    'overview': {
        'type': 'string',
        'maxLength': 100
    },
    'user_display_name': {
        'type': 'string',
        'minLength': 1,
        'maxLength': 30
    },
    'self_introduction': {
        'type': 'string',
        'maxLength': 100
    },
}

article_recent_default_limit = 20
USERS_ARTICLE_INDEX_DEFAULT_LIMIT = 10
article_id_length = 12

html_allowed_tags = ['a', 'b', 'blockquote', 'br', 'h2', 'h3', 'i', 'p', 'u', 'img']
html_allowed_attributes = {'a': ['href'], 'img': ['src', 'alt']}

LIKED_RETRY_COUNT = 3

ARTICLE_IMAGE_MAX_WIDTH = 1920
ARTICLE_IMAGE_MAX_HEIGHT = 1080

USER_ICON_WIDTH = 240
USER_ICON_HEIGHT = 240
