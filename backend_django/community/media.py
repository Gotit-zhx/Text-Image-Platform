import hashlib
import io
import json
import secrets
import warnings
from datetime import timedelta
from PIL import Image, ImageOps, UnidentifiedImageError
from django.core.files.base import ContentFile
from django.db import transaction
from django.http import FileResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_GET
from .accounts import body
from .http import api_error, api_success
from .models import Media, Draft, RequestReceipt
from .visibility import public_posts

def media_dto(asset):
    return {'id': asset.pk, 'url': f'/media/{asset.pk}/image', 'thumbnailUrl': f'/media/{asset.pk}/thumbnail', 'width': asset.width, 'height': asset.height, 'size': asset.size, 'format': asset.format}

@require_http_methods(['POST'])
def upload(request):
    if not request.user.is_authenticated:
        return api_error(request, '未登录', 401)
    file = request.FILES.get('file')
    if not file or file.size > 10 * 1024 * 1024:
        return api_error(request, '请选择10MiB以内的图片', 413)
    from .social import write_denial
    denial = write_denial(request)
    if denial:
        return denial
    if Media.objects.filter(owner=request.user, posts__isnull=True, drafts__isnull=True).count() >= 100:
        return api_error(request, '未使用图片过多，请先移除或保存草稿', 429)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            image = Image.open(file)
            if image.format not in {'JPEG', 'PNG', 'WEBP', 'GIF'} or image.width * image.height > 40000000:
                raise ValueError('仅支持JPEG/PNG/WebP/GIF，最多4000万像素')
            image.verify()
            file.seek(0)
            image = ImageOps.exif_transpose(Image.open(file))
            image.seek(0)
            image = image.convert('RGBA' if 'A' in image.getbands() else 'RGB')
            full = io.BytesIO()
            image.save(full, format='PNG' if image.mode == 'RGBA' else 'JPEG')
            thumb = image.copy()
            thumb.thumbnail((480, 600))
            small = io.BytesIO()
            thumb.save(small, format='PNG' if image.mode == 'RGBA' else 'JPEG')
    except (ValueError, UnidentifiedImageError, OSError, Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        return api_error(request, '图片格式损坏或超过尺寸限制')
    if len(full.getvalue()) > 10 * 1024 * 1024:
        return api_error(request, '处理后的图片仍超过10MiB，请缩小后重试', 413)
    suffix = '.png' if image.mode == 'RGBA' else '.jpg'
    asset = Media(owner=request.user, width=image.width, height=image.height, size=len(full.getvalue()), format='PNG' if image.mode == 'RGBA' else 'JPEG')
    try:
        asset.file.save(secrets.token_hex(20) + suffix, ContentFile(full.getvalue()), save=False)
        asset.thumbnail.save(secrets.token_hex(20) + suffix, ContentFile(small.getvalue()), save=False)
        asset.save()
    except Exception:
        if asset.file.name:
            asset.file.delete(save=False)
        if asset.thumbnail.name:
            asset.thumbnail.delete(save=False)
        raise
    return api_success(request, media_dto(asset), status=201)

@require_GET
def media_file(request, media_id, variant):
    asset = Media.objects.filter(pk=media_id).first()
    if not asset or variant not in {'image', 'thumbnail'}:
        return api_error(request, '图片不可用', 404)
    owner = request.user.is_authenticated and request.user.pk == asset.owner_id
    public = asset.posts.filter(pk__in=public_posts()).exists() or asset.avatar_profiles.filter(user__is_active=True, banned_at__isnull=True).exists()
    if not owner and (not public):
        return api_error(request, '图片不可用', 404)
    field = asset.file if variant == 'image' else asset.thumbnail
    try:
        response = FileResponse(field.open('rb'), content_type='image/png' if asset.format == 'PNG' else 'image/jpeg')
        response['Cache-Control'] = 'private, no-cache'
        response['X-Content-Type-Options'] = 'nosniff'
        return response
    except OSError:
        return api_error(request, '图片文件不可用', 404)

@require_http_methods(['GET', 'DELETE'])
def remove(request, media_id):
    if not request.user.is_authenticated:
        return api_error(request, '未登录', 401)
    with transaction.atomic():
        asset = Media.objects.select_for_update().filter(pk=media_id, owner=request.user).first()
        if not asset:
            return api_error(request, '图片不可用', 404)
        if request.method == 'GET':
            return api_success(request, media_dto(asset))
        if asset.posts.exists() or asset.drafts.exists() or asset.avatar_profiles.exists():
            return api_error(request, '图片仍被作品或草稿使用，请先移除引用', 409)
        asset.file.delete(save=False)
        asset.thumbnail.delete(save=False)
        asset.delete()
    return api_success(request, {'deleted': True})

def validate_media(data, user, existing=None):
    if 'images' in data and (not isinstance(data['images'], list) or any((not isinstance(src, str) for src in data['images']))):
        raise ValueError('图片列表格式无效')
    if 'mediaIds' not in data:
        if not existing and any((isinstance(i, str) and i.startswith('/media/') for i in data.get('images', []))):
            raise ValueError('新图片必须提供资源ID')
        return None
    ids = data['mediaIds']
    if not isinstance(ids, list) or len(ids) > 9 or len(set(map(str, ids))) != len(ids) or any((type(i) != int for i in ids)):
        raise ValueError('媒体ID须为最多9个不重复整数')
    assets = list(Media.objects.select_for_update().filter(pk__in=ids, owner=user))
    if len(assets) != len(ids):
        raise ValueError('不能引用不属于自己的图片')
    mapping = {a.pk: a for a in assets}
    return [mapping[i] for i in ids]

def validate_html_media(html, assets, existing=None):
    import re
    urls = {media_dto(a)['url'] for a in assets or []}
    if existing:
        legacy = list(existing.images) + re.findall('<img[^>]*src=[\\"\\\']([^\\"\\\']+)', existing.content_html, re.I)
        urls.update((src for src in legacy if not re.fullmatch('/media/\\d+/image', src)))
    for url in re.findall('<img[^>]*src=[\\"\\\']([^\\"\\\']+)', html, re.I):
        if url not in urls:
            raise ValueError('正文包含未授权的图片引用')

def receipt(user, action, data):
    key = data.get('requestKey')
    if not key:
        return None, False
    if not isinstance(key, str) or len(key) > 80:
        raise ValueError('请求标识无效')
    digest = hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    record, created = RequestReceipt.objects.select_for_update().get_or_create(
        user=user, action=action, key=key, defaults={'digest':digest})
    if record.digest != digest:
        raise ValueError('同一请求标识不能用于不同内容')
    return record, not created


def draft_dto(draft):
    mapping = {media_dto(asset)['url']: asset for asset in draft.media.all()}
    ordered = [mapping[url] for url in draft.images if url in mapping]
    return {'id': draft.pk, 'title': draft.title, 'summary': draft.summary, 'contentHtml': draft.content_html, 'tags': draft.tags, 'media': [media_dto(asset) for asset in ordered], 'mediaIds': [asset.pk for asset in ordered], 'images': draft.images, 'version': draft.version, 'updatedAt': draft.updated_at.isoformat()}

@require_http_methods(['GET', 'POST', 'PUT', 'DELETE'])
def drafts(request, draft_id=None):
    if not request.user.is_authenticated:
        return api_error(request, '未登录', 401)
    from .content import page_data, validate_post
    with transaction.atomic():
        draft = Draft.objects.select_for_update().filter(pk=draft_id, owner=request.user).first() if draft_id else None
        if draft_id and (not draft):
            return api_error(request, '草稿不存在', 404)
        if request.method == 'GET':
            if draft:
                return api_success(request, draft_dto(draft))
            return api_success(request, page_data(request, Draft.objects.filter(owner=request.user).order_by('-updated_at', '-id'), draft_dto))
        if request.method == 'DELETE' and draft:
            draft.delete()
            return api_success(request, {'deleted': True})
        if request.method == 'POST' and draft_id or (request.method == 'PUT' and (not draft_id)) or request.method == 'DELETE':
            return api_error(request, '请求方法与草稿地址不匹配', 405)
        data = body(request)
        if draft and data.get('version') != draft.version:
            return api_error(request, '草稿已被其他窗口修改，请保留输入并重新加载', 409)
        try:
            assets = validate_media(data, request.user, draft)
            values = validate_post(data, draft, draft=True)
            validate_html_media(values['content_html'], assets if assets is not None else list(draft.media.all()) if draft else [], draft)
            record, replay = receipt(request.user, 'draft.create', data) if not draft else (None, False)
            if replay:
                saved = Draft.objects.filter(pk=record.target_id, owner=request.user).first()
                return api_success(request, draft_dto(saved)) if saved else api_error(request, '该草稿已删除', 409)
        except ValueError as exc:
            return api_error(request, str(exc), 409 if '标识' in str(exc) else 400)
        if assets is not None:
            values['images'] = [media_dto(a)['url'] for a in assets]
        if draft:
            for key, value in values.items():
                setattr(draft, key, value)
            draft.version += 1
            draft.save()
        else:
            draft = Draft.objects.create(owner=request.user, **values)
        if assets is not None:
            draft.media.set(assets)
        if record:
            record.target_id = draft.pk
            record.save(update_fields=['target_id'])
    return api_success(request, draft_dto(draft), status=200 if draft_id else 201)
