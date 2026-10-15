from django.contrib import admin
from .models import Post, Category, PostImage, Tag, Comment, Profile


class PostImageInline(admin.TabularInline):
    model = PostImage
    extra = 1
    fields = ("image", "caption", "position", "paragraph")


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("title", "content")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("tags",)
    inlines = [PostImageInline]

    fieldsets = (
        (None, {
            "fields": ("title", "slug", "author", "status", "category", "tags", "content"),
        }),
        ("Main image (top of the post)", {
            "fields": ("image",),
        }),
        ("Optional: cover image (used instead of the main image if set)", {
            "fields": ("cover_image",),
            "classes": ("collapse",),
        }),
    )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("author", "post", "parent", "created_at")
    search_fields = ("text", "author__username")


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "is_verified")
    list_filter = ("is_verified",)