"""Shared social visibility, discussion, relations and durable events."""
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q, Count, Exists, OuterRef
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods
from .accounts import body, display_name, public_user_payload, limited
from .http import api_error, api_success
from .models import Comment, CommentLike, Follow, Post, PostInteraction, Notification, UserRelation, Profile
from .visibility import public_posts, visible_comments

def blocked(a, b):
    if not a or not b:
        return False
    return UserRelation.objects.filter(kind='block').filter(Q(owner_id=a, target_id=b) | Q(owner_id=b, target_id=a)).exists()

def consumption(query, viewer):
    if not viewer.is_authenticated:
        return query
    hidden = UserRelation.objects.filter(owner=viewer).values_list('target_id', flat=True)
    reverse = UserRelation.objects.filter(kind='block', target=viewer).values_list('owner_id', flat=True)
    return query.exclude(author_id__in=hidden).exclude(author_id__in=reverse)

def write_denial(request):
    if not request.user.is_authenticated or not request.user.is_active:
        return api_error(request, '未登录', 401)
    profile = getattr(request.user, 'profile', None)
    if profile and (profile.banned_at or (profile.muted_until and profile.muted_until > timezone.now())):
        return api_error(request, '账号受到禁言或封禁限制：' + profile.status_reason, 403)
    return None

def notify(recipient, actor, event, target_type, target_id, key, post_id=None, comment_id=None, snapshot=None):
    if not recipient or not recipient.is_active or recipient.pk == getattr(actor, 'pk', None) or blocked(recipient.pk, getattr(actor, 'pk', None)):
        return None
    notification, _ = Notification.objects.get_or_create(dedup_key=key, defaults={'recipient': recipient, 'actor': actor, 'event': event, 'target_type': target_type, 'target_id': target_id, 'post_id': post_id, 'comment_id': comment_id, 'snapshot': snapshot or {}})
    return notification

def comment_query(request, post_id):
    query = Comment.objects.filter(post__in=public_posts(), post_id=post_id).filter(Q(is_hidden=False) | Q(root__isnull=True, thread_replies__is_hidden=False)).distinct().select_related('author', 'author__profile', 'reply_to__author', 'root')
    if request.user.is_authenticated:
        query = query.annotate(viewer_hidden=Exists(UserRelation.objects.filter(owner=request.user, target_id=OuterRef('author_id'))) | Exists(UserRelation.objects.filter(kind='block', target=request.user, owner_id=OuterRef('author_id'))))
    return query

def comment_dto(comment, viewer):
    unavailable = bool(blocked(getattr(viewer,'pk',None),comment.author_id) or comment.deleted_at or comment.is_hidden or (not comment.author.is_active) or getattr(comment.author.profile if hasattr(comment.author, 'profile') else None, 'banned_at', None) or getattr(comment, 'viewer_hidden', False))
    name = '已不可用用户' if unavailable else display_name(comment.author)
    profile = getattr(comment.author, 'profile', None)
    placeholder = '该评论已删除' if comment.deleted_at else '该评论已不可用'
    return {'id': comment.pk, 'postId': comment.post_id, 'postTitle': comment.post.title, 'authorId': None if unavailable else comment.author_id, 'author': name, 'authorAvatarText': name[:1], 'authorAvatarUrl': profile.avatar_url if profile and (not unavailable) else '', 'content': placeholder if unavailable else comment.content, 'deleted': unavailable, 'createdAt': comment.created_at.isoformat(), 'date': comment.created_at.isoformat(), 'likes': comment.likes.count() if not unavailable else 0, 'isLiked': viewer.is_authenticated and comment.likes.filter(user=viewer).exists() if not unavailable else False, 'isMine': viewer.is_authenticated and comment.author_id == viewer.pk and (not unavailable), 'parentId': comment.parent_id, 'rootId': comment.root_id, 'replyToId': comment.reply_to_id, 'replyToName': display_name(comment.reply_to.author) if comment.reply_to and comment.reply_to.author.is_active and (not comment.reply_to.deleted_at) and (not comment.reply_to.is_hidden) and (not blocked(getattr(viewer, 'pk', None), comment.reply_to.author_id)) else '不可用评论' if comment.reply_to_id else '', 'replyCount': comment.thread_replies.filter(is_hidden=False).count() if not comment.root_id else 0}

@require_http_methods(['GET', 'POST'])
def comments(request, post_id):
    from .content import page_data
    from .media import receipt
    post = public_posts().filter(pk=post_id).first()
    if not post:
        return api_error(request, '内容已不可用', 404)
    if request.method == 'GET':
        query = comment_query(request, post_id).filter(root__isnull=True)
        if request.GET.get('sort') == 'hot':
            query = query.annotate(score=Count('likes',distinct=True)).order_by('-score', '-created_at', '-id')
        else:
            query = query.order_by('-created_at', '-id')
        return api_success(request, page_data(request, query, lambda c: comment_dto(c, request.user)))
    denial = write_denial(request)
    if denial:
        return denial
    if blocked(request.user.pk, post.author_id):
        return api_error(request, '拉黑关系限制评论', 403)
    if limited(request, 'comment', 60):
        return api_error(request, '评论过于频繁，请稍后重试', 429)
    data = body(request)
    text = data.get('content')
    if not isinstance(text, str) or not text.strip() or len(text) > 2000:
        return api_error(request, '评论须为1–2000字')
    with transaction.atomic():
        parent = None
        if data.get('replyToId') is not None:
            if type(data['replyToId']) != int:
                return api_error(request, '回复对象无效')
            parent = visible_comments().filter(pk=data['replyToId'], post=post, deleted_at__isnull=True, author__is_active=True,author__profile__banned_at__isnull=True).first()
            if not parent or blocked(request.user.pk, parent.author_id):
                return api_error(request, '回复对象不可用', 404)
        try:
            record, replay = receipt(request.user, 'comment.create', data | {'postId': post_id})
        except ValueError as exc:
            return api_error(request, str(exc), 409)
        if replay:
            saved = Comment.objects.filter(pk=record.target_id, deleted_at__isnull=True).first()
            return api_success(request, comment_dto(saved, request.user)) if saved else api_error(request, '原评论已不可用', 409)
        comment = Comment.objects.create(post=post, author=request.user, content=text.strip(), parent=parent, root=parent.root or parent if parent else None, reply_to=parent)
        if record:
            record.target_id = comment.pk
            record.save(update_fields=['target_id'])
        for recipient in {post.author, parent.author if parent else post.author}:
            notify(recipient, request.user, 'reply' if parent else 'comment', 'comment', comment.pk, f'comment:{comment.pk}:{recipient.pk}', post.pk, comment.pk)
    return api_success(request, comment_dto(comment, request.user), status=201)

@require_GET
def replies(request, comment_id):
    from .content import page_data
    comment = Comment.objects.filter(post__in=public_posts(), pk=comment_id).first()
    if not comment:
        return api_error(request, '评论不可用', 404)
    root_id = comment.root_id or comment.pk
    query = comment_query(request, comment.post_id).filter(root_id=root_id).order_by('created_at', 'id')
    return api_success(request, page_data(request, query, lambda c: comment_dto(c, request.user)))

@require_GET
def comment_detail(request, comment_id):
    candidate = Comment.objects.filter(pk=comment_id, post__in=public_posts()).first()
    comment = comment_query(request, candidate.post_id).filter(pk=comment_id).first() if candidate else None
    if not comment:
        return api_error(request, '评论不可用', 404)
    return api_success(request, comment_dto(comment, request.user))

@require_GET
def my_comments(request):
    from .content import page_data
    if not request.user.is_authenticated:
        return api_error(request, '未登录', 401)
    query = visible_comments().filter(author=request.user, deleted_at__isnull=True).select_related('author', 'reply_to__author', 'post').order_by('-created_at', '-id')
    return api_success(request, page_data(request, query, lambda c: comment_dto(c, request.user)))

@require_http_methods(['DELETE'])
def remove_comment(request, comment_id):
    denial = write_denial(request)
    if denial:
        return denial
    comment = Comment.objects.filter(pk=comment_id, author=request.user).first()
    if not comment:
        return api_error(request, '仅作者可删除', 403)
    comment.deleted_at = timezone.now()
    comment.content = ''
    comment.save(update_fields=['deleted_at', 'content'])
    return api_success(request, {'id': comment.pk, 'deleted': True})

@require_http_methods(['POST'])
def interaction(request, entity, entity_id, action):
    denial = write_denial(request)
    if denial:
        return denial
    data = body(request)
    field = {'like': 'isLiked', 'favorite': 'isFavorited', 'follow': 'isFollowing'}.get(action)
    if field and type(data.get(field)) != bool:
        return api_error(request, '互动状态必须是布尔值')
    desired = data.get(field, True)
    with transaction.atomic():
        if entity == 'author':
            target = User.objects.filter(pk=entity_id, is_active=True, profile__banned_at__isnull=True).first()
            if not target:
                return api_error(request, '用户不可用', 404)
            if target.pk == request.user.pk:
                return api_error(request, '不能关注自己')
            if blocked(target.pk, request.user.pk):
                return api_error(request, '拉黑关系限制关注', 403)
            if desired:
                follow, created = Follow.objects.get_or_create(follower=request.user, followee=target)
                if created:
                    notify(target, request.user, 'follow', 'user', request.user.pk, f'follow:{follow.pk}')
            else:
                Follow.objects.filter(follower=request.user, followee=target).delete()
            return api_success(request, {'authorId': target.pk, 'isFollowing': desired, 'fans': target.follower_relations.count()})
        if entity == 'comment':
            target = visible_comments().select_for_update().filter(pk=entity_id, deleted_at__isnull=True, author__is_active=True,author__profile__banned_at__isnull=True).first()
            if not target:
                return api_error(request, '评论不可用', 404)
            if blocked(target.author_id, request.user.pk):
                return api_error(request, '拉黑关系限制互动', 403)
            if desired:
                CommentLike.objects.get_or_create(comment=target, user=request.user)
            else:
                CommentLike.objects.filter(comment=target, user=request.user).delete()
            target.likes_count = target.likes.count()
            target.save(update_fields=['likes_count'])
            return api_success(request, {'commentId': target.pk, 'isLiked': desired, 'likes': target.likes_count})
        target = public_posts().select_for_update().filter(pk=entity_id).first()
        if not target:
            return api_error(request, '内容已不可用', 404)
        if blocked(target.author_id, request.user.pk):
            return api_error(request, '拉黑关系限制互动', 403)
        record, _ = PostInteraction.objects.get_or_create(post=target, user=request.user)
        before = record.is_liked
        record.is_read = True
        attribute = {'like': 'is_liked', 'favorite': 'is_favorited', 'read': 'is_read', 'share': 'is_shared'}[action]
        setattr(record, attribute, desired)
        record.save()
        target.likes_count = target.interactions.filter(is_liked=True).count()
        target.save(update_fields=['likes_count'])
        if action == 'like' and desired and (not before):
            notify(target.author, request.user, 'post.like', 'post', target.pk, f'post.like:{record.pk}', target.pk)
        return api_success(request, {'postId': target.pk, 'isLiked': record.is_liked, 'isFavorited': record.is_favorited, 'likes': target.likes_count})

@require_http_methods(['GET', 'POST', 'DELETE'])
def relations(request, kind, target_id=None):
    from .content import page_data
    if not request.user.is_authenticated:
        return api_error(request, '未登录', 401)
    if request.method == 'GET':
        query = User.objects.filter(target_relations__owner=request.user, target_relations__kind=kind).select_related('profile').order_by('-id')
        return api_success(request, page_data(request, query, public_user_payload))
    denial = write_denial(request)
    if denial:
        return denial
    target_id = target_id or body(request).get('userId')
    if type(target_id) != int or target_id == request.user.pk:
        return api_error(request, '目标用户无效')
    target = User.objects.filter(pk=target_id, is_active=True).first()
    if not target:
        return api_error(request, '用户不可用', 404)
    with transaction.atomic():
        if request.method == 'DELETE':
            UserRelation.objects.filter(owner=request.user, target=target, kind=kind).delete()
        else:
            UserRelation.objects.get_or_create(owner=request.user, target=target, kind=kind)
            if kind == 'block':
                Follow.objects.filter(Q(follower=request.user, followee=target) | Q(follower=target, followee=request.user)).delete()
    return api_success(request, {'success': True})

def notification_dto(item, viewer):
    available = True
    if item.post_id:
        available = public_posts().filter(pk=item.post_id).exists()
    if item.comment_id:
        available = available and visible_comments().filter(pk=item.comment_id, deleted_at__isnull=True, author__is_active=True).exists()
    if item.target_type == 'user':
        available = User.objects.filter(pk=item.target_id, is_active=True).exists()
    if blocked(viewer.pk, item.actor_id):
        available = False
    title = {'post.like': '赞了你的作品', 'follow': '关注了你', 'comment': '评论了你的作品', 'reply': '回复了评论', 'post.review': '作品审核结果', 'comment.moderation': '评论处置结果', 'report.resolved': '举报处理结果', 'appeal.resolved': '申诉处理结果', 'user.status': '账号状态变更', 'user.roles': '账号权限变更'}.get(item.event, '系统通知')
    system = item.event not in {'post.like', 'follow', 'comment', 'reply'}
    content = item.snapshot.get('reason', '') if system else ''
    return {'id': item.pk, 'event': item.event, 'title': title, 'content': content, 'actor': public_user_payload(item.actor) if item.actor and item.actor.is_active else None, 'targetType': item.target_type, 'targetId': item.target_id, 'postId': item.post_id, 'commentId': item.comment_id, 'manageUrl': f'/reports?appealPost={item.post_id}' if item.event == 'post.review' and item.post_id and Post.objects.filter(pk=item.post_id, author=viewer, deleted_at__isnull=True).exists() else None, 'unavailable': not available, 'createdAt': item.created_at.isoformat(), 'readAt': item.read_at.isoformat() if item.read_at else None}

@require_http_methods(['GET', 'POST'])
def notifications(request, notification_id=None, action=None):
    from .content import page_data
    if not request.user.is_authenticated:
        return api_error(request, '未登录', 401)
    query = Notification.objects.filter(recipient=request.user)
    if request.method == 'POST':
        if not notification_id and action != 'read-all':
            return api_error(request, '请选择单条或全部已读操作', 405)
        if notification_id:
            if not query.filter(pk=notification_id).exists():
                return api_error(request, '通知不存在', 404)
            query = query.filter(pk=notification_id)
        query.filter(read_at__isnull=True).update(read_at=timezone.now())
        return api_success(request, {'success': True})
    if action == 'unread':
        return api_success(request, {'count': query.filter(read_at__isnull=True).count()})
    category = request.GET.get('category')
    if category == 'social':
        query = query.filter(event__in=['post.like', 'follow', 'comment', 'reply'])
    elif category == 'system':
        query = query.exclude(event__in=['post.like', 'follow', 'comment', 'reply'])
    before_id = request.GET.get('beforeId')
    if before_id is not None:
        if not before_id.isdecimal() or len(before_id) > 19:
            return api_error(request, '通知分页游标无效')
        anchor = query.filter(pk=int(before_id)).first()
        if not anchor:
            return api_error(request, '通知分页游标无效')
        query = query.filter(Q(created_at__lt=anchor.created_at) | Q(created_at=anchor.created_at, pk__lt=anchor.pk))
    return api_success(request, page_data(request, query.select_related('actor', 'actor__profile').order_by('-created_at', '-id'), lambda n: notification_dto(n, request.user)))
