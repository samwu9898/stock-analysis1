# -*- coding: utf-8 -*-
"""Offline fundamental research report builders."""

from .research_report_v1 import (
    ALLOWED_EVIDENCE_LABELS,
    REPORT_TYPE,
    ResearchReportArtifactBoundaryError,
    ResearchReportBuildError,
    ResearchReportSecretError,
    build_research_report_v1,
    write_research_report_v1,
)
from .research_report_v1_presentation import (
    MARKDOWN_OUTPUT_FILENAME,
    render_research_report_v1_markdown,
    write_research_report_v1_markdown,
)

__all__ = [
    "ALLOWED_EVIDENCE_LABELS",
    "MARKDOWN_OUTPUT_FILENAME",
    "REPORT_TYPE",
    "ResearchReportArtifactBoundaryError",
    "ResearchReportBuildError",
    "ResearchReportSecretError",
    "build_research_report_v1",
    "render_research_report_v1_markdown",
    "write_research_report_v1",
    "write_research_report_v1_markdown",
]
