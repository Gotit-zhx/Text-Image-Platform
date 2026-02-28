import json
from functools import wraps
from datetime import datetime, timedelta
from pathlib import Path

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import Group, User
from django.db.models import Q
from django.db import models
from django.http import HttpRequest, JsonResponse
from django.utils import timezone
from django.utils.timezone import localtime
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods

from .models import AuditLog, Comment, CommentLike, Follow, Post, PostInteraction, Profile
from .http import api_error, api_success
from .recommendation import recommended_post_ids_for_user
from .recsys_pipeline import get_recsys_status_path

ADMIN_SESSION_KEY = 'community_admin_user_id'


def _get_admin_session_user(request: HttpRequest):
    admin_user_id = request.session.get(ADMIN_SESSION_KEY)
    if admin_user_id:
        admin_user = User.objects.filter(id=admin_user_id, is_staff=True, is_active=True).first()
        if admin_user:
            return admin_user
        request.session.pop(ADMIN_SESSION_KEY, None)

    if request.user.is_authenticated and request.user.is_staff and request.user.is_active:
        return request.user

    return None


def api_login_required(view_func):
    @wraps(view_func)
    def _wrapped(request: HttpRequest, *args, **kwargs):
        if not request.user.is_authenticated:
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


def _ensure_default_admin():
    _ensure_admin_groups()
    admin_user, _ = User.objects.get_or_create(username='管理员', defaults={'email': 'admin@example.com'})
    admin_user.email = 'admin@example.com'
    admin_user.is_staff = True
    admin_user.is_superuser = True
    admin_user.set_password('123456')
    admin_user.save(update_fields=['email', 'is_staff', 'is_superuser', 'password'])
    _ensure_profile(admin_user)
    admin_group = Group.objects.filter(name='super_admin').first()
    if admin_group:
        admin_user.groups.add(admin_group)
    return admin_user


def _write_audit_log(request: HttpRequest, action: str, target_type: str, target_id: int, detail: dict | None = None):
    actor = getattr(request, 'admin_user', None)
    if not actor and request.user.is_authenticated:
        actor = request.user

    AuditLog.objects.create(
        actor=actor,
        action=action,
        target_type=target_type,
        target_id=target_id,
        detail=detail or {},
        ip=request.META.get('REMOTE_ADDR', ''),
    )


def _json_body(request: HttpRequest):
    if not request.body:
        return {}
    try:
        return json.loads(request.body.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}


def _ensure_profile(user: User):
    Profile.objects.get_or_create(user=user)


def _user_to_login_payload(user: User):
    profile = getattr(user, 'profile', None)
    followers = Follow.objects.filter(followee=user).count()
    follows = Follow.objects.filter(follower=user).count()
    roles = _user_roles(user)
    return {
        'id': user.id,
        'name': user.username,
        'email': user.email,
        'avatarText': user.username[:1] if user.username else 'U',
        'avatarUrl': profile.avatar_url if profile else '',
        'gender': profile.gender if profile else 'private',
        'fans': followers,
        'follows': follows,
        'roles': roles,
        'isAdmin': bool(user.is_staff),
    }


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

    author_profile = getattr(post.author, 'profile', None)
    return {
        'id': post.id,
        'title': post.title,
        'summary': post.summary,
        'contentHtml': post.content_html,
        'author': post.author.username,
        'authorId': post.author_id,
        'authorAvatarText': post.author.username[:1] if post.author.username else 'U',
        'authorAvatarUrl': author_profile.avatar_url if author_profile else '',
        'time': _format_mmdd(post.created_at),
        'tags': post.tags,
        'images': post.images,
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


def _serialize_comment(comment: Comment, viewer: User | None):
    liked = False
    mine = False
    if viewer and viewer.is_authenticated:
        liked = CommentLike.objects.filter(user=viewer, comment=comment).exists()
        mine = comment.author_id == viewer.id

    author_profile = getattr(comment.author, 'profile', None)
    return {
        'id': comment.id,
        'postId': comment.post_id,
        'authorId': comment.author_id,
        'author': comment.author.username,
        'authorAvatarText': comment.author.username[:1] if comment.author.username else 'U',
        'authorAvatarUrl': author_profile.avatar_url if author_profile else '',
        'date': _format_mmdd(comment.created_at),
        'content': comment.content,
        'likes': comment.likes_count,
        'isLiked': liked,
        'isMine': mine,
    }


def _seed_demo_data():
    _ensure_default_admin()

    if Post.objects.exists():
        return

    demo_users: list[User] = []
    for idx in range(1, 14):
        username = f'用户{idx}'
        email = f'demo_user_{idx}@example.com'
        user, _ = User.objects.get_or_create(username=username, defaults={'email': email})
        user.email = email
        user.set_password('123456')
        user.save(update_fields=['email', 'password'])
        _ensure_profile(user)
        demo_users.append(user)

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

    created_posts: list[Post] = []
    for u_idx, user in enumerate(demo_users, start=1):
        post_count = 2 + ((u_idx * 3) % 5)
        for p_idx in range(post_count):
            topic = topics[(u_idx + p_idx) % len(topics)]
            title_seed = topic['titles'][(u_idx + p_idx * 2) % len(topic['titles'])]
            summary_seed = topic['summaries'][(u_idx + p_idx) % len(topic['summaries'])]
            title = f'{title_seed}｜{user.username}'
            post = Post.objects.create(
                author=user,
                title=title,
                summary=summary_seed,
                content_html=(
                    f'<p>{summary_seed}</p>'
                    f'<p>{user.username} 在这篇内容里记录了执行步骤、踩坑点和可复用结论，方便大家直接上手。</p>'
                ),
                tags=topic['tags'],
                images=['linear-gradient(135deg, #8ec5fc, #e0c3fc)'] if p_idx % 3 == 0 else [],
                likes_count=((u_idx * (p_idx + 3)) % 500) + (20 if p_idx % 2 == 0 else 0),
                comments_count=0,
            )
            created_posts.append(post)

    if not created_posts:
        return

    for idx, user in enumerate(demo_users):
        for offset in (1, 2, 3):
            followee = demo_users[(idx + offset) % len(demo_users)]
            if followee.id != user.id:
                Follow.objects.get_or_create(follower=user, followee=followee)

    for u_idx, user in enumerate(demo_users):
        for offset in range(6):
            post = created_posts[(u_idx * 5 + offset) % len(created_posts)]
            interaction, _ = PostInteraction.objects.get_or_create(user=user, post=post)
            interaction.is_liked = offset % 2 == 0
            interaction.is_favorited = offset % 3 == 0
            interaction.save(update_fields=['is_liked', 'is_favorited'])

    for u_idx, user in enumerate(demo_users):
        for offset in range(3):
            post = created_posts[(u_idx * 7 + offset * 2) % len(created_posts)]
            if post.author_id == user.id:
                post = created_posts[(u_idx * 7 + offset * 2 + 1) % len(created_posts)]
            Comment.objects.get_or_create(
                post=post,
                author=user,
                content=comment_templates[(u_idx + offset) % len(comment_templates)],
            )

    for post in created_posts:
        post.likes_count = PostInteraction.objects.filter(post=post, is_liked=True).count()
        post.comments_count = Comment.objects.filter(post=post).count()
        post.save(update_fields=['likes_count', 'comments_count'])


@csrf_exempt
@require_http_methods(['POST'])
def auth_register(request: HttpRequest):
    data = _json_body(request)
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or '123456'

    if not email:
        return api_error(request, 'email 不能为空', status=400)

    temp_username = f'user_tmp_{int(datetime.now().timestamp())}_{User.objects.count() + 1}'
    user = User.objects.create_user(username=temp_username, email=email, password=password)
    user.username = f'用户{user.id}'
    user.save(update_fields=['username'])
    _ensure_profile(user)
    login(request, user)
    return api_success(request, _user_to_login_payload(user), status=201)


@csrf_exempt
@require_http_methods(['POST'])
def auth_login(request: HttpRequest):
    data = _json_body(request)
    account = (data.get('account') or '').strip()
    password = data.get('password') or '123456'

    if not account:
        return api_error(request, 'account 不能为空', status=400)

    user = User.objects.filter(username=account).first() or User.objects.filter(email=account).first()
    if not user and '@' in account:
        user = User.objects.create_user(username=f'user_tmp_{int(datetime.now().timestamp())}', email=account, password=password)
        user.username = f'用户{user.id}'
        user.save(update_fields=['username'])
        _ensure_profile(user)

    if not user:
        return api_error(request, '账号不存在', status=404)

    auth_user = authenticate(request, username=user.username, password=password)
    if not auth_user:
        return api_error(request, '密码错误', status=401)

    login(request, auth_user)
    return api_success(request, _user_to_login_payload(auth_user))


@csrf_exempt
@require_http_methods(['POST'])
def auth_logout(request: HttpRequest):
    logout(request)
    return api_success(request, {'success': True})


@require_GET
@api_login_required
def users_me(request: HttpRequest):
    return api_success(request, _user_to_login_payload(request.user))


@require_GET
def community_user_profile(request: HttpRequest, user_id: int):
    user = User.objects.filter(id=user_id).first()
    if not user:
        return api_error(request, '用户不存在', status=404)

    payload = _user_to_login_payload(user)
    total_likes = (
        Post.objects.filter(author=user).aggregate(total=models.Sum('likes_count')).get('total') or 0
    ) + (
        Comment.objects.filter(author=user).aggregate(total=models.Sum('likes_count')).get('total') or 0
    )

    payload['totalLikes'] = int(total_likes)
    return api_success(request, payload)


@csrf_exempt
@require_http_methods(['PUT'])
@api_login_required
def users_me_profile_update(request: HttpRequest):
    data = _json_body(request)
    name = (data.get('name') or '').strip()
    avatar_url = (data.get('avatarUrl') or '').strip()
    gender = (data.get('gender') or 'private').strip()

    if not name:
        return api_error(request, '昵称不能为空', status=400)

    if gender not in {'male', 'female', 'private'}:
        return api_error(request, 'gender 非法', status=400)

    duplicated = User.objects.filter(username=name).exclude(id=request.user.id).exists()
    if duplicated:
        return api_error(request, '昵称已被占用', status=409)

    request.user.username = name
    request.user.save(update_fields=['username'])

    profile, _ = Profile.objects.get_or_create(user=request.user)
    profile.avatar_url = avatar_url
    profile.gender = gender
    profile.save(update_fields=['avatar_url', 'gender'])

    return api_success(request, _user_to_login_payload(request.user))


@require_GET
def community_bootstrap(request: HttpRequest):
    _seed_demo_data()

    viewer = request.user if request.user.is_authenticated else None
    post_queryset = Post.objects.select_related('author', 'author__profile').all()
    if viewer and viewer.is_authenticated:
        post_queryset = post_queryset.filter(
            Q(moderation_status=Post.MODERATION_APPROVED) | Q(author_id=viewer.id)
        )
    else:
        post_queryset = post_queryset.filter(moderation_status=Post.MODERATION_APPROVED)

    posts = [
        _serialize_post(post, viewer)
        for post in post_queryset
    ]
    comments = [
        _serialize_comment(comment, viewer)
        for comment in Comment.objects.filter(is_hidden=False).select_related('author', 'author__profile', 'post').all()[:50]
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
def community_search(request: HttpRequest):
    nav = request.GET.get('nav', '推荐')
    q = (request.GET.get('q') or '').strip().lower()
    page, page_size = _parse_page_params(request)

    viewer = request.user if request.user.is_authenticated else None
    queryset = Post.objects.filter(moderation_status=Post.MODERATION_APPROVED).select_related('author', 'author__profile').all()

    if nav == '热门':
        queryset = queryset.order_by('-likes_count', '-created_at')
    elif nav == '更新':
        queryset = queryset.order_by('-created_at')
    elif nav == '关注' and viewer:
        followed_ids = Follow.objects.filter(follower=viewer).values_list('followee_id', flat=True)
        queryset = queryset.filter(author_id__in=followed_ids).order_by('-created_at')
    else:
        queryset = queryset.order_by('-likes_count', '-created_at')

    if q:
        filtered = []
        for post in queryset:
            source = ' '.join([post.title, post.summary, post.author.username, *post.tags]).lower()
            if q in source:
                filtered.append(post)
        queryset = filtered

    if isinstance(queryset, list):
        total = len(queryset)
        offset = (page - 1) * page_size
        page_items = queryset[offset: offset + page_size]
    else:
        total = queryset.count()
        offset = (page - 1) * page_size
        page_items = queryset[offset: offset + page_size]

    posts = [_serialize_post(post, viewer) for post in page_items]
    return api_success(
        request,
        {
            'posts': posts,
            'pagination': {
                'total': total,
                'page': page,
                'pageSize': page_size,
                'hasMore': offset + len(posts) < total,
            },
        },
    )


@require_GET
def community_recommend(request: HttpRequest):
    _seed_demo_data()
    viewer = request.user if request.user.is_authenticated else None
    user_id = viewer.id if viewer else None
    page, page_size = _parse_page_params(request)

    try:
        k = max(1, min(100, int(request.GET.get('k', 20))))
    except ValueError:
        k = 20

    k = max(k, page * page_size)

    rec_ids = recommended_post_ids_for_user(user_id, k=k)
    posts_map = {
        p.id: p
        for p in Post.objects.filter(id__in=rec_ids, moderation_status=Post.MODERATION_APPROVED).select_related('author', 'author__profile')
    }
    ordered_posts = [posts_map[item_id] for item_id in rec_ids if item_id in posts_map]
    if len(ordered_posts) < k:
        existing_ids = {p.id for p in ordered_posts}
        fallback = (
            Post.objects.exclude(id__in=existing_ids).filter(moderation_status=Post.MODERATION_APPROVED)
            .select_related('author', 'author__profile')
            .order_by('-likes_count', '-created_at')[: k - len(ordered_posts)]
        )
        ordered_posts.extend(list(fallback))

    total = Post.objects.filter(moderation_status=Post.MODERATION_APPROVED).count()
    offset = (page - 1) * page_size
    paged_posts = ordered_posts[offset: offset + page_size]

    return api_success(
        request,
        {
            'posts': [_serialize_post(post, viewer) for post in paged_posts],
            'pagination': {
                'total': total,
                'page': page,
                'pageSize': page_size,
                'hasMore': offset + len(paged_posts) < total,
            },
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


@csrf_exempt
@require_http_methods(['POST'])
@api_login_required
def posts_create(request: HttpRequest):
    data = _json_body(request)
    title = (data.get('title') or '').strip()
    content_html = data.get('contentHtml') or ''

    if not title:
        return api_error(request, 'title 不能为空', status=400)

    post = Post.objects.create(
        author=request.user,
        title=title,
        summary=data.get('summary') or '',
        content_html=content_html,
        tags=data.get('tags') or [],
        images=data.get('images') or [],
    )
    return api_success(request, _serialize_post(post, request.user), status=201)


@csrf_exempt
@require_http_methods(['PUT'])
@api_login_required
def posts_update(request: HttpRequest, post_id: int):
    data = _json_body(request)
    post = Post.objects.filter(id=post_id).select_related('author').first()
    if not post:
        return api_error(request, '帖子不存在', status=404)

    if post.author_id != request.user.id:
        return api_error(request, '仅作者可编辑', status=403)

    post.title = (data.get('title') or post.title).strip()
    post.summary = data.get('summary') or post.summary
    post.content_html = data.get('contentHtml') or post.content_html
    post.tags = data.get('tags') or post.tags
    post.images = data.get('images') or post.images
    post.save()

    return api_success(
        request,
        {
            'title': post.title,
            'summary': post.summary,
            'contentHtml': post.content_html,
            'tags': post.tags,
            'images': post.images,
        },
    )


@csrf_exempt
@require_http_methods(['POST'])
@api_login_required
def comments_create(request: HttpRequest, post_id: int):
    data = _json_body(request)
    post = Post.objects.filter(id=post_id).first()
    if not post:
        return api_error(request, '帖子不存在', status=404)

    content = (data.get('content') or '').strip()
    if not content:
        return api_error(request, '评论不能为空', status=400)

    comment = Comment.objects.create(post=post, author=request.user, content=content)
    post.comments_count = post.comments.count()
    post.save(update_fields=['comments_count'])
    return api_success(request, _serialize_comment(comment, request.user), status=201)


@csrf_exempt
@require_http_methods(['POST'])
@api_login_required
def post_like_toggle(request: HttpRequest, post_id: int):
    data = _json_body(request)
    will_like = bool(data.get('isLiked'))
    post = Post.objects.filter(id=post_id).first()
    if not post:
        return api_error(request, '帖子不存在', status=404)

    interaction, _ = PostInteraction.objects.get_or_create(user=request.user, post=post)
    interaction.is_liked = will_like
    interaction.save(update_fields=['is_liked'])

    post.likes_count = PostInteraction.objects.filter(post=post, is_liked=True).count()
    post.save(update_fields=['likes_count'])
    return api_success(request, {'postId': post.id, 'isLiked': will_like})


@csrf_exempt
@require_http_methods(['POST'])
@api_login_required
def post_favorite_toggle(request: HttpRequest, post_id: int):
    data = _json_body(request)
    will_favorite = bool(data.get('isFavorited'))
    post = Post.objects.filter(id=post_id).first()
    if not post:
        return api_error(request, '帖子不存在', status=404)

    interaction, _ = PostInteraction.objects.get_or_create(user=request.user, post=post)
    interaction.is_favorited = will_favorite
    interaction.save(update_fields=['is_favorited'])

    return api_success(request, {'postId': post.id, 'isFavorited': will_favorite})


@csrf_exempt
@require_http_methods(['POST'])
@api_login_required
def author_follow_toggle(request: HttpRequest, author_id: int):
    data = _json_body(request)
    will_follow = bool(data.get('isFollowing'))

    if request.user.id == author_id:
        return api_error(request, '不能关注自己', status=400)

    target = User.objects.filter(id=author_id).first()
    if not target:
        return api_error(request, '用户不存在', status=404)

    if will_follow:
        Follow.objects.get_or_create(follower=request.user, followee=target)
    else:
        Follow.objects.filter(follower=request.user, followee=target).delete()

    return api_success(request, {'authorId': author_id, 'isFollowing': will_follow})


@csrf_exempt
@require_http_methods(['POST'])
@api_login_required
def comment_like_toggle(request: HttpRequest, comment_id: int):
    data = _json_body(request)
    will_like = bool(data.get('isLiked'))
    comment = Comment.objects.filter(id=comment_id).first()
    if not comment:
        return api_error(request, '评论不存在', status=404)

    if will_like:
        CommentLike.objects.get_or_create(user=request.user, comment=comment)
    else:
        CommentLike.objects.filter(user=request.user, comment=comment).delete()

    comment.likes_count = CommentLike.objects.filter(comment=comment).count()
    comment.save(update_fields=['likes_count'])
    return api_success(request, {'commentId': comment_id, 'isLiked': will_like})


@csrf_exempt
@require_http_methods(['DELETE'])
@api_login_required
def comment_delete(request: HttpRequest, comment_id: int):
    comment = Comment.objects.filter(id=comment_id).first()
    if not comment:
        return api_error(request, '评论不存在', status=404)

    if comment.author_id != request.user.id:
        return api_error(request, '仅作者可删除评论', status=403)

    post = comment.post
    comment.delete()
    post.comments_count = post.comments.count()
    post.save(update_fields=['comments_count'])

    return api_success(request, {'commentId': comment_id, 'deleted': True})


@csrf_exempt
@require_http_methods(['POST'])
def admin_auth_login(request: HttpRequest):
    _ensure_default_admin()
    data = _json_body(request)
    account = (data.get('account') or '').strip()
    password = data.get('password') or ''
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

    request.session[ADMIN_SESSION_KEY] = auth_user.id
    request.session.modified = True
    return api_success(request, _user_to_login_payload(auth_user))


@csrf_exempt
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
        'postPendingCount': Post.objects.filter(moderation_status=Post.MODERATION_PENDING).count(),
        'commentHiddenCount': Comment.objects.filter(is_hidden=True).count(),
        'todayActiveUsers': PostInteraction.objects.filter(post__created_at__date=today).values('user_id').distinct().count(),
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
        queryset = queryset.filter(title__icontains=keyword)

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
            'author': post.author.username,
            'status': post.moderation_status,
            'reviewReason': post.review_reason,
            'reviewedBy': post.reviewed_by.username if post.reviewed_by else '',
            'reviewedAt': localtime(post.reviewed_at).isoformat() if post.reviewed_at else None,
        },
    )


@csrf_exempt
@require_http_methods(['POST'])
@api_admin_required
def admin_post_review(request: HttpRequest, post_id: int):
    data = _json_body(request)
    action = (data.get('action') or '').strip()
    reason = (data.get('reason') or '').strip()
    post = Post.objects.filter(id=post_id).first()
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


@require_GET
@api_admin_required
def admin_comments(request: HttpRequest):
    keyword = (request.GET.get('keyword') or '').strip()
    visibility = (request.GET.get('visibility') or '').strip()
    queryset = Comment.objects.select_related('author', 'post').all().order_by('-created_at')
    if keyword:
        queryset = queryset.filter(content__icontains=keyword)
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


@csrf_exempt
@require_http_methods(['POST'])
@api_admin_required
def admin_comment_hide(request: HttpRequest, comment_id: int):
    comment = Comment.objects.filter(id=comment_id).first()
    if not comment:
        return api_error(request, '评论不存在', status=404)
    comment.is_hidden = True
    comment.save(update_fields=['is_hidden'])
    _write_audit_log(request, 'comment.hide', 'comment', comment_id)
    return api_success(request, {'id': comment_id, 'isHidden': True})


@csrf_exempt
@require_http_methods(['POST'])
@api_admin_required
def admin_comment_restore(request: HttpRequest, comment_id: int):
    comment = Comment.objects.filter(id=comment_id).first()
    if not comment:
        return api_error(request, '评论不存在', status=404)
    comment.is_hidden = False
    comment.save(update_fields=['is_hidden'])
    _write_audit_log(request, 'comment.restore', 'comment', comment_id)
    return api_success(request, {'id': comment_id, 'isHidden': False})


@csrf_exempt
@require_http_methods(['DELETE'])
@api_admin_required
def admin_comment_delete(request: HttpRequest, comment_id: int):
    comment = Comment.objects.filter(id=comment_id).first()
    if not comment:
        return api_error(request, '评论不存在', status=404)
    post = comment.post
    comment.delete()
    post.comments_count = post.comments.filter(is_hidden=False).count()
    post.save(update_fields=['comments_count'])
    _write_audit_log(request, 'comment.delete', 'comment', comment_id)
    return api_success(request, {'id': comment_id, 'deleted': True})


@require_GET
@api_admin_required
def admin_users(request: HttpRequest):
    keyword = (request.GET.get('keyword') or '').strip()
    queryset = User.objects.all().order_by('-id')
    if keyword:
        queryset = queryset.filter(username__icontains=keyword)

    page_items, pagination = _paginate(request, queryset)
    items = [
        {
            'id': user.id,
            'name': user.username,
            'email': user.email,
            'isActive': user.is_active,
            'isAdmin': user.is_staff,
            'roles': _user_roles(user),
        }
        for user in page_items
    ]
    return api_success(request, {'items': items, 'pagination': pagination})


@csrf_exempt
@require_http_methods(['PUT'])
@api_admin_required
def admin_user_roles(request: HttpRequest, user_id: int):
    if not request.admin_user.is_superuser:
        return api_error(request, '仅超级管理员可修改角色', status=403)
    data = _json_body(request)
    role_names = data.get('roles') or []
    if not isinstance(role_names, list):
        return api_error(request, 'roles 参数格式错误', status=400)

    user = User.objects.filter(id=user_id).first()
    if not user:
        return api_error(request, '用户不存在', status=404)

    _ensure_admin_groups()
    groups = list(Group.objects.filter(name__in=role_names))
    user.groups.set(groups)
    user.is_staff = bool(groups)
    user.save(update_fields=['is_staff'])
    _write_audit_log(request, 'user.roles.update', 'user', user_id, {'roles': role_names})
    return api_success(request, {'id': user.id, 'roles': _user_roles(user), 'isAdmin': user.is_staff})


@require_GET
@api_admin_required
def admin_audit_logs(request: HttpRequest):
    actor_id = request.GET.get('actorId')
    action = (request.GET.get('action') or '').strip()
    target_type = (request.GET.get('targetType') or '').strip()

    queryset = AuditLog.objects.select_related('actor').all()
    if actor_id:
        queryset = queryset.filter(actor_id=actor_id)
    if action:
        queryset = queryset.filter(action__icontains=action)
    if target_type:
        queryset = queryset.filter(target_type=target_type)

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
