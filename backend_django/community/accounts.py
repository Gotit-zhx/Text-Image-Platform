"""Account lifecycle. Reads never provision users; tokens are hashed and single use."""
import hashlib
import json
import secrets
from datetime import timedelta
from urllib.parse import urlencode
from django.conf import settings
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.db import IntegrityError, transaction
from django.middleware.csrf import get_token
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST
from .http import api_error, api_success
from .models import AccountToken, AuthAttempt, AuditLog, Comment, Follow, Post, Profile
GENERIC_MAIL = '请求已处理；开发环境请查看本地邮件输出，未确认真实邮箱送达。'

def body(request):
    try:
        data = json.loads(request.body)
        return data if isinstance(data, dict) else {}
    except (ValueError, UnicodeDecodeError):
        return {}

def text(data, key):
    value = data.get(key)
    return value if isinstance(value, str) else ''

def display_name(user):
    profile = getattr(user, 'profile', None)
    return (profile.nickname if profile else '') or user.username

def public_user_payload(user):
    profile = getattr(user, 'profile', None)
    name = display_name(user)
    return {'id': user.id, 'name': name, 'avatarText': name[:1] or 'U', 'avatarUrl': profile.avatar_url if profile else '', 'signature': profile.signature if profile else '', 'fans': Follow.objects.filter(followee=user).count(), 'follows': Follow.objects.filter(follower=user).count()}

def user_payload(user):
    result = public_user_payload(user)
    profile = getattr(user, 'profile', None)
    from .governance import can_admin
    result.update(isSuperuser=user.is_superuser, permissions={'moderate': can_admin(user, 'moderate'), 'operate': can_admin(user, 'operate'), 'roles': user.is_superuser}, email=user.email, emailVerified=bool(profile and profile.email_verified), gender=profile.gender if profile else 'private', roles=list(user.groups.values_list('name', flat=True)), isAdmin=user.is_staff)
    return result

def limited(request, action, limit=20):
    key = hashlib.sha256(f"{action}:{request.META.get('REMOTE_ADDR', '')}".encode()).hexdigest()
    since = timezone.now() - timedelta(minutes=15)
    if AuthAttempt.objects.filter(key=key, created_at__gt=since).count() >= limit:
        return True
    AuthAttempt.objects.create(key=key)
    return False

def issue_token(user, purpose):
    with transaction.atomic():
        user = User.objects.select_for_update().get(pk=user.pk)
        if AccountToken.objects.filter(user=user, purpose=purpose, created_at__gt=timezone.now() - timedelta(seconds=60)).exists():
            return
        raw = secrets.token_urlsafe(32)
        expires = timezone.now() + timedelta(hours=24 if purpose == 'verify' else 1)
        token = AccountToken.objects.create(user=user, purpose=purpose, email=user.email, digest=hashlib.sha256(raw.encode()).hexdigest(), expires_at=expires)
        link = settings.FRONTEND_ORIGIN.rstrip('/') + '/auth/' + ('verify' if purpose == 'verify' else 'reset') + '?' + urlencode({'token': raw})
        try:
            send_mail('百草园：验证邮箱' if purpose == 'verify' else '百草园：重置密码', f'请打开链接（单次使用）：{link}', settings.DEFAULT_FROM_EMAIL, [user.email])
        except Exception:
            token.delete()
            raise

@require_GET
def csrf(request):
    return api_success(request, {'token': get_token(request)})

def csrf_failure(request, reason=''):
    return api_error(request, '请求验证已失效，请刷新后重新确认操作', status=403, code=40301)

@require_POST
def auth_register(request):
    if limited(request, 'register', 10):
        return api_error(request, '请求过于频繁，请稍后再试', 429)
    data = body(request)
    email = text(data, 'email').strip().lower()
    password = text(data, 'password')
    try:
        validate_email(email)
        if len(email) > 254 or not password:
            raise ValidationError('请提供有效邮箱和密码')
        validate_password(password, User(email=email, username=email.split('@')[0]))
    except ValidationError as exc:
        return api_error(request, '；'.join(exc.messages))
    try:
        with transaction.atomic():
            if User.objects.filter(email__iexact=email).exists():
                return api_error(request, '邮箱已被使用，请登录或找回密码', 409)
            user = User.objects.create_user(username='u_' + secrets.token_hex(12), email=email, password=password)
            Profile.objects.create(user=user, nickname=f'用户{user.id}', requires_verification=True)
    except IntegrityError:
        return api_error(request, '邮箱已被使用，请登录或找回密码', 409)
    try:
        issue_token(user, 'verify')
    except Exception:
        return api_success(request, {'verificationRequired': True, 'message': '账号已创建，邮件输出失败，请重发验证链接。'}, status=201)
    return api_success(request, {'verificationRequired': True, 'message': GENERIC_MAIL}, status=201)

@require_POST
def auth_login(request):
    if limited(request, 'login', 30):
        return api_error(request, '请求过于频繁，请稍后再试', 429)
    data = body(request)
    account, password = (text(data, 'account').strip(), text(data, 'password'))
    if not account or not password:
        return api_error(request, '请输入账号和密码')
    user = User.objects.filter(email__iexact=account.lower()).first() if '@' in account else User.objects.filter(username=account).first()
    auth_user = authenticate(request, username=user.username if user else account, password=password)
    if not user or not auth_user:
        return api_error(request, '账号或密码错误', 401)
    profile = getattr(user, 'profile', None)
    if profile and profile.requires_verification and (not profile.email_verified):
        return api_error(request, '请先验证邮箱，可重发验证链接', 403)
    login(request, auth_user)
    return api_success(request, user_payload(auth_user))

@require_POST
def auth_logout(request):
    logout(request)
    return api_success(request, {'success': True})

@require_GET
def users_me(request):
    if not request.user.is_authenticated or not request.user.is_active:
        return api_error(request, '未登录', 401)
    return api_success(request, user_payload(request.user))

@require_POST
def request_email(request, purpose):
    if limited(request, 'mail', 15):
        return api_error(request, '请求过于频繁，请稍后再试', 429)
    email = text(body(request), 'email').strip().lower()
    user = User.objects.filter(email__iexact=email, is_active=True).first()
    if user and (purpose == 'reset' or not getattr(getattr(user, 'profile', None), 'email_verified', False)):
        try:
            issue_token(user, purpose)
        except Exception:
            pass
    return api_success(request, {'message': GENERIC_MAIL})

@require_POST
def consume_token(request, purpose):
    data = body(request)
    raw = text(data, 'token')
    with transaction.atomic():
        token = AccountToken.objects.select_for_update().select_related('user').filter(digest=hashlib.sha256(raw.encode()).hexdigest(), purpose=purpose, used_at__isnull=True, expires_at__gt=timezone.now(), user__is_active=True).first()
        if not raw or not token or token.email != token.user.email:
            return api_error(request, '链接已过期或已使用，请重新申请')
        user = User.objects.select_for_update().get(pk=token.user_id)
        if purpose == 'reset':
            password = text(data, 'newPassword')
            try:
                if not password:
                    raise ValidationError('请输入新密码')
                validate_password(password, user)
            except ValidationError as exc:
                return api_error(request, '；'.join(exc.messages))
            user.set_password(password)
            user.save(update_fields=['password'])
            AccountToken.objects.filter(user=user, purpose='reset', used_at__isnull=True).update(used_at=timezone.now())
            if request.user.is_authenticated and request.user.pk == user.pk:
                logout(request)
        else:
            profile, _ = Profile.objects.get_or_create(user=user)
            AccountToken.objects.filter(user=user, purpose='verify', used_at__isnull=True).update(used_at=timezone.now())
            profile.email_verified = True
            profile.save(update_fields=['email_verified'])
        token.used_at = timezone.now()
        token.save(update_fields=['used_at'])
    return api_success(request, {'success': True})

@require_POST
def change_password(request):
    if not request.user.is_authenticated:
        return api_error(request, '未登录', 401)
    data = body(request)
    if not request.user.check_password(text(data, 'oldPassword')):
        return api_error(request, '旧密码错误')
    password = text(data, 'newPassword')
    try:
        if not password:
            raise ValidationError('请输入新密码')
        validate_password(password, request.user)
    except ValidationError as exc:
        return api_error(request, '；'.join(exc.messages))
    request.user.set_password(password)
    request.user.save(update_fields=['password'])
    update_session_auth_hash(request, request.user)
    return api_success(request, {'success': True})

@require_POST
def deactivate(request):
    if not request.user.is_authenticated:
        return api_error(request, '未登录', 401)
    data = body(request)
    if text(data, 'confirmation') != '注销百草园账号' or not request.user.check_password(text(data, 'password')):
        return api_error(request, '请确认注销并输入正确密码')
    with transaction.atomic():
        user = User.objects.select_for_update().get(pk=request.user.pk)
        if user.is_superuser and (not getattr(getattr(user, 'profile', None), 'banned_at', None)) and (User.objects.filter(is_superuser=True, is_active=True, profile__banned_at__isnull=True).count() <= 1):
            return api_error(request, '不能注销最后一个超级管理员', 409)
        user.is_active = False
        user.email = ''
        user.username = 'deactivated_' + str(user.id)
        user.set_unusable_password()
        user.save(update_fields=['is_active', 'email', 'username', 'password'])
        profile, _ = Profile.objects.get_or_create(user=user)
        profile.nickname, profile.signature, profile.avatar_url = ('已注销用户', '', '')
        profile.avatar_media = None
        profile.email_verified = False
        profile.gender = 'private'
        profile.save()
        Follow.objects.filter(follower=user).delete()
        Follow.objects.filter(followee=user).delete()
        AccountToken.objects.filter(user=user).delete()
        AuditLog.objects.create(actor=user, action='account.deactivate', target_type='user', target_id=user.id)
    logout(request)
    return api_success(request, {'success': True})

def profile_update(request, data):
    name = text(data, 'name').strip()
    gender = data.get('gender', 'private')
    signature = text(data, 'signature')
    avatar = text(data, 'avatarUrl')
    if not name or len(name) > 80 or not isinstance(gender,str) or gender not in {'male', 'female', 'private'} or (len(signature) > 300):
        return api_error(request, '资料格式错误（昵称1–80字、简介最多300字）')
    current_profile = getattr(request.user, 'profile', None)
    if avatar and avatar != (current_profile.avatar_url if current_profile else '') and (not (avatar.startswith('/media/') or avatar.startswith('https://'))):
        return api_error(request, '头像地址无效')
    profile, _ = Profile.objects.get_or_create(user=request.user)
    from .models import Media
    if avatar.startswith('/media/'):
        import re
        match = re.fullmatch('/media/(\\d+)/image', avatar)
        asset = Media.objects.filter(pk=int(match.group(1)), owner=request.user).first() if match else None
        if not asset:
            return api_error(request, '头像必须使用本人上传的图片')
        profile.avatar_media = asset
    elif avatar and avatar != profile.avatar_url:
        return api_error(request, '新头像须上传为媒体资源')
    else:
        profile.avatar_media = None
    profile.nickname, profile.signature, profile.gender, profile.avatar_url = (name, signature, gender, avatar)
    profile.save()
    return api_success(request, user_payload(request.user))
