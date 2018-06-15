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
        '''

        expected_html = '''
        Sample text
        &lt;script&gt;document.alert('evil')&lt;/script&gt;
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
        <div data-alis-iframely-url="https://example.com/hoge">hoge</div>
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
