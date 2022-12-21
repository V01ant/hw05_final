from django.test import TestCase

from ..models import Post, Group, User


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='testgroup',
            description='Группа для теста'
        )

    def test_model_have_correct_object_name(self):
        """Проверяем что у модели group корректно работает __str__."""
        group = GroupModelTest.group
        expected_object_name = group.title
        self.assertEqual(expected_object_name, str(group))


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа 2',
            slug='testgroup2',
            description='Группа для теста 2'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='0123456789123456789',
        )

    def test_model_have_correct_object_name(self):
        """Проверяем что у модели Post корректно работает __str__."""
        post = PostModelTest.post
        expected_object_name = post.text[:15]
        self.assertEqual(expected_object_name, str(post))

    def test_model_have_verbous_name(self):
        """Проверяем что у полей модели Post есть атрибут verbous_name."""
        post = PostModelTest.post
        field_verbose_name = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
        }
        for value, expected in field_verbose_name.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).verbose_name, expected)

    def test_model_have_help_text(self):
        """Проверяем что у полей модели Post есть атрибут help_text."""
        post = PostModelTest.post
        field_help_text = {
            'text': 'Введите текст поста',
            'group': 'Группа, к которой будет относиться пост',
        }
        for value, expected in field_help_text.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).help_text, expected)
