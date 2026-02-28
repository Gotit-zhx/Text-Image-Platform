from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from community.models import Comment, Follow, Post, PostInteraction, Profile


class Command(BaseCommand):
    help = '初始化联调演示数据（用户/帖子/互动/评论）'

    def handle(self, *args, **options):
        users = []
        for idx in range(1, 14):
            username = f'用户{idx}'
            email = f'demo_user_{idx}@example.com'
            user, _ = User.objects.get_or_create(username=username, defaults={'email': email})
            user.set_password('123456')
            user.email = email
            user.save(update_fields=['password', 'email'])
            Profile.objects.get_or_create(user=user)
            users.append(user)

        topics = [
            {
                'tags': ['摄影', '夜景', '街拍'],
                'titles': ['雨后夜拍机位清单', '地铁口人像抓拍技巧', '城市反光面构图复盘'],
                'summaries': ['整理了 6 个稳定出片机位，附参数建议。', '晚高峰 20 分钟抓拍，保留环境光层次。', '利用店铺玻璃和积水做双重反射，画面更有纵深。'],
            },
            {
                'tags': ['手账', '模板', '效率'],
                'titles': ['一周任务拆解模板', '番茄钟学习计划实录', '月度复盘页面设计'],
                'summaries': ['把任务拆成 30 分钟颗粒度，执行更轻松。', '记录 14 天专注时长，找到最稳工作节奏。', '用一页复盘目标、结果与阻碍，下月迭代更快。'],
            },
            {
                'tags': ['徒步', '旅行', '装备'],
                'titles': ['周末轻徒步路线推荐', '山脊线天气突变应对', '露营补给清单实测'],
                'summaries': ['全程 12 公里，适合新手，补给点明确。', '强风和降温场景下的分层穿着方案。', '实测 2 天 1 夜食物和水量，避免背负过重。'],
            },
            {
                'tags': ['咖啡', '拉花', '日常'],
                'titles': ['家庭手冲风味对比', '奶泡稳定性练习记录', '晨间咖啡角布置'],
                'summaries': ['同一豆子三种水温萃取，酸甜平衡差异明显。', '蒸汽量和打发时长的组合对口感影响很大。', '桌面动线优化后，早晨出杯效率提升一倍。'],
            },
            {
                'tags': ['编程', '前端', '后端'],
                'titles': ['接口契约对齐实践', '前端列表渲染优化', '后端查询性能排查'],
                'summaries': ['统一错误码和字段命名，联调成本明显下降。', '通过分段渲染降低首屏与滚动卡顿。', '定位慢 SQL 后将接口响应压缩到 200ms 内。'],
            },
            {
                'tags': ['读书', '笔记', '成长'],
                'titles': ['本周阅读摘录', '知识卡片整理方法', '长期学习计划复盘'],
                'summaries': ['三本书各提炼 5 个可执行观点。', '用主题-问题-行动三段式沉淀阅读笔记。', '对比季度目标与实际投入，及时调整策略。'],
            },
        ]

        comment_templates = [
            '第 2 段方法很实用，我按你的步骤试了一次，效果很稳定。',
            '这个清单太及时了，省去了我自己摸索的大量时间。',
            '图文结构清晰，尤其是参数和注意事项部分，收藏了。',
            '我补充了一个小技巧，结合你的方案会更顺手。',
            '已经照着实践，结果比预期好很多，感谢分享。',
        ]

        posts = []
        for u_idx, user in enumerate(users, start=1):
            post_count = 2 + ((u_idx * 3) % 5)
            for p_idx in range(post_count):
                topic = topics[(u_idx + p_idx) % len(topics)]
                title_seed = topic['titles'][(u_idx + p_idx * 2) % len(topic['titles'])]
                summary_seed = topic['summaries'][(u_idx + p_idx) % len(topic['summaries'])]
                title = f'{title_seed}｜{user.username}'
                post, _ = Post.objects.get_or_create(
                    title=title,
                    defaults={
                        'author': user,
                        'summary': summary_seed,
                        'content_html': (
                            f'<p>{summary_seed}</p>'
                            f'<p>{user.username} 在这篇内容里记录了执行步骤、踩坑点和可复用结论，方便大家直接上手。</p>'
                        ),
                        'tags': topic['tags'],
                        'images': ['linear-gradient(135deg, #8ec5fc, #e0c3fc)'] if p_idx % 3 == 0 else [],
                    },
                )
                posts.append(post)

        for idx, user in enumerate(users):
            for offset in (1, 2, 3):
                followee = users[(idx + offset) % len(users)]
                if followee.id != user.id:
                    Follow.objects.get_or_create(follower=user, followee=followee)

        for u_idx, user in enumerate(users):
            for offset in range(6):
                post = posts[(u_idx * 5 + offset) % len(posts)]
                interaction, _ = PostInteraction.objects.get_or_create(user=user, post=post)
                interaction.is_liked = offset % 2 == 0
                interaction.is_favorited = offset % 3 == 0
                interaction.save(update_fields=['is_liked', 'is_favorited'])

        for u_idx, user in enumerate(users):
            for offset in range(3):
                post = posts[(u_idx * 7 + offset * 2) % len(posts)]
                if post.author_id == user.id:
                    post = posts[(u_idx * 7 + offset * 2 + 1) % len(posts)]
                Comment.objects.get_or_create(
                    post=post,
                    author=user,
                    content=comment_templates[(u_idx + offset) % len(comment_templates)],
                )

        for post in posts:
            post.likes_count = PostInteraction.objects.filter(post=post, is_liked=True).count()
            post.comments_count = Comment.objects.filter(post=post).count()
            post.save(update_fields=['likes_count', 'comments_count'])

        self.stdout.write(self.style.SUCCESS('社区内容初始化完成：13 个用户，每用户 2~6 篇文章，且每用户均有评论。默认密码：123456'))
