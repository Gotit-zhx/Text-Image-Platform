import numpy as np
import pandas as pd
import os
from typing import Dict, Tuple
from .config import Config, logger


class DataManager:
    """负责数据读取、过滤、映射与缓存管理。"""
    def __init__(self, config: Config):
        self.cfg = config
        self.user_map: Dict = {}
        self.item_map: Dict = {}
        self.rev_user_map: Dict = {}
        self.rev_item_map: Dict = {}

    def load_data(self) -> pd.DataFrame:
        """加载交互数据。

        Returns:
            pd.DataFrame: 过滤后的交互数据，含行为列。
        """
        # 优先读取缓存的 Parquet，加快启动；否则处理原始 CSV
        if os.path.exists(self.cfg.parquet_path):
            logger.info(f"Loading cached data: {self.cfg.parquet_path}")
            return pd.read_parquet(self.cfg.parquet_path)
        return self._process_csv()

    def _process_csv(self) -> pd.DataFrame:
        """处理原始 CSV，标准化布尔并过滤低频用户/物品。

        Returns:
            pd.DataFrame: 过滤后的交互数据。
        """
        logger.info(f"Processing CSV: {self.cfg.csv_path}")
        # 将字符串布尔标准化为 True/False
        to_bool = lambda col: col.astype(str).str.lower().str.strip().isin(["true", "1", "yes", "t"])
        chunks = []
        for chunk in pd.read_csv(
            self.cfg.csv_path,
            usecols=["user_id", "article_id"] + self.cfg.behavior_cols,
            chunksize=50_000,
            low_memory=False,
        ):
            for col in self.cfg.behavior_cols:
                chunk[col] = to_bool(chunk[col])
            mask = chunk[self.cfg.behavior_cols].any(axis=1)
            filtered = chunk[mask]
            if not filtered.empty:
                chunks.append(filtered)
        if not chunks:
            raise ValueError("No valid interactions found in CSV.")
        df = pd.concat(chunks, ignore_index=True)

        # 过滤极低频用户/物品，减少长尾噪声
        item_freq = df["article_id"].value_counts()
        keep_items = item_freq[item_freq >= self.cfg.min_item_interactions].index
        user_freq = df["user_id"].value_counts()
        keep_users = user_freq[user_freq >= self.cfg.min_user_interactions].index
        before = len(df)
        df = df[df["article_id"].isin(keep_items) & df["user_id"].isin(keep_users)]
        logger.info(f"Filtered rare entities: {before} -> {len(df)} rows")

        df.to_parquet(self.cfg.parquet_path, index=False)
        return df

    def get_interaction_arrays(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, Dict[str, np.ndarray], int, int]:
        """将 DataFrame 转为索引数组并缓存。

        Args:
            df: 交互 DataFrame。

        Returns:
            Tuple: (user_idx, item_idx, behaviors, n_users, n_items)。
        """
        # 优先使用 npz 缓存的索引与行为数组，减少重复预处理
        if os.path.exists(self.cfg.npz_path):
            logger.info("Loading interaction arrays from NPZ cache...")
            data = np.load(self.cfg.npz_path)
            self._build_mappings(df)
            behaviors = {col: data[col] for col in self.cfg.behavior_cols}
            return (
                data["user_idx"],
                data["item_idx"],
                behaviors,
                int(data["n_users"]),
                int(data["n_items"]),
            )

        logger.info("Building ID mappings and arrays...")
        self._build_mappings(df)
        user_idx = df["user_id"].map(self.user_map).astype(np.int32).values
        item_idx = df["article_id"].map(self.item_map).astype(np.int32).values
        behaviors = {col: df[col].values for col in self.cfg.behavior_cols}
        n_users, n_items = len(self.user_map), len(self.item_map)

        np.savez_compressed(
            self.cfg.npz_path,
            user_idx=user_idx,
            item_idx=item_idx,
            n_users=n_users,
            n_items=n_items,
            **behaviors,
        )
        return user_idx, item_idx, behaviors, n_users, n_items

    def _build_mappings(self, df: pd.DataFrame):
        """构建用户/物品 ID 映射。"""
        # 为用户与物品构建 ID 映射，便于矩阵化
        unique_users = df["user_id"].unique()
        unique_items = df["article_id"].unique()
        self.user_map = {uid: i for i, uid in enumerate(unique_users)}
        self.item_map = {iid: i for i, iid in enumerate(unique_items)}
        self.rev_user_map = {i: uid for uid, i in self.user_map.items()}
        self.rev_item_map = {i: iid for iid, i in self.item_map.items()}
