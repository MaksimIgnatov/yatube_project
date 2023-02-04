from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from ..models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def setUp(self):
        self.user = User.objects.create_user(username='HasNoName')
        self.client_without_post = Client()
        self.client_without_post.force_login(self.user)
        self.authorized_client = Client()
        self.authorized_client.force_login(PostURLTests.user)

    def test_posts_urls_correct_access_for_anonymous(self):
        """Проверяем общедоступные страницы для любого пользователя"""
        url_names_http_code = {
            '/': HTTPStatus.OK,
            f'/group/{self.group.slug}/': HTTPStatus.OK,
            f'/profile/{self.user.username}/': HTTPStatus.OK,
            f'/posts/{self.post.id}/': HTTPStatus.OK,
            '/unexisting_page/': HTTPStatus.NOT_FOUND,
        }

        for address, http_code in url_names_http_code.items():
            with self.subTest(address=address):
                response = self.client.get(address)
                self.assertEqual(response.status_code, http_code)

        for address, http_code in url_names_http_code.items():
            with self.subTest(address=address):
                response = self.client_without_post.get(address)
                self.assertEqual(response.status_code, http_code)

    def test_posts_edit_correct_access_for_avtor(self):
        """Проверяем /posts/1/edit/ для автора"""
        response = self.authorized_client.get(f'/posts/{self.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_posts_create_correct_access_for_client_without_post(self):
        """Проверяем /create/ для пользователя без поста"""
        response = self.client_without_post.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_posts_urls_redirect_access_for_guest_client(self):
        """
        Страница перенаправляется по определенному адресу
        для неавторизованного пользователя
        """
        url_names_redirect_url = {
            f'/posts/{self.post.id}/edit/':
                f'/auth/login/?next=/posts/{self.post.id}/edit/',
            '/create/': '/auth/login/?next=/create/',
        }

        for address, redirect_adress in url_names_redirect_url.items():
            with self.subTest(address=address):
                response = self.client.get(address, follow=True)
                self.assertRedirects(
                    response, (redirect_adress))

    def test_posts_urls_redirect_access_for_for_client_without_post(self):
        """
        Страница /posts/1/edit/ перенаправляется по определенному адресу
        для не автора поста
        """
        response = self.client_without_post.get(f'/posts/{self.post.id}/edit/',
                                                follow=True)
        self.assertRedirects(response, (f'/posts/{self.post.id}/'))

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user.username}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
            '/unexisting_page/': 'core/404.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
