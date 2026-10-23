import re
from html import escape
from html.parser import HTMLParser
from urllib.parse import urlsplit
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q, Count, Exists, OuterRef
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_GET
from .accounts import body, public_user_payload, display_name
from .http import api_error, api_success
from .models import Post, PostInteraction, Follow, Comment
from .visibility import public_posts, readable_posts, visible_comments

class SafeHTML(HTMLParser):
    tags = {'p', 'br', 'strong', 'b', 'em', 'i', 'u', 's', 'h1', 'h2', 'h3', 'h4', 'blockquote', 'ul', 'ol', 'li', 'a', 'img', 'pre', 'code'}

    def __init__(self, legacy_images=()):
        super().__init__(convert_charrefs=True)
        self.parts, self.stack, self.legacy_images, self.images = ([], [], set(legacy_images), [])

    def handle_starttag(self, tag, attrs):
        if tag not in self.tags:
            return
        clean = []
        attrs = dict(attrs)
        if tag == 'a':
            href = (attrs.get('href') or '').strip()
            if urlsplit(href).scheme.lower() in {'http', 'https', 'mailto'} or (href.startswith('/') and (not href.startswith('//'))):
                clean.append('href="' + escape(href, quote=True) + '"')
            clean.append('rel="nofollow noopener noreferrer"')
        if tag == 'img':
            src = (attrs.get('src') or '').strip()
            if not (src.startswith('/media/') or src in self.legacy_images):
                raise ValueError('图片须先上传为媒体资源；旧图片仅可原样保留')
            self.images.append(src)
            clean += ['src="' + escape(src, quote=True) + '"', 'alt="' + escape((attrs.get('alt') or '')[:255], quote=True) + '"']
        self.parts.append('<' + tag + (' ' + ' '.join(clean) if clean else '') + '>')
        if tag not in {'img', 'br'}:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in self.stack:
            while self.stack:
                current = self.stack.pop()
                self.parts.append('</' + current + '>')
                if current == tag:
                    break

    def handle_data(self, data):
        self.parts.append(escape(data))

    def result(self):
        while self.stack:
            self.parts.append('</' + self.stack.pop() + '>')
        return ''.join(self.parts)

def validate_post(data, post=None, draft=False):
    if not isinstance(data, dict):
        raise ValueError('请求必须为JSON对象')
    result = {}
    for field, attribute, limit in [('title', 'title', 255), ('summary', 'summary', 500), ('contentHtml', 'content_html', 100000)]:
        value = data.get(field, getattr(post, attribute, ''))
        if not isinstance(value, str) or len(value) > limit:
            raise ValueError(f'{field} 类型错误或超过长度限制 {limit}')
        result[attribute] = value.strip() if field != 'contentHtml' else value
    if not draft and (not result['title']):
        raise ValueError('标题不能为空')
    tags = data.get('tags', post.tags if post else [])
    if not isinstance(tags, list) or len(tags) > 5 or any((not isinstance(t, str) or not t.strip() or len(t) > 24 for t in tags)):
        raise ValueError('标签最多5个，每个1–24字')
    result['tags'] = list(dict.fromkeys((t.strip() for t in tags)))
    legacy = re.findall('<img[^>]*src=[\\"\\\']([^\\"\\\']+)', post.content_html, re.I) if post else []
    sanitizer = SafeHTML(legacy)
    sanitizer.feed(result['content_html'])
    if len(set(sanitizer.images))>9:
        raise ValueError('正文最多引用9张图片')
    result['content_html'] = sanitizer.result()
    images = data.get('images', post.images if post else sanitizer.images)
    if not isinstance(images, list) or len(images) > 9 or any((not isinstance(i, str) for i in images)):
        raise ValueError('图片格式错误或超过9张')
    if any((not i.startswith('/media/') and i not in legacy and (not post or i not in post.images) for i in images)):
        raise ValueError('新图片必须先上传')
    result['images'] = images
    return result

def hydrated(query, viewer):
    query = query.select_related('author', 'author__profile').prefetch_related('media_assets').annotate(actual_likes=Count('interactions', filter=Q(interactions__is_liked=True), distinct=True), actual_comments=Count('comments', filter=Q(comments__is_hidden=False, comments__author__is_active=True, comments__deleted_at__isnull=True, comments__author__profile__banned_at__isnull=True), distinct=True))
    if viewer.is_authenticated:
        query = query.annotate(viewer_liked=Exists(PostInteraction.objects.filter(post_id=OuterRef('pk'), user=viewer, is_liked=True)), viewer_favorited=Exists(PostInteraction.objects.filter(post_id=OuterRef('pk'), user=viewer, is_favorited=True)), viewer_following=Exists(Follow.objects.filter(followee_id=OuterRef('author_id'), follower=viewer)))
    return query

def post_dto(post, viewer, detail=False):
    if not hasattr(post, 'actual_likes'):
        post = hydrated(Post.objects.filter(pk=post.pk), viewer).get()
    profile = getattr(post.author, 'profile', None)
    name = display_name(post.author)
    images = post.images if isinstance(post.images, list) else []
    data = {'id': post.pk, 'title': post.title, 'summary': post.summary, 'authorId': post.author_id, 'author': name, 'authorAvatarText': name[:1], 'authorAvatarUrl': profile.avatar_url if profile else '', 'time': post.created_at.isoformat(), 'createdAt': post.created_at.isoformat(), 'updatedAt': post.updated_at.isoformat(), 'images': [src for src in images if isinstance(src, str) and (detail or not src.startswith('data:'))], 'tags': post.tags, 'likes': post.actual_likes, 'comments': post.actual_comments, 'isLiked': getattr(post, 'viewer_liked', False), 'isFavorited': getattr(post, 'viewer_favorited', False), 'isFollowingAuthor': getattr(post, 'viewer_following', False), 'moderationStatus': post.moderation_status}
    if detail:
        data['contentHtml'] = post.content_html
        if not images:
            data['images'] = re.findall('<img[^>]*src=[\\"\\\']([^\\"\\\']+)', post.content_html, re.I)
    if viewer.is_authenticated and viewer.pk == post.author_id:
        data['reviewReason'] = post.review_reason
    from .media import media_dto
    media_map = {media_dto(a)['url']: a for a in post.media_assets.all()}
    data['media'] = [media_dto(media_map[url]) for url in images if url in media_map]
    data['mediaIds'] = [a['id'] for a in data['media']]
    return data

def page_data(request, query, serialize, key='items'):
    from .views import _parse_page_params
    page, size = _parse_page_params(request, default_page_size=20)
    total = query.count()
    items = [serialize(item) for item in query[(page - 1) * size:page * size]]
    return {key: items, 'pagination': {'page': page, 'pageSize': size, 'total': total, 'hasMore': page * size < total}}

@require_GET
def search(request):
    from .social import consumption
    query = consumption(public_posts(), request.user).select_related('author', 'author__profile')
    keyword = (request.GET.get('q') or '').strip()
    nav = request.GET.get('nav', '推荐')
    if request.GET.get('type') == 'users':
        users = User.objects.filter(is_active=True, profile__banned_at__isnull=True)
        if keyword:
            users = users.filter(Q(profile__nickname__icontains=keyword) | Q(username__icontains=keyword))
        return api_success(request, page_data(request, users.select_related('profile').order_by('-id'), public_user_payload))
    if request.GET.get('tag'):
        query = query.filter(tags__icontains=request.GET['tag'])
    if keyword:
        query = query.filter(Q(title__icontains=keyword) | Q(summary__icontains=keyword) | Q(content_html__icontains=keyword) | Q(author__profile__nickname__icontains=keyword) | Q(author__username__icontains=keyword) | Q(tags__icontains=keyword))
    if nav == '关注':
        query = query.filter(author__follower_relations__follower=request.user) if request.user.is_authenticated else query.none()
    query = hydrated(query, request.user).defer('content_html')
    query = query.order_by('-created_at', '-id') if nav in {'更新', '关注'} else query.order_by('-actual_likes', '-created_at', '-id')
    return api_success(request, page_data(request, query, lambda p: post_dto(p, request.user), key='posts'))

@require_http_methods(['GET', 'POST'])
def posts(request):
    if request.method == 'GET':
        return search(request)
    if not request.user.is_authenticated:
        return api_error(request, '未登录', 401)
    from .media import validate_media, validate_html_media, media_dto, receipt
    from .models import Draft
    from .social import write_denial
    denial = write_denial(request)
    if denial:
        return denial
    data = body(request)
    with transaction.atomic():
        try:
            if data.get('draftId') is not None and (type(data['draftId'])!=int):raise ValueError('草稿ID必须是整数')
            record, replay = receipt(request.user, 'post.create', data)
            if replay:
                post = readable_posts(request.user, True).filter(pk=record.target_id).first()
                return api_success(request, post_dto(post, request.user, True)) if post else api_error(request, '原帖已不可用', 409)
            if data.get('draftId') is not None and not Draft.objects.filter(pk=data['draftId'],owner=request.user).exists():raise ValueError('草稿不属于当前用户或已删除')
            assets = validate_media(data, request.user)
            values = validate_post(data)
            validate_html_media(values['content_html'], assets)
        except ValueError as exc:
            transaction.set_rollback(True)
            return api_error(request, str(exc), 409 if '标识' in str(exc) else 400)
        if assets is not None:
            values['images'] = [media_dto(a)['url'] for a in assets]
        if 'summary' not in data:
            from django.utils.html import strip_tags
            values['summary'] = strip_tags(values['content_html'])[:220]
        post = Post.objects.create(author=request.user, **values)
        if assets is not None:
            post.media_assets.set(assets)
        if data.get('draftId'):
            Draft.objects.filter(pk=data['draftId'], owner=request.user).delete()
        if record:
            record.target_id = post.pk
            record.save(update_fields=['target_id'])
    return api_success(request, post_dto(post, request.user, True), status=201)

@require_http_methods(['GET', 'PUT', 'DELETE'])
def post_detail(request, post_id):
    query = readable_posts(request.user, own=request.method != 'GET' or request.GET.get('manage') == '1')
    post = query.select_related('author', 'author__profile').filter(pk=post_id).first()
    if not post:
        return api_error(request, '内容已不可用', 404)
    if request.method == 'GET':
        if request.GET.get('manage') == '1' and (not request.user.is_authenticated or post.author_id != request.user.pk):
            return api_error(request, '仅作者可管理', 403)
        return api_success(request, post_dto(post, request.user, True))
    if not request.user.is_authenticated:
        return api_error(request, '未登录', 401)
    from .social import write_denial
    denial = write_denial(request)
    if denial:
        return denial
    if post.author_id != request.user.pk:
        return api_error(request, '仅作者可修改或删除', 403)
    if request.method == 'DELETE':
        post.deleted_at = timezone.now()
        post.save(update_fields=['deleted_at', 'updated_at'])
        return api_success(request, {'id': post.pk, 'deleted': True})
    from .media import validate_media, validate_html_media, media_dto
    data = body(request)
    with transaction.atomic():
        try:
            assets = validate_media(data, request.user, post)
            values = validate_post(data, post)
            validate_html_media(values['content_html'], assets if assets is not None else list(post.media_assets.all()), post)
        except ValueError as e:
            return api_error(request, str(e))
        if assets is not None:
            values['images'] = [media_dto(a)['url'] for a in assets]
        for attr, value in values.items():
            setattr(post, attr, value)
        post.save()
        if assets is not None:
            post.media_assets.set(assets)
    return api_success(request, post_dto(post, request.user, True))

@require_GET
def user_posts(request, user_id=None, kind='posts'):
    own = user_id is None
    if own and (not request.user.is_authenticated):
        return api_error(request, '未登录', 401)
    user_id = request.user.pk if own else user_id
    if not User.objects.filter(pk=user_id, is_active=True).exists():
        return api_error(request, '用户不可用', 404)
    if kind == 'posts':
        query = (readable_posts(request.user, True) if own else public_posts()).filter(author_id=user_id)
        status = request.GET.get('status')
        if status and own:
            query = query.filter(moderation_status=status)
    else:
        query = public_posts().filter(interactions__user_id=user_id, interactions__is_favorited=True)
    return api_success(request, page_data(request, hydrated(query, request.user).defer('content_html').order_by('-created_at', '-id'), lambda p: post_dto(p, request.user)))

@require_GET
def relationships(request, user_id, kind):
    if not User.objects.filter(pk=user_id, is_active=True).exists():
        return api_error(request, '用户不可用', 404)
    query = User.objects.filter(is_active=True)
    query = query.filter(following_relations__followee_id=user_id) if kind == 'followers' else query.filter(follower_relations__follower_id=user_id)
    return api_success(request, page_data(request, query.select_related('profile').order_by('-id'), public_user_payload))
