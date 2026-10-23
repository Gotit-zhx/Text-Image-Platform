import io
import json
import tempfile
from datetime import timedelta
from io import StringIO
from PIL import Image
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone
from .models import Draft, Media, Post, RequestReceipt

class MediaDraftTests(TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.override = override_settings(MEDIA_ROOT=self.tmp.name)
        self.override.enable()
        self.addCleanup(self.override.disable)
        self.addCleanup(self.tmp.cleanup)
        self.a = User.objects.create_user(username='mediaA', email='mediaA@test.example')
        self.b = User.objects.create_user(username='mediaB', email='mediaB@test.example')
        self.client.force_login(self.a)

    def image(self):
        buf = io.BytesIO()
        Image.new('RGB', (64, 48), 'red').save(buf, format='PNG')
        return SimpleUploadedFile('test.png', buf.getvalue(), content_type='image/png')

    def upload(self):
        response = self.client.post('/api/media', {'file': self.image()})
        self.assertEqual(response.status_code, 201)
        return response.json()['data']

    def write(self, path, data, method='post'):
        return getattr(self.client, method)('/api/' + path, json.dumps(data), content_type='application/json')

    def test_image_validation_storage_and_ownership(self):
        asset = self.upload()
        self.assertEqual(self.write('community/posts', {'title': 'bad', 'images': 42}).status_code, 400)
        self.assertEqual(asset['width'], 64)
        self.assertEqual(asset['height'], 48)
        self.assertEqual(self.client.get(asset['url']).status_code, 200)
        self.assertEqual(self.client.post('/api/media', {'file': SimpleUploadedFile('fake.png', b'not an image')}).status_code, 400)
        self.client.force_login(self.b)
        self.assertEqual(self.client.get(asset['url']).status_code, 404)
        self.assertEqual(self.client.delete(f"/api/media/{asset['id']}").status_code, 404)
        self.assertEqual(self.write('community/posts', {'title': 'stolen', 'mediaIds': [asset['id']]}).status_code, 400)
        self.assertEqual(self.write('community/posts', {'title': 'stolen', 'contentHtml': f'''<img src="{asset['url']}">'''}).status_code, 400)

    def test_draft_reopen_conflict_and_publish_idempotency(self):
        asset = self.upload()
        second_asset = self.upload()
        payload = {'title': 'draft', 'contentHtml': f'''<p>body</p><img src="{asset['url']}">''', 'tags': [], 'mediaIds': [second_asset['id'], asset['id']], 'requestKey': 'draft-key'}
        response = self.write('drafts', payload)
        self.assertEqual(response.status_code, 201)
        draft = response.json()['data']
        self.assertEqual(draft['mediaIds'], [second_asset['id'], asset['id']])
        self.assertEqual(self.write('drafts', payload).json()['data']['id'], draft['id'])
        self.assertEqual(self.client.get(f"/api/drafts/{draft['id']}").json()['data']['title'], 'draft')
        self.assertEqual(self.write(f"drafts/{draft['id']}", {**payload, 'version': 0}, 'put').status_code, 409)
        self.assertEqual(self.write(f"drafts/{draft['id']}", {**payload, 'version': 1, 'title': 'changed'}, 'put').status_code, 200)
        self.client.force_login(self.b)
        self.assertEqual(self.client.get(f"/api/drafts/{draft['id']}").status_code, 404)
        self.client.force_login(self.a)
        self.assertEqual(self.client.delete(f"/api/media/{asset['id']}").status_code, 409)
        publish = {**payload, 'requestKey': 'publish-key', 'draftId': draft['id']}
        first = self.write('community/posts', publish)
        self.assertEqual(first.status_code, 201)
        second = self.write('community/posts', publish)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first.json()['data']['id'], second.json()['data']['id'])
        self.assertEqual(Post.objects.count(), 1)
        self.assertFalse(Draft.objects.exists())
        self.assertEqual(self.write('community/posts', {**publish, 'title': 'different'}).status_code, 409)
        self.client.logout()
        self.assertEqual(self.client.get(asset['url']).status_code, 200)
        Post.objects.update(moderation_status='offline')
        self.assertEqual(self.client.get(asset['url']).status_code, 404)

    def test_cleanup_protects_references_and_failed_receipt_rolls_back(self):
        asset = self.upload()
        old = timezone.now() - timedelta(days=2)
        Media.objects.update(created_at=old)
        self.write('drafts', {'title': 'keep', 'mediaIds': [asset['id']]})
        output = StringIO()
        call_command('cleanup_media', apply=True, stdout=output)
        self.assertTrue(Media.objects.exists())
        failed = self.write('community/posts', {'title': [], 'requestKey': 'failed-key'})
        self.assertEqual(failed.status_code, 400)
        self.assertFalse(RequestReceipt.objects.filter(key='failed-key').exists())
        Draft.objects.all().delete()
        call_command('cleanup_media', stdout=output)
        self.assertTrue(Media.objects.exists())
        call_command('cleanup_media', apply=True, stdout=output)
        self.assertFalse(Media.objects.exists())
