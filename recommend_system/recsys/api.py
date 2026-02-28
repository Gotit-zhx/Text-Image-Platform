from typing import Any, List, Tuple, Optional
from .config import Config
from .trainer import RecommenderSystem


class ALSRecommenderService:
    """面向业务的服务封装，可在 Django 视图/DRF 中直接调用。"""

    def __init__(self, cfg: Optional[Config] = None, model_path: Optional[str] = None):
        """初始化服务。

        Args:
            cfg: 配置对象；缺省则使用默认 Config。
            model_path: 可选模型路径（覆盖 cfg.model_path）。
        """
        self.cfg = cfg or Config()
        if model_path:
            self.cfg.model_path = model_path
        self.system = RecommenderSystem(self.cfg)

    def train(self, n_trials: Optional[int] = None, validation_ratio: float = 0.1):
        """运行训练与调参。"""
        self.system.fit(n_trials=n_trials, validation_ratio=validation_ratio)

    def load(self):
        """加载已训练模型与映射。"""
        self.system.load()

    def recommend(self, user_id: Any, k: int = 10) -> List[Tuple[Any, float]]:
        """单用户推荐。

        Args:
            user_id: 原始用户 ID。
            k: 返回的 Top-K 数量。

        Returns:
            List[Tuple[Any, float]]: (item_id, score) 列表。
        """
        return self.system.recommend(user_id, n=k)

    def recommend_batch(self, user_ids: List[Any], k: int = 10) -> dict:
        # 简单批量封装，异常时返回空列表
        """批量推荐。

        Args:
            user_ids: 用户 ID 列表。
            k: Top-K 数量。

        Returns:
            dict: {user_id: [(item_id, score), ...]}。
        """
        results = {}
        for uid in user_ids:
            try:
                results[uid] = self.recommend(uid, k=k)
            except Exception:
                results[uid] = []
        return results
