from datetime import date, datetime

from app.core.responses import success


def test_success_formats_date_and_datetime_values() -> None:
    response = success(
        {
            "created_at": datetime(2026, 6, 25, 2, 8, 0),
            "items": [{"purchase_date": date(2026, 6, 25)}],
        }
    )

    assert response["data"]["created_at"] == "2026-06-25 02:08:00"
    assert response["data"]["items"][0]["purchase_date"] == "2026-06-25"
