def test_matching_imports_without_fastapi():
    __import__("app.matching")


def test_repository_imports_without_redis():
    __import__("app.repository")
