from datetime import date
import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model

from ..models import Group, Post, Comment, Follow

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
today = date.today()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
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
            group=cls.group,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostCreateFormTests.user)
        self.authorized_client_without_posts = Client()
        self.user_2 = User.objects.create_user(username='HasNoName')
        self.authorized_client_without_posts.force_login(self.user_2)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
        small_gif = (b'\x47\x49\x46\x38\x39\x61\x02\x00'
                     b'\x01\x00\x80\x00\x00\x00\x00\x00'
                     b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
                     b'\x00\x00\x00\x2C\x00\x00\x00\x00'
                     b'\x02\x00\x01\x00\x00\x02\x02\x0C'
                     b'\x0A\x00\x3B')
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый текст',
            'group': PostCreateFormTests.group.pk,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('posts:profile',
                                               kwargs={'username': self.user}))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                author=self.user,
                group=PostCreateFormTests.group.pk,
                image=f'posts/{form_data["image"].name}'
            ).exists()
        )

    def test_edit_post(self):
        """Валидная форма изменяет запись в Post."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый измененный текст',
            'group': PostCreateFormTests.group.pk,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'pk': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('posts:post_detail',
                                               kwargs={'pk':
                                                       self.post.id}))
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(
            Post.objects.filter(
                id=self.post.id,
                text=form_data['text'],
                group=PostCreateFormTests.group.pk
            ).exists()
        )

    def test_comment_post(self):
        """Валидная форма создает запись в Comment"""
        form_data = {
            'text': 'Тестовый комментарий'
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'pk': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('posts:post_detail',
                                               kwargs={'pk':
                                                       self.post.id}))
        self.assertTrue(
            Comment.objects.filter(
                post=self.post,
                author=self.user,
                text=form_data['text'],
            ).exists()
        )

    def test_redirect_commet_post(self):
        """
        Неавторизованный пользователь перенаправляется
        на страницу авторизации
        """
        form_data = {
            'text': 'Тестовый комментарий от неавторизованного пользователя'
        }
        response = self.client.post(
            reverse('posts:add_comment', kwargs={'pk': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, (f'/auth/login/?next=/posts/'
                                        f'{self.post.id}/comment/'))

    def test_follow_system(self):
        """
        Авторизованный пользователь может подписываться
        на других пользователей
        """
        response = self.authorized_client_without_posts.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.user.username}),
            follow=True
        )
        self.assertRedirects(response, reverse('posts:profile',
                                               kwargs={'username':
                                                       self.user.username}))
        self.assertTrue(
            Follow.objects.filter(
                user=self.user_2,
                author=self.user,
            ).exists()
        )

    def test_unfollow_system(self):
        """
        Авторизованный пользователь может отписываться
        на других пользователей
        """
        response = self.authorized_client_without_posts.get(
            reverse('posts:profile_unfollow',
                    kwargs={'username': self.user.username}),
            follow=True
        )
        self.assertRedirects(response, reverse('posts:profile',
                                               kwargs={'username':
                                                       self.user.username}))
        self.assertFalse(
            Follow.objects.filter(
                user=self.user_2,
                author=self.user,
            ).exists()
        )
