import numpy as np
from scipy.sparse import csr_matrix
from implicit.nearest_neighbours import bm25_weight


class SafeCSR(csr_matrix):
    """Compatibility wrapper for pandas/scipy index types."""
    def __getitem__(self, index):
        try:
            return super().__getitem__(index)
        except AttributeError as e:
            if "dtype" in str(e):
                return super().__getitem__(np.asarray(index))
            raise e


def build_interaction_matrix(
    user_idx,
    item_idx,
    behaviors,
    shape,
    weights,
    weighting_mode="bm25",
    bm25_params=None,
    indices_subset=None,
):
    """根据多行为权重构建稀疏交互矩阵。

    Args:
        user_idx: 用户索引数组。
        item_idx: 物品索引数组。
        behaviors: 行为列名到 bool/数值数组的映射。
        shape: 矩阵形状 (n_users, n_items)。
        weights: 行为权重字典。
        weighting_mode: 权重模式，默认 "bm25"。
        bm25_params: BM25 参数字典，含 b 与 scale。
        indices_subset: 可选子集索引（用于切分）。

    Returns:
        csr_matrix: 加权后的用户-物品矩阵。
    """
    # 选择全部或子集索引（训练/验证切分）
    idx = indices_subset if indices_subset is not None else slice(None)
    # 多行为线性加权
    scores = np.zeros(len(user_idx) if indices_subset is None else len(indices_subset), dtype=np.float32)

    for b_name, weight in weights.items():
        if weight != 0:
            scores += behaviors[b_name][idx] * weight

    u_indices = user_idx[idx]
    i_indices = item_idx[idx]
    mat = csr_matrix((scores, (u_indices, i_indices)), shape=shape, dtype=np.float32)

    # 可选 BM25 权重，缓解热门偏置
    if weighting_mode == "bm25" and bm25_params:
        mat = bm25_weight(mat, B=bm25_params.get("b", 0.9)) * bm25_params.get("scale", 100.0)

    mat.eliminate_zeros()
    return mat.tocsr()
