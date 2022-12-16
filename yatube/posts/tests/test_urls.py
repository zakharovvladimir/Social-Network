from django.test import TestCase, Client
from ..models import Group, Post, User
from http import HTTPStatus


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="auth")
        cls.group = Group.objects.create(
            title="Test Group",
            slug="test-slug",
            description="Test Description",
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text="Test Post",
            group=cls.group,
        )

    def test_urls_correct_template(self):
        self.author = Client()
        self.author.force_login(PostURLTests.user)
        templates_urls = (
            ('/', 'posts/index.html'),
            (f'/group/{PostURLTests.group.slug}/', 'posts/group_list.html'),
            (f'/profile/{PostURLTests.user.username}/', 'posts/profile.html'),
            (f'/posts/{PostURLTests.post.id}/', 'posts/post_detail.html'),
            ('/create/', 'posts/create_post.html'),
            (f'/posts/{PostURLTests.post.id}/edit/', 'posts/create_post.html')
        )
        for address, template in templates_urls:
            with self.subTest(address=address):
                response = self.author.get(address)
                self.assertTemplateUsed(response, template)

    def test_urls_code_200(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author = Client()
        self.author.force_login(PostURLTests.user)
        urls_code_200 = (
            '/',
            f'/group/{PostURLTests.group.slug}/',
            f'/profile/{PostURLTests.user.username}/',
            f'/posts/{PostURLTests.post.id}/',
        )
        for address in urls_code_200:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                response = self.author.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_code_404(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author = Client()
        self.author.force_login(PostURLTests.user)
        response = self.guest_client.get('/none_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        response = self.authorized_client.get('/none_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        response = self.author.get('/none_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_404_template(self):
        self.guest_client = Client()
        response = self.guest_client.get('/pagenotfound/', follow=True)
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, 'core/404.html')

    def test_authors_edit_ability(self):
        self.author = Client()
        self.author.force_login(PostURLTests.user)
        response = self.author.get(f'/posts/{PostURLTests.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_post_ability(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        response = self.authorized_client.get("/create/")
        self.assertEqual(response.status_code, HTTPStatus.OK)


class StaticURLSTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_homepage(self):
        response = self.guest_client.get('/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_about_author(self):
        response = self.guest_client.get('/about/author/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_tech(self):
        response = self.guest_client.get('/about/tech/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
