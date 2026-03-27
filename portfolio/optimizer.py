"""Portfolio optimisation methods.

Planned implementations:
- Mean-Variance Optimisation (Modern Portfolio Theory / Markowitz)
- Black-Litterman model (incorporating analyst views)
- Risk-Parity
- Factor model-based optimisation (Fama-French)
"""

from __future__ import annotations

import numpy as np
import pandas as pd


class MeanVarianceOptimizer:
    """Markowitz mean-variance optimiser.

    TODO: Implement using scipy.optimize with constraints:
      - weights sum to 1
      - each weight in [min_weight, max_weight]
      - optional sector concentration limit
    """

    def __init__(
        self,
        risk_free_rate: float = 0.05,
        min_weight: float = 0.0,
        max_weight: float = 0.3,
    ) -> None:
        self.risk_free_rate = risk_free_rate
        self.min_weight = min_weight
        self.max_weight = max_weight

    def optimise(
        self,
        returns: pd.DataFrame,
        objective: str = "sharpe",
    ) -> dict[str, float]:
        """Compute optimal portfolio weights.

        Args:
            returns: Daily return DataFrame, columns = symbols.
            objective: One of "sharpe", "min_variance", "risk_parity".

        Returns:
            Mapping of symbol → weight.
        """
        raise NotImplementedError


class BlackLittermanOptimizer:
    """Black-Litterman model that blends market equilibrium with analyst views.

    TODO: Implement using the standard BL formula combining prior (market cap
    weights + CAPM equilibrium returns) with an investor view matrix P and
    confidence matrix Omega.
    """

    def optimise(
        self,
        market_cap_weights: dict[str, float],
        views: dict[str, float],
        view_confidence: dict[str, float],
        cov_matrix: pd.DataFrame,
    ) -> dict[str, float]:
        """Return BL posterior optimal weights.

        Args:
            market_cap_weights: Market-cap weighted prior weights.
            views: Analyst return views per symbol (fractional).
            view_confidence: Confidence in each view in (0, 1].
            cov_matrix: Covariance matrix of returns.

        Returns:
            Mapping of symbol → weight.
        """
        raise NotImplementedError
