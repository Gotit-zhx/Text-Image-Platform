from django.contrib.auth.models import User
from django.db import models


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar_url = models.URLField(blank=True, default='')
    gender = models.CharField(max_length=16, default='private')

    def __str__(self):
        return self.user.username


class Post(models.Model):
    MODERATION_PENDING = 'pending'
    MODERATION_APPROVED = 'approved'
    MODERATION_REJECTED = 'rejected'
    MODERATION_OFFLINE = 'offline'
    MODERATION_CHOICES = [
        (MODERATION_PENDING, '待审核'),
        (MODERATION_APPROVED, '已通过'),
        (MODERATION_REJECTED, '已驳回'),
        (MODERATION_OFFLINE, '已下架'),
    ]

    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    title = models.CharField(max_length=255)
    summary = models.TextField(blank=True, default='')
    content_html = models.TextField(blank=True, default='')
    tags = models.JSONField(default=list, blank=True)
    images = models.JSONField(default=list, blank=True)
    likes_count = models.PositiveIntegerField(default=0)
    comments_count = models.PositiveIntegerField(default=0)
    moderation_status = models.CharField(max_length=16, choices=MODERATION_CHOICES, default=MODERATION_APPROVED)
    review_reason = models.TextField(blank=True, default='')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_posts')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class PostInteraction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_interactions')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='interactions')
    is_read = models.BooleanField(default=False)
    is_liked = models.BooleanField(default=False)
    is_favorited = models.BooleanField(default=False)
    is_shared = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'post')


class Follow(models.Model):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following_relations')
    followee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='follower_relations')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'followee')


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    likes_count = models.PositiveIntegerField(default=0)
    is_hidden = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class CommentLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comment_likes')
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='likes')

    class Meta:
        unique_together = ('user', 'comment')


class AuditLog(models.Model):
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    action = models.CharField(max_length=64)
    target_type = models.CharField(max_length=64)
    target_id = models.PositiveIntegerField(default=0)
    detail = models.JSONField(default=dict, blank=True)
    ip = models.CharField(max_length=64, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
