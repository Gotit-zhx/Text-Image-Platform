from django.urls import path

from . import views

urlpatterns = [
    path('auth/register', views.auth_register),
    path('auth/login', views.auth_login),
    path('auth/logout', views.auth_logout),
    path('users/me', views.users_me),
    path('community/bootstrap', views.community_bootstrap),
    path('community/recommend', views.community_recommend),
    path('community/recommend/status', views.community_recommend_status),
    path('community/search', views.community_search),
    path('community/posts', views.posts_create),
    path('community/posts/<int:post_id>', views.posts_update),
    path('community/posts/<int:post_id>/comments', views.comments_create),
    path('community/posts/<int:post_id>/like', views.post_like_toggle),
    path('community/posts/<int:post_id>/favorite', views.post_favorite_toggle),
    path('community/authors/<int:author_id>/follow', views.author_follow_toggle),
    path('community/comments/<int:comment_id>/like', views.comment_like_toggle),
    path('community/comments/<int:comment_id>', views.comment_delete),
]
