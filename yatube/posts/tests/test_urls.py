from django.test import TestCase, Client
from http import HTTPStatus
from django.core.cache import cache

from ..models import Post, Group, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создаём авторизованный клиент
        cls.user = User.objects.create_user(username='Test_Username')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        # Создаём авторизованный клиент 2
        cls.user2 = User.objects.create_user(username='Test_Username_2')
        cls.authorized_client_2 = Client()
        cls.authorized_client_2.force_login(cls.user2)
        # Создаём неавторизованый клиент
        cls.guest_client = Client()

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовый дескрипшн'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='0123456789123456789',
            group=cls.group
        )

    def test_pages_reachability(self):
        """Проверка доступности существующих страниц."""
        app_pages = [
            '/',
            f'/group/{self.group.slug}/',
            f'/profile/{self.user.username}/',
            f'/posts/{self.post.pk}/',
            '/create/',
            f'/posts/{self.post.pk}/edit/',
            '/unexixting_page/',
        ]
        # Список страниц на которых требуется авторизация
        pages_for_authorized_client = [
            '/create/',
            f'/posts/{self.post.pk}/edit/',
        ]
        for url in app_pages:
            with self.subTest(url=url):
                if url == '/unexixting_page/':
                    response = self.guest_client.get(url)
                    self.assertEqual(response.status_code,
                                     HTTPStatus.NOT_FOUND)
                    self.assertTemplateUsed(response, 'core/404.html')
                elif url in pages_for_authorized_client:
                    response = self.authorized_client.get(url)
                    self.assertEqual(response.status_code, HTTPStatus.OK)
                else:
                    response = self.guest_client.get(url)
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_users_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        cache.clear()
        url_template_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user.username}/': 'posts/profile.html',
            f'/posts/{self.post.pk}/': 'posts/post_detail.html',
            f'/posts/{self.post.pk}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        # Список страниц на которых требуется авторизация
        pages_for_authorized_client = [
            '/create/',
            f'/posts/{self.post.pk}/edit/',
        ]
        for url, template in url_template_names.items():
            with self.subTest(url=url):
                if url in pages_for_authorized_client:
                    response = self.authorized_client.get(url)
                    self.assertTemplateUsed(response, template)
                else:
                    response = self.guest_client.get(url)
                    self.assertTemplateUsed(response, template)

    def test_post_edit_page(self):
        """Проверка редиректов у анонимного пользователя и авторизованного
           пользователя не автора поста.
        """
        response = self.guest_client.get(f'/posts/{self.post.pk}/edit/')
        self.assertRedirects(
            response,
            f'/auth/login/?next=/posts/{self.post.pk}/edit/'
        )
        response = self.authorized_client_2.get(f'/posts/{self.post.pk}/edit/')
        self.assertRedirects(response, f'/posts/{self.post.pk}/')

    def test_add_comment_guest_and_authorized_client(self):
        """Проверка редиректа для анонимного и авторизованного пользователя
           при попытке создать комментарий.
        """
        response = self.guest_client.get(f'/posts/{self.post.pk}/comment/')
        self.assertRedirects(
            response,
            f'/auth/login/?next=/posts/{self.post.pk}/comment/'
        )
        response = self.authorized_client_2.get(
            f'/posts/{self.post.pk}/comment/'
        )
        self.assertRedirects(response, f'/posts/{self.post.pk}/')
