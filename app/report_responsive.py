"""Backward-compatible entry point for post-processing generated reports.

The responsive layout and the light theme now live in ``app/static/report.css``
(see :mod:`app.report_theme`). This module no longer injects CSS; it only
installs and links the shared stylesheet.
"""
from .report_theme import apply_report_theme


def make_folder_responsive(folder):
    return apply_report_theme(folder)
