import json
from django.contrib.auth.models import User
from django.test import TestCase
from .models import Post, Comment, Follow, Notification, UserRelation, PostInteraction, CommentLike, Profile

class SocialFlowTests(TestCase):

    def setUp(self):
        self.a = User.objects.create_user(username='A', email='a@social.example')
        self.b = User.objects.create_user(username='B', email='b@social.example')
        self.c = User.objects.create_user(username='C', email='c@social.example')
        self.post = Post.objects.create(author=self.a, title='A post')
        self.client.force_login(self.b)

    def write(self, path, data=None, method='post'):
        return getattr(self.client, method)('/api/' + path, json.dumps(data or {}), content_type='application/json')

    def comment(self, content='comment', reply=None, key=None):
        return self.write(f'community/posts/{self.post.pk}/comments', {'content': content, 'replyToId': reply, 'requestKey': key})

    def test_reply_notification_dedup_and_deleted_parent(self):
        response = self.comment(key='comment-1')
        self.assertEqual(response.status_code, 201)
        root = response.json()['data']
        self.assertEqual(self.comment(key='comment-1').json()['data']['id'], root['id'])
        self.assertEqual(Comment.objects.count(), 1)
        self.assertEqual(Notification.objects.filter(recipient=self.a).count(), 1)
        self.client.force_login(self.a)
        reply = self.comment('reply', root['id'], 'reply-1').json()['data']
        self.assertEqual(reply['rootId'], root['id'])
        self.assertEqual(reply['replyToName'], 'B')
        second = self.comment('nested', reply['id'], 'reply-2').json()['data']
        self.assertEqual(second['rootId'], root['id'])
        self.assertEqual(second['parentId'], reply['id'])
        self.assertEqual(Notification.objects.filter(recipient=self.b).count(), 1)
        self.client.force_login(self.b)
        notice = self.client.get('/api/notifications').json()['data']['items'][0]
        self.assertEqual(notice['commentId'], reply['id'])
        self.write(f"notifications/{notice['id']}/read")
        self.assertIsNotNone(self.client.get('/api/notifications').json()['data']['items'][0]['readAt'])
        self.write('notifications/read-all')
        self.assertEqual(self.client.get('/api/notifications/unread').json()['data']['count'], 0)
        self.write(f"community/comments/{root['id']}", method='delete')
        result = self.client.get(f'/api/community/posts/{self.post.pk}/comments').json()['data']['items'][0]
        self.assertTrue(result['deleted'])
        self.assertEqual(result['content'], '该评论已删除')
        self.assertNotIn('comment', result['content'])
        self.assertEqual(result['replyCount'], 2)
        self.assertEqual(self.client.get(f"/api/community/comments/{root['id']}/replies").json()['data']['pagination']['total'], 2)
        self.assertEqual(self.comment('no', root['id']).status_code, 404)
        self.assertEqual(self.client.get(f'/api/community/posts/{self.post.pk}').json()['data']['comments'], 2)

    def test_cross_post_hidden_parent_and_complete_pagination(self):
        roots = [Comment.objects.create(post=self.post, author=self.b, content=str(i)) for i in range(61)]
        other = Post.objects.create(author=self.a, title='other')
        foreign = Comment.objects.create(post=other, author=self.a, content='foreign')
        self.assertEqual(self.comment('no', foreign.pk).status_code, 404)
        self.client.force_login(self.a)
        self.comment('visible child', roots[0].pk)
        roots[0].is_hidden = True
        roots[0].save()
        page1 = self.client.get(f'/api/community/posts/{self.post.pk}/comments?pageSize=50').json()['data']
        page2 = self.client.get(f'/api/community/posts/{self.post.pk}/comments?pageSize=50&page=2').json()['data']
        self.assertEqual(len(page1['items']) + len(page2['items']), 61)
        self.assertTrue(next((c for c in page2['items'] if c['id'] == roots[0].pk))['deleted'])
        self.assertEqual(next(c for c in page2['items'] if c['id'] == roots[0].pk)['content'], '该评论已不可用')
        self.assertEqual(self.comment('no', roots[0].pk).status_code, 404)

    def test_block_mute_and_server_interactions(self):
        self.write(f'community/authors/{self.a.pk}/follow', {'isFollowing': True})
        self.write(f'community/posts/{self.post.pk}/like', {'isLiked': True})
        self.write(f'community/posts/{self.post.pk}/like', {'isLiked': True})
        self.assertEqual(Notification.objects.count(), 2)
        self.assertEqual(self.client.get(f'/api/community/posts/{self.post.pk}').json()['data']['likes'], 1)
        self.write('users/me/mutes', {'userId': self.a.pk})
        self.assertEqual(self.client.get('/api/community/search').json()['data']['posts'], [])
        self.assertEqual(self.client.get(f'/api/community/posts/{self.post.pk}').status_code, 200)
        self.write('users/me/blocks', {'userId': self.a.pk})
        self.assertFalse(Follow.objects.exists())
        self.assertEqual(self.comment().status_code, 403)
        self.assertEqual(self.write(f'community/authors/{self.a.pk}/follow', {'isFollowing': True}).status_code, 403)
        self.client.force_login(self.a)
        self.assertEqual(self.write(f'community/authors/{self.b.pk}/follow', {'isFollowing': True}).status_code, 403)
        self.client.logout()
        self.assertEqual(self.client.get(f'/api/community/posts/{self.post.pk}').status_code, 200)

    def test_notifications_unavailable_and_no_self(self):
        self.client.force_login(self.a)
        self.comment('self')
        self.assertFalse(Notification.objects.exists())
        self.client.force_login(self.b)
        self.comment('by B')
        self.post.deleted_at = __import__('django.utils.timezone', fromlist=['now']).now()
        self.post.save()
        self.client.force_login(self.a)
        item = self.client.get('/api/notifications').json()['data']['items'][0]
        self.assertTrue(item['unavailable'])
        self.assertNotIn('by B', str(item))
        self.client.force_login(self.c)
        self.assertEqual(self.write(f"notifications/{item['id']}/read").status_code, 404)

    def test_notification_cursor_survives_new_events_and_rejects_foreign_anchor(self):
        from django.utils import timezone
        records = [Notification.objects.create(recipient=self.b, actor=self.a, event='follow',
                    target_type='user', target_id=self.a.pk, dedup_key=f'cursor:{i}') for i in range(45)]
        # Timestamp ties still have a stable descending ID boundary.
        Notification.objects.filter(pk__in=[n.pk for n in records]).update(created_at=timezone.now())
        first = self.client.get('/api/notifications').json()['data']
        first_ids = [n['id'] for n in first['items']]
        Notification.objects.bulk_create([Notification(recipient=self.b, actor=self.a, event='follow',
                    target_type='user', target_id=self.a.pk, dedup_key=f'new-cursor:{i}') for i in range(25)])
        second = self.client.get(f'/api/notifications?beforeId={first_ids[-1]}').json()['data']
        second_ids = [n['id'] for n in second['items']]
        third = self.client.get(f'/api/notifications?beforeId={second_ids[-1]}').json()['data']
        self.assertEqual(set(first_ids + second_ids + [n['id'] for n in third['items']]), {n.pk for n in records})
        self.assertFalse(third['pagination']['hasMore'])
        foreign = Notification.objects.create(recipient=self.a, event='user.status', target_type='user',
                    target_id=self.a.pk, dedup_key='foreign-cursor')
        self.assertEqual(self.client.get(f'/api/notifications?beforeId={foreign.pk}').status_code, 400)
        self.assertEqual(self.client.get('/api/notifications?beforeId=invalid').status_code, 400)
        self.assertEqual(self.client.get('/api/notifications?beforeId=' + '9' * 30).status_code, 400)
        self.assertEqual(self.client.get('/api/notifications?beforeId=9999999999999999999').status_code, 400)
        self.assertEqual(self.client.get(f'/api/notifications?category=system&beforeId={first_ids[-1]}').status_code, 400)
