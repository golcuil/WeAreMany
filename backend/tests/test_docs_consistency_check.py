from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from tools import docs_consistency_check  # noqa: E402


def test_docs_check_ok(monkeypatch, capsys, tmp_path):
    runbook = tmp_path / "operator_runbook.md"
    launch = tmp_path / "launch_checklist.md"
    go_no_go = tmp_path / "go_no_go_template.md"
    v1_complete = tmp_path / "V1_COMPLETE.md"
    staged_rollout = tmp_path / "staged_rollout.md"
    regression_baseline = tmp_path / "regression_baseline.md"
    canary_drill = tmp_path / "canary_drill.md"
    logging_policy = tmp_path / "logging_policy.md"
    workflow = tmp_path / "generate_regression_baseline.yml"
    runbook.write_text(
        "\n".join(
            [
                "status=insufficient_data",
                "reason=missing_env",
                "db_bootstrap_dry_run",
                "db_verify status=not_configured",
                "docs/launch_checklist.md",
                "docs/V1_COMPLETE.md",
                "docs/staged_rollout.md",
                "docs/regression_baseline.md",
                "docs/canary_drill.md",
                "docs/logging_policy.md",
            ]
        )
    )
    launch.write_text(
        "\n".join(
            [
                "pre_release_gate",
                "prod_rehearsal",
                "restore_dry_run",
                "secret_echo_guard",
            ]
        )
    )
    go_no_go.write_text("Go/No-Go Template")
    v1_complete.write_text("V1 Complete")
    staged_rollout.write_text("Staged Rollout")
    regression_baseline.write_text("Regression Baseline")
    canary_drill.write_text("Canary Drill")
    logging_policy.write_text("Logging Policy")
    workflow.write_text("retention-days: 30")
    monkeypatch.setattr(docs_consistency_check, "RUNBOOK_PATH", str(runbook))
    monkeypatch.setattr(
        docs_consistency_check, "LAUNCH_CHECKLIST_PATH", str(launch)
    )
    monkeypatch.setattr(
        docs_consistency_check, "GO_NO_GO_TEMPLATE_PATH", str(go_no_go)
    )
    monkeypatch.setattr(docs_consistency_check, "V1_COMPLETE_PATH", str(v1_complete))
    monkeypatch.setattr(
        docs_consistency_check, "STAGED_ROLLOUT_PATH", str(staged_rollout)
    )
    monkeypatch.setattr(
        docs_consistency_check, "REGRESSION_BASELINE_PATH", str(regression_baseline)
    )
    monkeypatch.setattr(
        docs_consistency_check, "CANARY_DRILL_PATH", str(canary_drill)
    )
    monkeypatch.setattr(
        docs_consistency_check, "LOGGING_POLICY_PATH", str(logging_policy)
    )
    monkeypatch.setattr(
        docs_consistency_check, "_load_ci_workflow", lambda: workflow.read_text()
    )
    monkeypatch.setattr(
        docs_consistency_check,
        "MODULE_REFERENCES",
        ["tools.db_bootstrap"],
    )
    exit_code = docs_consistency_check.main([])
    assert exit_code == 0
    output = capsys.readouterr().out.strip()
    assert output == "docs_check status=ok"


def test_docs_check_missing_token(monkeypatch, capsys, tmp_path):
    runbook = tmp_path / "operator_runbook.md"
    launch = tmp_path / "launch_checklist.md"
    go_no_go = tmp_path / "go_no_go_template.md"
    v1_complete = tmp_path / "V1_COMPLETE.md"
    staged_rollout = tmp_path / "staged_rollout.md"
    regression_baseline = tmp_path / "regression_baseline.md"
    canary_drill = tmp_path / "canary_drill.md"
    logging_policy = tmp_path / "logging_policy.md"
    workflow = tmp_path / "generate_regression_baseline.yml"
    runbook.write_text("status=insufficient_data")
    launch.write_text(
        "\n".join(
            [
                "pre_release_gate",
                "prod_rehearsal",
                "restore_dry_run",
                "secret_echo_guard",
            ]
        )
    )
    go_no_go.write_text("Go/No-Go Template")
    v1_complete.write_text("V1 Complete")
    staged_rollout.write_text("Staged Rollout")
    regression_baseline.write_text("Regression Baseline")
    canary_drill.write_text("Canary Drill")
    logging_policy.write_text("Logging Policy")
    workflow.write_text("retention-days: 30")
    monkeypatch.setattr(docs_consistency_check, "RUNBOOK_PATH", str(runbook))
    monkeypatch.setattr(
        docs_consistency_check, "LAUNCH_CHECKLIST_PATH", str(launch)
    )
    monkeypatch.setattr(
        docs_consistency_check, "GO_NO_GO_TEMPLATE_PATH", str(go_no_go)
    )
    monkeypatch.setattr(docs_consistency_check, "V1_COMPLETE_PATH", str(v1_complete))
    monkeypatch.setattr(
        docs_consistency_check, "STAGED_ROLLOUT_PATH", str(staged_rollout)
    )
    monkeypatch.setattr(
        docs_consistency_check, "REGRESSION_BASELINE_PATH", str(regression_baseline)
    )
    monkeypatch.setattr(
        docs_consistency_check, "CANARY_DRILL_PATH", str(canary_drill)
    )
    monkeypatch.setattr(
        docs_consistency_check, "LOGGING_POLICY_PATH", str(logging_policy)
    )
    monkeypatch.setattr(
        docs_consistency_check, "_load_ci_workflow", lambda: workflow.read_text()
    )
    monkeypatch.setattr(
        docs_consistency_check,
        "MODULE_REFERENCES",
        ["tools.db_bootstrap"],
    )
    exit_code = docs_consistency_check.main([])
    assert exit_code == 1
    output = capsys.readouterr().out.strip()
    assert output == "docs_check status=fail reason=missing_token"


def test_docs_check_suspicious_dsn(monkeypatch, capsys, tmp_path):
    runbook = tmp_path / "operator_runbook.md"
    launch = tmp_path / "launch_checklist.md"
    go_no_go = tmp_path / "go_no_go_template.md"
    v1_complete = tmp_path / "V1_COMPLETE.md"
    staged_rollout = tmp_path / "staged_rollout.md"
    regression_baseline = tmp_path / "regression_baseline.md"
    canary_drill = tmp_path / "canary_drill.md"
    logging_policy = tmp_path / "logging_policy.md"
    workflow = tmp_path / "generate_regression_baseline.yml"
    runbook.write_text(
        "\n".join(
            [
                "status=insufficient_data",
                "reason=missing_env",
                "db_bootstrap_dry_run",
                "db_verify status=not_configured",
                "postgres://user:pass@localhost:5432/db",
                "docs/launch_checklist.md",
                "docs/V1_COMPLETE.md",
                "docs/staged_rollout.md",
                "docs/regression_baseline.md",
                "docs/canary_drill.md",
                "docs/logging_policy.md",
            ]
        )
    )
    launch.write_text(
        "\n".join(
            [
                "pre_release_gate",
                "prod_rehearsal",
                "restore_dry_run",
                "secret_echo_guard",
            ]
        )
    )
    go_no_go.write_text("Go/No-Go Template")
    v1_complete.write_text("V1 Complete")
    staged_rollout.write_text("Staged Rollout")
    regression_baseline.write_text("Regression Baseline")
    canary_drill.write_text("Canary Drill")
    logging_policy.write_text("Logging Policy")
    workflow.write_text("retention-days: 30")
    monkeypatch.setattr(docs_consistency_check, "RUNBOOK_PATH", str(runbook))
    monkeypatch.setattr(
        docs_consistency_check, "LAUNCH_CHECKLIST_PATH", str(launch)
    )
    monkeypatch.setattr(
        docs_consistency_check, "GO_NO_GO_TEMPLATE_PATH", str(go_no_go)
    )
    monkeypatch.setattr(docs_consistency_check, "V1_COMPLETE_PATH", str(v1_complete))
    monkeypatch.setattr(
        docs_consistency_check, "STAGED_ROLLOUT_PATH", str(staged_rollout)
    )
    monkeypatch.setattr(
        docs_consistency_check, "REGRESSION_BASELINE_PATH", str(regression_baseline)
    )
    monkeypatch.setattr(
        docs_consistency_check, "CANARY_DRILL_PATH", str(canary_drill)
    )
    monkeypatch.setattr(
        docs_consistency_check, "LOGGING_POLICY_PATH", str(logging_policy)
    )
    monkeypatch.setattr(
        docs_consistency_check, "_load_ci_workflow", lambda: workflow.read_text()
    )
    monkeypatch.setattr(
        docs_consistency_check,
        "MODULE_REFERENCES",
        ["tools.db_bootstrap"],
    )
    exit_code = docs_consistency_check.main([])
    assert exit_code == 1
    output = capsys.readouterr().out.strip()
    assert output == "docs_check status=fail reason=suspicious_dsn"
