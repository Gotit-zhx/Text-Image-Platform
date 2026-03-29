from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path
from typing import List

from django.conf import settings

from .models import Follow, Post, PostInteraction
from .recsys_pipeline import get_recsys_paths

_RECSYS_READY = False
_RECSYS_LOAD_ERROR = None
_RECSYS_SERVICE = None


def reset_recsys_service():
    global _RECSYS_READY, _RECSYS_LOAD_ERROR, _RECSYS_SERVICE
    _RECSYS_READY = False
    _RECSYS_LOAD_ERROR = None
    _RECSYS_SERVICE = None


def _setup_recsys_service():
    global _RECSYS_READY, _RECSYS_LOAD_ERROR, _RECSYS_SERVICE
    if _RECSYS_READY or _RECSYS_LOAD_ERROR is not None:
        return

    try:
        recsys_root, cache_dir, export_csv, model_path = get_recsys_paths()
        if str(recsys_root) not in sys.path:
            sys.path.insert(0, str(recsys_root))

        from recsys import ALSRecommenderService, Config  # type: ignore

        default_csv = recsys_root / 'QK-article-cleaned.csv'
        csv_path = str(export_csv if export_csv.exists() else default_csv)
        cache_dir_str = str(cache_dir)
        model_path_str = str(model_path)

        cfg = Config(csv_path=csv_path, cache_dir=cache_dir_str, model_filename='trained_model.npz')
        service = ALSRecommenderService(cfg=cfg, model_path=model_path_str)
        service.load()

        _RECSYS_SERVICE = service
        _RECSYS_READY = True
    except Exception as exc:  # pragma: no cover - 联调兜底
        _RECSYS_LOAD_ERROR = exc


def _personalized_fallback_ids(user_id: int, k: int) -> List[int]:
    interactions = list(
        PostInteraction.objects.filter(user_id=user_id)
        .select_related('post')
        .order_by('-id')[:200]
    )
    interacted_post_ids = [item.post_id for item in interactions]

    followed_author_ids = set(
        Follow.objects.filter(follower_id=user_id).values_list('followee_id', flat=True)
    )

    if not interactions and not followed_author_ids:
        return []

    preferred_author_counter: Counter[int] = Counter()
    preferred_tag_counter: Counter[str] = Counter()

    for interaction in interactions:
        weight = 1
        if interaction.is_liked:
            weight += 2
        if interaction.is_favorited:
            weight += 3

        preferred_author_counter[interaction.post.author_id] += weight
        for tag in interaction.post.tags or []:
            if isinstance(tag, str) and tag.strip():
                preferred_tag_counter[tag.strip()] += weight

    candidate_posts = list(
        Post.objects.exclude(id__in=interacted_post_ids)
        .order_by('-created_at')[:500]
    )

    scored_items = []
    for post in candidate_posts:
        author_score = preferred_author_counter.get(post.author_id, 0)
        follow_score = 3 if post.author_id in followed_author_ids else 0
        tag_score = 0
        for tag in post.tags or []:
            if isinstance(tag, str):
                tag_score += preferred_tag_counter.get(tag.strip(), 0)

        heat_score = min(post.likes_count, 300) / 300
        score = author_score * 1.6 + follow_score + tag_score * 0.8 + heat_score

        if score > 0:
            scored_items.append((score, post.likes_count, post.id))

    scored_items.sort(key=lambda item: (item[0], item[1], item[2]), reverse=True)
    personalized_ids = [item[2] for item in scored_items]

    if len(personalized_ids) < k and followed_author_ids:
        followed_post_ids = list(
            Post.objects.filter(author_id__in=followed_author_ids)
            .exclude(id__in=personalized_ids)
            .order_by('-created_at')
            .values_list('id', flat=True)
        )
        personalized_ids.extend(followed_post_ids)

    return personalized_ids[:k]


def recommended_post_ids_for_user(user_id: int | None, k: int = 20) -> List[int]:
    _setup_recsys_service()

    if _RECSYS_READY and _RECSYS_SERVICE and user_id is not None:
        try:
            recs = _RECSYS_SERVICE.recommend(user_id, k=k)
            ids: List[int] = []
            for item_id, _score in recs:
                try:
                    ids.append(int(item_id))
                except (TypeError, ValueError):
                    continue
            if ids:
                return ids
        except Exception:
            pass

    if user_id is not None:
        personalized_ids = _personalized_fallback_ids(user_id, k)
        if personalized_ids:
            return personalized_ids

    # 冷启动/模型不可用回退：按热门排序
    return list(
        Post.objects.order_by('-likes_count', '-created_at').values_list('id', flat=True)[:k]
    )
