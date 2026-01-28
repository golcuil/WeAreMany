from pathlib import Path


def test_restore_fixture_schema_only():
    fixture = Path("fixtures/sanitized_restore_fixture.sql")
    contents = fixture.read_text(encoding="utf-8")
    lines = [line.strip().lower() for line in contents.splitlines() if line.strip()]
    create_tables = [
        line for line in lines if line.startswith("create table") or line.startswith("create table if not exists")
    ]
    assert any("schema_migrations" in line for line in create_tables)
    assert all("schema_migrations" in line for line in create_tables)
    assert not any(line.startswith("insert into") for line in lines)
