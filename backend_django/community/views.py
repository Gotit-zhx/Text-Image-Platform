import json
import re
from functools import wraps
from datetime import datetime, timedelta
from pathlib import Path

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import Group, User
from django.db.models import Q
from django.db import models, transaction
from django.http import HttpRequest, JsonResponse
from django.utils import timezone
from django.utils.timezone import localtime
from django.views.decorators.http import require_GET, require_http_methods

from .models import AuditLog, Comment, CommentLike, Follow, Post, PostInteraction, Profile
from .visibility import public_posts, readable_posts, visible_comments
from .http import api_error, api_success
from .recsys_pipeline import get_recsys_status_path

ADMIN_SESSION_KEY = 'community_admin_user_id'
IMG_SRC_PATTERN = re.compile(r'<img[^>]*\bsrc=["\']([^"\']+)["\']', re.IGNORECASE)


def _get_admin_session_user(request: HttpRequest):
    admin_user_id = request.session.get(ADMIN_SESSION_KEY)
    if admin_user_id:
        admin_user = User.objects.filter(id=admin_user_id, is_staff=True, is_active=True).first()
        if admin_user and request.session.get('community_admin_auth_hash') == admin_user.get_session_auth_hash():
            return admin_user
        request.session.pop(ADMIN_SESSION_KEY, None)

    if request.user.is_authenticated and request.user.is_staff and request.user.is_active:
        return request.user

    return None


def api_login_required(view_func):
    @wraps(view_func)
    def _wrapped(request: HttpRequest, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_active:
            return api_error(request, '未登录', status=401)
        return view_func(request, *args, **kwargs)

    return _wrapped


def api_admin_required(view_func):
    @wraps(view_func)
    def _wrapped(request: HttpRequest, *args, **kwargs):
        admin_user = _get_admin_session_user(request)
        if not admin_user:
            return api_error(request, '无权限执行该操作', status=403)
        request.admin_user = admin_user
        from .governance import can_admin
        profile = getattr(admin_user,'profile',None)
        if profile and profile.banned_at:
            return api_error(request,'管理账号已封禁',403)
        if request.method not in {'GET','HEAD','OPTIONS'} and 'auth/logout' not in request.path:
            permission = 'moderate' if '/moderation/' in request.path else 'operate'
            if '/roles' in request.path:
                if not admin_user.is_superuser:return api_error(request,'仅超级管理员可修改角色',403)
            elif not can_admin(admin_user,permission):return api_error(request,'角色不允许执行此操作',403)
        return view_func(request, *args, **kwargs)

    return _wrapped


def _paginate(request: HttpRequest, queryset):
    try:
        page = max(1, int(request.GET.get('page', 1)))
    except ValueError:
        page = 1
    try:
        page_size = max(1, min(100, int(request.GET.get('pageSize', 10))))
    except ValueError:
        page_size = 10

    total = queryset.count()
    offset = (page - 1) * page_size
    return queryset[offset: offset + page_size], {
        'total': total,
        'page': page,
        'pageSize': page_size,
    }


def _parse_page_params(request: HttpRequest, default_page_size=12, max_page_size=50):
    try:
        page = max(1, int(request.GET.get('page', 1)))
    except (TypeError, ValueError):
        page = 1

    raw_page_size = request.GET.get('pageSize', request.GET.get('page_size', default_page_size))
    try:
        page_size = max(1, min(max_page_size, int(raw_page_size)))
    except (TypeError, ValueError):
        page_size = default_page_size

    return page, page_size


def _user_roles(user: User):
    if not user or not user.is_authenticated:
        return []
    return list(user.groups.values_list('name', flat=True))


def _ensure_admin_groups():
    for name in ['super_admin', 'content_moderator', 'operations', 'auditor']:
        Group.objects.get_or_create(name=name)


def _write_audit_log(request, action, target_type, target_id, detail=None):
    from .governance import audit
    return audit(request,action,target_type,target_id,detail)


def _json_body(request: HttpRequest):
    if not request.body:
        return {}
    try:
        data = json.loads(request.body.decode('utf-8'))
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}


def _ensure_profile(user: User):
    Profile.objects.get_or_create(user=user)


def _extract_images_from_html(content_html: str, limit: int = 3):
    if not content_html:
        return []

    images = []
    for match in IMG_SRC_PATTERN.finditer(content_html):
        src = (match.group(1) or '').strip()
        if not src:
            continue
        images.append(src)
        if len(images) >= limit:
            break
    return images


def _normalize_post_images(raw_images, content_html: str):
    if not isinstance(raw_images, list):
        raw_images = []

    images: list[str] = []
    for item in raw_images:
        if isinstance(item, str):
            value = item.strip()
            if value:
                images.append(value)
        if len(images) >= 3:
            break

    if images:
        return images

    return _extract_images_from_html(content_html, limit=3)


def _user_to_login_payload(user):
    return user_payload(user)


def _format_mmdd(dt: datetime):
    return localtime(dt).strftime('%m-%d')


def _serialize_post(post: Post, viewer: User | None):
    is_liked = False
    is_favorited = False
    is_following_author = False

    if viewer and viewer.is_authenticated:
        interaction = PostInteraction.objects.filter(user=viewer, post=post).first()
        if interaction:
            is_liked = interaction.is_liked
            is_favorited = interaction.is_favorited
        is_following_author = Follow.objects.filter(follower=viewer, followee=post.author).exists()

    images = post.images if isinstance(post.images, list) else []
    if not images:
        images = _extract_images_from_html(post.content_html, limit=3)

    author_profile = getattr(post.author, 'profile', None)
    return {
        'id': post.id,
        'title': post.title,
        'summary': post.summary,
        'contentHtml': post.content_html,
        'author': display_name(post.author),
        'authorId': post.author_id,
        'authorAvatarText': post.author.username[:1] if post.author.username else 'U',
        'authorAvatarUrl': author_profile.avatar_url if author_profile else '',
        'time': _format_mmdd(post.created_at),
        'tags': post.tags,
        'images': images,
        'comments': post.comments_count,
        'likes': post.likes_count,
        'moderationStatus': post.moderation_status,
        'reviewReason': post.review_reason,
        'isLiked': is_liked,
        'isFavorited': is_favorited,
        'isFollowingAuthor': is_following_author,
    }


def _build_user_notifications(viewer: User):
    if not viewer or not viewer.is_authenticated:
        return []

    my_post_ids = list(Post.objects.filter(author=viewer).values_list('id', flat=True))
    my_comment_ids = list(Comment.objects.filter(author=viewer).values_list('id', flat=True))

    target_filter = Q(target_type='user', target_id=viewer.id)
    if my_post_ids:
        target_filter |= Q(target_type='post', target_id__in=my_post_ids)
    if my_comment_ids:
        target_filter |= Q(target_type='comment', target_id__in=my_comment_ids)

    logs = (
        AuditLog.objects.select_related('actor')
        .filter(target_filter)
        .exclude(actor_id=viewer.id)
        .order_by('-created_at')[:50]
    )

    action_title_map = {
        'post.review': '帖子审核状态变更',
        'comment.hide': '评论被隐藏',
        'comment.restore': '评论已恢复',
        'comment.delete': '评论被删除',
        'user.roles.update': '账号角色变更',
    }

    items = []
    for log in logs:
        title = action_title_map.get(log.action, '账号相关操作通知')
        detail = log.detail if isinstance(log.detail, dict) else {}
        reason = (detail.get('reason') or '').strip() if isinstance(detail.get('reason'), str) else ''
        action_text = (detail.get('action') or '').strip() if isinstance(detail.get('action'), str) else ''
        content = f'后台执行了 {log.action} 操作。'
        if action_text:
            content = f'后台执行了 {log.action}（{action_text}）操作。'
        if reason:
            content = f'{content} 原因：{reason}'

        items.append(
            {
                'id': log.id,
                'title': title,
                'content': content,
                'time': localtime(log.created_at).strftime('%m-%d %H:%M'),
                'action': log.action,
                'targetType': log.target_type,
                'targetId': log.target_id,
                'actorName': log.actor.username if log.actor else '',
            }
        )

    return items


def _serialize_comment(comment, viewer):
    from .social import comment_dto
    from django.contrib.auth.models import AnonymousUser
    return comment_dto(comment,viewer or AnonymousUser())


# Account endpoints are isolated from community read paths.
from .accounts import (auth_register, auth_login, auth_logout, users_me,
                       user_payload, public_user_payload)


@require_GET
def community_user_profile(request: HttpRequest, user_id: int):
    user = User.objects.filter(id=user_id, is_active=True, profile__banned_at__isnull=True).first()
    if not user:
        return api_error(request, '用户不存在', status=404)

    payload = public_user_payload(user)
    from .models import CommentLike
    total_likes = PostInteraction.objects.filter(post__in=public_posts().filter(author=user),is_liked=True).count() + CommentLike.objects.filter(comment__in=visible_comments().filter(author=user,deleted_at__isnull=True)).count()

    payload['totalLikes'] = int(total_likes)

    if request.user.is_authenticated:
        from .models import UserRelation
        payload['isFollowing'] = Follow.objects.filter(follower=request.user,followee=user).exists()
        payload['isBlocked'] = UserRelation.objects.filter(owner=request.user,target=user,kind='block').exists()
        payload['isMuted'] = UserRelation.objects.filter(owner=request.user,target=user,kind='mute').exists()
    return api_success(request, payload)


@require_http_methods(['PUT'])
@api_login_required
def users_me_profile_update(request: HttpRequest):
    data = _json_body(request)
    return profile_update(request, data)


from .accounts import profile_update, display_name


@require_GET
def community_bootstrap(request: HttpRequest):

    viewer = request.user if request.user.is_authenticated else None
    post_queryset = readable_posts(request.user, own=True).select_related('author','author__profile')
    if viewer and viewer.is_authenticated:
        post_queryset = post_queryset.filter(
            Q(moderation_status=Post.MODERATION_APPROVED) | Q(author_id=viewer.id)
        )
    else:
        post_queryset = post_queryset.filter(moderation_status=Post.MODERATION_APPROVED, author__is_active=True)

    posts = [
        _serialize_post(post, viewer)
        for post in post_queryset
    ]
    comments = [
        _serialize_comment(comment, viewer)
        for comment in visible_comments().select_related('author', 'author__profile', 'post').all()[:50]
    ]

    favorite_post_ids = []
    liked_post_ids = []
    followed_author_ids = []
    followings = []

    if viewer:
        interactions = PostInteraction.objects.filter(user=viewer)
        liked_post_ids = [i.post_id for i in interactions if i.is_liked]
        favorite_post_ids = [i.post_id for i in interactions if i.is_favorited]

        followed_users = User.objects.filter(follower_relations__follower=viewer)
        followed_author_ids = [u.id for u in followed_users]
        followings = [
            {'id': u.id, 'name': u.username, 'avatarText': u.username[:1] or 'U'}
            for u in followed_users
        ]
        followings_total = len(followed_author_ids)

        user_comments = [c for c in comments if c['authorId'] == viewer.id]
    else:
        user_comments = []
        followings_total = 0

    user_comment_post_ids = {c['postId'] for c in user_comments}
    post_title_map = {
        p.id: p.title
        for p in Post.objects.filter(id__in=user_comment_post_ids).only('id', 'title')
    }

    fans = [
        {'id': u.id, 'name': u.username, 'avatarText': u.username[:1] or 'U'}
        for u in User.objects.filter(following_relations__followee=viewer)[:30]
    ] if viewer else []
    fans_total = Follow.objects.filter(followee=viewer).count() if viewer else 0
    notifications = _build_user_notifications(viewer) if viewer else []

    return api_success(
        request,
        {
            'userTestData': {
                'fans': fans,
                'followings': followings,
                'fansTotal': fans_total,
                'followingsTotal': followings_total,
                'comments': [
                    {
                        'id': c['id'],
                        'postId': c['postId'],
                        'postTitle': post_title_map.get(c['postId'], '帖子已删除'),
                        'content': c['content'],
                        'date': c['date'],
                        'likes': c['likes'],
                    }
                    for c in user_comments
                ],
                'favoritePostIds': favorite_post_ids,
            },
            'interactionTestData': {
                'likedPostIds': liked_post_ids,
                'favoritedPostIds': favorite_post_ids,
                'followedAuthorIds': followed_author_ids,
            },
            'posts': posts,
            'comments': comments,
            'notifications': notifications,
        },
    )


@require_GET
def community_recommend_status(request: HttpRequest):
    status_path: Path = get_recsys_status_path()
    if not status_path.exists():
        return api_success(
            request,
            {
                'status': 'unknown',
                'message': '暂无训练状态，请先执行 train_recsys',
            },
        )

    try:
        payload = json.loads(status_path.read_text(encoding='utf-8'))
    except Exception:
        payload = {'status': 'unknown', 'message': '训练状态文件解析失败'}

    return api_success(request, payload)


@require_http_methods(['POST'])
def admin_auth_login(request: HttpRequest):
    from .accounts import text, limited
    if limited(request,'admin.login',30):return api_error(request,'请求过于频繁，请稍后再试',429)
    data = _json_body(request)
    account = text(data,'account').strip()
    password = text(data,'password')
    if not account:
        return api_error(request, 'account 不能为空', status=400)

    user = User.objects.filter(username=account).first() or User.objects.filter(email=account).first()
    if not user:
        return api_error(request, '账号不存在', status=404)

    auth_user = authenticate(request, username=user.username, password=password)
    if not auth_user:
        return api_error(request, '密码错误', status=401)
    if not auth_user.is_staff or not auth_user.is_active:
        return api_error(request, '非管理员账号', status=403)

    profile=getattr(auth_user,'profile',None)
    if profile and (profile.banned_at or profile.requires_verification and not profile.email_verified):return api_error(request,'账号不可用于管理登录',403)
    request.session.cycle_key()
    from django.middleware.csrf import rotate_token
    rotate_token(request)
    request.session[ADMIN_SESSION_KEY] = auth_user.id
    request.session['community_admin_auth_hash'] = auth_user.get_session_auth_hash()
    request.session.modified = True
    return api_success(request, _user_to_login_payload(auth_user))


@require_http_methods(['POST'])
@api_admin_required
def admin_auth_logout(request: HttpRequest):
    request.session.pop(ADMIN_SESSION_KEY, None)
    request.session.modified = True
    return api_success(request, {'success': True})


@require_GET
@api_admin_required
def admin_auth_me(request: HttpRequest):
    return api_success(request, _user_to_login_payload(request.admin_user))


@require_GET
@api_admin_required
def admin_dashboard_overview(request: HttpRequest):
    today = timezone.now().date()
    data = {
        'postPendingCount': Post.objects.filter(moderation_status=Post.MODERATION_PENDING,deleted_at__isnull=True).count(),
        'commentHiddenCount': Comment.objects.filter(is_hidden=True,deleted_at__isnull=True).count(),
        'auditEvents24h': AuditLog.objects.filter(created_at__gte=timezone.now() - timedelta(hours=24)).count(),
    }
    return api_success(request, data)


@require_GET
@api_admin_required
def admin_posts(request: HttpRequest):
    status = (request.GET.get('status') or '').strip()
    keyword = (request.GET.get('keyword') or '').strip().lower()
    queryset = Post.objects.select_related('author', 'reviewed_by').all().order_by('-created_at')
    if status:
        queryset = queryset.filter(moderation_status=status)
    if keyword:
        queryset = queryset.filter(Q(title__icontains=keyword) | Q(author__username__icontains=keyword))

    page_items, pagination = _paginate(request, queryset)
    items = [
        {
            'id': p.id,
            'title': p.title,
            'author': p.author.username,
            'authorId': p.author_id,
            'status': p.moderation_status,
            'reviewReason': p.review_reason,
            'likes': p.likes_count,
            'comments': p.comments_count,
            'createdAt': localtime(p.created_at).isoformat(),
            'reviewedAt': localtime(p.reviewed_at).isoformat() if p.reviewed_at else None,
            'reviewedBy': p.reviewed_by.username if p.reviewed_by else '',
        }
        for p in page_items
    ]
    return api_success(request, {'items': items, 'pagination': pagination})


@require_GET
@api_admin_required
def admin_post_detail(request: HttpRequest, post_id: int):
    post = Post.objects.select_related('author', 'reviewed_by').filter(id=post_id).first()
    if not post:
        return api_error(request, '帖子不存在', status=404)

    return api_success(
        request,
        {
            'id': post.id,
            'title': post.title,
            'summary': post.summary,
            'contentHtml': post.content_html,
            'author': display_name(post.author),
            'status': post.moderation_status,
            'reviewReason': post.review_reason,
            'reviewedBy': post.reviewed_by.username if post.reviewed_by else '',
            'reviewedAt': localtime(post.reviewed_at).isoformat() if post.reviewed_at else None,
        },
    )


@require_http_methods(['POST'])
@api_admin_required
@transaction.atomic
def admin_post_review(request: HttpRequest, post_id: int):
    data = _json_body(request)
    from .accounts import text
    action = text(data,'action').strip()
    reason = text(data,'reason').strip()
    if len(reason)>500:return api_error(request,'原因最多500字')
    post = Post.objects.select_for_update().filter(id=post_id,deleted_at__isnull=True).first()
    if not post:
        return api_error(request, '帖子不存在', status=404)

    action_to_status = {
        'approve': Post.MODERATION_APPROVED,
        'reject': Post.MODERATION_REJECTED,
        'offline': Post.MODERATION_OFFLINE,
        'pending': Post.MODERATION_PENDING,
    }
    if action not in action_to_status:
        return api_error(request, '无效审核动作', status=400)
    if action in {'reject', 'offline'} and not reason:
        return api_error(request, '驳回/下架时必须填写原因', status=400)

    post.moderation_status = action_to_status[action]
    post.review_reason = reason
    post.reviewed_by = request.admin_user
    post.reviewed_at = timezone.now()
    post.save(update_fields=['moderation_status', 'review_reason', 'reviewed_by', 'reviewed_at'])
    _write_audit_log(request, 'post.review', 'post', post.id, {'action': action, 'reason': reason})

    return api_success(
        request,
        {
            'id': post.id,
            'status': post.moderation_status,
            'reviewReason': post.review_reason,
            'reviewedBy': request.admin_user.username,
            'reviewedAt': localtime(post.reviewed_at).isoformat() if post.reviewed_at else None,
        },
    )


@require_http_methods(['POST'])
@api_admin_required
@transaction.atomic
def admin_post_batch_review(request: HttpRequest):
    data = _json_body(request)
    post_ids = data.get('postIds') or []
    from .accounts import text
    action = text(data,'action').strip()
    reason = text(data,'reason').strip()
    if len(reason)>500:return api_error(request,'原因最多500字')

    if not isinstance(post_ids, list) or not post_ids:
        return api_error(request, 'postIds 不能为空', status=400)

    normalized_ids: list[int] = []
    for value in post_ids:
        try:
            normalized = int(value)
        except (TypeError, ValueError):
            return api_error(request, 'postIds 必须为数字数组', status=400)
        if normalized > 0:
            normalized_ids.append(normalized)

    if not normalized_ids:
        return api_error(request, 'postIds 不能为空', status=400)

    action_to_status = {
        'approve': Post.MODERATION_APPROVED,
        'reject': Post.MODERATION_REJECTED,
        'offline': Post.MODERATION_OFFLINE,
        'pending': Post.MODERATION_PENDING,
    }
    if action not in action_to_status:
        return api_error(request, '无效审核动作', status=400)
    if action in {'reject', 'offline'} and not reason:
        return api_error(request, '驳回/下架时必须填写原因', status=400)

    now = timezone.now()
    target_status = action_to_status[action]
    updated = Post.objects.filter(id__in=normalized_ids,deleted_at__isnull=True).update(
        moderation_status=target_status,
        review_reason=reason,
        reviewed_by=request.admin_user,
        reviewed_at=now,
    )

    for post_id in normalized_ids:
        _write_audit_log(request, 'post.review', 'post', post_id, {'action': action, 'reason': reason, 'batch': True})

    return api_success(
        request,
        {
            'updated': updated,
            'status': target_status,
            'postIds': normalized_ids,
            'reviewReason': reason,
            'reviewedBy': request.admin_user.username,
            'reviewedAt': localtime(now).isoformat(),
        },
    )


@require_GET
@api_admin_required
def admin_comments(request: HttpRequest):
    keyword = (request.GET.get('keyword') or '').strip()
    visibility = (request.GET.get('visibility') or '').strip()
    queryset = Comment.objects.select_related('author', 'post').all().order_by('-created_at')
    if keyword:
        queryset = queryset.filter(Q(content__icontains=keyword) | Q(author__username__icontains=keyword))
    if visibility == 'hidden':
        queryset = queryset.filter(is_hidden=True)
    elif visibility == 'visible':
        queryset = queryset.filter(is_hidden=False)

    page_items, pagination = _paginate(request, queryset)
    items = [
        {
            'id': c.id,
            'content': c.content,
            'author': c.author.username,
            'authorId': c.author_id,
            'postId': c.post_id,
            'postTitle': c.post.title,
            'isHidden': c.is_hidden,
            'createdAt': localtime(c.created_at).isoformat(),
        }
        for c in page_items
    ]
    return api_success(request, {'items': items, 'pagination': pagination})


@require_http_methods(['POST'])
@api_admin_required
@transaction.atomic
def admin_comment_hide(request: HttpRequest, comment_id: int):
    comment = Comment.objects.select_for_update().filter(id=comment_id,deleted_at__isnull=True).first()
    if not comment:
        return api_error(request, '评论不存在', status=404)
    comment.is_hidden = True
    comment.save(update_fields=['is_hidden'])
    _write_audit_log(request, 'comment.hide', 'comment', comment_id)
    return api_success(request, {'id': comment_id, 'isHidden': True})


@require_http_methods(['POST'])
@api_admin_required
@transaction.atomic
def admin_comment_restore(request: HttpRequest, comment_id: int):
    comment = Comment.objects.select_for_update().filter(id=comment_id,deleted_at__isnull=True).first()
    if not comment:
        return api_error(request, '评论不存在', status=404)
    comment.is_hidden = False
    comment.save(update_fields=['is_hidden'])
    _write_audit_log(request, 'comment.restore', 'comment', comment_id)
    return api_success(request, {'id': comment_id, 'isHidden': False})


@require_http_methods(['DELETE'])
@api_admin_required
@transaction.atomic
def admin_comment_delete(request: HttpRequest, comment_id: int):
    comment = Comment.objects.select_for_update().filter(id=comment_id,deleted_at__isnull=True).first()
    if not comment:
        return api_error(request, '评论不存在', status=404)
    post = comment.post
    comment.deleted_at = timezone.now()
    comment.content = ''
    comment.save(update_fields=['deleted_at','content'])
    post.comments_count = post.comments.filter(is_hidden=False,deleted_at__isnull=True,author__is_active=True).count()
    post.save(update_fields=['comments_count'])
    _write_audit_log(request, 'comment.delete', 'comment', comment_id)
    return api_success(request, {'id': comment_id, 'deleted': True})


@require_GET
@api_admin_required
def admin_users(request: HttpRequest):
    keyword = (request.GET.get('keyword') or '').strip()
    queryset = User.objects.all().order_by('-id')
    if keyword:
        queryset = queryset.filter(Q(username__icontains=keyword) | Q(email__icontains=keyword))

    page_items, pagination = _paginate(request, queryset)
    items = [
        {
            'id': user.id,
            'name': user.username,
            **({'email': user.email} if request.admin_user.is_superuser else {}),
            'mutedUntil': user.profile.muted_until.isoformat() if hasattr(user,'profile') and user.profile.muted_until else None,
            'banned': bool(hasattr(user,'profile') and user.profile.banned_at),
            'isActive': user.is_active,
            'isAdmin': user.is_staff,
            'roles': _user_roles(user),
        }
        for user in page_items
    ]
    return api_success(request, {'items': items, 'pagination': pagination})


@require_http_methods(['PUT'])
@api_admin_required
@transaction.atomic
def admin_user_roles(request: HttpRequest, user_id: int):
    if not request.admin_user.is_superuser:
        return api_error(request, '仅超级管理员可修改角色', status=403)
    data = _json_body(request)

    if 'isAdmin' in data and not isinstance(data.get('isAdmin'), bool):
        return api_error(request, 'isAdmin 参数格式错误', status=400)

    role_names = data.get('roles') if isinstance(data.get('roles'), list) else None

    if 'roles' in data and (not isinstance(data['roles'],list) or any(not isinstance(role,str) for role in data['roles'])):return api_error(request,'角色必须是字符串列表')
    if 'roles' not in data and 'isAdmin' not in data:return api_error(request,'请提供角色变更')
    user = User.objects.select_for_update().filter(id=user_id).first()
    if not user:
        return api_error(request, '用户不存在', status=404)

    if user.is_superuser and ('isAdmin' in data and not data['isAdmin'] or role_names is not None and 'super_admin' not in role_names):
        if User.objects.filter(is_superuser=True,is_active=True,profile__banned_at__isnull=True).count() <= 1:return api_error(request,'不能降级最后一个超级管理员',409)
    if role_names is not None:
        if any(name not in {'content_moderator','operations','auditor','super_admin'} for name in role_names):return api_error(request,'角色无效')
        if 'super_admin' in role_names and not user.is_superuser:return api_error(request,'超级管理员须通过显式管理命令授权',400)
        _ensure_admin_groups()
        groups = list(Group.objects.filter(name__in=role_names))
        user.groups.set(groups)
        user.is_staff = bool(groups)
        if user.is_superuser and 'super_admin' not in role_names:user.is_superuser=False
        detail = {'roles': role_names}
    else:
        is_admin = bool(data.get('isAdmin'))
        user.is_staff = is_admin
        if not is_admin:user.is_superuser=False
        if is_admin and not user.is_superuser:
            group,_=Group.objects.get_or_create(name='content_moderator');user.groups.add(group)
        if not is_admin:
            user.groups.clear()
        detail = {'isAdmin': is_admin}

    user.save(update_fields=['is_staff','is_superuser'])
    _write_audit_log(request, 'user.roles.update', 'user', user_id, detail)
    return api_success(request, {'id': user.id, 'roles': _user_roles(user), 'isAdmin': user.is_staff})


@require_GET
@api_admin_required
def admin_audit_logs(request: HttpRequest):
    actor_id = request.GET.get('actorId')
    action = (request.GET.get('action') or '').strip()
    target_type = (request.GET.get('targetType') or '').strip()

    queryset = AuditLog.objects.select_related('actor').all()
    if actor_id:
        if not str(actor_id).isdigit():return api_error(request,'actorId必须是整数')
        queryset = queryset.filter(actor_id=actor_id)
    if action:
        queryset = queryset.filter(action__icontains=action)
    if target_type:
        queryset = queryset.filter(target_type=target_type)

    if not request.admin_user.is_superuser and not request.admin_user.groups.filter(name='auditor').exists():queryset=queryset.filter(actor=request.admin_user)
    page_items, pagination = _paginate(request, queryset)
    items = [
        {
            'id': log.id,
            'actorId': log.actor_id,
            'actorName': log.actor.username if log.actor else '',
            'action': log.action,
            'targetType': log.target_type,
            'targetId': log.target_id,
            'detail': log.detail,
            'ip': log.ip,
            'createdAt': localtime(log.created_at).isoformat(),
        }
        for log in page_items
    ]
    return api_success(request, {'items': items, 'pagination': pagination})
