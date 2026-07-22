"""
====================================================
ML Artifact Loader (compat shim)
====================================================
Re-exports MLArtifactLoader from the canonical home
(``app.services.ml_loader``) so legacy imports like
``from ml.ml_loader import MLArtifactLoader`` continue
to work alongside the new ``from app.services.ml_loader
import MLArtifactLoader``.

There is intentionally no implementation here — the
loader lives in ``app.services.ml_loader``.
====================================================
"""
from app.services.ml_loader import MLArtifactLoader  # noqa: F401

__all__ = ["MLArtifactLoader"]
