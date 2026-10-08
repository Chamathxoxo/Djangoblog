from django.urls import path
from .views import (
    PostListView, PostDetailView, PostCreateView,
    PostUpdateView, PostDeleteView, CategoryPostListView,
    RegisterView, about, contact
)

urlpatterns = [
    path("", PostListView.as_view(), name="home"),
    path("register/", RegisterView.as_view(), name="register"),
    path("posts/new/", PostCreateView.as_view(), name="post_create"),
    path("posts/<slug:slug>/edit/", PostUpdateView.as_view(), name="post_edit"),
    path("posts/<slug:slug>/delete/", PostDeleteView.as_view(), name="post_delete"),
    path("posts/<slug:slug>/", PostDetailView.as_view(), name="post_detail"),
    path("category/<str:category_name>/", CategoryPostListView.as_view(), name="category_posts"),
    path("about/", about, name="about"),
    path("contact/", contact, name="contact"),
]