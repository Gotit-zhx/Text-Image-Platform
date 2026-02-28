import os
import logging
import warnings
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

logging.basicConfig(level=logging.INFO, format='[%(name)s] %(message)s')
logger = logging.getLogger("RecSys")
warnings.filterwarnings("ignore")


@dataclass
class Config:
    """全局配置。

    Attributes:
        csv_path: 原始交互 CSV 路径。
        cache_dir: 缓存目录（parquet/npz/model）。
        model_filename: 模型文件名（保存在 cache_dir）。
        use_gpu: 是否启用 GPU 训练 ALS。
        behavior_cols: 多行为列名列表。
        random_state: 随机种子。
    """

    # 数据与缓存路径配置
    csv_path: str = "QK-article-cleaned.csv"
    cache_dir: str = "cache"
    model_filename: str = "trained_model.npz"
    use_gpu: bool = False
    # 多行为列名
    behavior_cols: List[str] = field(default_factory=lambda: ["read", "like", "favorite", "share"])
    random_state: int = 49
    # 评估指标 Top-K
    eval_k: int = 20
    # 小样本过滤阈值（数据库早期数据建议较低）
    min_user_interactions: int = 1
    min_item_interactions: int = 1

    def __post_init__(self):
        # 创建缓存目录，并根据原始 CSV 推导缓存文件名
        os.makedirs(self.cache_dir, exist_ok=True)
        base_name = os.path.splitext(os.path.basename(self.csv_path))[0]
        self.parquet_path = os.path.join(self.cache_dir, f"sampled_{base_name}.parquet")
        self.npz_path = os.path.join(self.cache_dir, f"interactions_{base_name}.npz")
        self.model_path = os.path.join(self.cache_dir, self.model_filename)
        self.mappings_path = os.path.join(self.cache_dir, f"{os.path.splitext(self.model_filename)[0]}_mappings.npz")


@dataclass
class TuningSpace:
    """统一管理 Optuna 搜索空间与默认值。"""

    # 行为权重范围 (min, max)
    w_read: Tuple[float, float] = (5.0, 20.0)
    w_like: Tuple[float, float] = (10.0, 40.0)
    w_favorite: Tuple[float, float] = (15.0, 60.0)
    w_share: Tuple[float, float] = (20.0, 80.0)

    # BM25 范围
    bm25_b: Tuple[float, float] = (0.1, 1.0)
    bm25_scale: Tuple[float, float] = (0.01, 10.0)

    # ALS 范围
    rank: Tuple[int, int] = (256, 512)
    reg: Tuple[float, float] = (0.01, 0.5)
    alpha: Tuple[float, float] = (1.0, 100.0)
    iterations_search: int = 20
    n_trials: int = 50

    # 初始搜索点（基于过往最佳 Trial）
    initial_params: Dict[str, float] = field(default_factory=lambda: {
        "w_read": 10,
        "w_like": 15,
        "w_favorite": 120,
        "w_share": 25,
        "bm25_b": 0.5,
        "bm25_scale": 0.6,
        "rank": 512,
        "reg": 0.3,
        "alpha": 24,
    })

    # 最终训练默认值
    final_rank: int = 384
    final_reg: float = 0.32
    final_alpha: float = 24.0
    final_iterations: int = 32
