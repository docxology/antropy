# Copyright (c) 2026 Daniel Ari Friedman
# Consumed interfaces verified against PDFRenderer at the pinned Git revision.
from pathlib import Path

from infrastructure.rendering.config import RenderingConfig

class PDFRenderer:
    def __init__(self, config: RenderingConfig) -> None: ...
    def render_combined(
        self,
        source_files: list[Path],
        manuscript_dir: Path,
        project_name: str = "project",
    ) -> Path: ...
