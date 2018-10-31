import settings
import bleach
import os
import json
from urllib.parse import urlparse
from enum import Enum


class Block(Enum):
    Rule = 'Rule'
    Text = 'Text'
    Paragraph = 'Paragraph'
    Image = 'Image'
    Quote = 'Quote'
    Heading = 'Heading'
    Embed = 'Embed'
    Link = 'Link'


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
    def sanitize_article_object(params):
        if params is None:
            return

        if len(params) >= 2:
            for obj in params:
                # オブジェクトのtypeが想定通りのものであるかをチェック
                TextSanitizer.raise_invalid_type_exception(obj)

                if obj['type'] == Block.Paragraph.value:
                    TextSanitizer.sanitize_paragraph(obj)
                if obj['type'] == Block.Text.value:
                    obj['payload']['body'] = bleach.clean(text=obj['payload']['body'], tags=[])
                if obj['type'] == Block.Image.value:
                    TextSanitizer.sanitize_image_block(obj)
                if obj['type'] == Block.Heading.value:
                    TextSanitizer.sanitize_heading_block(obj)
                if obj['type'] == Block.Embed.value:
                    obj['payload']['src'] = bleach.clean(text=obj['payload']['src'], tags=[])

                if 'children' in obj:
                    if len(obj['children']) != 0:
                        for children in obj['children']:
                            TextSanitizer.sanitize_article_object([children])
        else:
            TextSanitizer.raise_invalid_type_exception(params[0])
            if params[0]['type'] == Block.Paragraph.value:
                TextSanitizer.sanitize_paragraph(params[0])
            if params[0]['type'] == Block.Text.value:
                params[0]['payload']['body'] = bleach.clean(text=params[0]['payload']['body'], tags=[])
            if params[0]['type'] == Block.Image.value:
                TextSanitizer.sanitize_image_block(params[0])
            if params[0]['type'] == Block.Heading.value:
                TextSanitizer.sanitize_heading_block(params[0])
            if params[0]['type'] == Block.Embed.value:
                params[0]['payload']['src'] = bleach.clean(text=params[0]['payload']['src'], tags=[])

            if 'children' in params[0]:
                if len(params[0]['children']) != 0:
                    for children in params[0]['children']:
                        TextSanitizer.sanitize_article_object([children])

        return json.dumps(params, ensure_ascii=False)

    @staticmethod
    def raise_invalid_type_exception(obj):
        if obj['type'] != Block.Paragraph.value and obj['type'] != Block.Text.value and \
           obj['type'] != Block.Image.value and obj['type'] != Block.Heading.value and \
           obj['type'] != Block.Embed.value and obj['type'] != Block.Quote.value and \
           obj['type'] != Block.Rule.value and obj['type'] != Block.Link.value:
            raise Exception

    @staticmethod
    def sanitize_paragraph(obj):
        if 'payload' in obj and obj['payload']['body'] is not None:
            obj['payload']['body'] = bleach.clean(
                text=obj['payload']['body'],
                tags=settings.alis_editor_allowed_tags,
                attributes={
                    'a': ['href', 'target'],
                    'div': ['class', 'style']
                }
            )

    @staticmethod
    def sanitize_image_block(obj):
        if 'align' in obj['payload']:
            obj['payload']['align'] = bleach.clean(text=obj['payload']['align'], tags=[])
        p = urlparse(obj['payload']['src'])
        if (not p.netloc) or p.netloc == os.environ['DOMAIN']:
            return
        else:
            raise Exception

    @staticmethod
    def sanitize_heading_block(obj):
        size = obj['payload']['size']
        if size == 'h2' or size == 'h3':
            pass
        else:
            obj['payload']['size'] = 'h2'
        obj['payload']['body'] = bleach.clean(text=obj['payload']['body'], tags=[])
