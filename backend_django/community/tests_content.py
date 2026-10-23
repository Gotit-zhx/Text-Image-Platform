import json
from django.contrib.auth.models import User
from django.test import TestCase
from .models import Post, Comment, Follow, PostInteraction

class ContentLifecycleTests(TestCase):

    def setUp(self):
        self.author = User.objects.create_user(username='author', email='author@test.example', password='Garden!2026')
        self.other = User.objects.create_user(username='other', email='other@test.example', password='Garden!2026')
        self.post = Post.objects.create(author=self.author, title='标题', summary='摘要', content_html='<p>正文</p>', tags=['日常'])

    def write(self, method, path, data):
        return getattr(self.client, method)('/api/' + path, json.dumps(data), content_type='application/json')

    def test_independent_detail_summary_and_pagination(self):
        for i in range(25):
            Post.objects.create(author=self.author, title=f'标题{i}', content_html='大正文')
        response = self.client.get('/api/community/search?page=2&pageSize=12').json()['data']
        self.assertEqual(len(response['posts']), 12)
        self.assertTrue(response['pagination']['hasMore'])
        for item in response['posts']:
            self.assertNotIn('contentHtml', item)
            self.assertIn('T', item['createdAt'])
        self.assertEqual(self.client.get(f'/api/community/posts/{self.post.pk}').json()['data']['contentHtml'], '<p>正文</p>')

    def test_clear_optional_fields_sanitize_and_soft_delete(self):
        self.client.force_login(self.author)
        response = self.write('put', f'community/posts/{self.post.pk}', {'summary': '', 'tags': [], 'images': [], 'contentHtml': '<p onclick="bad()">safe</p><script>alert(1)</script><a href="javascript:bad()">link</a>'})
        self.assertEqual(response.status_code, 200)
        data = response.json()['data']
        self.assertEqual(data['summary'], '')
        self.assertEqual(data['tags'], [])
        self.assertNotIn('onclick', data['contentHtml'])
        self.assertNotIn('<script', data['contentHtml'])
        self.assertNotIn('javascript:', data['contentHtml'])
        self.assertEqual(self.client.delete(f'/api/community/posts/{self.post.pk}').status_code, 200)
        self.assertTrue(Post.objects.filter(pk=self.post.pk, deleted_at__isnull=False).exists())
        self.assertEqual(self.client.get(f'/api/community/posts/{self.post.pk}').status_code, 404)
        for action in ['like', 'favorite', 'read', 'share', 'comments']:
            self.assertEqual(self.write('post', f'community/posts/{self.post.pk}/{action}', {'content': 'x', 'isLiked': True, 'isFavorited': True}).status_code, 404)

    def test_permissions_invisible_post_comments_and_interactions(self):
        comment = Comment.objects.create(post=self.post, author=self.other, content='private comment')
        self.client.force_login(self.other)
        self.assertEqual(self.write('put', f'community/posts/{self.post.pk}', {'title': 'no'}).status_code, 403)
        self.assertEqual(self.client.delete(f'/api/community/posts/{self.post.pk}').status_code, 403)
        self.post.moderation_status = 'offline'
        self.post.save()
        self.assertEqual(self.client.get(f'/api/community/posts/{self.post.pk}').status_code, 404)
        self.assertEqual(self.write('post', f'community/posts/{self.post.pk}/comments', {'content': 'no'}).status_code, 404)
        self.assertEqual(self.write('post', f'community/comments/{comment.pk}/like', {'isLiked': True}).status_code, 404)
        self.assertEqual(self.client.get('/api/community/bootstrap').json()['data']['comments'], [])
        self.client.force_login(self.author)
        self.assertEqual(self.client.get(f'/api/community/posts/{self.post.pk}?manage=1').status_code, 200)
        self.write('put', f'community/posts/{self.post.pk}', {'title': 'changed'})
        self.post.refresh_from_db()
        self.assertEqual(self.post.moderation_status, 'offline')

    def test_field_validation_and_legacy_images(self):
        self.client.force_login(self.author)
        for data in [{'title': []}, {'title': 'x' * 256}, {'tags': 'bad'}, {'tags': ['x'] * 6}, {'images': ['data:image/png;base64,new']}]:
            self.assertEqual(self.write('put', f'community/posts/{self.post.pk}', data).status_code, 400)
        self.post.content_html = '<p>old</p><img src="data:image/png;base64,old">'
        self.post.images = ['data:image/png;base64,old']
        self.post.save()
        self.assertIn('data:image', self.client.get(f'/api/community/posts/{self.post.pk}').json()['data']['contentHtml'])
        self.assertEqual(self.write('put', f'community/posts/{self.post.pk}', {'title': 'preserved'}).status_code, 200)
        self.assertEqual(self.client.get('/api/community/search').json()['data']['posts'][0]['images'], [])

    def test_all_relationships_and_bookmark_visibility(self):
        for i in range(35):
            user = User.objects.create_user(username=f'fan{i}', email=f'fan{i}@test.example')
            Follow.objects.create(follower=user, followee=self.author)
        response = self.client.get(f'/api/community/users/{self.author.pk}/followers?page=2&pageSize=30').json()['data']
        self.assertEqual(len(response['items']), 5)
        self.assertEqual(response['pagination']['total'], 35)
        PostInteraction.objects.create(user=self.other, post=self.post, is_favorited=True)
        self.client.force_login(self.other)
        self.assertEqual(len(self.client.get('/api/users/me/bookmarks').json()['data']['items']), 1)
        self.post.moderation_status = 'offline'
        self.post.save()
        self.assertEqual(self.client.get('/api/users/me/bookmarks').json()['data']['items'], [])
