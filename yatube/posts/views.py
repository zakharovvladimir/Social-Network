from django.shortcuts import render, get_object_or_404, redirect
from .models import Post, Group, User, Follow
from .forms import PostForm, CommentForm
from .utils import paginate_page
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page


@cache_page(20, key_prefix='index_page')
def index(request):
    """Homepage return"""
    posts = Post.objects.select_related('author', 'group').all()
    context = {
        'page_obj': paginate_page(posts, request),
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    """Group page return"""
    group = get_object_or_404(Group, slug=slug)
    posts = group.group_posts.select_related('author').all()
    context = {
        'group': group,
        'posts': posts,
        'page_obj': paginate_page(posts, request),
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    """Profile page return"""
    author = get_object_or_404(User, username=username)
    posts = author.author_posts.select_related('group').all()
    context = {
        'author': author,
        'page_obj': paginate_page(posts, request),
        'following':
            request.user.is_authenticated
            and request.user != author
            and Follow.objects.filter(author=author,
                                      user=request.user).exists(),
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    """Post detail page return"""
    post = get_object_or_404(Post, id=post_id)
    context = {
        'post': post,
        'form': CommentForm(),
        'comments': post.comments.all(),
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_edit(request, post_id):
    """Post edit return"""
    posts = get_object_or_404(Post, id=post_id)
    if request.user != posts.author:
        return redirect('posts:post_detail', post_id)
    form = PostForm(request.POST or None, files=request.FILES or None,
                    instance=posts)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    context = {
        'form': form,
        'is_edit': True,
        'post_id': post_id,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def post_create(request):
    """Post create return"""
    form = PostForm(request.POST or None)
    if form.is_valid():
        new_post = form.save(commit=False)
        new_post.author = request.user
        new_post.save()
        return redirect('posts:profile', new_post.author.username)
    context = {
        'form': form,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    """Add comment return. Get the post and save it in the post variable"""
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    """The posts of the authors that the current user is subscribed to"""
    posts = Post.objects.filter(author__following__user=request.user)
    context = {
        'page_obj': paginate_page(posts, request),
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    """Subscription follow function"""
    author = get_object_or_404(User, username=username)
    if request.user.username == username or Follow.objects.filter(
        user=request.user, author=author
    ).exists():
        return redirect('posts:index')
    follower = Follow.objects.create(
        author=author, user=request.user,
    )
    follower.save()
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    """Subscription unfollow function"""
    author = get_object_or_404(User, username=username)
    following = Follow.objects.filter(user=request.user, author=author)
    if following.exists():
        following.delete()
    return redirect('posts:index')
