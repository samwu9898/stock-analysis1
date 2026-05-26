# -*- coding: utf-8 -*-

import json
import shutil
from pathlib import Path

import pytest

from src.fundamental_skill.data_providers.comparison_artifacts import (
    BASE_ARTIFACT_NAMES,
    EXPLAINABILITY_ARTIFACT_NAMES,
    P1_ARTIFACT_NAMES,
    ComparisonArtifactError,
    plan_comparison_artifacts,
    write_json_artifact,
    write_text_artifact,
)


def test_plan_comparison_artifacts_uses_isolated_timestamp_directory(tmp_path):
    output_dir = tmp_path / "output" / "provider_comparison"

    plan = plan_comparison_artifacts(["600406"], output_dir=output_dir, timestamp="20260526T120000")
    code_plan = plan.codes["600406"]

    assert plan.timestamp_dir == output_dir / "20260526T120000"
    assert code_plan.code_dir == output_dir / "20260526T120000" / "600406"
    assert set(code_plan.paths) == set(BASE_ARTIFACT_NAMES)
    assert code_plan.paths["akshare_raw.json"].name == "akshare_raw.json"
    assert code_plan.paths["tushare_evidence_pack.json"].parent == code_plan.code_dir


def test_plan_comparison_artifacts_can_plan_p1_paths_without_running_p1(tmp_path):
    plan = plan_comparison_artifacts(
        ["002050"],
        output_dir=tmp_path / "output" / "provider_comparison",
        timestamp="phase4",
        include_p1=True,
    )

    assert plan.include_p1 is True
    for name in P1_ARTIFACT_NAMES:
        assert name in plan.codes["002050"].paths


def test_plan_comparison_artifacts_can_plan_explainability_path_only_when_enabled(tmp_path):
    default_plan = plan_comparison_artifacts(
        ["002837"],
        output_dir=tmp_path / "output" / "provider_comparison",
        timestamp="default",
    )
    explainability_plan = plan_comparison_artifacts(
        ["002837"],
        output_dir=tmp_path / "output" / "provider_comparison",
        timestamp="with_explainability",
        include_explainability=True,
    )

    assert "score_confidence_explainability.json" not in default_plan.codes["002837"].paths
    for name in EXPLAINABILITY_ARTIFACT_NAMES:
        assert name in explainability_plan.codes["002837"].paths


def test_artifact_writer_writes_only_inside_comparison_dir_and_can_delete_timestamp(tmp_path):
    plan = plan_comparison_artifacts(
        ["002371"],
        output_dir=tmp_path / "output" / "provider_comparison",
        timestamp="delete_me",
    )

    json_path = write_json_artifact(plan, "002371", "diff_report.json", {"ok": True})
    md_path = write_text_artifact(plan, "002371", "diff_report.md", "# report\n")

    assert json.loads(json_path.read_text(encoding="utf-8")) == {"ok": True}
    assert md_path.read_text(encoding="utf-8") == "# report\n"
    assert plan.timestamp_dir.exists()

    shutil.rmtree(plan.timestamp_dir)

    assert not plan.timestamp_dir.exists()
    assert not (tmp_path / "output" / "raw_002371.json").exists()
    assert not (tmp_path / "output" / "fundamental_002371.json").exists()
    assert not (tmp_path / "output" / "evidence_pack_002371.json").exists()
    assert not (tmp_path / "output" / "reports").exists()


def test_explainability_artifact_name_allowlist_is_explicit(tmp_path):
    default_plan = plan_comparison_artifacts(
        ["000426"],
        output_dir=tmp_path / "output" / "provider_comparison",
        timestamp="default",
    )
    explainability_plan = plan_comparison_artifacts(
        ["000426"],
        output_dir=tmp_path / "output" / "provider_comparison",
        timestamp="with_explainability",
        include_explainability=True,
    )

    with pytest.raises(ComparisonArtifactError, match="not in artifact plan"):
        write_json_artifact(default_plan, "000426", "score_confidence_explainability.json", {})

    path = write_json_artifact(
        explainability_plan,
        "000426",
        "score_confidence_explainability.json",
        {"automatic_acceptance": False},
    )
    assert path.name == "score_confidence_explainability.json"
    assert path.parent == explainability_plan.codes["000426"].code_dir


def test_writer_rejects_paths_outside_timestamp_directory(tmp_path):
    plan = plan_comparison_artifacts(
        ["000426"],
        output_dir=tmp_path / "output" / "provider_comparison",
        timestamp="phase4",
    )
    plan.codes["000426"].paths["diff_report.json"] = tmp_path / "output" / "raw_000426.json"

    with pytest.raises(ComparisonArtifactError, match="escapes timestamp directory"):
        write_json_artifact(plan, "000426", "diff_report.json", {})


def test_comparison_artifacts_are_under_ignored_output_tree():
    gitignore = Path(".gitignore").read_text(encoding="utf-8")

    assert "output/" in gitignore
