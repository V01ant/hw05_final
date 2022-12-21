from django.test import TestCase, Client
from http import HTTPStatus


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_of_urls_at_about_app(self):
        """URL-адрес приложения about использует соответствующий шаблон."""
        template_url_names = {
            'about/author.html': '/about/author/',
            'about/tech.html': '/about/tech/',
        }
        for template, url in template_url_names.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_of_templates_at_about_app(self):
        """Проверка доступности существующих страниц приложения about."""
        app_pages = [
            '/about/author/',
            '/about/tech/',
        ]
        for page in app_pages:
            with self.subTest():
                response = self.guest_client.get(page)
                self.assertEqual(response.status_code, HTTPStatus.OK)
