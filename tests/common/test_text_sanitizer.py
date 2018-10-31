from unittest import TestCase
from text_sanitizer import TextSanitizer
import os


class TestTextSanitizer(TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ['DOMAIN'] = 'example.com'

    def test_sanitize_text(self):
        target_html = '''
        Sample text
        <script>document.alert('evil')</script>
        <b>bold</b>
        <h2>sample h2</h2>
        <h3>sample h3</h3>
        <i>icon</i><p>sentence</p><u>under bar</u>
        <b>bold</b><br><blockquote>blockquote</blockquote>
        '''

        expected_html = '''
        Sample text
        &lt;script&gt;document.alert('evil')&lt;/script&gt;
        &lt;b&gt;bold&lt;/b&gt;
        &lt;h2&gt;sample h2&lt;/h2&gt;
        &lt;h3&gt;sample h3&lt;/h3&gt;
        &lt;i&gt;icon&lt;/i&gt;&lt;p&gt;sentence&lt;/p&gt;&lt;u&gt;under bar&lt;/u&gt;
        &lt;b&gt;bold&lt;/b&gt;&lt;br&gt;&lt;blockquote&gt;blockquote&lt;/blockquote&gt;
        '''

        result = TextSanitizer.sanitize_text(target_html)

        self.assertEqual(result, expected_html)

    def test_sanitize_text_with_none_text(self):
        result = TextSanitizer.sanitize_text(None)

        self.assertEqual(result, None)

    def test_sanitize_article_body(self):
        target_html = '''
        <h2>sample h2</h2>

        <h3>sample h3</h3>

        <i>icon</i><p>sentence</p><u>under bar</u>

        <b>bold</b><br><blockquote>blockquote</blockquote>
        <div class="medium-insert-images">
            <figure contenteditable="false">
                <img src="http://{domain}/hoge">
                <figcaption class="" contenteditable="true">aaaaaa</figcaption>
            </figure>
        </div>
        <div class="medium-insert-images medium-insert-images-left" contenteditable="false">
            <figure contenteditable="false">
                <img src="http://{domain}/hoge">
                <figcaption class="" contenteditable="true"></figcaption>
            </figure>
        </div>
        <div class="medium-insert-images medium-insert-images-right" contenteditable="false">
            <figure contenteditable="false">
                <img src="http://{domain}/hoge">
                <figcaption contenteditable="true">aaaaaa</figcaption>
            </figure>
        </div>
        <div class="medium-insert-images medium-insert-images-grid">
            <figure contenteditable="false">
                <img src="http://{domain}/hoge">
                <figcaption class="">aaaaaa</figcaption>
            </figure>
        </div>
        <div class="medium-insert-images medium-insert-images-wide">
            <figure contenteditable="false">
                <img src="http://{domain}/hoge">
            </figure>
        </div>
        <a href="http://example.com">link</a>
        <div data-alis-iframely-url="https://twitter.com/hoge">hoge</div>
        <div data-alis-iframely-url="https://example.com/hoge?x=1">hoge</div>
        <div data-alis-iframely-url="http://example.com/hoge?x=1%3Cdiv%3Ehoge%3C%2Fdiv%3E">hoge</div>
        '''.format(domain=os.environ['DOMAIN'])

        result = TextSanitizer.sanitize_article_body(target_html)

        self.assertEqual(result, target_html)

    def test_sanitize_article_body_with_none_text(self):
        result = TextSanitizer.sanitize_text(None)

        self.assertEqual(result, None)

    def test_sanitize_article_body_with_evil_a_tag(self):
        target_html = '''
        <h2>sample h2</h2>
        <a href="http://example.com" onclick="document.alert("evil")">link</a>
        '''

        expected_html = '''
        <h2>sample h2</h2>
        <a href="http://example.com">link</a>
        '''

        result = TextSanitizer.sanitize_article_body(target_html)

        self.assertEqual(result, expected_html)

    def test_sanitize_article_body_with_evil_img_tag(self):
        target_html = '''
        <h2>sample h2</h2>
        <img src="http://{domain}/hoge.png" onerror='document.alert('evil')'>
        '''.format(domain=os.environ['DOMAIN'])

        expected_html = '''
        <h2>sample h2</h2>
        <img src="http://{domain}/hoge.png">
        '''.format(domain=os.environ['DOMAIN'])

        result = TextSanitizer.sanitize_article_body(target_html)

        self.assertEqual(result, expected_html)

    def test_sanitize_article_body_with_evil_other_site_url(self):
        target_html = '''
        <h2>sample h2</h2>
        <img src="http://hoge.com/hoge.png">
        '''

        expected_html = '''
        <h2>sample h2</h2>
        <img>
        '''

        result = TextSanitizer.sanitize_article_body(target_html)

        self.assertEqual(result, expected_html)

    def test_sanitize_article_body_with_div_unauthorized_class(self):
        target_html = '''
        <h2>sample h2</h2>
        <div class='hoge piyo' data='aaa'></div>
        '''

        expected_html = '''
        <h2>sample h2</h2>
        <div></div>
        '''

        result = TextSanitizer.sanitize_article_body(target_html)

        self.assertEqual(result, expected_html)

    def test_sanitize_article_body_with_div_unauthorized_url(self):
        target_html = '''
        <h2>sample h2</h2>
        <div class='hoge piyo' data='aaa' contenteditable='true'></div>
        <div data-alis-iframely-url="https://example.com/hoge?<script>piyo</script>">hoge</div>
        '''

        expected_html = '''
        <h2>sample h2</h2>
        <div></div>
        <div>hoge</div>
        '''

        result = TextSanitizer.sanitize_article_body(target_html)

        self.assertEqual(result, expected_html)

    def test_sanitize_article_body_with_figure_unauthorized_contenteditable(self):
        target_html = '''
        <h2>sample h2</h2>
        <figure contenteditable='true' data='aaa'></figure>
        '''

        expected_html = '''
        <h2>sample h2</h2>
        <figure></figure>
        '''

        result = TextSanitizer.sanitize_article_body(target_html)

        self.assertEqual(result, expected_html)

    def test_sanitize_article_body_with_figcaption_unauthorized_attribute(self):
        target_html = '''
        <h2>sample h2</h2>
        <figcaption contenteditable='false' class='hoge' data='aaa'></figcaption>
        '''

        expected_html = '''
        <h2>sample h2</h2>
        <figcaption></figcaption>
        '''

        result = TextSanitizer.sanitize_article_body(target_html)

        self.assertEqual(result, expected_html)

    def test_sanitize_article_body_with_script_tag(self):
        target_html = '''
        <h2>sample h2</h2>
        <script>document.alert('evil')</script>
        '''

        expected_html = '''
        <h2>sample h2</h2>
        &lt;script&gt;document.alert('evil')&lt;/script&gt;
        '''

        result = TextSanitizer.sanitize_article_body(target_html)

        self.assertEqual(result, expected_html)

    def test_sanitize_article_body_with_div(self):
        target_html = '''
        <h2>sample h2</h2>
        <script>document.alert('evil')</script>
        '''

        expected_html = '''
        <h2>sample h2</h2>
        &lt;script&gt;document.alert('evil')&lt;/script&gt;
        '''

        result = TextSanitizer.sanitize_article_body(target_html)

        self.assertEqual(result, expected_html)

    def test_invalid_type_block(self):
        obj = [{
            "type": "Hoge",
            "payload": {
              "body": "hogehoge"
            }
        }]

        self.assertRaises(Exception, lambda: TextSanitizer.raise_invalid_type_exception(obj[0]))

    def test_sanitize_paragraph_with_div(self):
        div_class_paragraph = [{
            "type": "Paragraph",
            "payload": {
              "body": "<div class='test_class'>テスト</div>"
            },
            "children": []
        }]
        TextSanitizer.sanitize_paragraph(div_class_paragraph)
        self.assertEqual(div_class_paragraph[0]['payload']['body'], "<div class='test_class'>テスト</div>")

        div_style_paragraph = [{
            "type": "Paragraph",
            "payload": {
                "body": "<div style='test_style'>テスト</div>"
            },
            "children": []
        }]
        TextSanitizer.sanitize_paragraph(div_style_paragraph)
        self.assertEqual(div_style_paragraph[0]['payload']['body'], "<div style='test_style'>テスト</div>")

        invalid_div_attribute_paragraph = [{
            "type": "Paragraph",
            "payload": {
                "body": "<div hoge='hoge'>テスト</div>"
            },
            "children": []
        }]
        TextSanitizer.sanitize_paragraph(invalid_div_attribute_paragraph[0])
        self.assertEqual(invalid_div_attribute_paragraph[0]['payload']['body'], "<div>テスト</div>")

    def test_sanitize_paragraph_with_a(self):
        a_tag_with_href_params = [{
            "type": "Paragraph",
            "payload": {
              "body": "<a href='https://example.com'>テスト</a>"
            },
            "children": []
        }]
        TextSanitizer.sanitize_paragraph(a_tag_with_href_params)
        self.assertEqual(a_tag_with_href_params[0]['payload']['body'],
                         "<a href='https://example.com'>テスト</a>")

        a_tag_with_target_params = [{
            "type": "Paragraph",
            "payload": {
                "body": '<a href="https://example.com" target="_blank">テスト</a>'
            },
            "children": []
        }]
        TextSanitizer.sanitize_paragraph(a_tag_with_target_params)
        self.assertEqual(a_tag_with_target_params[0]['payload']['body'],
                         '<a href="https://example.com" target="_blank">テスト</a>')

        invalid_a_attribute_paragraph = [{
            "type": "Paragraph",
            "payload": {
                "body": "<a href='https://example.com' hoge='hoge'>テスト</div>"
            },
            "children": []
        }]
        TextSanitizer.sanitize_paragraph(invalid_a_attribute_paragraph[0])
        self.assertEqual(invalid_a_attribute_paragraph[0]['payload']['body'],
                         '<a href="https://example.com">テスト</a>')

    def test_sanitize_paragraph_with_script_tag(self):
        invalid_script_tag_paragraph = [{
            "type": "Paragraph",
            "payload": {
                "body": "<script>テスト</script>"
            },
            "children": []
        }]
        TextSanitizer.sanitize_paragraph(invalid_script_tag_paragraph[0])
        self.assertEqual(invalid_script_tag_paragraph[0]['payload']['body'], "&lt;script&gt;テスト&lt;/script&gt;")

    def test_sanitize_article_object_with_text_and_link_ok(self):
        obj = [{
            "type": "Paragraph",
            "payload": {
              "body": '<img src="a"><b>test</b><a href="bbb">a</a><p>b</p><hr><div>c</div><u>d</u><i>e</i><br>'
            },
            "children": [
              {
                "type": "Text",
                "payload": {
                  "body": "<b>詳細は</b>"
                }
              },
              {
                "type": "Link",
                "payload": {
                  "href": "https://example.com"
                },
                "children": [
                  {
                    "type": "Text",
                    "payload": {
                      "body": "こちら"
                    }
                  }
                ]
              },
              {
                "type": "Text",
                "payload": {
                  "body": "です"
                }
              }
            ]
        }]
        TextSanitizer.sanitize_article_object(obj)
        sanitized_paragraph_body_param = {
            "payload": {
                "body": '&lt;img src="a"&gt;<b>test</b><a href="bbb">a</a><p>b</p><hr><div>c</div><u>d</u><i>e</i><br>'
            }
        }

        self.assertEqual(obj[0]['payload']['body'], sanitized_paragraph_body_param['payload']['body'])
        self.assertEqual(obj[0]['children'][0]['payload']['body'], "&lt;b&gt;詳細は&lt;/b&gt;")
        self.assertEqual(obj[0]['children'][1]['children'][0]['payload']['body'], "こちら")
        self.assertEqual(obj[0]['children'][2]['payload']['body'], "です")

    def test_sanitize_article_object_with_heading_and_img_and_embed_ok(self):
        obj = [{
            "type": "Paragraph",
            "payload": {
                "body": "テスト"
            },
            "children": [
              {
                "type": "Heading",
                "payload": {
                    "size": 'h2',
                    "body": "テスト"
                }
              },
              {
                "type": "Image",
                "payload": {
                    "src": "https://example.com/gra67grea7gra.png"
                },
                "children": []
              },
              {
                "type": "Embed",
                "payload": {
                    "src": "https://example.com"
                }
              }
            ]
        }]

        os.environ['DOMAIN'] = 'example.com'
        TextSanitizer.sanitize_article_object(obj)

        self.assertEqual(obj,
                         [{
                             "type": "Paragraph",
                             "payload": {
                                 "body": "テスト"
                             },
                             "children": [
                                 {
                                     "type": "Heading",
                                     "payload": {
                                         "size": 'h2',
                                         "body": "テスト"
                                     }
                                 },
                                 {
                                     "type": "Image",
                                     "payload": {
                                         "src": "https://example.com/gra67grea7gra.png"
                                     },
                                     "children": []
                                 },
                                 {
                                     "type": "Embed",
                                     "payload": {
                                         "src": "https://example.com"
                                     }
                                 }
                             ]
                         }]
                         )
