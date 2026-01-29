from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from tools import docs_consistency_check  # noqa: E402


def test_docs_check_ok(monkeypatch, capsys, tmp_path):
    backlink_block = "\n".join(
        [
            "Back to [OPERATOR_GOLDEN_PATH](OPERATOR_GOLDEN_PATH.md)",
            "Back to [RELEASE_READINESS](RELEASE_READINESS.md)",
            "",
        ]
    )
    runbook = tmp_path / "operator_runbook.md"
    golden_path = tmp_path / "OPERATOR_GOLDEN_PATH.md"
    release_readiness = tmp_path / "RELEASE_READINESS.md"
    operator_rehearsal = tmp_path / "operator_rehearsal.md"
    staged_rollout = tmp_path / "staged_rollout.md"
    regression_baseline = tmp_path / "regression_baseline.md"
    logging_policy = tmp_path / "logging_policy.md"
    disaster_recovery = tmp_path / "disaster_recovery.md"
    launch_checklist = tmp_path / "launch_checklist.md"

    runbook.write_text(backlink_block + "Runbook")
    operator_rehearsal.write_text(backlink_block + "Operator rehearsal")
    staged_rollout.write_text(backlink_block + "Staged rollout")
    regression_baseline.write_text(backlink_block + "Regression baseline")
    logging_policy.write_text(backlink_block + "Logging policy")
    disaster_recovery.write_text(backlink_block + "DR")
    launch_checklist.write_text(backlink_block + "Launch checklist")

    golden_path.write_text(
        "\n".join(
            [
                "docs/RELEASE_READINESS.md",
                "docs/operator_rehearsal.md",
                "docs/staged_rollout.md",
                "docs/regression_baseline.md",
                "docs/logging_policy.md",
                "docs/disaster_recovery.md",
                "docs/launch_checklist.md",
            ]
        )
    )
    release_readiness.write_text(
        "\n".join(
            [
                "docs/OPERATOR_GOLDEN_PATH.md",
                "docs/launch_checklist.md",
                "docs/staged_rollout.md",
                "docs/disaster_recovery.md",
                "docs/logging_policy.md",
            ]
        )
    )
    monkeypatch.setattr(docs_consistency_check, "RUNBOOK_PATH", str(runbook))
    monkeypatch.setattr(
        docs_consistency_check, "STAGED_ROLLOUT_PATH", str(staged_rollout)
    )
    monkeypatch.setattr(
        docs_consistency_check, "REGRESSION_BASELINE_PATH", str(regression_baseline)
    )
    monkeypatch.setattr(
        docs_consistency_check, "LOGGING_POLICY_PATH", str(logging_policy)
    )
    monkeypatch.setattr(
        docs_consistency_check, "GOLDEN_PATH", str(golden_path)
    )
    monkeypatch.setattr(
        docs_consistency_check, "RELEASE_READINESS_PATH", str(release_readiness)
    )
    exit_code = docs_consistency_check.main([])
    assert exit_code == 0
    output = capsys.readouterr().out.strip()
    assert output == "docs_check status=ok"


def test_docs_check_missing_token(monkeypatch, capsys, tmp_path):
    backlink_block = "\n".join(
        [
            "Back to [OPERATOR_GOLDEN_PATH](OPERATOR_GOLDEN_PATH.md)",
            "Back to [RELEASE_READINESS](RELEASE_READINESS.md)",
            "",
        ]
    )
    runbook = tmp_path / "operator_runbook.md"
    golden_path = tmp_path / "OPERATOR_GOLDEN_PATH.md"
    release_readiness = tmp_path / "RELEASE_READINESS.md"
    runbook.write_text(backlink_block + "Runbook")
    golden_path.write_text("docs/RELEASE_READINESS.md")
    release_readiness.write_text("docs/OPERATOR_GOLDEN_PATH.md")
    monkeypatch.setattr(docs_consistency_check, "RUNBOOK_PATH", str(runbook))
    monkeypatch.setattr(
        docs_consistency_check, "GOLDEN_PATH", str(golden_path)
    )
    monkeypatch.setattr(
        docs_consistency_check, "RELEASE_READINESS_PATH", str(release_readiness)
    )
    exit_code = docs_consistency_check.main([])
    assert exit_code == 1
    output = capsys.readouterr().out.strip()
    assert output == "docs_check status=fail reason=missing_golden_path_link"


def test_docs_check_suspicious_dsn(monkeypatch, capsys, tmp_path):
    backlink_block = "\n".join(
        [
            "Back to [OPERATOR_GOLDEN_PATH](OPERATOR_GOLDEN_PATH.md)",
            "Back to [RELEASE_READINESS](RELEASE_READINESS.md)",
            "",
        ]
    )
    runbook = tmp_path / "operator_runbook.md"
    golden_path = tmp_path / "OPERATOR_GOLDEN_PATH.md"
    release_readiness = tmp_path / "RELEASE_READINESS.md"
    operator_rehearsal = tmp_path / "operator_rehearsal.md"
    staged_rollout = tmp_path / "staged_rollout.md"
    regression_baseline = tmp_path / "regression_baseline.md"
    logging_policy = tmp_path / "logging_policy.md"
    disaster_recovery = tmp_path / "disaster_recovery.md"
    launch_checklist = tmp_path / "launch_checklist.md"

    runbook.write_text(backlink_block + "postgres://user:pass@localhost:5432/db")
    operator_rehearsal.write_text(backlink_block + "Operator rehearsal")
    staged_rollout.write_text(backlink_block + "Staged rollout")
    regression_baseline.write_text(backlink_block + "Regression baseline")
    logging_policy.write_text(backlink_block + "Logging policy")
    disaster_recovery.write_text(backlink_block + "DR")
    launch_checklist.write_text(backlink_block + "Launch checklist")
    golden_path.write_text(
        "\n".join(
            [
                "docs/RELEASE_READINESS.md",
                "docs/operator_rehearsal.md",
                "docs/staged_rollout.md",
                "docs/regression_baseline.md",
                "docs/logging_policy.md",
                "docs/disaster_recovery.md",
                "docs/launch_checklist.md",
            ]
        )
    )
    release_readiness.write_text(
        "\n".join(
            [
                "docs/OPERATOR_GOLDEN_PATH.md",
                "docs/launch_checklist.md",
                "docs/staged_rollout.md",
                "docs/disaster_recovery.md",
                "docs/logging_policy.md",
            ]
        )
    )
    monkeypatch.setattr(docs_consistency_check, "RUNBOOK_PATH", str(runbook))
    monkeypatch.setattr(
        docs_consistency_check, "STAGED_ROLLOUT_PATH", str(staged_rollout)
    )
    monkeypatch.setattr(
        docs_consistency_check, "REGRESSION_BASELINE_PATH", str(regression_baseline)
    )
    monkeypatch.setattr(
        docs_consistency_check, "LOGGING_POLICY_PATH", str(logging_policy)
    )
    monkeypatch.setattr(
        docs_consistency_check, "GOLDEN_PATH", str(golden_path)
    )
    monkeypatch.setattr(
        docs_consistency_check, "RELEASE_READINESS_PATH", str(release_readiness)
    )
    exit_code = docs_consistency_check.main([])
    assert exit_code == 1
    output = capsys.readouterr().out.strip()
    assert output == "docs_check status=fail reason=suspicious_dsn"
