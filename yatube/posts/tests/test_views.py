from django.test import TestCase, Client
from django.urls import reverse
from django import forms
from django.db import models
from django.core.cache import cache
import time

from django.conf import settings
from ..models import Post, Group, User


class TaskPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cache.clear()
        # Создаём авторизованный клиент
        cls.user = User.objects.create_user(username='Test_Username')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

        # Создаём пару пользователей
        cls.user2 = User.objects.create_user(username='Test_Username_2')
        cls.user3 = User.objects.create_user(username='Test_Username_3')

        # Создаём неавторизованый клиент
        cls.guest_client = Client()

        cls.group = Group.objects.create(
            title='Тестовая группа 3',
            slug='test_slug_3',
            description='Тестовый дескрипшн 3'
        )

        # Наполнеям db постами с разными значениями в полях.
        Post.objects.bulk_create(
            Post(author=cls.user, group=cls.group, text=f'Тестовый пост {i}')
            for i in range(1, 9)
        )
        Post.objects.bulk_create(
            Post(author=cls.user, text=f'Тестовый пост {i}')
            for i in range(9, 12)
        )
        Post.objects.bulk_create(
            Post(author=cls.user2, text=f'Тестовый пост {i}')
            for i in range(12, 13)
        )

        # Создаём пост с новым временем публикации.
        time.sleep(0.1)
        cls.post = Post.objects.create(author=cls.user2,
                                       text='Новый Тестовый пост',
                                       group=cls.group)

    def test_namespace(self):
        """URL-адрес использует соответствующий шаблон."""
        cache.clear()
        urls_templates = {
            'posts:index': 'posts/index.html',
            'posts:post_edit': 'posts/create_post.html',
            'posts:post_create': 'posts/create_post.html',
            'posts:profile': 'posts/profile.html',
            'posts:post_detail': 'posts/post_detail.html',
            'posts:group_list': 'posts/group_list.html',
        }
        urls_kwargs = {
            'posts:post_edit': {'post_id': Post.objects.get(pk=8).pk},
            'posts:profile': {'username': Post.objects.get(pk=8).author},
            'posts:post_detail': {'post_id': Post.objects.get(pk=8).pk},
            'posts:group_list': {'slug': self.group.slug},
        }
        for value, expected in urls_templates.items():
            with self.subTest(value=value):
                if value in urls_kwargs.keys():
                    response = self.authorized_client.get(
                        reverse(value, kwargs=urls_kwargs[value])
                    )
                    self.assertTemplateUsed(response, expected)
                else:
                    response = self.authorized_client.get(reverse(value))
                    self.assertTemplateUsed(response, expected)

    def test_index_page_shows_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        cache.clear()
        response = self.guest_client.get(reverse('posts:index'))
        expected = list(Post.objects.all()[:settings.COUNT_OF_MESSAGES])
        self.assertEqual(list(response.context['page_obj']), expected)
        self.assertEqual(
            response.context['page_obj'].object_list[0].text,
            self.post.text
        )

    def test_group_post_shows_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        self.assertEqual(
            len(response.context['page_obj']),
            Post.objects.filter(group=self.group).count()
        )
        self.assertEqual(
            response.context['page_obj'].object_list[0].group,
            self.post.group
        )

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user2.username})
        )
        self.assertEqual(
            len(response.context["page_obj"]),
            Post.objects.filter(author=self.user2).count()
        )
        self.assertEqual(
            response.context['page_obj'].object_list[0].author,
            self.post.author
        )

    def test_profile_page_show_correct_context_second_page(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user.username})
            + '?page=2'
        )
        self.assertEqual(
            len(response.context['page_obj']),
            (Post.objects.filter(author=self.user).count()
             - settings.COUNT_OF_MESSAGES)
        )

    def test_post_detail_shows_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': Post.objects.get(pk=8).pk}
                    )
        )
        self.assertEqual(
            response.context['post'].text,
            Post.objects.get(pk=8).text
        )

    def test_create_post_shows_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон create_post cодержит форму редактирования поста."""
        response = self.authorized_client.get(
            reverse('posts:post_edit',
                    kwargs={'post_id': Post.objects.get(pk=8).pk}
                    )
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_context_has_image_on_pages(self):
        """Изображение содержится в словаре context
           при обращении к главной странице,
           при обращении к странице профайла,
           при обращении к странице группы,
           при обращении к информации о посте.
        """
        cache.clear()
        urls_kwargs = {
            'posts:index': '',
            'posts:profile': {'username': self.user.username},
            'posts:group_list': {'slug': self.group.slug},
            'posts:post_detail': {'post_id': Post.objects.get(pk=8).pk}
        }
        for value, dict_kwargs in urls_kwargs.items():
            with self.subTest(value=value):
                if value == 'posts:post_detail':
                    response = self.authorized_client.get(
                        reverse(value, kwargs=dict_kwargs)
                    )
                    self.assertIsInstance(
                        response.context['post'].image.field,
                        models.fields.files.ImageField
                    )
                elif value == 'posts:index':
                    response = self.authorized_client.get(
                        reverse(value)
                    )
                    page_obj = response.context['page_obj']
                    self.assertIsInstance(
                        page_obj.object_list[0].image.field,
                        models.fields.files.ImageField
                    )
                else:
                    response = self.authorized_client.get(
                        reverse(value, kwargs=dict_kwargs)
                    )
                    page_obj = response.context['page_obj']
                    self.assertIsInstance(
                        page_obj.object_list[0].image.field,
                        models.fields.files.ImageField
                    )

    def test_cache(self):
        """Тестирование работы кеша."""
        response = self.guest_client.get(reverse('posts:index'))
        cache_1 = response.content
        Post.objects.get(id=13).delete()
        response2 = self.guest_client.get(reverse('posts:index'))
        cache_2 = response2.content
        self.assertEqual(cache_1, cache_2)

    def test_follow_function(self):
        """Тестирование механизма подписки и отписки на авторов."""
        # Печатаем количество подписок до запроса
        subscription_count_before = self.user.follower.count()
        # Получаем список подписок первого пользователя
        authors_list_before = self.user.follower.all().values_list(
            'author',
            flat=True
        )
        # Получаем количество постов в ленте первого пользователя
        posts_count_before = Post.objects.filter(
            author__in=authors_list_before
        ).count()
        # Получаем количество подписок третьего пользователя
        authors_list_before_user3 = self.user3.follower.all().values_list(
            'author',
            flat=True
        )
        # Получаем количество постов в ленте третьего пользователя
        posts_count_before_user3 = Post.objects.filter(
            author__in=authors_list_before_user3
        ).count()
        # Первый пользователь подписывается на второго
        self.authorized_client.get(
            reverse('posts:profile_follow', args=(self.user2,))
        )
        # Получаем список авторов первого пользователя после запроса
        authors_list_after = self.user.follower.all().values_list(
            'author',
            flat=True
        )
        # Получаем количество постов в ленте первого пользователя
        posts_count_after = Post.objects.filter(
            author__in=authors_list_after
        ).count()
        # Получаем список авторов третьего пользователя после запроса
        authors_list_after_user3 = self.user3.follower.all().values_list(
            'author',
            flat=True
        )
        # Получаем количество постов в ленте третьего пользователя
        posts_count_after_user3 = Post.objects.filter(
            author__in=authors_list_after_user3
        ).count()
        # Проверка количества подписок первого пользователя
        self.assertEqual(
            self.user.follower.count(),
            subscription_count_before + self.user.follower.count()
        )
        # Проверка количества постов в ленте первого пользователя
        self.assertEqual(
            posts_count_after,
            posts_count_before + posts_count_after
        )
        # Проверка количества постов в ленте третьего пользователя
        self.assertEqual(
            posts_count_after_user3,
            posts_count_before_user3
        )
        # Отписываемся от пользователя 2
        self.authorized_client.get(
            reverse('posts:profile_unfollow', args=(self.user2,))
        )
        # Проверяем количество подписок первого пользователя
        self.assertEqual(
            self.user.follower.count(),
            subscription_count_before
        )
