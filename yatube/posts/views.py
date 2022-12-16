from django.shortcuts import render, get_object_or_404, redirect
from .models import Post, Group, User, Follow
from .forms import PostForm, CommentForm
from .utils import paginator_context
from django.contrib.auth.decorators import login_required
# Uncomment if cache is activated:
# from django.views.decorators.cache import cache_page


# @cache_page(20, key_prefix='index_page')
def index(request):
    context = {
        'page_obj': paginator_context(Post.objects.all(), request),
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.group_posts.all()
    context = {
        'group': group,
        'posts': posts,
        'page_obj': paginator_context(group.group_posts.all(), request),
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    context = {
        'author': author,
        'page_obj': paginator_context(author.author_posts.all(), request),
        'following':
            request.user.is_authenticated
            and request.user != author
            and Follow.objects.filter(author=author,
                                      user=request.user).exists(),
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    posts = get_object_or_404(Post, id=post_id)
    context = {
        'post': posts,
        'form': CommentForm(),
        'comments': posts.comments.all(),
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_edit(request, post_id):
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
    context = {
        'page_obj': paginator_context(Post.objects.filter(
            author__following__user=request.user), request),
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    follower = Follow()
    if request.user.username == username:
        return redirect('posts:index')
    author = get_object_or_404(User, username=username)
    if Follow.objects.filter(user=request.user, author=author).exists():
        return redirect('posts:index')
    follower.author = author
    follower.user = request.user
    follower.save()
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    following = Follow.objects.filter(user=request.user, author=author)
    if following.exists():
        following.delete()
    return redirect('posts:index')
