from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from community.models import Media
from django.db import transaction


class Command(BaseCommand):
    help='清理至少24小时前未被帖子/草稿引用的孤儿媒体，默认仅预览'
    def add_arguments(self,parser):parser.add_argument('--apply',action='store_true')
    def handle(self,*args,**options):
        query=Media.objects.filter(created_at__lt=timezone.now()-timedelta(hours=24),posts__isnull=True,drafts__isnull=True,avatar_profiles__isnull=True)
        self.stdout.write(f'符合条件的资源：{query.count()}，apply={options["apply"]}')
        if options['apply']:
            for asset_id in query.values_list('id',flat=True).iterator():
                with transaction.atomic():
                    asset=Media.objects.select_for_update().filter(pk=asset_id,posts__isnull=True,drafts__isnull=True,avatar_profiles__isnull=True).first()
                    if asset:
                        asset.file.delete(save=False);asset.thumbnail.delete(save=False);asset.delete()
