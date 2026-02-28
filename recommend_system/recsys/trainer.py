import numpy as np
import pandas as pd
import optuna
import os
from typing import Any
from sklearn.model_selection import train_test_split
from implicit.als import AlternatingLeastSquares

from .config import Config, TuningSpace, logger
from .data import DataManager
from .matrix import build_interaction_matrix, SafeCSR
from .metrics import MetricsEvaluator


class RecommenderSystem:
    """ALS 训练与推荐主类。"""
    def __init__(self, config_or_path: Any = None):
        self.cfg = Config(csv_path=config_or_path) if isinstance(config_or_path, str) else (config_or_path or Config())
        self.data_manager = DataManager(self.cfg)
        self.model = None
        self.best_params = None
        self.train_mat = None
        self.tuning = TuningSpace()

    def _stratified_split(self, user_idx, behaviors, n_users, validation_ratio=0.2, min_interactions=5):
        """基于全行为的分层切分，保证验证标签一致。

        Args:
            user_idx: 用户索引数组。
            behaviors: 行为布尔/数值字典。
            n_users: 用户数量。
            validation_ratio: 验证比例。
            min_interactions: 分层所需最少交互数。

        Returns:
            Tuple[np.ndarray, np.ndarray]: (train_idx, val_idx)。
        """
        # 使用全行为掩码，确保验证标签与训练一致
        all_mask = behaviors['read'] | behaviors['like'] | behaviors['favorite'] | behaviors['share']
        all_indices = np.where(all_mask)[0]

        if len(all_indices) < 2:
            logger.warning("Not enough interactions for validation split; using all interactions for training.")
            return np.arange(len(user_idx)), np.array([], dtype=np.int64)

        df_ind = pd.DataFrame({'u': user_idx[all_indices], 'idx': all_indices})
        user_counts = df_ind.groupby('u')['idx'].count()
        valid_users = user_counts[user_counts >= min_interactions].index.values

        eligible_mask = df_ind['u'].isin(valid_users)
        eligible_indices = df_ind.loc[eligible_mask, 'idx'].values
        eligible_uids = df_ind.loc[eligible_mask, 'u'].values

        if len(eligible_indices) == 0:
            logger.warning("No users with sufficient interactions; falling back to random split on all events.")
            eligible_indices = all_indices
            eligible_uids = user_idx[all_indices]

        if len(eligible_indices) < 2:
            logger.warning("Too few eligible interactions for split; using all interactions for training.")
            return np.arange(len(user_idx)), np.array([], dtype=np.int64)

        try:
            _, val_el_idx = train_test_split(
                eligible_indices,
                test_size=validation_ratio,
                stratify=eligible_uids,
                random_state=42,
            )
        except ValueError as e:
            logger.warning(f"Stratified split failed: {e}. Falling back to random split.")
            _, val_el_idx = train_test_split(eligible_indices, test_size=validation_ratio, random_state=42)

        val_mask = np.zeros(len(user_idx), dtype=bool)
        val_mask[list(val_el_idx)] = True
        full_indices = np.arange(len(user_idx))
        train_idx = full_indices[~val_mask]
        val_idx = full_indices[val_mask]

        logger.info(f"Split (all-behavior): Train={len(train_idx)} Val={len(val_idx)} | Eligible users={len(valid_users)}/{n_users}")
        return train_idx, val_idx

    def fit(self, n_trials=None, validation_ratio=0.1):
        """调参 + 训练入口。"""
        if n_trials is None:
            n_trials = self.tuning.n_trials
        
        logger.info(f"[Fit] Starting process. GPU Enabled: {self.cfg.use_gpu}")
        df = self.data_manager.load_data()
        user_idx, item_idx, behaviors, n_u, n_i = self.data_manager.get_interaction_arrays(df)

        train_idx, val_idx = self._stratified_split(
            user_idx, behaviors, n_u, validation_ratio=validation_ratio, min_interactions=5
        )
        logger.info(f"[Fit] Split: {len(train_idx)} train, {len(val_idx)} val interactions.")

        val_weights = {k: 1.0 for k in self.cfg.behavior_cols}
        val_mat = build_interaction_matrix(
            user_idx, item_idx, behaviors, (n_u, n_i), weights=val_weights, indices_subset=val_idx
        )

        study = optuna.create_study(direction="maximize")
        if hasattr(self.tuning, "initial_params") and self.tuning.initial_params:
            logger.info(f"Enqueuing initial params: {self.tuning.initial_params}")
            study.enqueue_trial(self.tuning.initial_params)

        study.optimize(
            lambda t: self._objective(t, user_idx, item_idx, behaviors, (n_u, n_i), train_idx, val_mat),
            n_trials=n_trials,
            gc_after_trial=True,
        )

        self.best_params = study.best_params
        logger.info(f"[Fit] Best NDCG: {study.best_value:.4f} | Params: {self.best_params}")

        self._train_final_model(user_idx, item_idx, behaviors, (n_u, n_i), train_idx)
        self.save()

    def _objective(self, trial, u_idx, i_idx, behaviors, shape, train_idx, val_mat):
        """Optuna 目标函数：返回 NDCG@10。"""
        # 行为权重搜索空间（避免单一行为权重过高）
        t = self.tuning
        weights = {
            "read": trial.suggest_float("w_read", *t.w_read),
            "like": trial.suggest_float("w_like", *t.w_like),
            "favorite": trial.suggest_float("w_favorite", *t.w_favorite),
            "share": trial.suggest_float("w_share", *t.w_share),
        }

        bm25_cfg = {
            "b": trial.suggest_float("bm25_b", *t.bm25_b),
            "scale": trial.suggest_float("bm25_scale", *t.bm25_scale),
        }

        # 训练矩阵（子集）
        train_mat = build_interaction_matrix(
            u_idx, i_idx, behaviors, shape, weights, weighting_mode="bm25", bm25_params=bm25_cfg, indices_subset=train_idx
        )

        n_val_users = val_mat.getnnz(axis=1).nonzero()[0].shape[0]
        if n_val_users == 0:
            return 0.0

        model = AlternatingLeastSquares(
            factors=trial.suggest_int("rank", *t.rank),
            regularization=trial.suggest_float("reg", *t.reg),
            alpha=trial.suggest_float("alpha", *t.alpha),
            iterations=t.iterations_search,
            random_state=self.cfg.random_state,
            use_gpu=self.cfg.use_gpu,
        )
        model.fit(train_mat)

        metrics = MetricsEvaluator.eval(model, SafeCSR(train_mat), SafeCSR(val_mat), K=self.cfg.eval_k)
        
        # Log multiple metrics for observation
        logger.info(
            f"Trial {trial.number} metrics: "
            f"NDCG@{self.cfg.eval_k}={metrics['ndcg']:.4f}, "
            f"MAP@{self.cfg.eval_k}={metrics['map']:.4f}, "
            f"Precision@{self.cfg.eval_k}={metrics['precision']:.4f}, "
            f"AUC={metrics['auc']:.4f}"
        )
        
        return metrics["ndcg"]

    def _train_final_model(self, u_idx, i_idx, behaviors, shape, train_idx):
        """使用最优超参训练全量模型并保存。"""
        # 使用最优超参训练全量模型
        p = self.best_params or {}
        t = self.tuning
        weights = {
            "read": p.get("w_read", t.w_read[0]),
            "like": p.get("w_like", t.w_like[0]),
            "favorite": p.get("w_favorite", t.w_favorite[0]),
            "share": p.get("w_share", t.w_share[0]),
        }

        bm25_cfg = {"b": p.get("bm25_b", t.bm25_b[0]), "scale": p.get("bm25_scale", t.bm25_scale[0])}

        logger.info("Building final training matrix (bm25)...")
        self.train_mat = build_interaction_matrix(
            u_idx, i_idx, behaviors, shape, weights, weighting_mode="bm25", bm25_params=bm25_cfg, indices_subset=train_idx
        )

        logger.info("Training final ALS model...")
        self.model = AlternatingLeastSquares(
            factors=p.get("rank", t.final_rank),
            regularization=p.get("reg", t.final_reg),
            alpha=p.get("alpha", t.final_alpha),
            iterations=t.final_iterations,
            random_state=self.cfg.random_state,
            use_gpu=self.cfg.use_gpu,
        )
        self.model.fit(self.train_mat)

    def recommend(self, user_id, n=10):
        if not self.model:
            raise RuntimeError("Model not trained.")
        if user_id not in self.data_manager.user_map:
            return []
        u_idx = self.data_manager.user_map[user_id]
        user_items = self.train_mat[u_idx]
        ids, scores = self.model.recommend(u_idx, user_items, N=n, filter_already_liked_items=True)
        return [(self.data_manager.rev_item_map.get(i), float(s)) for i, s in zip(ids, scores)]

    def save(self):
        if self.model:
            self.model.save(self.cfg.model_path)
            np.savez_compressed(
                self.cfg.mappings_path,
                user_map=self.data_manager.user_map,
                item_map=self.data_manager.item_map,
                rev_user_map=self.data_manager.rev_user_map,
                rev_item_map=self.data_manager.rev_item_map,
                best_params=self.best_params,
            )
            logger.info(f"Saved model to {self.cfg.model_path}")

    def load(self):
        if not os.path.exists(self.cfg.model_path):
            raise FileNotFoundError("No model found.")
        self.model = AlternatingLeastSquares()
        self.model.load(self.cfg.model_path)
        maps = np.load(self.cfg.mappings_path, allow_pickle=True)
        self.data_manager.user_map = maps["user_map"].item()
        self.data_manager.item_map = maps["item_map"].item()
        self.data_manager.rev_user_map = maps["rev_user_map"].item()
        self.data_manager.rev_item_map = maps["rev_item_map"].item()
        self.best_params = maps["best_params"].item()
        logger.info("Model loaded.")
