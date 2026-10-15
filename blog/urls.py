from django.urls import path
from .views import (
    PostListView, PostDetailView, PostCreateView,
    PostUpdateView, PostDeleteView, CategoryPostListView,
    RegisterView, MyPostsView, check_username, about, contact,
    add_comment, toggle_like, toggle_pin, delete_comment,
)

urlpatterns = [
    path("", PostListView.as_view(), name="home"),
    path("my-posts/", MyPostsView.as_view(), name="my_posts"),
    path("register/", RegisterView.as_view(), name="register"),
    path("check-username/", check_username, name="check_username"),
    path("posts/new/", PostCreateView.as_view(), name="post_create"),
    path("posts/<slug:slug>/edit/", PostUpdateView.as_view(), name="post_edit"),
    path("posts/<slug:slug>/delete/", PostDeleteView.as_view(), name="post_delete"),
    path("posts/<slug:slug>/comment/", add_comment, name="comment_add"),
    path("posts/<slug:slug>/", PostDetailView.as_view(), name="post_detail"),
    path("comments/<int:pk>/like/", toggle_like, name="comment_like"),
    path("comments/<int:pk>/pin/", toggle_pin, name="comment_pin"),
    path("comments/<int:pk>/delete/", delete_comment, name="comment_delete"),
    path("category/<str:category_name>/", CategoryPostListView.as_view(), name="category_posts"),
    path("about/", about, name="about"),
    path("contact/", contact, name="contact"),
]