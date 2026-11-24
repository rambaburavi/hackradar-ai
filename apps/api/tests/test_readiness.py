from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.main import app


client = TestClient(app)


def test_readiness_success():
    with patch("app.main.engine") as mock_engine:
        connection = MagicMock()

        mock_engine.connect.return_value.__enter__.return_value = (
            connection
        )

        connection.execute.return_value.scalar_one.return_value = 1

        response = client.get("/ready")

        assert response.status_code == 200

        assert response.json() == {
            "status": "ready",
            "database": "connected",
        }


def test_readiness_database_unavailable():
    with patch("app.main.engine") as mock_engine:
        mock_engine.connect.side_effect = OperationalError(
            "SELECT 1",
            {},
            Exception("Database unavailable"),
        )

        response = client.get("/ready")

        assert response.status_code == 503

        assert response.json()["detail"]["status"] == "not_ready"


def test_health_independent_of_database():
    with patch("app.main.engine") as mock_engine:
        mock_engine.connect.side_effect = Exception(
            "Database unavailable"
        )

        response = client.get("/health")

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

        mock_engine.connect.assert_not_called()