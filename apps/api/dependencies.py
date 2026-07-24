"""API dependencies for dependency injection."""

from __future__ import annotations

from .main import get_state


def get_project_service():
    return get_state().project_service


def get_dataset_service():
    return get_state().dataset_service


def get_factor_service():
    return get_state().factor_service


def get_run_service():
    return get_state().run_service


def get_report_service():
    return get_state().report_service


def get_settings_service():
    return get_state().settings_service


def get_job_manager():
    return get_state().job_manager


def get_workspace():
    return get_state().workspace
