from django.test import TestCase, Client
from ..models import User, Post, Group, Follow
from django.urls import reverse
from django.conf import settings
from django import forms
from ..forms import PostForm
from django.core.files.uploadedfile import SimpleUploadedFile
# Uncomment if cache is activated:
# from django.core.cache import cache
# import time


class PostPagesTests(TestCase):
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
        cls.user = User.objects.create(username='author')
        cls.group = Group.objects.create(
            title='TestGroup',
            slug='testslug',
            description='TestDescription',
        )
        cls.post = Post.objects.create(
            text='TestPost',
            author=cls.user,
            group=cls.group,
            image=cls.uploadedfile,
        )
        post_create_args = ()
        post_edit_args = (cls.post.id)
        group_args = (cls.group.slug)
        profile_args = (cls.user.username)
        index_args = ()
        post_detail_args = (cls.post.id)

        cls.index_url = ('posts:index', 'posts/index.html', index_args)
        cls.post_create_url = ('posts:post_create', 'posts/create_post.html',
                               post_create_args)
        cls.edit_post_url = ('posts:post_edit', 'posts/create_post.html',
                             [post_edit_args])
        cls.group_url = ('posts:group_list', 'posts/group_list.html',
                         [group_args])
        cls.profile_url = ('posts:profile', 'posts/profile.html',
                           [profile_args])
        cls.post_detail_url = ('posts:post_detail', 'posts/post_detail.html',
                               [post_detail_args])

        cls.paginated_urls = (
            cls.index_url,
            cls.group_url,
            cls.profile_url,
        )
        cls.other_urls = (
            cls.post_create_url,
            cls.edit_post_url,
            cls.profile_url,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostPagesTests.user)

    # 1. Template tests
    def test_name_post_edit_correct_template(self):
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        )
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_names_correct_template(self):
        for name, template, args in (PostPagesTests.paginated_urls
                                     + PostPagesTests.other_urls):
            with self.subTest(name=name):
                response = self.authorized_client.get(reverse(name, args=args))
                self.assertTemplateUsed(response,
                                        template,
                                        f'{name} expected {template}')

    # 2. Context tests
    def test_group_list_context(self):
        self.guest_client = Client()
        response = self.guest_client.get(
            reverse(
                'posts:group_list', kwargs={
                    'slug': PostPagesTests.group.slug
                }
            )
        )
        first_object = response.context['page_obj'][0]
        self.assertEqual(
            first_object.text, PostPagesTests.post.text
        )
        self.assertEqual(
            first_object.author, PostPagesTests.user
        )
        self.assertEqual(
            first_object.group, PostPagesTests.group
        )
        self.assertEqual(
            first_object.image, PostPagesTests.post.image
        )

    # 2.1 Create and edit post context tests
    def test_post_create_gets_correct_context(self):
        response = self.authorized_client.get(reverse('posts:post_create'))
        self.assertIn('form', response.context)
        self.assertIsInstance(response.context['form'],
                              PostForm
                              )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField
        }
        for data, classname_data in form_fields.items():
            with self.subTest(data=data):
                self.assertIsInstance(
                    response.context[0]['form'].fields.get(data),
                    classname_data)

    def test_post_edit_gets_correct_context(self):
        response = self.authorized_client.get(reverse('posts:post_edit',
                                              kwargs={'post_id': self.post.id})
                                              )
        self.assertIn('form', response.context)
        self.assertIsInstance(response.context['form'],
                              PostForm
                              )
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
        )
        test_data = response.context.get('is_edit')
        self.assertEqual(test_data, True)

    def test_post_create_correct_placement(self):
        urls_list = [reverse('posts:index'), 'page_obj'],
        [reverse('posts:group_list',
                 kwargs={'slug': self.group.slug}), 'page_obj'],
        [reverse('posts:profile',
                 kwargs={'username': self.user}), 'page_obj'],
        for urls, obj in urls_list:
            with self.subTest(urls=urls):
                response = self.authorized_client.get(urls).context[obj]
                self.assertIn(self.post, response, 'Error: No Post')

    def test_post_correct_creation_in_correct_users_groups(self):
        # Создаем пользователя для проверки assertNotIn()
        self.wrong_user = User.objects.create(username='wrong_user')
        second_group = Group.objects.create(
            title='Second Group', slug='second_group_slug'
        )
        posts_counter = Post.objects.filter(group=self.group).count()
        post = Post.objects.create(
            text="Other author's post",
            author=self.wrong_user,
            group=second_group)
        response_profile = self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': self.user}))
        posts_counter_2 = Post.objects.filter(group=self.group).count()
        profile = response_profile.context['page_obj']
        self.assertEqual(posts_counter_2, posts_counter,
                         'Error: Wrong group post placement found')
        self.assertNotIn(post, profile,
                         'Error: Wrong user post placement found')

    # 2.2 Other context tests
    def check_context(self, context, post):
        if post == 'post':
            self.assertIn('post', context)
            post = context['post']
        elif post == 'page_obj':
            self.assertIn('page_obj', context)
            post = context['page_obj'][0]
        self.assertEqual(post.author, PostPagesTests.user)
        self.assertEqual(post.text, PostPagesTests.post.text)
        self.assertEqual(post.group, PostPagesTests.post.group)
        self.assertEqual(post.image, PostPagesTests.post.image)

    def test_index_group_list_post_detail_have_page_obj_or_post_context(self):
        urls = [
            [reverse('posts:index'), 'page_obj'],
            [reverse('posts:group_list',
                     kwargs={'slug': self.group.slug}), 'page_obj'],
            [reverse('posts:post_detail',
                     kwargs={'post_id': self.post.id}), 'post'],
            [reverse('posts:profile',
                     kwargs={'username': self.user}), 'page_obj'],
        ]
        for url, obj in urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.check_context(response.context, obj)

    def test_guest_client_cannot_comment(self):
        comment_url = reverse('posts:add_comment',
                              kwargs={'post_id': self.post.id})
        self.guest_client = Client()
        response = self.guest_client.get(comment_url)
        url = f'/auth/login/?next={comment_url}'
        self.assertRedirects(response, url, status_code=302)

    def test_authorized_client_can_comment(self):
        comment_url = reverse('posts:add_comment',
                              kwargs={'post_id': self.post.id})
        redirect_url = reverse('posts:post_detail',
                               kwargs={'post_id': self.post.id})
        self.authorized_client = Client()
        test_comment_user = User.objects.create(username='TestCommentUser')
        self.authorized_client.force_login(test_comment_user)
        response = self.authorized_client.post(comment_url,
                                               {'text': 'TestComment'},
                                               follow=True)
        self.assertContains(response, 'TestComment')
        self.assertRedirects(response, redirect_url, status_code=302)

    # IMPORTANT: Uncomment while cache is activated:
    # def test_cache(self):
    #    response = self.authorized_client.get(reverse('posts:index'))
    #    self.assertEqual(response.context, None)
    #    time.sleep(20)
    #    response = self.authorized_client.get(reverse('posts:index'))
    #    self.assertNotEqual(response.context, None)
    #    self.assertEqual(response.context['page_obj'][0].text, 'TestPost')

    def test_follow(self):
        follow_user = User.objects.create(username='TestAuthor')
        self.authorized_client.force_login(follow_user)
        self.authorized_client.get(reverse('posts:profile_follow',
                                           kwargs={'username': self.user}))
        follow = Follow.objects.first()
        self.assertEqual(Follow.objects.count(), 1)
        self.assertEqual(follow.author, self.user)
        self.assertEqual(follow.user, follow_user)

    def test_unfollow(self):
        self.authorized_client.get(reverse('posts:profile_follow',
                                           kwargs={'username': self.user}))
        self.authorized_client.get(reverse('posts:profile_unfollow',
                                           kwargs={'username': self.user}))
        self.assertFalse(Follow.objects.exists())


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(
            username='author',
        )
        cls.group = Group.objects.create(
            title='Test Group',
            slug='test_slug',
            description='Test Description',
        )
        Post.objects.bulk_create(
            Post(
                author=cls.user,
                text=f'Тest post {i}',
                group=cls.group,
            )
            for i in range(12)
        )
        cls.post = Post.objects.latest('created')

    def setUp(self):
        self.client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PaginatorViewsTest.user)

    def test_start_page_posts_quantity(self):
        page_posts_qty = (
            self.authorized_client.get(reverse("posts:index")),
            self.authorized_client.get(
                reverse("posts:group_list", kwargs={"slug": self.group.slug})
            ),
            self.authorized_client.get(
                reverse("posts:profile", kwargs={"username": self.user})
            ),
        )
        for response in page_posts_qty:
            with self.subTest(response=response):
                self.assertEqual(
                    len(response.context['page_obj']), settings.NMB_OF_ITEMS
                )

    def test_second_page_posts_quantity(self):
        page_posts_qty = (
            self.authorized_client.get(reverse("posts:index") + "?page=2"),
            self.authorized_client.get(
                reverse("posts:group_list", kwargs={"slug": self.group.slug})
                + "?page=2",
            ),
            self.authorized_client.get(
                reverse("posts:profile", kwargs={"username": self.user})
                + "?page=2"
            ),
        )
        for response in page_posts_qty:
            with self.subTest(response=response):
                self.assertEqual(len(response.context['page_obj']), 2)
