"""Seed a small, auditable public demo cohort for a fresh Baicaoyuan install.

The command keeps the existing ``seed_demo_data`` content, adds a second batch
of clearly disclosed demo accounts, and uses only the checked-in CC0 images.
It never deletes non-demo data and never creates synthetic likes or comments.
"""

from django.core.management import BaseCommand, call_command
from django.contrib.auth.models import User

from community.models import Comment, Follow, Media, Post, PostInteraction, Profile


PEOPLE = [
    ("demo_garden_10", "窗边读者", "喜欢在安静的角落读完一章。"),
    ("demo_garden_11", "沿河慢跑", "把路线和沿途的小发现记下来。"),
    ("demo_garden_12", "胶片散步", "用镜头收集普通日子里的颜色。"),
    ("demo_garden_13", "厨房新手", "从一道家常菜开始练习。"),
    ("demo_garden_14", "周末去郊外", "偏爱轻装出发和不赶时间的路。"),
    ("demo_garden_15", "旧物修补", "修好一件东西，也留住一段记忆。"),
    ("demo_garden_16", "植物观察簿", "记录阳台植物每周的变化。"),
    ("demo_garden_17", "地图收藏家", "把想去的地方慢慢走成自己的地图。"),
    ("demo_garden_18", "晨间写作者", "用几行字给一天一个开头。"),
    ("demo_garden_19", "街巷拾光", "留意城市里容易错过的小细节。"),
    ("demo_garden_20", "茶桌边", "把喝茶、读书和发呆都当作正经事。"),
    ("demo_garden_21", "轻徒步日记", "分享适合普通人的短线徒步准备。"),
    ("demo_garden_22", "手作慢慢来", "记录做东西时的试错过程。"),
    ("demo_garden_23", "雨天收藏者", "喜欢雨后的街道和窗上的水痕。"),
    ("demo_garden_24", "书单交换", "整理读过的书，也写下读后的问题。"),
    ("demo_garden_25", "山野便当", "出门前做一份简单耐放的午餐。"),
    ("demo_garden_26", "一人食练习", "把简单的一餐认真做好。"),
    ("demo_garden_27", "小城建筑记", "观察老房子的门窗、颜色和光。"),
    ("demo_garden_28", "四季采集", "记录季节在餐桌和路边的变化。"),
    ("demo_garden_29", "安静的旅行者", "更喜欢在一个地方多待一会儿。"),
    ("demo_garden_30", "日常摄影课", "每天挑一个主题练习观察。"),
]

STORIES = [
    ("把旧书店放进散步路线", "走进一家书店，常常会让行程多出半小时。", "阅读,城市", 5),
    ("沿河走到天色变蓝", "熟悉的地方换一个时间再看，也会有新发现。", "城市,散步", 2),
    ("窗边的光每天都不同", "同一个位置，光线会替日子写下日期。", "摄影,记录", 0),
    ("晚饭做简单一点", "一道家常菜，也值得慢慢准备。", "生活,做饭", 4),
    ("第一次走这条短线", "不拼速度，准备充分就已经很好。", "徒步,户外", 3),
    ("修好一把用了很久的椅子", "修补不是把痕迹藏起来，而是让它继续陪伴。", "手作,生活", 2),
    ("阳台植物的新叶", "小小的变化，值得单独记下来。", "植物,日常", 4),
    ("把想去的地方变成步行图", "地图上的收藏点，最后还是要用脚去认识。", "城市,地图", 0),
    ("清晨写下三件小事", "不必先想好一篇完整的文章。", "写作,日常", 1),
    ("雨停以后去买面包", "雨后的街道有一种刚刚整理过的感觉。", "摄影,生活", 2),
    ("给下周留一份书单", "书单不需要很长，能开始读就好。", "阅读,书单", 5),
    ("山路午餐怎么准备", "简单、耐放、方便收拾，是我最看重的三点。", "徒步,饮食", 3),
    ("晚茶时读两页书", "留一段不被通知打断的时间。", "阅读,慢生活", 1),
    ("把雨声写进今天的笔记", "天气也可以成为日常记录的线索。", "写作,天气", 0),
    ("街角的蓝色招牌", "旧招牌的颜色比新漆更有时间感。", "街拍,城市", 2),
    ("给家里的餐桌换一束花", "一点小变化，就能让晚饭更有仪式感。", "生活,花艺", 4),
    ("旅行前只查三件事", "天气、交通和返程，其他留给现场决定。", "旅行,准备", 3),
    ("一本书读到第二遍", "第二次阅读时，问题往往比答案更多。", "阅读,笔记", 5),
    ("把周末留给一条小路", "短短一段路，也能让心情重新排好顺序。", "徒步,周末", 3),
    ("每天一个取景框", "先练习观察，再考虑拍得好不好。", "摄影,练习", 0),
    ("收拾厨房也是收拾一天", "把台面擦干净，明天就有了一个轻松的开始。", "生活,整理", 4),
]

SOURCE_URLS = {
    "mongolia-landscape.jpg": "https://commons.wikimedia.org/wiki/File:Landscape_of_Mongolia_01.jpg",
    "coffee-cup.jpg": "https://commons.wikimedia.org/wiki/File:Coffee_cup_and_coffee_bean.jpg",
    "street-craftsman.jpg": "https://commons.wikimedia.org/wiki/File:Street_Craftsman_in_Olinda.jpg",
    "hiking-trip.jpg": "https://commons.wikimedia.org/wiki/File:HIking_trip.jpg",
    "market-food.jpg": "https://commons.wikimedia.org/wiki/File:Food_from_a_food_retailer%27s_container.jpg",
    "elephant-clock.jpg": "https://commons.wikimedia.org/wiki/File:%22The_Elephant_Clock%22,_Folio_from_a_Book_of_the_Knowledge_of_Ingenious_Mechanical_Devices_by_al-Jazari_MET_DP234075.jpg",
}
IMAGE_NAMES = list(SOURCE_URLS)


class Command(BaseCommand):
    help = "导入可审计的百草园初始社区内容（30 个演示账号）"

    def add_arguments(self, parser):
        parser.add_argument("--disable-login", action="store_true", help="禁用演示账号密码登录")

    def handle(self, *args, **options):
        call_command("seed_demo_data", disable_login=True)
        assets = {
            item.file.name.rsplit("/", 1)[-1]: item
            for item in Media.objects.filter(file__contains="demo/")
        }
        people = list(self._ensure_users(options["disable_login"]))
        for index, (title, summary, tags, image_index) in enumerate(STORIES):
            author = people[index % len(people)]
            asset = assets[IMAGE_NAMES[image_index]]
            source = SOURCE_URLS[IMAGE_NAMES[image_index]]
            body = f"<p>{summary}</p><p>这是演示账号的原创记录，文字用于展示图文社区的阅读节奏和发布结构。</p>"
            body += f'<p>图片来源：Wikimedia Commons，CC0 公共领域。<a href="{source}">查看素材与许可</a></p>'
            post, _ = Post.objects.update_or_create(
                author=author,
                title=title,
                defaults={
                    "summary": summary,
                    "content_html": body,
                    "tags": tags.split(","),
                    "images": [f"/media/{asset.pk}/image"],
                    "moderation_status": Post.MODERATION_APPROVED,
                    "deleted_at": None,
                    "likes_count": 0,
                    "comments_count": 0,
                },
            )
            post.media_assets.set([asset])
            post.images = [f"/media/{asset.pk}/image"]
            post.save(update_fields=["images", "updated_at"])
        self._normalize_demo_state(people)
        self.stdout.write(self.style.SUCCESS(
            f"已准备 {len(people)} 个演示账号、{Post.objects.filter(author__in=people).count()} 篇帖子和 "
            f"{Follow.objects.filter(follower__in=people, followee__in=people).count()} 条关注关系。"
        ))

    def _ensure_users(self, disable_login):
        users = []
        for username, nickname, bio in PEOPLE:
            user, _ = User.objects.get_or_create(username=username, defaults={"email": f"{username}@example.com"})
            user.set_unusable_password()
            user.save(update_fields=["password"])
            profile, _ = Profile.objects.get_or_create(user=user)
            profile.nickname = nickname
            profile.signature = f"演示账号｜{bio}"
            profile.email_verified = True
            avatar = Media.objects.filter(file__contains=f"demo/{IMAGE_NAMES[len(users) % len(IMAGE_NAMES)]}").first()
            if avatar:
                profile.avatar_media = avatar
                profile.avatar_url = f"/media/{avatar.pk}/image"
            profile.save(update_fields=["nickname", "signature", "email_verified", "avatar_media", "avatar_url"])
            users.append(user)
        existing = list(User.objects.filter(username__in={"demo_muyu", "demo_shanlu", "demo_kafei", "demo_shuye", "demo_chengshi", "demo_yuanfang", "demo_suishou", "demo_guangying", "demo_qingchen"}).order_by("id"))
        for index, user in enumerate(existing):
            profile = user.profile
            if not profile.signature.startswith("演示账号｜"):
                profile.signature = f"演示账号｜{profile.signature}"
            avatar = Media.objects.filter(file__contains=f"demo/{IMAGE_NAMES[index % len(IMAGE_NAMES)]}").first()
            if avatar:
                profile.avatar_media = avatar
                profile.avatar_url = f"/media/{avatar.pk}/image"
            profile.save(update_fields=["signature", "avatar_media", "avatar_url"])
        return existing + users

    def _normalize_demo_state(self, users):
        demo_posts = Post.objects.filter(author__in=users)
        Comment.objects.filter(post__in=demo_posts).delete()
        PostInteraction.objects.filter(post__in=demo_posts).delete()
        for index, user in enumerate(users):
            for step in (1, 2, 3):
                Follow.objects.get_or_create(follower=user, followee=users[(index + step) % len(users)])
        for post in demo_posts:
            if "演示账号原创图文" not in post.content_html:
                links = []
                for asset in post.media_assets.all():
                    filename = asset.file.name.rsplit("/", 1)[-1]
                    if filename in SOURCE_URLS:
                        links.append(f'<a href="{SOURCE_URLS[filename]}">查看图片来源与许可</a>')
                if links:
                    post.content_html += "<p>演示账号原创图文。</p><p>" + "；".join(links) + "</p>"
                    post.save(update_fields=["content_html"])
            post.likes_count = 0
            post.comments_count = 0
            post.save(update_fields=["likes_count", "comments_count"])
