from pathlib import Path


def test_restore_fixture_schema_only():
    fixture = Path("fixtures/sanitized_restore_fixture.sql")
    contents = fixture.read_text(encoding="utf-8")
    assert "schema_migrations" in contents
    assert "CREATE TABLE" in contents
    assert "restore_fixture_check" not in contents
    assert "INSERT INTO" not in contents
