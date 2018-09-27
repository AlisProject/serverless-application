import settings
from urllib.parse import parse_qsl


class TwitterUtil:
    @staticmethod
    def parse_api_response(response):
        return dict(parse_qsl(response.content.decode('utf-8')))

    def get_authentication_url(oauth_token):
        return '%s?oauth_token=%s' \
            % (settings.TWITTER_API_AUTHENTICATE_URL, oauth_token)
