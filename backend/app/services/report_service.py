"""
====================================================
Report Service
====================================================
Generates downloadable reports (CSV, PDF, GeoJSON, JSON).
====================================================
"""
from __future__ import annotations

import csv
import io
import json
import os
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional
from uuid import UUID

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import NotFoundException, ReportGenerationException
from app.database.models.saved_report import (
    ReportFormat,
    ReportStatus,
    ReportType,
    SavedReport,
)
from app.repositories.report_repository import ReportRepository
from app.schemas.report import ReportCreate
from app.services.ml_loader import MLArtifactLoader

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import (
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False
    logger.warning("reportlab not installed — PDF reports disabled")


class ReportService:
    """Service for generating and serving reports."""

    def __init__(
        self,
        ml_loader: MLArtifactLoader,
        db: AsyncSession,
        storage_dir: Optional[str] = None,
    ) -> None:
        self.ml_loader = ml_loader
        self.db = db
        self.storage_dir = Path(storage_dir or "./reports_storage")
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    async def create_report(
        self,
        report_data: ReportCreate,
        user_id: UUID,
    ) -> SavedReport:
        """Create a new report and queue it for generation."""
        repo = ReportRepository(self.db)
        report = SavedReport(
            id=uuid.uuid4(),
            user_id=user_id,
            title=report_data.title,
            description=report_data.description,
            report_type=report_data.report_type,
            format=report_data.format,
            status=ReportStatus.PENDING,
            filters=report_data.filters or {},
            parameters=report_data.parameters or {},
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        return await repo.create(report)

    async def generate_report(self, report_id: UUID) -> SavedReport:
        """Generate a report and save to disk."""
        repo = ReportRepository(self.db)
        report = await repo.get_by_id(report_id)
        if not report:
            raise NotFoundException(f"Report {report_id} not found")

        try:
            report.status = ReportStatus.PROCESSING
            report.generation_started_at = datetime.now(timezone.utc)
            await repo.update(report)

            # Generate payload based on type
            payload = self._build_payload(report.report_type, report.filters)

            # Render to file format
            file_path = self._render_file(report, payload)
            file_size = os.path.getsize(file_path)

            # Update report
            report.status = ReportStatus.COMPLETED
            report.file_path = str(file_path)
            report.file_size = file_size
            report.generation_completed_at = datetime.now(timezone.utc)

            await repo.update(report)
            logger.info(f"✅ Report generated: {report.id} ({file_size} bytes)")
            return report

        except Exception as e:
            logger.error(f"❌ Report generation failed: {e}")
            report.status = ReportStatus.FAILED
            report.error_message = str(e)
            report.retry_count += 1
            await repo.update(report)
            raise ReportGenerationException(f"Report generation failed: {e}")

    def _build_payload(self, report_type: ReportType, filters: dict | None) -> dict:
        """Build the data payload for a report."""
        raw = self.ml_loader.get_analytics_report()

        if report_type == ReportType.DASHBOARD_SUMMARY:
            metrics = self.ml_loader.get_dashboard_metrics()
            rankings = raw.get("risk_rankings", [])[:20]
            return {"metrics": metrics, "top_districts": rankings}

        elif report_type == ReportType.RISK_RANKING:
            try:
                rows = [{k: v for k, v in row.items()}
                        for _, row in self.ml_loader.get_risk_rankings().iterrows()]
            except Exception:
                rows = raw.get("risk_rankings", [])
            return {"rankings": rows}

        elif report_type == ReportType.HOTSPOT_ANALYSIS:
            try:
                rows = [{k: v for k, v in row.items()}
                        for _, row in self.ml_loader.get_hotspot_rankings().iterrows()]
            except Exception:
                rows = raw.get("risk_rankings", [])
            return {"rankings": rows, "geojson": self.ml_loader.get_hotspots_geojson()}

        elif report_type == ReportType.ANALYTICS_REPORT:
            return raw

        else:
            return {"generated_at": time.time()}

    def _render_file(self, report: SavedReport, payload: dict) -> Path:
        """Render payload to file in the requested format."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        safe_title = "".join(c for c in report.title if c.isalnum() or c in "._-")[:50]
        base_name = f"{safe_title}_{timestamp}_{str(report.id)[:8]}"
        file_path = self.storage_dir / f"{base_name}.{report.format.value}"

        if report.format == ReportFormat.CSV:
            self._write_csv(file_path, payload)
        elif report.format == ReportFormat.JSON:
            self._write_json(file_path, payload)
        elif report.format == ReportFormat.GEOJSON:
            self._write_geojson(file_path, payload)
        elif report.format == ReportFormat.PDF:
            if not HAS_REPORTLAB:
                raise ReportGenerationException("PDF reports not available")
            self._write_pdf(file_path, payload, report)

        return file_path

    def _write_csv(self, path: Path, payload: dict) -> None:
        # Use the first list-of-dicts we find
        rows = None
        for key in ("rankings", "top_districts", "categories"):
            if key in payload and isinstance(payload[key], list):
                rows = payload[key]
                break
        if rows is None:
            rows = [payload]
        if not rows:
            path.write_text("")
            return
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

    def _write_json(self, path: Path, payload: dict) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, default=str)

    def _write_geojson(self, path: Path, payload: dict) -> None:
        geojson = payload.get("geojson", {"type": "FeatureCollection", "features": []})
        with open(path, "w", encoding="utf-8") as f:
            json.dump(geojson, f, indent=2, default=str)

    def _write_pdf(self, path: Path, payload: dict, report: SavedReport) -> None:
        if not HAS_REPORTLAB:
            raise ReportGenerationException("reportlab not installed")
        doc = SimpleDocTemplate(str(path), pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []

        elements.append(Paragraph(f"<b>{report.title}</b>", styles["Title"]))
        elements.append(Spacer(1, 12))
        elements.append(Paragraph(
            f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
            styles["Normal"]
        ))
        elements.append(Spacer(1, 12))

        # Add metrics if present
        if "metrics" in payload:
            m = payload["metrics"]
            data = [["Metric", "Value"]]
            for k, v in m.items():
                data.append([k.replace("_", " ").title(), str(v)])
            t = Table(data)
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]))
            elements.append(t)
            elements.append(Spacer(1, 12))

        # Add rankings if present
        for key in ("rankings", "top_districts"):
            if key in payload and payload[key]:
                rows = payload[key][:50]
                data = [list(rows[0].keys())]
                for r in rows:
                    data.append([str(r.get(c, "")) for c in rows[0].keys()])
                t = Table(data)
                t.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("FONTSIZE", (0, 0), (-1, -1), 7),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                ]))
                elements.append(t)
                break

        doc.build(elements)
