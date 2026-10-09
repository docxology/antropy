# Copyright (c) 2026 Daniel Ari Friedman
# Consumed constructor subset verified against RenderingConfig at the pinned Git revision.
class RenderingConfig:
    def __init__(
        self,
        manuscript_dir: str = "manuscript",
        figures_dir: str = "output/figures",
        output_dir: str = "output",
        *,
        pdf_dir: str = "output/pdf",
        latex_compiler: str = "xelatex",
    ) -> None: ...
