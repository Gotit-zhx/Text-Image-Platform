from django.contrib.auth.models import User
from django.db import models


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar_media = models.ForeignKey('Media',null=True,blank=True,on_delete=models.SET_NULL,related_name='avatar_profiles')
    avatar_url = models.URLField(blank=True, default='')
    gender = models.CharField(max_length=16, default='private')
    muted_until = models.DateTimeField(null=True, blank=True)
    banned_at = models.DateTimeField(null=True, blank=True)
    status_reason = models.CharField(max_length=500, blank=True, default='')
    nickname = models.CharField(max_length=80, blank=True, default='')
    signature = models.CharField(max_length=300, blank=True, default='')
    email_verified = models.BooleanField(default=False)
    requires_verification = models.BooleanField(default=False)

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
    deleted_at = models.DateTimeField(null=True, blank=True)
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
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='children')
    root = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='thread_replies')
    reply_to = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='direct_replies')
    deleted_at = models.DateTimeField(null=True, blank=True)
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


class AccountToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='account_tokens')
    digest = models.CharField(max_length=64, unique=True)
    purpose = models.CharField(max_length=16)
    email = models.EmailField()
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class AuthAttempt(models.Model):
    key = models.CharField(max_length=64, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Media(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='media_assets')
    file = models.FileField(upload_to='uploads/')
    thumbnail = models.FileField(upload_to='thumbnails/')
    width = models.PositiveIntegerField()
    height = models.PositiveIntegerField()
    size = models.PositiveIntegerField()
    format = models.CharField(max_length=8)
    posts = models.ManyToManyField(Post, related_name='media_assets', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Draft(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='drafts')
    title = models.CharField(max_length=255, blank=True, default='')
    summary = models.TextField(blank=True, default='')
    content_html = models.TextField(blank=True, default='')
    tags = models.JSONField(default=list)
    images = models.JSONField(default=list)
    media = models.ManyToManyField(Media, related_name='drafts', blank=True)
    version = models.PositiveIntegerField(default=1)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)


class RequestReceipt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=40)
    key = models.CharField(max_length=80)
    digest = models.CharField(max_length=64)
    target_id = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['user','action','key'], name='unique_request_receipt')]


class UserRelation(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_relations')
    target = models.ForeignKey(User, on_delete=models.CASCADE, related_name='target_relations')
    kind = models.CharField(max_length=8, choices=[('block','拉黑'),('mute','屏蔽')])
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['owner','target','kind'], name='unique_user_relation')]


class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    actor = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name='sent_notifications')
    event = models.CharField(max_length=64)
    target_type = models.CharField(max_length=16)
    target_id = models.PositiveIntegerField()
    post_id = models.PositiveIntegerField(null=True, blank=True)
    comment_id = models.PositiveIntegerField(null=True, blank=True)
    snapshot = models.JSONField(default=dict)
    dedup_key = models.CharField(max_length=180, unique=True)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        indexes = [models.Index(fields=['recipient','-created_at'])]


class Report(models.Model):
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports')
    target_type = models.CharField(max_length=16)
    target_id = models.PositiveIntegerField()
    reason = models.CharField(max_length=64)
    description = models.CharField(max_length=2000, blank=True, default='')
    status = models.CharField(max_length=16, default='open')
    outcome = models.CharField(max_length=500, blank=True, default='')
    resolved_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name='resolved_reports')
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['reporter','target_type','target_id'], name='unique_user_report')]


class Appeal(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appeals')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='appeals')
    description = models.CharField(max_length=2000)
    status = models.CharField(max_length=16, default='open')
    outcome = models.CharField(max_length=500, blank=True, default='')
    resolved_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name='resolved_appeals')
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['author','post'],condition=models.Q(status='open'),name='unique_open_appeal')]
