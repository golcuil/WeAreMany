from app.repository import PostgresRepository


def test_postgres_repository_has_required_methods():
    assert hasattr(PostgresRepository, "get_eligible_candidates")
    assert hasattr(PostgresRepository, "record_security_event")
