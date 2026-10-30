"""Production policy and safe demo imports, without touching the working database."""
import json
import os
from pathlib import Path
import subprocess
import sys
from io import StringIO
from tempfile import TemporaryDirectory

from django.contrib.auth.models import User
from django.core import mail
from django.core.management import call_command, CommandError
from django.test import SimpleTestCase, TestCase, override_settings

from .models import AccountToken, Post


class ProductionConfigurationTests(SimpleTestCase):
    def load_settings(self, **overrides):
        environment = {key: value for key, value in os.environ.items() if key not in {
            'DJANGO_SECRET_KEY_FILE', 'EMAIL_HOST_PASSWORD_FILE',
        }}
        environment.update({
            'DJANGO_ENV': 'production', 'DJANGO_DEBUG': 'false',
            'DJANGO_SECRET_KEY': 'isolated-test-only-' + 'abcdef12' * 10,
            'DJANGO_ALLOWED_HOSTS': 'demo.example.com,localhost',
            'FRONTEND_ORIGIN': 'https://demo.example.com',
            'TIP_ALLOW_REGISTRATION': 'false',
            'EMAIL_BACKEND': 'django.core.mail.backends.filebased.EmailBackend',
            'EMAIL_HOST': '', 'DEFAULT_FROM_EMAIL': 'baicaoyuan@localhost',
            'EMAIL_USE_TLS': 'true', 'EMAIL_USE_SSL': 'false',
        })
        environment.update(overrides)
        return subprocess.run(
            [sys.executable, '-c', (
                'import json; import backend_django.settings as s; '
                'print(json.dumps({"debug":s.DEBUG,"secure":s.SESSION_COOKIE_SECURE,'
                '"csrf_secure":s.CSRF_COOKIE_SECURE,"redirect":s.SECURE_SSL_REDIRECT,'
                '"register":s.TIP_ALLOW_REGISTRATION,"email":s.TIP_EMAIL_AVAILABLE}))'
            )],
            cwd=Path(__file__).resolve().parents[1], env=environment,
            capture_output=True, text=True, timeout=10,
        )

    def test_public_https_and_loopback_preview(self):
        result = self.load_settings()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {
            'debug': False, 'secure': True, 'csrf_secure': True,
            'redirect': True, 'register': False, 'email': False,
        })
        result = self.load_settings(FRONTEND_ORIGIN='http://localhost:8080')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(json.loads(result.stdout)['secure'])

    def test_insecure_production_configuration_fails_closed(self):
        for change in [
            {'DJANGO_DEBUG': 'true'}, {'DJANGO_SECRET_KEY': 'weak'},
            {'DJANGO_ALLOWED_HOSTS': '*'}, {'DJANGO_ALLOWED_HOSTS': ''},
            {'FRONTEND_ORIGIN': 'http://demo.example.com'},
            {'FRONTEND_ORIGIN': 'https://demo.example.com/path'},
            {'FRONTEND_ORIGIN': 'https://user:pass@demo.example.com'},
            {'TIP_ALLOW_REGISTRATION': 'true'},
            {'EMAIL_USE_SSL': 'true'},
        ]:
            with self.subTest(change=change):
                self.assertNotEqual(self.load_settings(**change).returncode, 0)

    def test_real_smtp_configuration_can_enable_registration(self):
        result = self.load_settings(
            TIP_ALLOW_REGISTRATION='true',
            EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend',
            EMAIL_HOST='smtp.example.com', DEFAULT_FROM_EMAIL='garden@example.com',
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)['register'])

    def test_production_admin_has_a_separate_namespace(self):
        environment = dict(os.environ, DJANGO_ENV='production', DJANGO_DEBUG='false',
                           DJANGO_SECRET_KEY='isolated-test-only-' + 'abcdef12' * 10,
                           DJANGO_ALLOWED_HOSTS='demo.example.com,localhost',
                           FRONTEND_ORIGIN='https://demo.example.com',
                           TIP_ALLOW_REGISTRATION='false')
        environment.pop('DJANGO_SECRET_KEY_FILE', None)
        environment.pop('EMAIL_HOST_PASSWORD_FILE', None)
        environment['DJANGO_SETTINGS_MODULE'] = 'backend_django.settings'
        environment['EMAIL_BACKEND'] = 'django.core.mail.backends.filebased.EmailBackend'
        result = subprocess.run([sys.executable, '-c', (
            'import django; django.setup(); '
            'from django.urls import reverse; '
            'assert reverse("admin:login") == "/django-admin/login/"'
        )], cwd=Path(__file__).resolve().parents[1], env=environment,
            capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class DeploymentAccountPolicyTests(TestCase):
    def post(self, path, payload):
        return self.client.post('/api/' + path, json.dumps(payload), content_type='application/json')

    @override_settings(PRODUCTION=True)
    def test_production_rejects_acceptance_fixtures(self):
        with self.assertRaisesMessage(CommandError, '生产模式禁止'):
            call_command('seed_acceptance_data')
        self.assertFalse(User.objects.exists())

    @override_settings(TIP_ALLOW_REGISTRATION=False, TIP_EMAIL_AVAILABLE=False)
    def test_closed_registration_and_email_are_enforced_on_the_server(self):
        self.assertEqual(self.client.get('/api/auth/config').json()['data'], {
            'registrationEnabled': False, 'emailAvailable': False,
        })
        self.assertEqual(self.post('auth/register', {
            'email': 'closed@example.com', 'password': 'ValidGarden!2026',
        }).status_code, 403)
        for endpoint in ['auth/password-reset', 'auth/resend-verification']:
            self.assertEqual(self.post(endpoint, {'email': 'closed@example.com'}).status_code, 503)
        self.assertFalse(User.objects.exists())
        self.assertFalse(AccountToken.objects.exists())

    @override_settings(TIP_EMAIL_AVAILABLE=True)
    def test_password_reset_cannot_enable_disabled_demo_login(self):
        User.objects.create_user(username='demo_disabled', email='disabled@example.com', password=None)
        known = self.post('auth/password-reset', {'email': 'disabled@example.com'})
        unknown = self.post('auth/password-reset', {'email': 'unknown@example.com'})
        self.assertEqual(known.json()['data'], unknown.json()['data'])
        self.assertEqual(len(mail.outbox), 0)
        self.assertFalse(AccountToken.objects.exists())


class SafeDemoSeedTests(TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.settings_override = override_settings(MEDIA_ROOT=self.temp.name)
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)

    def seed(self, **options):
        call_command('seed_demo_data', stdout=StringIO(), **options)

    def test_disable_login_is_idempotent_and_keeps_public_content(self):
        self.seed(disable_login=True)
        self.assertEqual(User.objects.count(), 9)
        self.assertEqual(Post.objects.count(), 12)
        self.assertTrue(all(not user.has_usable_password() for user in User.objects.all()))
        self.assertTrue(all(user.is_active for user in User.objects.all()))
        self.assertEqual(len(self.client.get('/api/community/recommend').json()['data']['posts']), 12)
        self.seed(disable_login=True)
        self.assertEqual(Post.objects.count(), 12)
        self.assertTrue(all(not user.has_usable_password() for user in User.objects.all()))

    @override_settings(PRODUCTION=True)
    def test_production_always_disables_demo_login(self):
        self.seed()
        self.assertTrue(all(not user.has_usable_password() for user in User.objects.all()))

    def test_reset_preserves_privileged_legacy_accounts_and_posts(self):
        admin = User.objects.create_user(username='demo_123', is_superuser=True, password=None)
        post = Post.objects.create(author=admin, title='preserve admin content')
        self.seed(reset=True, disable_login=True)
        self.assertTrue(User.objects.filter(pk=admin.pk).exists())
        self.assertTrue(Post.objects.filter(pk=post.pk).exists())

    def test_privileged_username_collision_aborts_before_reset(self):
        admin = User.objects.create_user(username='demo_muyu', is_staff=True, password=None)
        legacy = User.objects.create_user(username='demo_321', password=None)
        post = Post.objects.create(author=legacy, title='preserve on failed import')
        with self.assertRaises(CommandError):
            self.seed(reset=True, disable_login=True)
        self.assertTrue(User.objects.filter(pk=admin.pk).exists())
        self.assertTrue(Post.objects.filter(pk=post.pk).exists())
