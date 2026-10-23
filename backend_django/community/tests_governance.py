import json
from django.contrib.auth.models import User, Group
from django.test import TestCase
from .models import Profile, Post, Comment, Notification, Report, Appeal, AuditLog

class GovernanceFlowTests(TestCase):

    def setUp(self):
        self.a = self.user('A')
        self.b = self.user('B')
        self.mod = self.user('M', 'content_moderator')
        self.ops = self.user('O', 'operations')
        self.auditor = self.user('D', 'auditor')
        self.super = self.user('S', superuser=True)
        self.post = Post.objects.create(author=self.a, title='reported post')

    def user(self, name, role=None, superuser=False):
        user = User.objects.create_user(username=name, email=name.lower() + '@governance.example', is_staff=bool(role or superuser), is_superuser=superuser)
        Profile.objects.create(user=user)
        if role:
            group, _ = Group.objects.get_or_create(name=role)
            user.groups.add(group)
        return user

    def write(self, path, data, method='post'):
        return getattr(self.client, method)('/api/' + path, json.dumps(data), content_type='application/json')

    def test_full_report_offline_appeal_restore(self):
        self.client.force_login(self.b)
        data = {'targetType': 'post', 'targetId': self.post.pk, 'reason': '骚扰', 'description': '说明'}
        report = self.write('reports', data)
        self.assertEqual(report.status_code, 201)
        case_id = report.json()['data']['id']
        self.assertEqual(self.write('reports', data).status_code, 409)
        self.client.force_login(self.mod)
        response = self.write(f'admin/reports/{case_id}/resolve', {'action': 'offline', 'reason': '审核下架'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get(f'/api/community/posts/{self.post.pk}').status_code, 404)
        self.assertTrue(Notification.objects.filter(recipient=self.a, event='post.review').exists())
        self.assertTrue(Notification.objects.filter(recipient=self.b, event='report.resolved').exists())
        self.assertEqual(self.write(f'admin/reports/{case_id}/resolve', {'action': 'offline', 'reason': '重复'}).status_code, 409)
        self.client.force_login(self.a)
        self.assertEqual(self.write(f'community/posts/{self.post.pk}', {'title': 'changed'}, 'put').status_code, 200)
        self.post.refresh_from_db()
        self.assertEqual(self.post.moderation_status, 'offline')
        appeal = self.write('appeals', {'postId': self.post.pk, 'description': '请求重新检查'})
        self.assertEqual(appeal.status_code, 201)
        appeal_id = appeal.json()['data']['id']
        self.client.force_login(self.mod)
        self.assertEqual(self.write(f'admin/appeals/{appeal_id}/resolve', {'action': 'approve', 'reason': '复核通过'}).status_code, 200)
        self.assertEqual(self.client.get(f'/api/community/posts/{self.post.pk}').status_code, 200)
        self.assertTrue(Notification.objects.filter(recipient=self.a, event='appeal.resolved').exists())
        self.assertTrue(AuditLog.objects.filter(action='report.resolve').exists())

    def test_role_denial_last_super_and_existing_session_ban(self):
        self.client.force_login(self.auditor)
        self.assertEqual(self.client.get('/api/admin/moderation/posts').status_code, 200)
        self.assertEqual(self.write(f'admin/moderation/posts/{self.post.pk}/review', {'action': 'offline', 'reason': 'no'}).status_code, 403)
        self.assertEqual(self.write(f'admin/users/{self.a.pk}/status', {'action': 'ban', 'reason': 'no'}).status_code, 403)
        self.client.force_login(self.mod)
        self.assertEqual(self.write(f'admin/users/{self.a.pk}/roles', {'roles': ['operations']}, 'put').status_code, 403)
        old = __import__('django.test', fromlist=['Client']).Client()
        old.force_login(self.a)
        self.client.force_login(self.ops)
        self.assertEqual(self.write(f'admin/users/{self.a.pk}/status', {'action': 'ban', 'reason': '违规'}).status_code, 200)
        self.assertEqual(old.post('/api/community/posts', json.dumps({'title': 'blocked'}), content_type='application/json').status_code, 403)
        self.assertEqual(self.client.get(f'/api/community/posts/{self.post.pk}').status_code, 404)
        self.assertEqual(self.write(f'admin/users/{self.a.pk}/status', {'action': 'restore', 'reason': '解除'}).status_code, 200)
        self.assertEqual(old.post('/api/community/posts', json.dumps({'title': 'restored'}), content_type='application/json').status_code, 201)
        self.client.force_login(self.super)
        self.assertEqual(self.write(f'admin/users/{self.super.pk}/status', {'action': 'ban', 'reason': 'no'}).status_code, 409)
        self.assertEqual(self.write(f'admin/users/{self.super.pk}/roles', {'isAdmin': False}, 'put').status_code, 409)
        self.assertNotIn('todayActiveUsers', self.client.get('/api/admin/dashboard/overview').json()['data'])

    def test_resubmit_does_not_self_approve_and_private_data(self):
        self.post.moderation_status = 'rejected'
        self.post.review_reason = '原因'
        self.post.save()
        self.client.force_login(self.b)
        self.assertEqual(self.write(f'community/posts/{self.post.pk}/resubmit', {}).status_code, 409)
        self.client.force_login(self.a)
        self.assertEqual(self.write(f'community/posts/{self.post.pk}/resubmit', {}).status_code, 200)
        self.post.refresh_from_db()
        self.assertEqual(self.post.moderation_status, 'pending')
        self.client.force_login(self.mod)
        users = self.client.get('/api/admin/users').json()['data']['items']
        self.assertTrue(all(('email' not in user for user in users)))
        self.client.force_login(self.b)
        self.assertEqual(self.client.get('/api/admin/reports').status_code, 403)

    def test_muted_user_cannot_write_comment_or_like(self):
        self.client.force_login(self.ops)
        self.write(f'admin/users/{self.a.pk}/status', {'action': 'mute', 'reason': '7天禁言'})
        self.client.force_login(self.a)
        self.assertEqual(self.write(f'community/posts/{self.post.pk}/comments', {'content': 'blocked'}).status_code, 403)
        self.assertEqual(self.write(f'community/posts/{self.post.pk}/like', {'isLiked': True}).status_code, 403)
        self.assertEqual(self.client.get(f'/api/community/posts/{self.post.pk}').status_code, 200)

    def test_review_pending_and_restore_hidden_comment(self):
        self.client.force_login(self.mod)
        self.post.moderation_status='pending'
        self.post.save()
        self.assertEqual(self.write(f'admin/moderation/posts/{self.post.pk}/review',{'action':'approve','reason':'通过'}).status_code,200)
        comment=Comment.objects.create(post=self.post,author=self.b,content='可恢复评论')
        self.assertEqual(self.write(f'admin/moderation/comments/{comment.pk}/hide',{}).status_code,200)
        self.assertEqual(self.write(f'admin/moderation/comments/{comment.pk}/restore',{}).status_code,200)
        comment.refresh_from_db()
        self.assertFalse(comment.is_hidden)
        self.assertEqual(self.write(f'admin/moderation/posts/{self.post.pk}/review',{'action':[]}).status_code,400)
