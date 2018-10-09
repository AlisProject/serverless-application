class SendTransactionError(Exception):
    pass


class TwitterOauthError(Exception):
    def __init__(self, endpoint, status_code, message):
        self._endpoint = endpoint
        self._status_code = status_code
        self._message = message

    def get_endpoint(self):
        return self._endpoint

    def get_status_code(self):
        return self._status_code

    def get_message(self):
        return self._message

    def __str__(self):
        return '[Twitter API Error]endpoint:' + str(self._endpoint) + ' status_code:' + str(self._status_code) + ' message:' + str(self._message)

    enpoint = property(get_status_code)
    status_code = property(get_status_code)
    message = property(get_message)
