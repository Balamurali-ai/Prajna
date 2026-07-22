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
        # Try predictions.csv first
        try:
            df = self.ml_loader.get_risk_rankings()
            result = [self._row_to_ranking(row) for _, row in df.iterrows()]
            if result:
                return result
        except Exception:
            pass

        # Fallback: derive from analytics_report risk_rankings
        try:
            raw = self.ml_loader.get_analytics_report()
            rankings = raw.get("risk_rankings", [])
            return [
                RiskRanking(
                    district=r["district"],
                    risk_score=float(r["score"]),
                    risk_rank=int(r["rank"]),
                )
                for r in rankings
            ]
        except Exception as e:
            logger.warning(f"Could not build risk rankings: {e}")
            return []

    async def get_top_n(self, n: int = 10) -> TopDistricts:
        """Get top N districts by risk."""
        all_rankings = await self.get_all_rankings()
        return TopDistricts(top_n=n, districts=all_rankings[:n])

    async def get_district(self, district: str) -> DistrictPrediction:
        """Get a specific district's prediction."""
        # Try predictions.csv first
        try:
            row_dict = self.ml_loader.get_district_prediction(district)
            if row_dict:
                return DistrictPrediction(
                    district=str(row_dict.get("district", district)),
                    state=row_dict.get("state"),
                    risk_score=float(row_dict.get("risk_score", 0)),
                    risk_rank=int(row_dict.get("risk_rank", 0)),
                    confidence=float(row_dict.get("confidence", 0)),
                    predicted_crime_count=(
                        int(row_dict["predicted_crime_count"])
                        if row_dict.get("predicted_crime_count") is not None else None
                    ),
                )
        except Exception:
            pass

        # Fallback: analytics_report risk_rankings
        try:
            raw = self.ml_loader.get_analytics_report()
            rankings = raw.get("risk_rankings", [])
            match = next((r for r in rankings if r["district"].lower() == district.lower()), None)
            if match:
                return DistrictPrediction(
                    district=match["district"],
                    risk_score=float(match["score"]),
                    risk_rank=int(match["rank"]),
                )
        except Exception:
            pass

        raise NotFoundException(f"District '{district}' not found", details={"district": district})

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
