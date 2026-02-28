import numpy as np
from implicit.evaluation import ranking_metrics_at_k

class MetricsEvaluator:
    """评估指标计算工具。"""

    @staticmethod
    def eval(model, train_mat, val_mat, K=10, batch_size=2000):
        """批量评估模型指标 (使用 implicit 高效评估)。

        Args:
            model: 训练好的 ALS 模型。
            train_mat: 训练稀疏矩阵（用于过滤已交互）。
            val_mat: 验证稀疏矩阵（标签）。
            K: Top-K 截断。
            batch_size: 批处理用户数量（此处由 implicit 内部控制，参数保留兼容）。

        Returns:
            dict: 包含 ndcg/precision/recall/map/auc。
        """
        metrics = ranking_metrics_at_k(
            model, 
            train_mat, 
            val_mat, 
            K=K,
            show_progress=True,
            num_threads=0 # Use all cores
        )
        return metrics
