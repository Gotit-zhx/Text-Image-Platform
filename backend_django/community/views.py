import json
from functools import wraps
from datetime import datetime
from pathlib import Path

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import HttpRequest, JsonResponse
from django.utils.timezone import localtime
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods

from .models import Comment, CommentLike, Follow, Post, PostInteraction, Profile
from .http import api_error, api_success
from .recommendation import recommended_post_ids_for_user
from .recsys_pipeline import get_recsys_status_path


def api_login_required(view_func):
    @wraps(view_func)
    def _wrapped(request: HttpRequest, *args, **kwargs):
        if not request.user.is_authenticated:
            return api_error(request, '未登录', status=401)
        return view_func(request, *args, **kwargs)

    return _wrapped


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
    return {
        'id': user.id,
        'name': user.username,
        'email': user.email,
        'avatarText': user.username[:1] if user.username else 'U',
        'avatarUrl': profile.avatar_url if profile else '',
        'gender': profile.gender if profile else 'private',
        'fans': followers,
        'follows': follows,
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
        'isLiked': is_liked,
        'isFavorited': is_favorited,
        'isFollowingAuthor': is_following_author,
    }


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
    if Post.objects.exists():
        return

    demo_users: list[User] = []
    for idx in range(1, 21):
        username = f'用户{idx}'
        email = f'demo_user_{idx}@example.com'
        user, _ = User.objects.get_or_create(username=username, defaults={'email': email})
        user.email = email
        user.set_password('123456')
        user.save(update_fields=['email', 'password'])
        _ensure_profile(user)
        demo_users.append(user)

    topics = [
        ('摄影', '夜景', '街拍'),
        ('手账', '模板', '效率'),
        ('徒步', '旅行', '装备'),
        ('咖啡', '拉花', '日常'),
        ('编程', '前端', '后端'),
        ('读书', '笔记', '成长'),
    ]

    created_posts: list[Post] = []
    for u_idx, user in enumerate(demo_users, start=1):
        post_count = (u_idx * 7) % 21
        for p_idx in range(post_count):
            tags = list(topics[(u_idx + p_idx) % len(topics)])
            title = f'{user.username} 的演示帖子 {p_idx + 1}'
            post = Post.objects.create(
                author=user,
                title=title,
                summary=f'这是 {user.username} 的第 {p_idx + 1} 篇演示文章。',
                content_html=f'<p>{title} 正文演示内容。</p>',
                tags=tags,
                images=['linear-gradient(135deg, #8ec5fc, #e0c3fc)'] if p_idx % 3 == 0 else [],
                likes_count=((u_idx * (p_idx + 3)) % 500) + (20 if p_idx % 2 == 0 else 0),
                comments_count=0,
            )
            created_posts.append(post)

    if not created_posts:
        return

    viewer = demo_users[-1]
    for followed in demo_users[:10]:
        if followed.id != viewer.id:
            Follow.objects.get_or_create(follower=viewer, followee=followed)

    for idx, post in enumerate(created_posts):
        interaction, _ = PostInteraction.objects.get_or_create(user=viewer, post=post)
        interaction.is_liked = idx % 2 == 0
        interaction.is_favorited = idx % 3 == 0
        interaction.save(update_fields=['is_liked', 'is_favorited'])

        if idx % 4 == 0:
            Comment.objects.get_or_create(post=post, author=viewer, content='演示评论：内容已读，欢迎交流。')

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
def community_bootstrap(request: HttpRequest):
    _seed_demo_data()

    viewer = request.user if request.user.is_authenticated else None
    posts = [_serialize_post(post, viewer) for post in Post.objects.select_related('author', 'author__profile').all()]
    comments = [
        _serialize_comment(comment, viewer)
        for comment in Comment.objects.select_related('author', 'author__profile', 'post').all()[:50]
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

        user_comments = [c for c in comments if c['authorId'] == viewer.id]
    else:
        user_comments = []

    fans = [
        {'id': u.id, 'name': u.username, 'avatarText': u.username[:1] or 'U'}
        for u in User.objects.filter(following_relations__followee=viewer)[:30]
    ] if viewer else []

    return api_success(
        request,
        {
            'userTestData': {
                'fans': fans,
                'followings': followings,
                'comments': [
                    {
                        'id': c['id'],
                        'postId': c['postId'],
                        'postTitle': Post.objects.filter(id=c['postId']).values_list('title', flat=True).first() or '帖子已删除',
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
        },
    )


@require_GET
def community_search(request: HttpRequest):
    nav = request.GET.get('nav', '推荐')
    q = (request.GET.get('q') or '').strip().lower()

    viewer = request.user if request.user.is_authenticated else None
    queryset = Post.objects.select_related('author', 'author__profile').all()

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

    posts = [_serialize_post(post, viewer) for post in queryset]
    return api_success(request, {'posts': posts})


@require_GET
def community_recommend(request: HttpRequest):
    _seed_demo_data()
    viewer = request.user if request.user.is_authenticated else None
    user_id = viewer.id if viewer else None

    try:
        k = max(1, min(100, int(request.GET.get('k', 20))))
    except ValueError:
        k = 20

    rec_ids = recommended_post_ids_for_user(user_id, k=k)
    posts_map = {
        p.id: p
        for p in Post.objects.filter(id__in=rec_ids).select_related('author', 'author__profile')
    }
    ordered_posts = [posts_map[item_id] for item_id in rec_ids if item_id in posts_map]
    if len(ordered_posts) < k:
        existing_ids = {p.id for p in ordered_posts}
        fallback = (
            Post.objects.exclude(id__in=existing_ids)
            .select_related('author', 'author__profile')
            .order_by('-likes_count', '-created_at')[: k - len(ordered_posts)]
        )
        ordered_posts.extend(list(fallback))

    return api_success(request, {'posts': [_serialize_post(post, viewer) for post in ordered_posts]})


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
