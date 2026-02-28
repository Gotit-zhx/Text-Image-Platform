import json

from django.contrib.auth.models import Group
from django.contrib.auth.models import User
from django.test import TestCase

from .models import Comment, Follow, Post, PostInteraction


class CommunityApiTests(TestCase):
    def _post_json(self, url: str, payload: dict):
        return self.client.post(
            url,
            data=json.dumps(payload),
            content_type='application/json',
        )

    def _put_json(self, url: str, payload: dict):
        return self.client.put(
            url,
            data=json.dumps(payload),
            content_type='application/json',
        )

    def test_bootstrap_returns_posts(self):
        response = self.client.get('/api/community/bootstrap')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['code'], 0)
        self.assertGreaterEqual(len(data['data']['posts']), 1)

    def test_create_post_requires_login(self):
        response = self._post_json('/api/community/posts', {'title': 'x', 'contentHtml': '<p>x</p>'})
        self.assertEqual(response.status_code, 401)

    def test_register_and_create_post_success(self):
        register = self._post_json(
            '/api/auth/register',
            {'email': 'api_tester@example.com', 'password': '123456'},
        )
        self.assertEqual(register.status_code, 201)

        create_post = self._post_json(
            '/api/community/posts',
            {
                'title': '测试帖子',
                'summary': '摘要',
                'contentHtml': '<p>内容</p>',
                'tags': ['测试'],
                'images': [],
            },
        )
        self.assertEqual(create_post.status_code, 201)
        payload = create_post.json()
        self.assertEqual(payload['code'], 0)
        self.assertEqual(payload['data']['title'], '测试帖子')

    def test_only_author_can_update_post(self):
        author = User.objects.create_user(username='author', email='a@example.com', password='123456')
        other = User.objects.create_user(username='other', email='o@example.com', password='123456')
        post = Post.objects.create(author=author, title='A', summary='S', content_html='C')

        self.client.force_login(other)
        response = self._put_json(f'/api/community/posts/{post.id}', {'title': 'B'})
        self.assertEqual(response.status_code, 403)

    def test_like_and_comment_flow(self):
        user = User.objects.create_user(username='u1', email='u1@example.com', password='123456')
        author = User.objects.create_user(username='u2', email='u2@example.com', password='123456')
        post = Post.objects.create(author=author, title='T', summary='S', content_html='C')

        self.client.force_login(user)

        like_resp = self._post_json(f'/api/community/posts/{post.id}/like', {'isLiked': True})
        self.assertEqual(like_resp.status_code, 200)
        self.assertTrue(PostInteraction.objects.filter(user=user, post=post, is_liked=True).exists())

        comment_resp = self._post_json(
            f'/api/community/posts/{post.id}/comments',
            {'content': '不错'},
        )
        self.assertEqual(comment_resp.status_code, 201)

        comment_id = comment_resp.json()['data']['id']
        like_comment_resp = self._post_json(f'/api/community/comments/{comment_id}/like', {'isLiked': True})
        self.assertEqual(like_comment_resp.status_code, 200)

        del_comment_resp = self.client.delete(f'/api/community/comments/{comment_id}')
        self.assertEqual(del_comment_resp.status_code, 200)
        self.assertFalse(Comment.objects.filter(id=comment_id).exists())

    def test_follow_self_blocked(self):
        user = User.objects.create_user(username='self_u', email='self@example.com', password='123456')
        self.client.force_login(user)
        response = self._post_json(f'/api/community/authors/{user.id}/follow', {'isFollowing': True})
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Follow.objects.filter(follower=user, followee=user).exists())

    def test_admin_auth_me_requires_staff(self):
        user = User.objects.create_user(username='normal_u', email='normal@example.com', password='123456')
        self.client.force_login(user)
        response = self.client.get('/api/admin/auth/me')
        self.assertEqual(response.status_code, 403)

    def test_admin_review_post_success(self):
        admin = User.objects.create_user(
            username='admin_u',
            email='admin_u@example.com',
            password='123456',
            is_staff=True,
            is_superuser=True,
        )
        group, _ = Group.objects.get_or_create(name='super_admin')
        admin.groups.add(group)
        author = User.objects.create_user(username='writer_u', email='writer@example.com', password='123456')
        post = Post.objects.create(author=author, title='待审核内容', summary='s', content_html='c')

        self.client.force_login(admin)
        response = self._post_json(
            f'/api/admin/moderation/posts/{post.id}/review',
            {'action': 'offline', 'reason': '测试下架'},
        )
        self.assertEqual(response.status_code, 200)

        post.refresh_from_db()
        self.assertEqual(post.moderation_status, 'offline')

    def test_update_profile_persisted(self):
        user = User.objects.create_user(username='before_name', email='before@example.com', password='123456')
        self.client.force_login(user)

        response = self._put_json(
            '/api/users/me/profile',
            {
                'name': 'after_name',
                'avatarUrl': 'https://example.com/avatar.png',
                'gender': 'female',
            },
        )
        self.assertEqual(response.status_code, 200)

        user.refresh_from_db()
        self.assertEqual(user.username, 'after_name')
        self.assertEqual(user.profile.avatar_url, 'https://example.com/avatar.png')
        self.assertEqual(user.profile.gender, 'female')
