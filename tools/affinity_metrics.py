from collections import Counter
import os
from typing import Dict, Tuple

try:
    import psycopg
except Exception:  # pragma: no cover
    psycopg = None


def _bucket(score: float) -> str:
    if score <= 0:
        return "0"
    if score <= 1:
        return "0-1"
    if score <= 3:
        return "1-3"
    if score <= 10:
        return "3-10"
    return "10+"


def _fetch_metrics(dsn: str) -> Tuple[int, Dict[str, float], Dict[str, int]]:
    with psycopg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("SELECT sender_device_id, theme_id, score FROM affinity_scores")
        rows = cur.fetchall()
    actors = {row[0] for row in rows}
    aggregate: Dict[str, float] = {}
    buckets: Counter[str] = Counter()
    for _, theme_id, score in rows:
        aggregate[theme_id] = aggregate.get(theme_id, 0.0) + float(score)
        buckets[_bucket(float(score))] += 1
    return len(actors), aggregate, dict(buckets)


def main() -> int:
    dsn = os.getenv("POSTGRES_DSN")
    if not dsn or psycopg is None:
        print("affinity_metrics: POSTGRES_DSN not set or psycopg missing; skipping.")
        return 0
    actor_count, aggregate, buckets = _fetch_metrics(dsn)
    top_themes = sorted(aggregate.items(), key=lambda item: item[1], reverse=True)[:5]
    print(f"actors_with_affinity={actor_count}")
    print("top_themes=" + ", ".join(f"{theme}:{score:.2f}" for theme, score in top_themes))
    print("buckets=" + ", ".join(f"{bucket}:{count}" for bucket, count in sorted(buckets.items())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
