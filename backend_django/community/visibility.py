from django.db.models import Q
from .models import Post, Comment

def public_posts():
    return Post.objects.filter(moderation_status=Post.MODERATION_APPROVED, deleted_at__isnull=True, author__is_active=True, author__profile__banned_at__isnull=True)

def readable_posts(viewer, own=False):
    query = Post.objects.filter(deleted_at__isnull=True, author__is_active=True, author__profile__banned_at__isnull=True)
    if own and viewer.is_authenticated:
        return query.filter(Q(moderation_status=Post.MODERATION_APPROVED) | Q(author=viewer))
    return public_posts()

def visible_comments():
    return Comment.objects.filter(post__in=public_posts(), is_hidden=False)
