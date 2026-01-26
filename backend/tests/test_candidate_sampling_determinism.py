from app.repository import Candidate, InMemoryRepository, _candidate_sort_key


def test_in_memory_candidate_sampling_deterministic(monkeypatch):
    repo = InMemoryRepository()
    repo.candidate_pool = [
        Candidate(candidate_id="c1", intensity="low", themes=["calm"]),
        Candidate(candidate_id="c2", intensity="low", themes=["calm"]),
        Candidate(candidate_id="c3", intensity="low", themes=["calm"]),
    ]
    monkeypatch.setattr(
        "app.repository._candidate_seed",
        lambda sender_id, day_key: "seed-1",
    )
    first = repo.get_eligible_candidates("sender", "low", ["calm"], limit=3)
    second = repo.get_eligible_candidates("sender", "low", ["calm"], limit=3)
    assert [c.candidate_id for c in first] == [c.candidate_id for c in second]


def test_in_memory_candidate_sampling_differs_with_seed(monkeypatch):
    repo = InMemoryRepository()
    repo.candidate_pool = [
        Candidate(candidate_id="c1", intensity="low", themes=["calm"]),
        Candidate(candidate_id="c2", intensity="low", themes=["calm"]),
        Candidate(candidate_id="c3", intensity="low", themes=["calm"]),
    ]
    keys_seed_1 = [
        _candidate_sort_key(candidate.candidate_id, "seed-1")
        for candidate in repo.candidate_pool
    ]
    keys_seed_2 = [
        _candidate_sort_key(candidate.candidate_id, "seed-2")
        for candidate in repo.candidate_pool
    ]
    assert keys_seed_1 != keys_seed_2
