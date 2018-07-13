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
        'maxLength': 30,
        'pattern': '^(?!.*--)[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]$'
    },
    'phone_number': {
        'type': 'string',
        'minLength': 13,
        'maxLength': 13,
        'pattern': '^\+81[6-9]0\d{8}$'
    },
    'icon_image': {
        'type': 'string',
        'maxLength': 8388608
    },
    'evaluated_at': {
        'type': 'integer',
        'minimum': 1,
        'maximum': 2147483647000000
    },
    'sort_key': {
        'type': 'integer',
        'minimum': 1,
        'maximum': 2147483647000000
    },
    'score': {
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
    'notification_id': {
        'type': 'string',
        'maxLength': 80
    },
    'comment': {
        'text': {
            'type': 'string',
            'minLength': 1,
            'maxLength': 400
        },
        'comment_id': {
            'type': 'string',
            'minLength': 12,
            'maxLength': 12
        }
    }
}

article_recent_default_limit = 20
users_articles_public_default_limit = 10
articles_popular_default_limit = 20

USERS_ARTICLE_INDEX_DEFAULT_LIMIT = 10
NOTIFICATION_INDEX_DEFAULT_LIMIT = 10
COMMENT_INDEX_DEFAULT_LIMIT = 10

article_id_length = 12
COMMENT_ID_LENGTH = 12

html_allowed_tags = ['a', 'b', 'blockquote', 'br', 'h2', 'h3', 'i', 'p', 'u', 'img', 'hr',
                     'div', 'figure', 'figcaption']

ng_user_name = [
    'about', 'account', 'activity', 'add', 'admin', 'all', 'alpha', 'analysis',
    'api', 'app', 'archive', 'article', 'asct', 'asset', 'atom', 'auth',
    'balancer-manager', 'beta', 'blog', 'book', 'bookmark', 'bot', 'bug',
    'business', 'calendar', 'call', 'captcha', 'career', 'cart', 'case',
    'category', 'cgi', 'cgi-bin', 'code', 'comment', 'community', 'company',
    'config', 'connect', 'contact', 'contest', 'contribute', 'corp', 'count',
    'create', 'css', 'dashboard', 'data', 'default', 'delete', 'design', 'destroy',
    'dev', 'developer', 'diagram', 'diary', 'dict', 'dictionary', 'die', 'dir',
    'dist', 'doc', 'download', 'edit', 'else', 'empty', 'end', 'entry', 'error',
    'eval', 'event', 'exit', 'explore', 'faq', 'feature', 'feed', 'file', 'find',
    'first', 'flash', 'forgot', 'form', 'forum', 'friend', 'game', 'get', 'gift',
    'graph', 'group', 'guest', 'help', 'home', 'howto', 'icon', 'image', 'img',
    'index', 'info', 'information', 'inquiry', 'issue', 'item', 'javascript',
    'join', 'json', 'jump', 'language', 'last', 'ldap-status', 'legal', 'license',
    'log', 'login', 'logout', 'mail', 'maintenance', 'manual', 'master', 'member',
    'message', 'mobile', 'msg', 'nan', 'navi', 'navigation', 'new', 'news',
    'notify', 'null', 'off', 'offer', 'official', 'old', 'order', 'organization',
    'out', 'owner', 'page', 'password', 'phone', 'photo', 'plan', 'policy',
    'popular', 'portal', 'post', 'premium', 'press', 'price', 'privacy', 'private',
    'product', 'profile', 'project', 'public', 'purpose', 'put', 'query',
    'ranking', 'read', 'recent', 'recruit', 'register', 'release', 'remove',
    'report', 'repository', 'req', 'request', 'reset', 'roc', 'root', 'rss',
    'rule', 'sag', 'school', 'script', 'search', 'secure', 'security', 'select',
    'self', 'server-info', 'server-status', 'service', 'session', 'setting',
    'share', 'shop', 'show', 'signin', 'signout', 'signup', 'site', 'sitemap',
    'source', 'spec', 'special', 'src', 'start', 'state', 'static', 'status',
    'store', 'style', 'stylesheet', 'support', 'svn', 'swf', 'switch', 'sys',
    'system', 'tag', 'term', 'test', 'theme', 'then', 'thread', 'tool', 'top',
    'topic', 'tour', 'tutorial', 'tux', 'undef', 'update', 'upload', 'usage',
    'user', 'ver', 'version', 'video', 'watch', 'when', 'widget', 'wiki', 'word',
    'xml', 'year'
]

LIKED_RETRY_COUNT = 3

ARTICLE_IMAGE_MAX_WIDTH = 3840
ARTICLE_IMAGE_MAX_HEIGHT = 2160

USER_ICON_WIDTH = 240
USER_ICON_HEIGHT = 240

S3_ARTICLES_IMAGES_PATH = 'd/api/articles_images/'
S3_INFO_ICON_PATH = 'd/api/info_icon/'

LIKE_NOTIFICATION_TYPE = 'like'
COMMENT_NOTIFICATION_TYPE = 'comment'

FRAUD_REASONS = [
    'violence',
    'spam',
    'plagiarism',
    'slander',
    'illegal',
    'other'
]

FRAUD_NEED_ORIGINAL_REASONS = ['plagiarism']

FRAUD_NEED_DETAIL_REASONS = ['illegal', 'other']
