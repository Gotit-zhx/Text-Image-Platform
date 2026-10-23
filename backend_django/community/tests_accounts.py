import hashlib
import importlib
import json
import re
from datetime import timedelta
from io import StringIO
from django.contrib.auth.models import User
from django.core import mail
from django.core.management import call_command
from django.db import IntegrityError, connection, transaction
from django.test import Client, TestCase, override_settings
from django.utils import timezone
from .models import AccountToken, Comment, Post, Profile
PASSWORD = 'GardenField!2026'
NEW_PASSWORD = 'NewGardenField!2026'

@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class AccountLifecycleTests(TestCase):

    def post(self, url, data, client=None):
        return (client or self.client).post('/api/' + url, json.dumps(data), content_type='application/json')

    def user(self, name='writer', email='writer@example.com', **kwargs):
        return User.objects.create_user(username=name, email=email, password=PASSWORD, **kwargs)

    def register(self):
        response = self.post('auth/register', {'email': ' New@Example.com ', 'password': PASSWORD})
        self.assertEqual(response.status_code, 201)
        self.assertNotIn('_auth_user_id', self.client.session)
        return User.objects.get(email='new@example.com')

    def mail_token(self):
        return re.search('token=([\\w-]+)', mail.outbox[-1].body).group(1)

    def test_read_paths_do_not_create_or_reset_accounts(self):
        user = self.user('管理员', 'admin@example.com', is_staff=True, is_superuser=True)
        before = user.password
        for url in ['community/bootstrap', 'community/recommend', 'community/users/%s/profile' % user.id]:
            self.assertEqual(self.client.get('/api/' + url).status_code, 200)
        user.refresh_from_db()
        self.assertEqual(user.password, before)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(Post.objects.count(), 0)
        self.post('admin/auth/login', {'account': user.username, 'password': 'wrong'})
        user.refresh_from_db()
        self.assertEqual(user.password, before)

    def test_unknown_login_and_missing_or_weak_password_rejected(self):
        self.assertEqual(self.post('auth/login', {'account': 'missing@example.com', 'password': PASSWORD}).status_code, 401)
        for password in ['', '123456']:
            self.assertEqual(self.post('auth/register', {'email': 'test@example.com', 'password': password}).status_code, 400)
        self.assertEqual(User.objects.count(), 0)
        for payload in [[], {'email': 42, 'password': ['bad']}, {}]:
            self.assertEqual(self.post('auth/register', payload).status_code, 400)

    def test_verify_duplicate_email_and_single_use_token(self):
        user = self.register()
        self.assertEqual(self.post('auth/login', {'account': user.email, 'password': PASSWORD}).status_code, 403)
        raw = self.mail_token()
        token = AccountToken.objects.get(user=user)
        self.assertNotEqual(token.digest, raw)
        self.assertEqual(token.digest, hashlib.sha256(raw.encode()).hexdigest())
        self.assertEqual(self.post('auth/verify-email', {'token': raw}).status_code, 200)
        self.assertEqual(self.post('auth/verify-email', {'token': raw}).status_code, 400)
        self.assertEqual(self.post('auth/login', {'account': 'NEW@EXAMPLE.COM', 'password': PASSWORD}).status_code, 200)
        self.assertEqual(self.post('auth/register', {'email': ' NEW@example.COM ', 'password': PASSWORD}).status_code, 409)
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.user('duplicate', ' NEW@EXAMPLE.COM ')

    def test_expiry_and_resend_frequency_and_generic_response(self):
        user = self.register()
        raw = self.mail_token()
        AccountToken.objects.filter(user=user).update(expires_at=timezone.now() - timedelta(seconds=1))
        self.assertEqual(self.post('auth/verify-email', {'token': raw}).status_code, 400)
        known = self.post('auth/resend-verification', {'email': user.email}).json()['data']
        unknown = self.post('auth/resend-verification', {'email': 'absent@example.com'}).json()['data']
        self.assertEqual(known, unknown)
        self.assertEqual(len(mail.outbox), 1)
        AccountToken.objects.filter(user=user).update(created_at=timezone.now() - timedelta(seconds=61))
        self.post('auth/resend-verification', {'email': user.email})
        self.assertEqual(len(mail.outbox), 2)

    def test_password_change_and_reset_revoke_old_sessions(self):
        user = self.user()
        other = Client()
        self.client.force_login(user)
        other.force_login(user)
        self.assertEqual(self.post('users/me/password', {'oldPassword': 'wrong', 'newPassword': NEW_PASSWORD}).status_code, 400)
        self.assertEqual(self.post('users/me/password', {'oldPassword': PASSWORD, 'newPassword': NEW_PASSWORD}).status_code, 200)
        self.assertEqual(self.client.get('/api/users/me').status_code, 200)
        self.assertEqual(self.client.get('/api/users/me').status_code, 200)
        self.assertEqual(other.get('/api/users/me').status_code, 401)
        user.refresh_from_db()
        self.assertTrue(user.check_password(NEW_PASSWORD))
        self.assertFalse(user.check_password(PASSWORD))
        self.post('auth/password-reset', {'email': user.email})
        raw = self.mail_token()
        self.assertEqual(self.post('auth/password-reset/confirm', {'token': raw, 'newPassword': PASSWORD}, other).status_code, 200)
        self.assertEqual(self.client.get('/api/users/me').status_code, 401)
        self.assertEqual(self.post('auth/password-reset/confirm', {'token': raw, 'newPassword': NEW_PASSWORD}).status_code, 400)

    def test_reset_revokes_independent_admin_session(self):
        user = self.user(is_staff=True, is_superuser=True)
        self.assertEqual(self.post('admin/auth/login', {'account': user.email, 'password': PASSWORD}).status_code, 200)
        other = Client()
        self.post('auth/password-reset', {'email': user.email}, other)
        self.post('auth/password-reset/confirm', {'token': self.mail_token(), 'newPassword': NEW_PASSWORD}, other)
        self.assertEqual(self.client.get('/api/admin/auth/me').status_code, 403)

    def test_csrf_enforced_including_login_and_admin(self):
        user = self.user(is_staff=True, is_superuser=True)
        client = Client(enforce_csrf_checks=True)
        for url in ['auth/login', 'auth/register', 'auth/logout', 'admin/auth/login']:
            self.assertEqual(self.post(url, {}, client).status_code, 403)
        token = client.get('/api/auth/csrf').json()['data']['token']
        response = client.post('/api/auth/login', json.dumps({'account': user.email, 'password': PASSWORD}), content_type='application/json', HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.post('community/posts', {'title': 'Missing CSRF'}, client).status_code, 403)
        token = client.get('/api/auth/csrf').json()['data']['token']
        self.assertEqual(client.post('/api/community/posts', json.dumps({'title': 'Valid'}), content_type='application/json', HTTP_X_CSRFTOKEN=token).status_code, 201)

    def test_public_privacy_and_stable_identity(self):
        user = self.user()
        self.client.force_login(user)
        response = self.client.put('/api/users/me/profile', json.dumps({'name': '新昵称', 'gender': 'private', 'signature': '简介'}), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertEqual(user.username, 'writer')
        self.assertEqual(user.profile.nickname, '新昵称')
        self.client.logout()
        data = self.client.get(f'/api/community/users/{user.id}/profile').json()['data']
        self.assertEqual(data['name'], '新昵称')
        for key in ['email', 'roles', 'isAdmin', 'gender']:
            self.assertNotIn(key, data)

    def test_deactivation_confirmation_sessions_and_content(self):
        user = self.user()
        post = Post.objects.create(author=user, title='private after deactivation')
        other_author = self.user('other', 'other@example.com')
        other_post = Post.objects.create(author=other_author, title='still public')
        comment = Comment.objects.create(post=other_post, author=user, content='should be unavailable')
        other = Client()
        self.client.force_login(user)
        other.force_login(user)
        for data in [{'password': PASSWORD}, {'password': 'wrong', 'confirmation': '注销百草园账号'}]:
            self.assertEqual(self.post('users/me/deactivate', data).status_code, 400)
        self.assertEqual(self.post('users/me/deactivate', {'password': PASSWORD, 'confirmation': '注销百草园账号'}).status_code, 200)
        user.refresh_from_db()
        self.assertFalse(user.is_active)
        self.assertEqual(user.email, '')
        self.assertEqual(user.profile.nickname, '已注销用户')
        self.assertEqual(other.get('/api/users/me').status_code, 401)
        bootstrap = self.client.get('/api/community/bootstrap').json()['data']
        self.assertNotIn(post.id, [p['id'] for p in bootstrap['posts']])
        self.assertEqual(next((c for c in bootstrap['comments'] if c['id'] == comment.id))['content'], '该评论已不可用')
        self.assertNotIn(post.id, [p['id'] for p in self.client.get('/api/community/recommend').json()['data']['posts']])
        self.assertEqual(self.client.get(f'/api/community/users/{user.id}/profile').status_code, 404)
        self.assertTrue(Post.objects.filter(id=post.id).exists())

    def test_last_superuser_deactivation_blocked(self):
        user = self.user(is_staff=True, is_superuser=True)
        self.client.force_login(user)
        self.assertEqual(self.post('users/me/deactivate', {'password': PASSWORD, 'confirmation': '注销百草园账号'}).status_code, 409)
        user.refresh_from_db()
        self.assertTrue(user.is_active)

    def test_email_conflict_preflight_does_not_mutate(self):
        from django.apps import apps
        migration = importlib.import_module('community.migrations.0005_normalized_email_unique')
        with connection.cursor() as cursor:
            cursor.execute('DROP INDEX community_user_normalized_email')
        try:
            a = self.user('one', 'same@example.com')
            User.objects.filter(pk=a.pk).update(email=' SAME@example.com ')
            b = self.user('two', 'same@example.com')
            with self.assertRaisesRegex(RuntimeError, '冲突'):
                migration.normalize_accounts(apps, None)
            a.refresh_from_db()
            self.assertEqual(a.email, ' SAME@example.com ')
            report = StringIO()
            call_command('audit_accounts', stdout=report)
            self.assertIn(str(a.pk), report.getvalue())
            self.assertNotIn('same@example.com', report.getvalue())
            b.delete()
        finally:
            User.objects.filter(username='two').delete()
            with connection.cursor() as cursor:
                cursor.execute("CREATE UNIQUE INDEX community_user_normalized_email ON auth_user (LOWER(TRIM(email))) WHERE TRIM(email) <> ''")
