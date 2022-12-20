from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from ..models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploadedfile = SimpleUploadedFile(
            name='sample.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Test Group',
            slug='Test Slug',
            description='Test Description',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='This is the Super Post Test',
            image=cls.uploadedfile,
        )

    def test_models_correct_object_names(self):
        correct_names = {
            self.post.text[:15]: str(self.post),
            self.group.title: str(self.group),
        }
        for object, correct_name in correct_names.items():
            with self.subTest(correct_names=correct_names):
                self.assertEqual(correct_name, object)
