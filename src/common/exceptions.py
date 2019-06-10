class ReceiptError(Exception):
    pass


class SendTransactionError(Exception):
    pass


class YahooOauthError(Exception):
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
        return '[Yahoo API Error]endpoint:' + str(self._endpoint) + ' status_code:' + \
               str(self._status_code) + ' message:' + str(self._message)

    endpoint = property(get_status_code)
    status_code = property(get_status_code)
    message = property(get_message)


class FacebookOauthError(Exception):
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
        return '[Facebook API Error]endpoint:' + str(self._endpoint) + ' status_code:' + \
               str(self._status_code) + ' message:' + str(self._message)

    endpoint = property(get_status_code)
    status_code = property(get_status_code)
    message = property(get_message)


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
        return '[Twitter API Error]endpoint:' + str(self._endpoint) + ' status_code:' + \
               str(self._status_code) + ' message:' + str(self._message)

    endpoint = property(get_status_code)
    status_code = property(get_status_code)
    message = property(get_message)


class LineOauthError(Exception):
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
        return '[Line API Error]endpoint:' + str(self._endpoint) + ' status_code:' + str(self._status_code) \
               + ' message:' + str(self._message)

    endpoint = property(get_status_code)
    status_code = property(get_status_code)
    message = property(get_message)


class Error(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return str(self.message)


class YahooVerifyException(Error):
    pass


class FacebookVerifyException(Error):
    pass


class PrivateChainApiError(Error):
    pass
