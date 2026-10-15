from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.text import slugify
from PIL import Image
from django.conf import settings


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    is_verified = models.BooleanField(default=False, help_text="Shows a verified tick next to the name.")

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.avatar:
            img = Image.open(self.avatar.path)
            if img.height > 300 or img.width > 300:
                img.thumbnail((300, 300))
                img.save(self.avatar.path)

    def __str__(self):
        return f"{self.user.username}'s profile"


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


class Post(models.Model):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("published", "Published"),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    cover_image = models.ImageField(upload_to="post_covers/", blank=True, null=True)
    content = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="published")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="posts")
    tags = models.ManyToManyField(Tag, blank=True, related_name="posts")
    image = models.ImageField(upload_to="post_images/", blank=True, null=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="posts")

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Post.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

        if self.image:
            img = Image.open(self.image.path)
            if img.height > 1200 or img.width > 1200:
                img.thumbnail((1200, 1200))
                img.save(self.image.path, quality=85, optimize=True)

        if self.cover_image:
            img = Image.open(self.cover_image.path)
            if img.height > 800 or img.width > 800:
                img.thumbnail((800, 800))
                img.save(self.cover_image.path)

    def body_blocks(self):
        """Split the content into paragraphs and attach each extra image
        to the paragraph it belongs to."""
        text = self.content.replace("\r\n", "\n")
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        images = list(self.images.all())
        blocks = [
            {"text": p, "images": [img for img in images if img.paragraph == i]}
            for i, p in enumerate(paragraphs, start=1)
        ]
        if blocks:
            last = len(paragraphs)
            blocks[-1]["images"] += [img for img in images if img.paragraph > last]
        return blocks

    def __str__(self):
        return self.title


class PostImage(models.Model):
    POSITIONS = [("left", "Left"), ("right", "Right"), ("center", "Full width")]

    post = models.ForeignKey(Post, related_name="images", on_delete=models.CASCADE)
    image = models.ImageField(upload_to="post_extra_images/")
    caption = models.CharField(max_length=200, blank=True)
    position = models.CharField(max_length=6, choices=POSITIONS, default="right")
    paragraph = models.PositiveIntegerField(
        "Paragraph #",
        default=1,
        help_text="The image appears next to this paragraph (1 = first).",
    )

    class Meta:
        ordering = ["paragraph", "id"]
        verbose_name = "extra image"
        verbose_name_plural = "extra images"

    def __str__(self):
        return self.caption or "Extra image"


class Comment(models.Model):
    post = models.ForeignKey(Post, related_name="comments", on_delete=models.CASCADE)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="comments", on_delete=models.CASCADE)
    parent = models.ForeignKey("self", null=True, blank=True, related_name="replies", on_delete=models.CASCADE)
    text = models.TextField(max_length=1000)
    likes = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="liked_comments", blank=True)
    is_pinned = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # pinned comment first, then newest first
        ordering = ["-is_pinned", "-created_at"]

    def is_by_post_author(self):
        return self.author_id == self.post.author_id

    def liked_by_post_author(self):
        return self.likes.filter(pk=self.post.author_id).exists()

    def ordered_replies(self):
        return self.replies.select_related("author__profile").order_by("created_at")

    def __str__(self):
        return f"{self.author.username}: {self.text[:40]}"