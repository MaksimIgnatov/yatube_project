from django.test import TestCase, Client

from http import HTTPStatus


class AboutURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_about_urls_correct_access(self):
        """Проверяем общедоступные страницы для любого пользователя"""

        url_names_http_code = {
            '/about/author/': HTTPStatus.OK,
            '/about/tech/': HTTPStatus.OK,
        }

        for address, http_code in url_names_http_code.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, http_code)
