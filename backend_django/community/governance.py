from datetime import timedelta
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from .accounts import body, text, limited
from .http import api_error, api_success
from .models import Report, Appeal, Post, Comment, Profile, AuditLog
from .social import notify, write_denial
from .visibility import public_posts, visible_comments

def can_admin(user, permission):
    if user.is_superuser:
        return True
    roles = set(user.groups.values_list('name', flat=True))
    return bool(roles & {'content_moderator'} if permission == 'moderate' else roles & {'operations'} if permission == 'operate' else False)

def audit(request, action, target_type, target_id, detail=None):
    actor = getattr(request, 'admin_user', None) or (request.user if request.user.is_authenticated else None)
    log = AuditLog.objects.create(actor=actor, action=action, target_type=target_type, target_id=target_id, detail=detail or {}, ip=request.META.get('REMOTE_ADDR', ''))
    recipient = None
    post_id = None
    comment_id = None
    if target_type == 'post':
        post = Post.objects.filter(pk=target_id).first()
        recipient = post.author if post else None
        post_id = target_id
    elif target_type == 'comment':
        comment = Comment.objects.filter(pk=target_id).first()
        recipient = comment.author if comment else None
        post_id = comment.post_id if comment else None
        comment_id = target_id
    elif target_type == 'user':
        recipient = User.objects.filter(pk=target_id).first()
    if recipient:
        notify(recipient, actor, {'post.review': 'post.review', 'comment.hide': 'comment.moderation', 'comment.restore': 'comment.moderation', 'comment.delete': 'comment.moderation', 'user.roles.update': 'user.roles', 'user.status': 'user.status'}.get(action, action), target_type, target_id, f'audit:{log.pk}', post_id, comment_id, detail)
    return log

@require_http_methods(['GET', 'POST'])
def reports(request):
    from .content import page_data
    if not request.user.is_authenticated:
        return api_error(request, '未登录', 401)
    if request.method == 'GET':
        return api_success(request, page_data(request, Report.objects.filter(reporter=request.user).order_by('-created_at', '-id'), report_dto))
    denial = write_denial(request)
    if denial:
        return denial
    if limited(request, 'report', 20):
        return api_error(request, '举报过于频繁，请稍后再试', 429)
    data = body(request)
    kind = data.get('targetType')
    target = data.get('targetId')
    reason = text(data, 'reason')
    description = text(data, 'description')
    if kind not in {'post', 'comment', 'user'} or type(target) != int or (not reason) or (len(reason) > 64) or (len(description) > 2000):
        return api_error(request, '举报格式无效')
    query = {'post': public_posts(), 'comment': visible_comments().filter(deleted_at__isnull=True), 'user': User.objects.filter(is_active=True)}[kind]
    if not query.filter(pk=target).exists():
        return api_error(request, '目标不可用', 404)
    try:
        with transaction.atomic():
            report = Report.objects.create(reporter=request.user, target_type=kind, target_id=target, reason=reason, description=description)
    except IntegrityError:
        return api_error(request, '你已举报过该目标，可在记录查看处理进展', 409)
    return api_success(request, report_dto(report), status=201)

def report_dto(report):
    return {'id': report.pk, 'targetType': report.target_type, 'targetId': report.target_id, 'reason': report.reason, 'description': report.description, 'status': report.status, 'outcome': report.outcome, 'createdAt': report.created_at.isoformat(), 'resolvedAt': report.resolved_at.isoformat() if report.resolved_at else None}

def appeal_dto(appeal):
    return {'id': appeal.pk, 'postId': appeal.post_id, 'description': appeal.description, 'status': appeal.status, 'outcome': appeal.outcome, 'createdAt': appeal.created_at.isoformat()}

@require_http_methods(['GET', 'POST'])
def appeals(request):
    from .content import page_data
    if not request.user.is_authenticated:
        return api_error(request, '未登录', 401)
    if request.method == 'GET':
        return api_success(request, page_data(request, Appeal.objects.filter(author=request.user).order_by('-created_at', '-id'), appeal_dto))
    denial = write_denial(request)
    if denial:
        return denial
    data = body(request)
    description = text(data, 'description')
    if type(data.get('postId')) != int or not description.strip() or len(description) > 2000:
        return api_error(request, '请提供作品ID和1–2000字说明')
    post = Post.objects.filter(pk=data['postId'], author=request.user, deleted_at__isnull=True, moderation_status__in=['rejected', 'offline']).first()
    if not post:
        return api_error(request, '作品不属于可申诉状态', 404)
    try:
        with transaction.atomic():
            appeal = Appeal.objects.create(author=request.user, post=post, description=description)
    except IntegrityError:
        return api_error(request, '已有待处理申诉', 409)
    return api_success(request, appeal_dto(appeal), status=201)

@require_http_methods(['POST'])
def resubmit(request, post_id):
    denial = write_denial(request)
    if denial:
        return denial
    with transaction.atomic():
        post = Post.objects.select_for_update().filter(pk=post_id, author=request.user, deleted_at__isnull=True, moderation_status__in=['rejected', 'offline']).first()
        if not post:
            return api_error(request, '作品不属于可复核状态', 409)
        post.moderation_status = 'pending'
        post.save(update_fields=['moderation_status', 'updated_at'])
        audit(request, 'post.resubmit', 'post', post.pk)
    return api_success(request, {'id': post.pk, 'status': 'pending'})

def set_account_status(request, user, action, reason):
    user = User.objects.select_for_update().get(pk=user.pk)
    if user.is_superuser:
        if not request.admin_user.is_superuser:
            return api_error(request, '只有超级管理员可处置超级管理员', 403)
        if action == 'ban' and User.objects.filter(is_superuser=True, is_active=True, profile__banned_at__isnull=True).count() <= 1:
            return api_error(request, '不能封禁最后一个超级管理员', 409)
    profile, _ = Profile.objects.get_or_create(user=user)
    if action == 'ban':
        profile.banned_at = timezone.now()
    elif action == 'mute':
        profile.muted_until = timezone.now() + timedelta(days=7)
    elif action == 'restore':
        profile.banned_at = None
        profile.muted_until = None
    else:
        return api_error(request, '账号处置动作无效')
    profile.status_reason = reason
    profile.save()
    audit(request, 'user.status', 'user', user.pk, {'action': action, 'reason': reason})
    return None

@require_http_methods(['GET', 'POST'])
def admin_queue(request, kind, case_id=None):
    from .views import _get_admin_session_user
    from .content import page_data
    admin = _get_admin_session_user(request)
    if not admin or getattr(getattr(admin, 'profile', None), 'banned_at', None):
        return api_error(request, '无管理权限', 403)
    request.admin_user = admin
    model = Report if kind == 'reports' else Appeal
    if request.method == 'GET':
        query = model.objects.all().order_by('-created_at', '-id')
        if request.GET.get('status'):
            query = query.filter(status=request.GET['status'])
        data = page_data(request, query, report_dto if kind == 'reports' else appeal_dto)
        for item in data['items']:
            target_type = item.get('targetType', 'post')
            target_id = item.get('targetId', item.get('postId'))
            if target_type == 'post':
                post = Post.objects.filter(pk=target_id).first()
                item['context'] = {'id': post.pk, 'title': post.title, 'summary': post.summary, 'contentHtml': post.content_html, 'status': post.moderation_status, 'deleted': bool(post.deleted_at)} if post else {'unavailable': True}
            elif target_type == 'comment':
                comment = Comment.objects.filter(pk=target_id).first()
                item['context'] = {'content': comment.content if comment and (not comment.deleted_at) else '评论不可用', 'postId': comment.post_id if comment else None}
            else:
                user = User.objects.filter(pk=target_id).first()
                item['context'] = {'name': user.username if user else '用户不可用'}
        return api_success(request, data)
    data = body(request)
    reason = text(data, 'reason').strip()
    action = text(data, 'action')
    if not reason or len(reason) > 500:
        return api_error(request, '处置结果须有1–500字说明')
    with transaction.atomic():
        case = model.objects.select_for_update().filter(pk=case_id).first()
        if not case:
            return api_error(request, '记录不存在', 404)
        if case.status != 'open':
            return api_error(request, '该记录已处理', 409)
        target_type = case.target_type if kind == 'reports' else 'post'
        target_id = case.target_id if kind == 'reports' else case.post_id
        required = 'operate' if target_type == 'user' else 'moderate'
        if not can_admin(admin, required):
            return api_error(request, '该角色无处置权限', 403)
        if action not in (['dismiss', 'approve'] if kind == 'appeals' else ['dismiss', 'offline', 'hide', 'ban', 'mute']):
            return api_error(request, '动作不适用于该队列')
        if action != 'dismiss':
            if target_type == 'post' and action in {'offline', 'approve'}:
                post = Post.objects.filter(pk=target_id, deleted_at__isnull=True).first()
                if not post:
                    return api_error(request, '作品不可处置', 404)
                post.moderation_status = 'approved' if action == 'approve' else 'offline'
                post.review_reason = reason
                post.reviewed_by = admin
                post.reviewed_at = timezone.now()
                post.save()
                audit(request, 'post.review', 'post', post.pk, {'action': action, 'reason': reason})
            elif target_type == 'comment' and action == 'hide':
                comment = Comment.objects.filter(pk=target_id, deleted_at__isnull=True).first()
                if not comment:
                    return api_error(request, '评论不可处置', 404)
                comment.is_hidden = True
                comment.save(update_fields=['is_hidden'])
                audit(request, 'comment.hide', 'comment', comment.pk, {'reason': reason})
            elif target_type == 'user' and action in {'ban', 'mute'}:
                target = User.objects.filter(pk=target_id, is_active=True).first()
                if not target:
                    return api_error(request, '用户不可处置', 404)
                denial = set_account_status(request, target, action, reason)
                if denial:
                    return denial
            else:
                return api_error(request, '动作与目标类型不匹配')
        case.status = 'dismissed' if action == 'dismiss' else 'resolved'
        case.outcome = reason
        case.resolved_by = admin
        case.resolved_at = timezone.now()
        case.save()
        log = audit(request, 'report.resolve' if kind == 'reports' else 'appeal.resolve', kind[:-1], case.pk, {'action': action, 'reason': reason})
        recipient = case.reporter if kind == 'reports' else case.author
        notify(recipient, admin, 'report.resolved' if kind == 'reports' else 'appeal.resolved', kind[:-1], case.pk, f'case:{kind}:{case.pk}:{log.pk}', snapshot={'reason': reason})
    return api_success(request, report_dto(case) if kind == 'reports' else appeal_dto(case))

@require_http_methods(['POST'])
def admin_status(request, user_id):
    from .views import _get_admin_session_user
    admin = _get_admin_session_user(request)
    if not admin or getattr(getattr(admin, 'profile', None), 'banned_at', None) or (not can_admin(admin, 'operate')):
        return api_error(request, '无账号处置权限', 403)
    request.admin_user = admin
    data = body(request)
    reason = text(data, 'reason').strip()
    if not reason or len(reason) > 500:
        return api_error(request, '请输入1–500字处置原因')
    user = User.objects.filter(pk=user_id, is_active=True).first()
    if not user:
        return api_error(request, '用户不可用', 404)
    with transaction.atomic():
        denial = set_account_status(request, user, text(data, 'action'), reason)
        if denial:
            return denial
    return api_success(request, {'success': True})
