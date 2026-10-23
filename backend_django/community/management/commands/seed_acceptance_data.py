"""Explicit, synthetic fixtures. Refuses the ordinary workspace database."""
import os
import base64
from pathlib import Path
from django.conf import settings
from django.contrib.auth.models import User, Group
from django.core.management.base import BaseCommand, CommandError
from PIL import Image, ImageDraw
from community.models import Profile, Post, Comment, Follow, Media
from django.core.files.base import ContentFile


class Command(BaseCommand):
    help = '为独立测试库生成验收账号/内容；禁止用于真实数据环境'
    def handle(self, *args, **options):
        if not os.environ.get('TIP_DATABASE_PATH') or Path(settings.DATABASES['default']['NAME']).resolve()==(settings.BASE_DIR/'db.sqlite3').resolve():
            raise CommandError('必须显式设置独立 TIP_DATABASE_PATH，不能使用工作数据库')
        users=[]
        for code,name in [('a','验收用户A'),('b','验收用户B'),('m','验收审核员'),('o','验收运营'),('d','验收审计员'),('s','验收管理员')]:
            user,created=User.objects.get_or_create(username='acceptance_'+code,defaults={'email':code+'@acceptance.example.com','is_staff':code in 'mods','is_superuser':code=='s'})
            if created:
                user.set_password('GardenField!2026');user.save()
            Profile.objects.get_or_create(user=user,defaults={'nickname':name,'email_verified':True})
            if code in 'mod':
                group,_=Group.objects.get_or_create(name={'m':'content_moderator','o':'operations','d':'auditor'}[code]);user.groups.add(group)
            users.append(user)
        folder=settings.MEDIA_ROOT/'acceptance';folder.mkdir(parents=True,exist_ok=True)
        colors=[('#ead8b8','#5a795d'),('#dfb7a2','#744e44'),('#cbd5df','#4d6681'),('#d8d6b6','#7a824d')]
        for i in range(4):
            path=folder/f'example-{i}.jpg'
            if not path.exists():
                bg,fg=colors[i];img=Image.new('RGB',(660,825),bg);draw=ImageDraw.Draw(img)
                draw.ellipse((100,100,560,560),fill=fg);draw.rectangle((190,430,470,720),fill=bg);draw.line((0,720,660,720),fill=fg,width=8);img.save(path)
        assets={}
        for owner in users[:2]:
            for i in range(4):
                asset=Media.objects.filter(owner=owner,file__endswith=f'acceptance-{owner.pk}-{i}.jpg').first()
                if not asset:
                    payload=(folder/f'example-{i}.jpg').read_bytes()
                    asset=Media(owner=owner,width=660,height=825,size=len(payload),format='JPEG')
                    asset.file.save(f'acceptance-{owner.pk}-{i}.jpg',ContentFile(payload),save=False)
                    asset.thumbnail.save(f'acceptance-thumb-{owner.pk}-{i}.jpg',ContentFile(payload),save=False)
                    asset.save()
                assets[(owner.pk,i)]=asset
        titles=['给日常留一点空白','沿着山路，寻找慢下来的时刻','书桌的一角，和今天的阅读笔记','从一颗种子开始的阳台日记','雨后的街道有新的颜色','一段没有图片的真实文字记录']
        for i in range(25):
            post,_=Post.objects.get_or_create(author=users[i%2],title=f'{titles[i%6]} · {i+1}',defaults={'summary':'这是独立验收环境中的合成内容，用于检查长标题、卡片、分页和页面布局。','content_html':'<p>这是一份用于本地验收的图文记录。</p><p>保持好奇，记录生活中的微小片段。</p>','images':[] if i%6==5 else [f'/media/acceptance/example-{i%4}.jpg'],'tags':['验收样本','日常']})
            if i%6!=5:
                asset=assets[(users[i%2].pk,i%4)]
                post.media_assets.set([asset]);post.images=[f'/media/{asset.pk}/image'];post.save(update_fields=['images'])
        for index in range(35):
            fan,_=User.objects.get_or_create(username=f'acceptance_fan_{index}',defaults={'email':f'fan{index}@acceptance.example.com'})
            Profile.objects.get_or_create(user=fan,defaults={'nickname':f'验收粉丝{index}'})
            Follow.objects.get_or_create(follower=fan,followee=users[0])
        first=Post.objects.get(author=users[0],title=f'{titles[0]} · 25')
        for index in range(61):Comment.objects.get_or_create(post=first,author=users[1],content=f'验收分页评论 {index}')
        root=first.comments.filter(root__isnull=True).first()
        for index in range(31):Comment.objects.get_or_create(post=first,author=users[0],root=root,parent=root,reply_to=root,content=f'验收楼中楼回复 {index}')
        multi,_=Post.objects.get_or_create(author=users[1],title='验收样本：双图查看器',defaults={'content_html':'<p>本地合成图片，用于键盘、缩放和嵌套弹层验收。</p>'})
        multi_assets=[assets[(users[1].pk,i)] for i in (0,1)]
        multi.media_assets.set(multi_assets)
        multi.images=[f'/media/{asset.pk}/image' for asset in multi_assets]
        multi.save(update_fields=['images'])
        broken,_=Post.objects.get_or_create(author=users[1],title='验收专用：图片加载失败',defaults={'content_html':'<p>检查图片错误、重试与关闭。</p>','images':['/media/999999/image']})
        legacy='data:image/jpeg;base64,'+base64.b64encode((folder/'example-0.jpg').read_bytes()).decode('ascii')
        Post.objects.get_or_create(author=users[0],title='验收样本：历史内嵌图片',defaults={'content_html':f'<p>旧文章兼容展示。</p><img src="{legacy}" alt="历史图片">','images':[legacy]})
        Post.objects.get_or_create(author=users[0],title='验收样本：长文与长标题 · '+ '记录日常的细节'*8,defaults={'content_html':'<p>长文可读性验收：记录生活中的细小片段。</p>'*80})
        Post.objects.get_or_create(author=users[0],title='验收样本：已下架内容',defaults={'content_html':'<p>公共接口不可泄露此正文。</p>','moderation_status':'offline'})
        inactive,_=User.objects.get_or_create(username='acceptance_inactive',defaults={'is_active':False})
        Profile.objects.get_or_create(user=inactive,defaults={'nickname':'验收停用作者'})
        Post.objects.get_or_create(author=inactive,title='验收样本：停用作者内容',defaults={'content_html':'<p>公共接口不可泄露停用作者正文。</p>'})
        Follow.objects.get_or_create(follower=users[1],followee=users[0])
        self.stdout.write(f'交互脚本参数 imagePostId={multi.pk}, discussionPostId={first.pk}; 图片错误 postId={broken.pk}')
        self.stdout.write('已生成独立验收数据；账号 acceptance_a/b/m/o/d/s；新账号密码 GardenField!2026；已有账号密码不变。')
