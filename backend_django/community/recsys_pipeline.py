from __future__ import annotations

import csv
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Tuple

from django.conf import settings

from .models import Comment, PostInteraction


def get_recsys_paths() -> Tuple[Path, Path, Path, Path]:
    backend_root = Path(settings.BASE_DIR)
    workspace_root = backend_root.parent
    recsys_root = workspace_root / 'recommend_system'
    cache_dir = recsys_root / 'cache'
    export_csv = cache_dir / 'daily_interactions.csv'
    model_path = cache_dir / 'trained_model.npz'
    return recsys_root, cache_dir, export_csv, model_path


def get_recsys_status_path() -> Path:
    backend_root = Path(settings.BASE_DIR)
    return backend_root / 'recsys_train_status.json'


def write_recsys_status(status: dict):
    payload = {
        'updatedAt': datetime.now().isoformat(timespec='seconds'),
        **status,
    }
    path = get_recsys_status_path()
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')


def export_interactions_csv(export_csv: Path) -> int:
    export_csv.parent.mkdir(parents=True, exist_ok=True)

    interactions: Dict[Tuple[int, int], Dict[str, bool]] = {}

    for row in PostInteraction.objects.values('user_id', 'post_id', 'is_liked', 'is_favorited'):
        key = (int(row['user_id']), int(row['post_id']))
        cur = interactions.setdefault(
            key,
            {'read': False, 'like': False, 'favorite': False, 'share': False},
        )
        cur['read'] = True
        cur['like'] = bool(row['is_liked'])
        cur['favorite'] = bool(row['is_favorited'])

    for row in Comment.objects.values('author_id', 'post_id'):
        key = (int(row['author_id']), int(row['post_id']))
        cur = interactions.setdefault(
            key,
            {'read': False, 'like': False, 'favorite': False, 'share': False},
        )
        cur['read'] = True

    if not interactions:
        return 0

    with export_csv.open('w', newline='', encoding='utf-8') as fp:
        writer = csv.DictWriter(
            fp,
            fieldnames=['user_id', 'article_id', 'read', 'like', 'favorite', 'share'],
        )
        writer.writeheader()
        for (user_id, post_id), actions in interactions.items():
            writer.writerow(
                {
                    'user_id': user_id,
                    'article_id': post_id,
                    'read': actions['read'],
                    'like': actions['like'],
                    'favorite': actions['favorite'],
                    'share': actions['share'],
                }
            )

    return len(interactions)


def run_recsys_training(recsys_root: Path, export_csv: Path, cache_dir: Path, trials: int, val_ratio: float) -> None:
    base_name = export_csv.stem
    parquet_cache = cache_dir / f'sampled_{base_name}.parquet'
    npz_cache = cache_dir / f'interactions_{base_name}.npz'
    for cache_path in [parquet_cache, npz_cache]:
        if cache_path.exists():
            cache_path.unlink()

    cmd = [
        sys.executable,
        'recommender.py',
        '--mode',
        'train',
        '--csv',
        str(export_csv),
        '--cache',
        str(cache_dir),
        '--trials',
        str(trials),
        '--val_ratio',
        str(val_ratio),
    ]

    subprocess.run(cmd, cwd=str(recsys_root), check=True)
