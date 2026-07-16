from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import pandas as pd


async def compute_3d_embedding(path: str | Path, *, sample: int = 800) -> dict[str, Any]:
    """Project a dataset into 3D space for visualisation.

    Numeric columns are standardised and reduced to three principal components
    with PCA. Categorical columns are one-hot encoded before reduction so the
    embedding reflects both numeric structure and category membership. The
    result is consumed by the 3D scatter UI.
    """
    file_path = Path(path)

    def _embed() -> dict[str, Any]:
        if file_path.suffix.lower() == ".parquet":
            df = pd.read_parquet(file_path)
        else:
            df = pd.read_csv(file_path)
        if len(df) > sample:
            df = df.sample(sample, random_state=0)
        df = df.dropna()

        numeric = df.select_dtypes(include="number")
        categorical = df.select_dtypes(exclude="number")
        parts: list[pd.DataFrame] = []
        if not numeric.empty:
            parts.append((numeric - numeric.mean()) / (numeric.std() + 1e-9))
        if not categorical.empty:
            parts.append(pd.get_dummies(categorical.astype("object")).astype(float))

        if not parts:
            return {"points": [], "axes": ["PC1", "PC2", "PC3"], "variance": [0, 0, 0]}

        matrix = pd.concat(parts, axis=1).fillna(0)
        from sklearn.decomposition import PCA

        n_components = min(3, matrix.shape[1], matrix.shape[0])
        if n_components < 3:
            # Pad with zeros when we cannot produce 3 components.
            coords = matrix.values[:, :n_components]
            pad = [[0.0, 0.0, 0.0] for _ in range(len(coords))]
            for i, row in enumerate(coords):
                for j in range(n_components):
                    pad[i][j] = float(row[j])
            coords = pad
            explained = [1.0 / max(n_components, 1)] * 3
        else:
            pca = PCA(n_components=3, random_state=0)
            coords = pca.fit_transform(matrix.values)
            explained = [float(v) for v in pca.explained_variance_ratio_]

        points = [
            {
                "x": float(coords[i][0]),
                "y": float(coords[i][1]),
                "z": float(coords[i][2]),
                "label": str(df.index[i]) if df.index.dtype == "object" else int(df.index[i]),
            }
            for i in range(len(coords))
        ]
        return {"points": points, "axes": ["PC1", "PC2", "PC3"], "variance": explained}

    return await asyncio.to_thread(_embed)
