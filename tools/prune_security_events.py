from datetime import datetime, timezone

from app.repository import get_repository


def main() -> None:
    repo = get_repository()
    now = datetime.now(timezone.utc)
    deleted = repo.prune_security_events(now)
    print(f"security_events pruned={deleted}")


if __name__ == "__main__":
    main()
