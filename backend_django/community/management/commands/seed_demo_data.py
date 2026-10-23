"""Create a polished, local-only demonstration community.

The image files are checked-in public-domain/CC0 downloads under ``demo_assets``.
This command only removes accounts whose usernames are in the demo namespace;
it never deletes staff or superuser accounts.
"""

from pathlib import Path
import re

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from PIL import Image

from community.models import Comment, Follow, Media, Post, PostInteraction, Profile


DEMO_USERNAMES = {
    'demo_muyu', 'demo_shanlu', 'demo_kafei', 'demo_shuye', 'demo_chengshi',
    'demo_yuanfang', 'demo_suishou', 'demo_guangying', 'demo_qingchen',
}
LEGACY_DEMO_PATTERN = re.compile(r'^(?:demo_\d+|用户\d+)$')


class Command(BaseCommand):
    help = '重建本地演示内容：清理旧演示账号，导入公开图片并生成社区数据'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset', action='store_true',
            help='清理旧的本地演示账号和内容后再生成；不会删除 staff/superuser。',
        )

    def handle(self, *args, **options):
        if options['reset']:
            self._reset_demo_data()

        asset_dir = Path(__file__).resolve().parents[4] / 'demo_assets'
        image_names = [
            'mongolia-landscape.jpg', 'coffee-cup.jpg', 'street-craftsman.jpg',
            'hiking-trip.jpg', 'market-food.jpg', 'elephant-clock.jpg',
        ]
        missing = [name for name in image_names if not (asset_dir / name).is_file()]
        if missing:
            self.stderr.write(self.style.ERROR(
                '缺少 demo_assets 图片：' + ', '.join(missing) +
                '。请先获取 docs/demo-media-sources.md 中列出的公开素材。'
            ))
            return

        people = [
            ('demo_muyu', '木鱼', '记录城市和自然之间的慢节奏。'),
            ('demo_shanlu', '山路观察员', '周末去山里，平时在地图上做功课。'),
            ('demo_kafei', '咖啡实验室', '把每一杯咖啡的变量写下来。'),
            ('demo_shuye', '书页之间', '读书、做笔记，也分享一些安静时刻。'),
            ('demo_chengshi', '小城散步', '街角、菜市场和下班后的风。'),
            ('demo_yuanfang', '远方来信', '把旅途中看到的细节带回来。'),
            ('demo_suishou', '随手记', '不追求完整，只记录真实发生过的事。'),
            ('demo_guangying', '光影练习生', '练习观察光如何改变一张照片。'),
            ('demo_qingchen', '清晨六点', '早起的人，先看到一天的颜色。'),
        ]

        users = []
        for username, nickname, signature in people:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={'email': f'{username}@example.com'},
            )
            if created:
                user.set_password('DemoGarden!2026')
                user.save(update_fields=['password'])
            Profile.objects.update_or_create(
                user=user,
                defaults={'nickname': nickname, 'signature': signature, 'email_verified': True},
            )
            users.append(user)

        assets = self._load_assets(users, asset_dir, image_names)
        posts = self._create_posts(users, assets)
        self._create_relationships(users)
        self._create_interactions(users, posts)
        self._create_comments(users, posts)
        self._refresh_counts(posts)

        self.stdout.write(self.style.SUCCESS(
            f'演示内容已更新：{len(users)} 位创作者、{len(posts)} 篇帖子、'
            f'{len(assets)} 张公开图片。演示账号密码仍为 DemoGarden!2026。'
        ))

    def _reset_demo_data(self):
        demo_users = User.objects.filter(username__in=DEMO_USERNAMES)
        legacy_users = User.objects.filter(username__regex=r'^(demo_[0-9]+|用户[0-9]+)$')
        users = (demo_users | legacy_users).distinct()
        Post.objects.filter(author__in=users).delete()
        users.delete()
        Media.objects.filter(owner__username__in=DEMO_USERNAMES).delete()
        self.stdout.write('已清理旧演示账号、帖子、评论和互动；保留 staff/superuser。')

    def _load_assets(self, users, asset_dir, image_names):
        assets = []
        for index, filename in enumerate(image_names):
            owner = users[index % len(users)]
            payload = (asset_dir / filename).read_bytes()
            with Image.open(asset_dir / filename) as image:
                width, height = image.size
                image_format = image.format or 'JPEG'
            media, _ = Media.objects.get_or_create(
                owner=owner,
                file=f'uploads/demo/{filename}',
                defaults={'width': width, 'height': height, 'size': len(payload), 'format': image_format},
            )
            if not media.thumbnail or not media.thumbnail.storage.exists(media.thumbnail.name):
                media.thumbnail.save(f'{Path(filename).stem}-thumb.jpg', ContentFile(payload), save=False)
            if media.width != width or media.height != height or media.size != len(payload):
                media.width, media.height, media.size, media.format = width, height, len(payload), image_format
            if not media.file or not media.file.storage.exists(media.file.name):
                media.file.save(f'demo/{filename}', ContentFile(payload), save=False)
            media.save()
            assets.append(media)
        return assets

    def _create_posts(self, users, assets):
        entries = [
            ('沿着草原的风走一段', '旅行', '在地图上看了很久的路，真正走进去以后，最先记住的却是风的方向。', [0]),
            ('一杯咖啡的三个变量', '咖啡', '同一支豆子，水温、研磨度和等待时间稍微变化，杯子里的层次就完全不同。', [1]),
            ('街角手艺人的下午', '城市', '在市场拐角遇到一位修理旧物的师傅。手艺让时间变慢，也让一件东西重新获得价值。', [2]),
            ('给周末留一条山路', '徒步', '不赶日落，也不设置必须抵达的终点。带上水和一件薄外套，走到想停下的地方。', [3]),
            ('菜市场的颜色练习', '日常', '红色的番茄、绿色的香草和一块旧木板，生活本身就是很好的构图课。', [4]),
            ('一本旧书的边角', '阅读', '书页有被翻过的痕迹，才像真正进入过某个人的生活。今天读到一句话，想留在这里。', [5]),
            ('不带计划的城市散步', '街拍', '从一条不熟悉的街开始，走过三家小店和一座没有名字的小桥。', [2, 4]),
            ('清晨六点的光', '摄影', '同一个窗台，在清晨和傍晚有两种完全不同的情绪。光线会替我们记录时间。', [0, 1]),
            ('把旅行收进一张清单', '攻略', '轻装出发，留下余地。真正有用的清单，应该让人更自由，而不是更紧张。', [3, 5]),
            ('今晚做一顿简单的饭', '生活', '不复杂的食材也能让一天有一个温柔的收尾。', [4]),
            ('读完一本书以后', '笔记', '合上书并不代表结束，真正有用的部分常常发生在第二天的行动里。', [5]),
            ('把喜欢的风景分享出去', '随手记', '有些照片不需要解释，看到它的时候，心里会先亮一下。', [0]),
        ]
        posts = []
        for index, (title, tag, summary, image_indexes) in enumerate(entries):
            author = users[index % len(users)]
            post, _ = Post.objects.update_or_create(
                author=author,
                title=title,
                defaults={
                    'summary': summary,
                    'content_html': f'<p>{summary}</p><p>这是百草园本地演示内容，欢迎在评论区分享你的经验和看法。</p>',
                    'tags': [tag, '生活记录'],
                    'moderation_status': Post.MODERATION_APPROVED,
                    'deleted_at': None,
                },
            )
            selected = [assets[i] for i in image_indexes]
            post.media_assets.set(selected)
            post.images = [f'/media/{asset.pk}/image' for asset in selected]
            post.save(update_fields=['images', 'updated_at', 'moderation_status', 'deleted_at'])
            posts.append(post)
        return posts

    def _create_relationships(self, users):
        for index, user in enumerate(users):
            for step in (1, 2, 3):
                Follow.objects.get_or_create(follower=user, followee=users[(index + step) % len(users)])

    def _create_interactions(self, users, posts):
        for index, user in enumerate(users):
            for post in posts[index % len(posts)::3]:
                interaction, _ = PostInteraction.objects.get_or_create(user=user, post=post)
                interaction.is_liked = (post.id + index) % 3 != 0
                interaction.is_favorited = (post.id + index) % 4 == 0
                interaction.save(update_fields=['is_liked', 'is_favorited'])

    def _create_comments(self, users, posts):
        texts = [
            '这段记录很有画面感，收藏下来周末试试。',
            '同感，最近也在练习放慢一点。',
            '谢谢分享，尤其喜欢你写的细节。',
            '这个方法我还没试过，准备照着做一次。',
            '照片和文字的节奏很舒服。',
        ]
        for index, post in enumerate(posts):
            for offset in range(2):
                author = users[(index + offset + 1) % len(users)]
                Comment.objects.get_or_create(
                    post=post,
                    author=author,
                    content=texts[(index + offset) % len(texts)],
                )

    def _refresh_counts(self, posts):
        for post in posts:
            post.likes_count = PostInteraction.objects.filter(post=post, is_liked=True).count()
            post.comments_count = Comment.objects.filter(post=post, deleted_at__isnull=True, is_hidden=False).count()
            post.save(update_fields=['likes_count', 'comments_count'])
