from app.services.shop_repository import DB_PATH, count_shops, ensure_database, fetch_active_shops


def test_sqlite_repository_seed_and_query() -> None:
    ensure_database()
    assert DB_PATH.exists()

    shops = fetch_active_shops()
    assert len(shops) >= 8
    assert count_shops() == len(shops)
    assert {"id", "name", "avg_price"}.issubset(set(shops[0].keys()))
