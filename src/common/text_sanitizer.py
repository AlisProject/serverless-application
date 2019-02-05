import settings
import bleach
import os
from urllib.parse import urlparse


class TextSanitizer:
    @staticmethod
    def sanitize_text(text):
        if text is None:
            return

        return bleach.clean(text=text, tags=[])

    @staticmethod
    def allow_img_src(tag, name, value):
        if name in 'alt':
            return True
        if name == 'src':
            p = urlparse(value)
            return (not p.netloc) or p.netloc == os.environ['DOMAIN']
        return False

    @staticmethod
    def allow_div_attributes(tag, name, value):
        if name == 'class':
            allow_classes = [
                'medium-insert-images',
                'medium-insert-images medium-insert-images-wide',
                'medium-insert-images medium-insert-images-left',
                'medium-insert-images medium-insert-images-right',
                'medium-insert-images medium-insert-images-grid'
            ]
            if value in allow_classes:
                return True
        if name == 'data-alis-iframely-url':
            p = urlparse(value)
            is_url = len(p.scheme) > 0 and len(p.netloc) > 0
            is_clean = True if bleach.clean(value) == value else False
            return is_url and is_clean
        if name == 'contenteditable':
            if value == 'false':
                return True
        return False

    @staticmethod
    def allow_figure_contenteditable(tag, name, value):
        if name == 'contenteditable':
            if value == 'false':
                return True
        return False

    @staticmethod
    def allow_figcaption_attributes(tag, name, value):
        if name == 'class':
            if value == '':
                return True
        if name == 'contenteditable':
            if value == 'true':
                return True
        return False

    @staticmethod
    def sanitize_article_body(text):
        if text is None:
            return

        return bleach.clean(
            text=text,
            tags=settings.html_allowed_tags,
            attributes={
                'a': ['href'],
                'img': TextSanitizer.allow_img_src,
                'div': TextSanitizer.allow_div_attributes,
                'figure': TextSanitizer.allow_figure_contenteditable,
                'figcaption': TextSanitizer.allow_figcaption_attributes
            }
        )

    @staticmethod
    def allow_img_v2(tag, name, value):
        if name == 'src':
            p = urlparse(value)
            return (not p.netloc) or p.netloc == os.environ['DOMAIN']
        return False

    @staticmethod
    def allow_figure_v2(tag, name, value):
        if name == 'class':
            allow_classes = [
                'media',
                'image',
                'image image-style-align-right',
                'image image-style-align-left',
            ]
            if value in allow_classes:
                return True
        return False

    @staticmethod
    def allow_oembed_v2(tag, name, value):
        if name == 'url':
            p = urlparse(value)
            is_url = len(p.scheme) > 0 and len(p.netloc) > 0
            return is_url
        return False

    @staticmethod
    def allow_a_v2(tag, name, value):
        if name == 'href':
            p = urlparse(value)
            is_url = len(p.scheme) > 0 and len(p.netloc) > 0
            return is_url
        return False

    @staticmethod
    def sanitize_article_body_v2(text):
        if text is None:
            return

        return bleach.clean(
            text=text,
            tags=settings.html_allowed_tags_v2,
            attributes={
                'a': TextSanitizer.allow_a_v2,
                'img': TextSanitizer.allow_img_v2,
                'figure': TextSanitizer.allow_figure_v2,
                'oembed': TextSanitizer.allow_oembed_v2
            }
        )
