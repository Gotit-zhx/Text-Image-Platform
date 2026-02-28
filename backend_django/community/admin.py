from django.contrib import admin

from .models import Comment, CommentLike, Follow, Post, PostInteraction, Profile

admin.site.register(Profile)
admin.site.register(Post)
admin.site.register(PostInteraction)
admin.site.register(Comment)
admin.site.register(CommentLike)
admin.site.register(Follow)
