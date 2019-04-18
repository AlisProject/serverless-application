from unittest import TestCase
from text_sanitizer import TextSanitizer
from jsonschema import ValidationError
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

    def test_sanitize_article_body_v2(self):
        target_html = '''
            <p>test</p>
            <h2>H2</h2>
            <h3>H3</h3>
            <blockquote>
              <p>引用</p>
            </blockquote>
            <p><strong>太字</strong></p>
            <p><i>斜体</i></p>
            <p><a href="https://example.com/">リンク付与</a></p>
            <figure class="media">
              <oembed url="https://{domain}/"></oembed>
            </figure>
            <figure class="image">
              <img src="https://{domain}/test.png">
            </figure>
            <figure class="image image-style-align-right">
              <img src="https://{domain}/test.png">
            </figure>
            <figure class="image image-style-align-left">
              <img src="https://{domain}/test.png">
            </figure>
            <figure class="image image-style-align-left">
              <img src="https://{domain}/test.png">
              <figcaption>hoge</figcaption>
            </figure>
            <p>shift+enter<br>test</p>
        '''.format(domain=os.environ['DOMAIN'])

        result = TextSanitizer.sanitize_article_body_v2(target_html)

        self.assertEqual(result, target_html)

    def test_sanitize_article_body_v2_with_evil_img_tag(self):
        target_html = '''
        <h2>sample h2</h2>
        <img src="http://{domain}/hoge.png" onerror='document.alert('evil')'>
        '''.format(domain=os.environ['DOMAIN'])

        expected_html = '''
        <h2>sample h2</h2>
        <img src="http://{domain}/hoge.png">
        '''.format(domain=os.environ['DOMAIN'])

        result = TextSanitizer.sanitize_article_body_v2(target_html)

        self.assertEqual(result, expected_html)

    def test_sanitize_article_body_v2_with_evil_other_site_url(self):
        target_html = '''
         <h2>sample h2</h2>
         <img src="http://hoge.com/hoge.png">
         '''

        expected_html = '''
         <h2>sample h2</h2>
         <img>
         '''

        result = TextSanitizer.sanitize_article_body_v2(target_html)

        self.assertEqual(result, expected_html)

    def test_sanitize_article_body_v2_with_evil_a_tag(self):
        target_html = '''
        <h2>sample h2</h2>
        <a href="http://example.com" onclick="document.alert('evil')">link</a>
        '''

        expected_html = '''
        <h2>sample h2</h2>
        <a href="http://example.com">link</a>
        '''

        result = TextSanitizer.sanitize_article_body(target_html)

        self.assertEqual(result, expected_html)

    def test_sanitize_article_body_with_figure_unauthorized_class(self):
        target_html = '''
        <h2>sample h2</h2>
        <figure class='image hogehoge' data='aaa'></figure>
        '''

        expected_html = '''
        <h2>sample h2</h2>
        <figure></figure>
        '''

        result = TextSanitizer.sanitize_article_body_v2(target_html)

        self.assertEqual(result, expected_html)

    def test_sanitize_article_body_with_oembed_unauthorized_class(self):
        target_html = '''
        <h2>sample h2</h2>
        <oembed src='hogehoge' data='aaa'></oembed>
        '''

        expected_html = '''
        <h2>sample h2</h2>
        <oembed></oembed>
        '''

        result = TextSanitizer.sanitize_article_body_v2(target_html)

        self.assertEqual(result, expected_html)

    def test_sanitize_article_body_with_a_unauthorized_class(self):
        target_html = '''
        <h2>sample h2</h2>
        <a href="hogehoge" data='aaa'></a>
        '''

        expected_html = '''
        <h2>sample h2</h2>
        <a href="hogehoge"></a>
        '''

        result = TextSanitizer.sanitize_article_body_v2(target_html)

        self.assertEqual(result, expected_html)

    def test_validate_img_url_ok(self):
        img_url = 'https://' + os.environ['DOMAIN'] + '/img/test.jpg'
        result = TextSanitizer.validate_img_url(img_url)

        self.assertEqual(result, True)

    def test_validate_img_url_ok_root_path(self):
        img_url = 'img/test.jpg'
        result = TextSanitizer.validate_img_url(img_url)

        self.assertEqual(result, True)

    def test_validate_img_url_ng_not_domain(self):
        with self.assertRaises(ValidationError):
            img_url = 'https://test.to/test.jpg'
            TextSanitizer.validate_img_url(img_url)
