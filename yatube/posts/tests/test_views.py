import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

from ..models import Group, Post, Follow

User = get_user_model()
first_ogject_number = 0
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.user_2 = User.objects.create_user(username='HasNoName')
        cls.follow = Follow.objects.create(
            user=cls.user_2,
            author=cls.user,
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        small_gif = (b'\x47\x49\x46\x38\x39\x61\x02\x00'
                     b'\x01\x00\x80\x00\x00\x00\x00\x00'
                     b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
                     b'\x00\x00\x00\x2C\x00\x00\x00\x00'
                     b'\x02\x00\x01\x00\x00\x02\x02\x0C'
                     b'\x0A\x00\x3B')
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.follower_client = Client()
        self.follower_client.force_login(self.user_2)

    def test_post_pages_uses_correct_template(self):
        """View-класс использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': self.group.slug}):
                'posts/group_list.html',
            reverse('posts:profile', kwargs={'username':
                                             self.user.username}):
                'posts/profile.html',
            reverse('posts:post_detail', kwargs={'pk': self.post.id}):
                'posts/post_detail.html',
            reverse('posts:post_edit', kwargs={'pk': self.post.id}):
                'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def correct_post(self, first_object):
        context_data_true_result = {
            first_object.id: self.post.id,
            first_object.text: self.post.text,
            first_object.author.id: self.user.id,
            first_object.author: self.user,
            first_object.group.id: self.group.id,
            first_object.group: self.group,
            first_object.image: self.post.image,
        }
        for context_data, true_result in context_data_true_result.items():
            with self.subTest(context_data=context_data):
                self.assertEqual(context_data, true_result)

    def test_index_show_correct_context(self):
        """Словарь context соотвествует критериям в шаблоне index"""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][first_ogject_number]
        self.correct_post(first_object)

    def test_group_list_show_correct_context(self):
        """Словарь context соотвествует критериям в шаблоне group_list"""
        response = (self.authorized_client
                    .get(reverse('posts:group_list',
                                 kwargs={'slug': self.group.slug})))
        first_object = response.context['page_obj'][first_ogject_number]
        second_object = response.context['group']
        context_data_true_result = {
            second_object.id: self.group.id,
            second_object.title: self.group.title,
            second_object.slug: self.group.slug,
            second_object.description: self.group.description,
        }
        self.correct_post(first_object)
        for context_data, true_result in context_data_true_result.items():
            with self.subTest(context_data=context_data):
                self.assertEqual(context_data, true_result)

    def test_profile_show_correct_context(self):
        """Словарь context соотвествует критериям в шаблоне profile"""
        response = (self.authorized_client
                    .get(reverse('posts:profile',
                                 kwargs={'username': self.user})))
        first_object = response.context['page_obj'][first_ogject_number]
        second_object = response.context['author']
        third_object = response.context['count']
        context_data_true_result = {
            second_object.id: self.user.id,
            second_object: self.user,
            third_object: Post.objects.count(),
        }
        self.correct_post(first_object)
        for context_data, true_result in context_data_true_result.items():
            with self.subTest(context_data=context_data):
                self.assertEqual(context_data, true_result)

    def test_post_detail_show_correct_context(self):
        """Словарь context соотвествует критериям в шаблоне post_detail"""
        response = (self.authorized_client
                    .get(reverse('posts:post_detail',
                                 kwargs={'pk': self.post.id})))
        first_object = response.context['post']
        second_object = response.context['count']
        self.correct_post(first_object)
        self.assertEqual(second_object, Post.objects.count())

    def test_post_edit_show_correct_context(self):
        """Словарь context соотвествует критериям в шаблоне post_edit"""
        response = (self.authorized_client
                    .get(reverse('posts:post_edit', kwargs={'pk':
                                                            self.post.id})))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_createshow_correct_context(self):
        """Словарь context соотвествует критериям в шаблоне create"""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_cache_index(self):
        """Корректно работает кеширование старницыц index"""
        response = self.client.get(reverse('posts:index'))
        posts = response.content
        Post.objects.create(text='Тестовый пост для проверки кеширования',
                            group=self.group,
                            author=self.user)
        response_bas = self.client.get(reverse('posts:index'))
        posts_bas = response_bas.content
        self.assertEqual(posts, posts_bas)
        cache.clear()
        response_new_content = self.client.get(reverse('posts:index'))
        posts_new = response_new_content.content
        self.assertNotEqual(posts, posts_new)

    def test_follow_index_context(self):
        response = self.follower_client.get(reverse('posts:follow_index'))
        first_object = response.context['page_obj'][first_ogject_number]
        self.correct_post(first_object)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        post_count = 13
        for post_number in range(post_count):
            Post.objects.create(author=cls.user,
                                text='Тестовый пост %s' % post_number,
                                group=cls.group)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_index_first_page_contains_ten_records(self):
        """
        Проверка паджинатора на первой странице шаблонов,
        где он используется
        """
        page_names = [reverse('posts:index'),
                      reverse('posts:group_list',
                              kwargs={'slug': self.group.slug}),
                      reverse('posts:profile',
                              kwargs={'username':
                                      PaginatorViewsTest.user.username})]
        for page_name in page_names:
            with self.subTest(page_name=page_name):
                response = self.authorized_client.get(page_name)
                self.assertEqual(len(response.context['page_obj']),
                                 settings.POSTS_PER_PAGE)

    def test_index_second_page_contains_three_records(self):
        """
        Проверка паджинатора на второй странице шаблонов,
        где он используется
        """
        page_names = [reverse('posts:index'),
                      reverse('posts:group_list',
                              kwargs={'slug': self.group.slug}),
                      reverse('posts:profile',
                              kwargs={'username':
                                      self.user.username})]
        for page_name in page_names:
            with self.subTest(page_name=page_name):
                response = (self.authorized_client
                            .get(reverse('posts:index') + '?page=2'))
                self.assertEqual(len(response.context['page_obj']),
                                 (Post.objects.count()
                                  - settings.POSTS_PER_PAGE))
