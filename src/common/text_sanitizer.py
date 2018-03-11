import settings
import bleach


class TextSanitizer:
    @staticmethod
    def sanitize_text(text):
        if text is None:
            return

        return bleach.clean(text=text)

    @staticmethod
    def sanitize_article_body(text):
        if text is None:
            return

        return bleach.clean(
            text=text,
            tags=settings.html_allowed_tags,
            attributes=settings.html_allowed_attributes,
        )
