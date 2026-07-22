"""
====================================================
Risk Service
====================================================
"""
from __future__ import annotations

from typing import List, Optional

from loguru import logger

from app.core.exceptions import NotFoundException
from app.schemas.risk import DistrictPrediction, RiskRanking, TopDistricts
from app.services.cache import CacheService
from ml.ml_loader import MLArtifactLoader


class RiskService:
    """Service for risk-related operations."""

    def __init__(
        self,
        ml_loader: MLArtifactLoader,
        cache: Optional[CacheService] = None,
    ) -> None:
        self.ml_loader = ml_loader
        self.cache = cache or CacheService()

    async def get_all_rankings(self) -> List[RiskRanking]:
        """Get all district risk rankings."""
        cache_key = "risk:all"
        cached = await self.cache.get(cache_key)
        if cached:
            return [RiskRanking(**r) for r in cached]

        df = self.ml_loader.get_risk_rankings()
        result = []
        for _, row in df.iterrows():
            result.append(self._row_to_ranking(row))
        await self.cache.set(cache_key, [r.model_dump() for r in result], ttl=300)
        return result

    async def get_top_n(self, n: int = 10) -> TopDistricts:
        """Get top N districts by risk."""
        all_rankings = await self.get_all_rankings()
        return TopDistricts(top_n=n, districts=all_rankings[:n])

    async def get_district(self, district: str) -> DistrictPrediction:
        """Get a specific district's prediction."""
        cache_key = f"risk:district:{district.lower()}"
        cached = await self.cache.get(cache_key)
        if cached:
            return DistrictPrediction(**cached)

        row_dict = self.ml_loader.get_district_prediction(district)
        if not row_dict:
            raise NotFoundException(
                f"District '{district}' not found",
                details={"district": district},
            )

        prediction = DistrictPrediction(
            district=str(row_dict.get("district", district)),
            state=row_dict.get("state"),
            risk_score=float(row_dict.get("risk_score", 0)),
            risk_rank=int(row_dict.get("risk_rank", 0)),
            confidence=float(row_dict.get("confidence", 0)),
            predicted_crime_count=(
                int(row_dict["predicted_crime_count"])
                if "predicted_crime_count" in row_dict
                and row_dict["predicted_crime_count"] is not None
                else None
            ),
            additional_metrics={
                k: v for k, v in row_dict.items()
                if k not in ("district", "state", "risk_score", "risk_rank",
                             "confidence", "predicted_crime_count")
            },
        )
        await self.cache.set(cache_key, prediction.model_dump(), ttl=300)
        return prediction

    def _row_to_ranking(self, row) -> RiskRanking:
        return RiskRanking(
            district=str(row.get("district", "")),
            state=row.get("state"),
            risk_score=float(row.get("risk_score", 0)),
            risk_rank=int(row.get("risk_rank", 0)),
            confidence=float(row.get("confidence", 0)),
            predicted_crime_count=(
                int(row["predicted_crime_count"])
                if "predicted_crime_count" in row
                and row["predicted_crime_count"] is not None
                else None
            ),
        )
