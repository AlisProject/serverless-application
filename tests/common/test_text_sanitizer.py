from unittest import TestCase
from text_sanitizer import TextSanitizer
import os
import json


class TestTextSanitizer(TestCase):
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

        <a href="http://example.com">link</a>
        <img src="http://example.com">
        '''

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
        <img src="http://example.com" onerror='document.alert('evil')'>
        '''

        expected_html = '''
        <h2>sample h2</h2>
        <img src="http://example.com">
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
