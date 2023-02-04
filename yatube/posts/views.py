from django.conf import settings
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth import get_user_model
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.detail import DetailView
from django.views.generic.edit import UpdateView, CreateView
from django.urls import reverse
from django.views import View

from .models import Group, Post, Follow
from .forms import PostForm, CommentForm

User = get_user_model()


class IndexView(ListView):
    paginate_by = settings.POSTS_PER_PAGE
    model = Post
    template_name = 'posts/index.html'
    extra_context = {'index': True}


class GroupPostsView(ListView):
    paginate_by = settings.POSTS_PER_PAGE
    template_name = 'posts/group_list.html'

    def get_queryset(self):
        self.group = get_object_or_404(Group, slug=self.kwargs['slug'])
        return self.group.posts.select_related()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['group'] = self.group
        return context


class ProfileView(ListView):
    paginate_by = settings.POSTS_PER_PAGE
    template_name = 'posts/profile.html'

    def get_queryset(self):
        self.author = get_object_or_404(User, username=self.kwargs['username'])
        self.posts = self.author.posts.select_related()
        return self.posts

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['author'] = self.author
        context['count'] = self.posts.count()
        following = False
        if self.request.user.is_authenticated:
            following = Follow.objects.filter(author=self.author,
                                              user=self.request.user).exists()
        context['following'] = following
        return context


class PostDetailView(DetailView):
    model = Post
    context_object_name = 'post'
    form_class = CommentForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm(self.request.POST)
        context['comments'] = self.get_object().comments.select_related()
        context['count'] = self.get_object().author.posts.count()
        return context


class AddCommentView(LoginRequiredMixin, CreateView):
    form_class = CommentForm

    def get_success_url(self):
        return reverse('posts:post_detail', kwargs={'pk': self.kwargs['pk']})

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = get_object_or_404(Post, id=self.kwargs['pk'])
        return super().form_valid(form)


class PostCreateView(LoginRequiredMixin, CreateView):
    template_name = 'posts/create_post.html'
    form_class = PostForm
    model = Post

    def get_success_url(self):
        return reverse('posts:profile', kwargs={'username':
                                                self.request.user.username})

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostEditView(LoginRequiredMixin, UpdateView):
    template_name = 'posts/create_post.html'
    form_class = PostForm
    model = Post

    def get_success_url(self):
        return reverse('posts:post_detail', kwargs={'pk':
                                                    self.kwargs['pk']})

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if request.user.is_authenticated and obj.author != self.request.user:
            return redirect('posts:post_detail', pk=self.kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)


class FollowIndexView(LoginRequiredMixin, ListView):
    paginate_by = settings.POSTS_PER_PAGE
    template_name = 'posts/follow.html'
    extra_context = {'follow': True}

    def get_queryset(self):
        return Post.objects.filter(author__following__user=self.request.user)


class ProfileFollowView(LoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        author = get_object_or_404(User, username=self.kwargs['username'])
        if author != request.user:
            Follow.objects.get_or_create(user=request.user, author=author)
        return redirect('posts:profile', username=self.kwargs['username'])


class ProfileUnfollowView(LoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        author = get_object_or_404(User, username=self.kwargs['username'])
        Follow.objects.filter(user=request.user, author=author).delete()
        return redirect('posts:profile', username=self.kwargs['username'])
