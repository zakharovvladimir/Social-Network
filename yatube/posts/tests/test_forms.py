from django.urls import reverse
from ..models import Post, User, Group
from django.test import TestCase, Client
from http import HTTPStatus
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

class FormsTests(TestCase):
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
        cls.group = Group.objects.create(
            title="TestGroup",
            slug="test-slug",
            description="Test Description",
        )

    def setUp(self):
        cache.clear()
        self.user = User.objects.create(username='auth')

    def test_authorized_edit_post(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.post = Post.objects.create(
            author=self.user,
            text='Test Post',
            group=self.group,
            image=self.uploadedfile,
        )
        form_data = {
            'text': 'Test Post',
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        get_post = Post.objects.first()
        self.assertEqual(get_post.text, form_data['text'])
        self.assertEqual(get_post.author, self.post.author)

    def test_authorized_create_post(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        posts_counter = Post.objects.count()
        form_data = {
            'text': 'Form Text',
            'group': self.group.id,
            'image': self.uploadedfile,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response, reverse('posts:profile', kwargs={'username': 'auth'})
        )
        get_post = Post.objects.first()
        self.assertEqual(Post.objects.count(), posts_counter + 1)
        self.assertEqual(get_post.text, form_data['text'])
        self.assertEqual(get_post.author, self.user)

    def test_guest_client_is_redirected(self):
        self.guest_client = Client()
        self.post = Post.objects.create(
            author=self.user,
            text="Test Post",
            group=self.group,
            image=self.uploadedfile
        )
        form_data = {'text': 'Form text',
            'image': self.uploadedfile,}
        response = self.guest_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response,
                             '/auth/login/?next=/posts/1/edit/')

    def test_guest_client_edit_post_restriction(self):
        self.guest_client = Client()
        posts_counter = Post.objects.count()
        form_data = {'text': 'Form text',
                     'group': self.group.id,
                     'image': self.uploadedfile,}
        response = self.guest_client.post(reverse('posts:post_create'),
                                          data=form_data,
                                          follow=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertNotEqual(Post.objects.count(),
                            posts_counter + 1,
                            'Post edit error')
