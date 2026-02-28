from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from community.models import Comment, Follow, Post, PostInteraction, Profile


class Command(BaseCommand):
    help = '初始化联调演示数据（用户/帖子/互动/评论）'

    def handle(self, *args, **options):
        users = []
        for idx in range(1, 21):
            username = f'用户{idx}'
            email = f'demo_user_{idx}@example.com'
            user, _ = User.objects.get_or_create(username=username, defaults={'email': email})
            user.set_password('123456')
            user.email = email
            user.save(update_fields=['password', 'email'])
            Profile.objects.get_or_create(user=user)
            users.append(user)

        topics = [
            ['摄影', '夜景', '街拍'],
            ['手账', '模板', '效率'],
            ['徒步', '旅行', '装备'],
            ['咖啡', '拉花', '日常'],
            ['编程', '前端', '后端'],
            ['读书', '笔记', '成长'],
        ]

        posts = []
        for u_idx, user in enumerate(users, start=1):
            post_count = (u_idx * 7) % 21
            for p_idx in range(post_count):
                title = f'{user.username} 的演示帖子 {p_idx + 1}'
                tags = topics[(u_idx + p_idx) % len(topics)]
                post, _ = Post.objects.get_or_create(
                    title=title,
                    defaults={
                        'author': user,
                        'summary': f'演示数据：{user.username} 的第 {p_idx + 1} 篇文章',
                        'content_html': f'<p>{title} 正文演示内容</p>',
                        'tags': tags,
                        'images': ['linear-gradient(135deg, #8ec5fc, #e0c3fc)'] if p_idx % 3 == 0 else [],
                    },
                )
                posts.append(post)

        viewer = users[-1]
        for followee in users[:10]:
            if followee.id != viewer.id:
                Follow.objects.get_or_create(follower=viewer, followee=followee)

        for idx, post in enumerate(posts):
            interaction, _ = PostInteraction.objects.get_or_create(user=viewer, post=post)
            interaction.is_liked = idx % 2 == 0
            interaction.is_favorited = idx % 3 == 0
            interaction.save(update_fields=['is_liked', 'is_favorited'])

            if idx % 4 == 0:
                Comment.objects.get_or_create(post=post, author=viewer, content='联调评论样本')

            post.likes_count = PostInteraction.objects.filter(post=post, is_liked=True).count()
            post.comments_count = Comment.objects.filter(post=post).count()
            post.save(update_fields=['likes_count', 'comments_count'])

        self.stdout.write(self.style.SUCCESS('演示数据初始化完成：20 个用户，单用户 0~20 篇文章。默认密码：123456'))
