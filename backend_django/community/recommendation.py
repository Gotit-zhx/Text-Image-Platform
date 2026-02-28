from __future__ import annotations

import sys
from pathlib import Path
from typing import List

from django.conf import settings

from .models import Post
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

    # 冷启动/模型不可用回退：按热门排序
    return list(
        Post.objects.order_by('-likes_count', '-created_at').values_list('id', flat=True)[:k]
    )
