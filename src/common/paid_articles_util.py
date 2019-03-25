from not_authorized_error import NotAuthorizedError


class PaidArticlesUtil:

    @staticmethod
    def validate_paid_article_existence(paid_article):
        if paid_article is None or paid_article['status'] != 'done':
            raise NotAuthorizedError('Forbidden')

        return True
