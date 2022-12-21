import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, override_settings
from django.urls import reverse

from ..models import Post, Group, User, Comment


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создаём авторизованный клиент
        cls.user = User.objects.create_user(username='Test_Username')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

        cls.group = Group.objects.create(
            title='Тестовая группа 4',
            slug='test_slug_4',
            description='Тестовый дескрипшн 4'
        )

        cls.group2 = Group.objects.create(
            title='Новая тестовая группа',
            slug='test_slug_5',
            description='Дескрипшн новой тестовой группы'
        )

        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )
        cls.post1 = Post.objects.create(
            author=cls.user,
            text='Второй тестовый пост',
            group=cls.group,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_send_post_with_image(self):
        """При отправке поста с картинкой создаётся запись в db."""
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Новейший тестовый пост',
            'author': self.user,
            'group': self.group.pk,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response, reverse('posts:profile',
                              kwargs={'username': self.post.author})
        )
        self.assertEqual(
            Post.objects.count(),
            posts_count + 1
        )
        self.assertTrue(
            Post.objects.filter(image='posts/small.gif').exists()
        )

    def test_create_post_form(self):
        """Валидная форма create_post создаёт новую запись в db."""
        form_data = {
            'text': 'Новый тестовый пост',
            'author': self.user,
            'group': self.group.pk,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse('posts:profile',
                              kwargs={'username': self.post.author})
        )
        self.assertEqual(
            Post.objects.latest('pub_date').author,
            self.user
        )
        self.assertEqual(
            Post.objects.latest('pub_date').group,
            self.group
        )

    def test_edit_post_form(self):
        """Валидная форма post_edit редактирует пост с post_id в bd."""
        post_count = Post.objects.count()
        form_data = {
            'text': 'Отредактированный второй тестовый пост',
            'group': self.group2.pk,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post1.pk}),
            data=form_data,
            follow=True
        )
        old_group_response = self.authorized_client.get(
            reverse('posts:group_list', args=(self.group.slug,))
        )
        new_group_response = self.authorized_client.get(
            reverse('posts:group_list', args=(self.group2.slug,))
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': self.post1.pk})
        )
        self.assertEqual(
            Post.objects.count(), post_count
        )
        self.assertEqual(
            Post.objects.get(
                text='Отредактированный второй тестовый пост'
            ).text,
            form_data['text']
        )
        self.assertEqual(
            old_group_response.context['page_obj'].paginator.count, 0
        )
        self.assertEqual(
            new_group_response.context['page_obj'].paginator.count, 1
        )

    def test_comments(self):
        """Авторизованный пользователь создаёт комментарий в db."""
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Текст комментария!',
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post1.pk}),
            data=form_data,
            follow=True
        )
        self.assertEqual(
            response.context["post"].comments.count(),
            comments_count + 1
        )
        self.assertEqual(
            response.context["post"].comments.values()[0]["text"],
            form_data['text']
        )
