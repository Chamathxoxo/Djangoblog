from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.db import models
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse_lazy, reverse
from django.views.decorators.http import require_POST
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from .models import Post, Category, Comment
from .forms import PostForm, RegisterForm
from django.http import JsonResponse
from django.contrib.auth.models import User

HOME_TITLE = "DjangoBlog Homepage"


class PostListView(ListView):
    model = Post
    template_name = "blog/post_list.html"
    paginate_by = 6

    def get_queryset(self):
        qs = Post.objects.filter(status="published").order_by("-created_at")
        category_name = self.request.GET.get("category")
        if category_name:
            qs = qs.filter(category__name__iexact=category_name)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = HOME_TITLE
        context["categories"] = Category.objects.all()
        return context


class PostDetailView(DetailView):
    model = Post
    template_name = "blog/post_detail.html"
    context_object_name = "post"
    slug_field = "slug"

    def get_queryset(self):
        post = Post.objects.filter(status="published")
        if self.request.user.is_authenticated:
            post = Post.objects.filter(
                models.Q(status="published") | models.Q(author=self.request.user)
            )
        return post

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = self.object
        context["comments"] = (
            post.comments.filter(parent=None)
            .select_related("author__profile")
            .prefetch_related("likes")
        )
        context["comment_count"] = post.comments.count()
        return context


class CategoryPostListView(ListView):
    model = Post
    template_name = "blog/post_list.html"
    paginate_by = 6

    def get_queryset(self):
        self.category = get_object_or_404(Category, name=self.kwargs["category_name"])
        return Post.objects.filter(status="published", category=self.category).order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = HOME_TITLE
        context["categories"] = Category.objects.all()
        return context


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = "blog/post_form.html"
    login_url = "login"

    def form_valid(self, form):
        form.instance.author = self.request.user
        messages.success(self.request, "Post published successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("post_detail", kwargs={"slug": self.object.slug})


class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = "blog/post_form.html"
    login_url = "login"

    def test_func(self):
        return self.get_object().author == self.request.user

    def form_valid(self, form):
        messages.success(self.request, "Post updated successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("post_detail", kwargs={"slug": self.object.slug})


class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post
    template_name = "blog/post_confirm_delete.html"
    login_url = "login"
    success_url = reverse_lazy("home")

    def test_func(self):
        return self.get_object().author == self.request.user

    def form_valid(self, form):
        messages.success(self.request, "Post deleted.")
        return super().form_valid(form)


class MyPostsView(LoginRequiredMixin, ListView):
    model = Post
    template_name = "blog/my_posts.html"
    paginate_by = 6
    login_url = "login"

    def get_queryset(self):
        return Post.objects.filter(author=self.request.user).order_by("-created_at")


class RegisterView(CreateView):
    form_class = RegisterForm
    template_name = "blog/register.html"
    success_url = "/"

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response


def custom_403(request, exception=None):
    return render(request, "blog/403.html", status=403)


def about(request):
    return render(request, "blog/about.html", {"title": "Us"})


def contact(request):
    return render(request, "blog/contact.html", {"title": "Us"})


def check_username(request):
    username = request.GET.get("username", "").strip()
    taken = User.objects.filter(username=username).exists() if username else False
    return JsonResponse({"taken": taken})


# ---------- Comments ----------

def _is_ajax(request):
    return request.headers.get("x-requested-with") == "XMLHttpRequest"


def _back_to_comment(post, comment=None):
    url = reverse("post_detail", kwargs={"slug": post.slug})
    return redirect(f"{url}#comment-{comment.id}" if comment else f"{url}#comments")


@login_required
@require_POST
def add_comment(request, slug):
    posts = Post.objects.filter(models.Q(status="published") | models.Q(author=request.user))
    post = get_object_or_404(posts, slug=slug)

    text = request.POST.get("text", "").strip()[:1000]
    if not text:
        if _is_ajax(request):
            return JsonResponse({"error": "empty"}, status=400)
        messages.error(request, "Comment can't be empty.")
        return _back_to_comment(post)

    parent = None
    parent_id = request.POST.get("parent")
    if parent_id:
        parent = get_object_or_404(Comment, pk=parent_id, post=post)
        # replies stay one level deep, like YouTube
        if parent.parent_id:
            text = f"@{parent.author.username} {text}"
            parent = parent.parent

    comment = Comment.objects.create(post=post, author=request.user, parent=parent, text=text)

    if _is_ajax(request):
        html = render_to_string(
            "blog/_comment.html",
            {
                "c": comment,
                "is_reply": comment.parent_id is not None,
                "post": post,
            },
            request=request,
        )
        return JsonResponse({
            "html": html,
            "id": comment.id,
            "parent": comment.parent_id,
            "count": post.comments.count(),
        })
    return _back_to_comment(post, comment)


@login_required
@require_POST
def toggle_like(request, pk):
    comment = get_object_or_404(Comment, pk=pk)

    # only the owner of the post can heart comments
    if request.user != comment.post.author:
        raise PermissionDenied

    if comment.likes.filter(pk=request.user.pk).exists():
        comment.likes.remove(request.user)
        liked = False
    else:
        comment.likes.add(request.user)
        liked = True

    if _is_ajax(request):
        return JsonResponse({"liked": liked})
    return _back_to_comment(comment.post, comment)


@login_required
@require_POST
def toggle_pin(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    post = comment.post

    # only the owner of the post can pin, and only top-level comments
    if request.user != post.author or comment.parent_id:
        raise PermissionDenied

    if comment.is_pinned:
        comment.is_pinned = False
    else:
        # only one pinned comment per post
        post.comments.filter(is_pinned=True).update(is_pinned=False)
        comment.is_pinned = True
    comment.save(update_fields=["is_pinned"])

    if _is_ajax(request):
        order = list(post.comments.filter(parent=None).values_list("id", flat=True))
        return JsonResponse({
            "pinned_id": comment.id if comment.is_pinned else None,
            "order": order,
        })
    return _back_to_comment(post, comment)


@login_required
@require_POST
def delete_comment(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    # the comment's writer, or the owner of the post, can delete it
    if request.user != comment.author and request.user != comment.post.author:
        raise PermissionDenied

    post = comment.post
    deleted_ids = [comment.id] + list(comment.replies.values_list("id", flat=True))
    comment.delete()

    if _is_ajax(request):
        return JsonResponse({"deleted": deleted_ids, "count": post.comments.count()})
    messages.success(request, "Comment deleted.")
    return _back_to_comment(post)