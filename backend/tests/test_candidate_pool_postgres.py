import os
from datetime import datetime, timezone

import pytest

try:
    import psycopg
except Exception:  # pragma: no cover
    psycopg = None

from app.repository import PostgresRepository


POSTGRES_DSN = os.getenv("POSTGRES_DSN_TEST")


@pytest.mark.skipif(POSTGRES_DSN is None or psycopg is None, reason="POSTGRES_DSN_TEST not set")
def test_postgres_candidate_pool_sampling_respects_filters():
    repo = PostgresRepository(POSTGRES_DSN)
    now_bucket = datetime.now(timezone.utc)
    principals = [
        ("p1", "low", ["loss"], now_bucket),
        ("p2", "low", ["uncertainty"], now_bucket),
        ("p3", "high", ["loss"], now_bucket),
    ]

    with psycopg.connect(POSTGRES_DSN) as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM eligible_principals WHERE principal_id IN ('p1','p2','p3')")
        for principal_id, intensity, themes, bucket in principals:
            cur.execute(
                """
                INSERT INTO eligible_principals
                (principal_id, intensity_bucket, theme_tags, last_active_bucket, updated_at)
                VALUES (%s, %s, %s, %s, now())
                """,
                (principal_id, intensity, themes, bucket),
            )

    try:
        candidates = repo.get_eligible_candidates("sender", "low", ["loss"], limit=10)
        ids = {candidate.candidate_id for candidate in candidates}
        assert "p1" in ids
        assert "p2" not in ids
        assert "p3" not in ids
    finally:
        with psycopg.connect(POSTGRES_DSN) as conn, conn.cursor() as cur:
            cur.execute("DELETE FROM eligible_principals WHERE principal_id IN ('p1','p2','p3')")
