"""Route tests via TestClient — mocking DB at source for both auth and handler."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from rfr.api.app import create_app


class TestRoutesWithSourceMocks:
    """Route handlers tested via TestClient with source-module DB mocks."""

    @patch("rfr.models.database.create_session")
    @patch("rfr.models.orm.ApiKey")
    def test_create_api_key(self, mock_apikey_cls: MagicMock, mock_cs: MagicMock) -> None:
        """POST /auth/keys should create and return a key."""
        # Mock session for both auth check and route handler
        mock_sess = MagicMock()
        mock_cs.return_value.__enter__.return_value = mock_sess

        # Mock auth DB lookup — return admin key record
        key_record = MagicMock()
        key_record.role = "admin"
        key_record.key_hash = "mock_hash"
        key_record.key_prefix = "rfr_admin"
        mock_sess.query.return_value.filter.return_value.first.return_value = key_record

        app = create_app()
        client = TestClient(app)
        response = client.post(
            "/api/v1/auth/keys",
            json={"name": "test-key", "role": "admin"},
            headers={"Authorization": "Bearer rfr_any_admin_key"},
        )
        assert response.status_code == 201, response.text
        data = response.json()
        assert "key" in data
        assert data["name"] == "test-key"
        assert data["key"].startswith("rfr_")
        assert data["key_prefix"] == data["key"][:10]

    @patch("rfr.models.database.create_session")
    @patch("rfr.models.orm.ApiKey")
    def test_list_api_keys(self, mock_apikey_cls: MagicMock, mock_cs: MagicMock) -> None:
        """GET /auth/keys should list keys."""
        mock_sess = MagicMock()
        mock_cs.return_value.__enter__.return_value = mock_sess

        # Mock auth DB lookup
        key_record = MagicMock()
        key_record.role = "admin"
        mock_sess.query.return_value.filter.return_value.first.return_value = key_record

        # Mock keys list
        key1 = MagicMock()
        key1.key_prefix = "rfr_abc"
        key1.name = "key1"
        key1.role = "user"
        key1.is_active = True
        key2 = MagicMock()
        key2.key_prefix = "rfr_def"
        key2.name = "key2"
        key2.role = "admin"
        key2.is_active = True
        mock_sess.query.return_value.all.return_value = [key1, key2]

        app = create_app()
        client = TestClient(app)
        response = client.get(
            "/api/v1/auth/keys",
            headers={"Authorization": "Bearer rfr_admin_key"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["keys"]) == 2
        assert data["keys"][0]["prefix"] == "rfr_abc"

    @patch("rfr.models.database.create_session")
    @patch("rfr.models.orm.ApiKey")
    def test_deactivate_api_key(self, mock_apikey_cls: MagicMock, mock_cs: MagicMock) -> None:
        """DELETE /auth/keys/{prefix} should deactivate a key."""
        mock_sess = MagicMock()
        mock_cs.return_value.__enter__.return_value = mock_sess

        # Mock auth DB lookup
        key_record = MagicMock()
        key_record.role = "admin"
        mock_sess.query.return_value.filter.return_value.first.return_value = key_record

        # Mock the key to deactivate (resets the mock for route handler)
        target_key = MagicMock()
        target_key.key_prefix = "rfr_target"
        # Second call to query().filter().first() returns the target key
        mock_sess.query.return_value.filter.return_value.first.side_effect = [
            key_record,  # auth check
            target_key,  # deactivate lookup
        ]

        app = create_app()
        client = TestClient(app)
        response = client.delete(
            "/api/v1/auth/keys/rfr_target",
            headers={"Authorization": "Bearer rfr_admin_key"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["deactivated"] is True
        assert target_key.is_active is False

    @patch("rfr.models.database.create_session")
    @patch("rfr.models.orm.ApiKey")
    def test_deactivate_nonexistent_key(self, mock_apikey_cls: MagicMock, mock_cs: MagicMock) -> None:
        """Deleting nonexistent key returns 404."""
        mock_sess = MagicMock()
        mock_cs.return_value.__enter__.return_value = mock_sess

        # Mock auth DB lookup
        key_record = MagicMock()
        key_record.role = "admin"
        mock_sess.query.return_value.filter.return_value.first.side_effect = [
            key_record,  # auth check passes
            None,  # deactivate lookup returns None
        ]

        app = create_app()
        client = TestClient(app)
        response = client.delete(
            "/api/v1/auth/keys/nonexistent",
            headers={"Authorization": "Bearer rfr_admin_key"},
        )
        assert response.status_code == 404
