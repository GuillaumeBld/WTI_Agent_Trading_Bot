"""Generate human-readable risk reports."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict


@dataclass
class RiskReport:
    generated_at: datetime
    metrics: Dict[str, float]

    def render_markdown(self) -> str:
        lines = ["# Daily Risk Report", f"Generated at: {self.generated_at.isoformat()}", ""]
        for key, value in self.metrics.items():
            lines.append(f"- **{key.replace('_', ' ').title()}**: {value:.4f}")
        return "\n".join(lines)

    def save(self, path: Path) -> Path:
        path.write_text(self.render_markdown())
        return path


__all__ = ["RiskReport"]
