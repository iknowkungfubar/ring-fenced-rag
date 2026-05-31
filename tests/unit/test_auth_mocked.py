"""Auth tests with properly targeted mocks — hits lazy import source paths."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException, Request

from rfr.api.auth import get_current_role, require_admin_role


class TestGetCurrentRoleWithMockDb:
    """get_current_role with DB mocked at the source module."""

    @pytest.mark.asyncio
    @patch("rfr.api.auth.AppConfig")
    async def test_auth_disabled_returns_default(self, mock_config: MagicMock) -> None:
        cfg = mock_config.return_value
        cfg.auth.enabled = False
        cfg.ingestion.default_role = "viewer"
        req = MagicMock(spec=Request)
        result = await get_current_role(request=req)
        assert result == "viewer"

    @pytest.mark.asyncio
    @patch("rfr.models.database.create_session")
    @patch("rfr.models.orm.ApiKey")
    @patch("rfr.api.auth.AppConfig")
    async def test_valid_key_returns_role(
        self, mock_config: MagicMock, mock_apikey_cls: MagicMock, mock_create_session: MagicMock
    ) -> None:
        cfg = mock_config.return_value
        cfg.auth.enabled = True

        mock_sess = MagicMock()
        mock_create_session.return_value.__enter__.return_value = mock_sess

        key_record = MagicMock()
        key_record.role = "senior_engineer"
        mock_sess.query.return_value.filter.return_value.first.return_value = key_record

        req = MagicMock(spec=Request)
        req.headers = {"Authorization": "Bearer rfr_valid_key"}

        result = await get_current_role(request=req)
        assert result == "senior_engineer"

    @pytest.mark.asyncio
    @patch("rfr.api.auth.AppConfig")
    async def test_missing_header_raises_401(self, mock_config: MagicMock) -> None:
        cfg = mock_config.return_value
        cfg.auth.enabled = True
        req = MagicMock(spec=Request)
        req.headers = {}
        with pytest.raises(HTTPException) as exc:
            await get_current_role(request=req)
        assert exc.value.status_code == 401

    @pytest.mark.asyncio
    @patch("rfr.models.database.create_session")
    @patch("rfr.models.orm.ApiKey")
    @patch("rfr.api.auth.AppConfig")
    async def test_invalid_key_raises_401(
        self, mock_config: MagicMock, mock_apikey_cls: MagicMock, mock_create_session: MagicMock
    ) -> None:
        cfg = mock_config.return_value
        cfg.auth.enabled = True
        mock_sess = MagicMock()
        mock_create_session.return_value.__enter__.return_value = mock_sess
        mock_sess.query.return_value.filter.return_value.first.return_value = None

        req = MagicMock(spec=Request)
        req.headers = {"Authorization": "Bearer bad_key"}
        with pytest.raises(HTTPException) as exc:
            await get_current_role(request=req)
        assert exc.value.status_code == 401


class TestRequireAdminRoleWithMockDb:
    """require_admin_role with DB mocked at the source module."""

    @pytest.mark.asyncio
    @patch("rfr.models.database.create_session")
    @patch("rfr.models.orm.ApiKey")
    @patch("rfr.api.auth.AppConfig")
    async def test_admin_role_allowed(
        self, mock_config: MagicMock, mock_apikey_cls: MagicMock, mock_create_session: MagicMock
    ) -> None:
        cfg = mock_config.return_value
        cfg.auth.enabled = True
        cfg.auth.admin_roles = ["admin"]

        mock_sess = MagicMock()
        mock_create_session.return_value.__enter__.return_value = mock_sess
        key_record = MagicMock()
        key_record.role = "admin"
        mock_sess.query.return_value.filter.return_value.first.return_value = key_record

        req = MagicMock(spec=Request)
        req.headers = {"Authorization": "Bearer admin_key"}
        result = await require_admin_role(request=req)
        assert result == "admin"

    @pytest.mark.asyncio
    @patch("rfr.models.database.create_session")
    @patch("rfr.models.orm.ApiKey")
    @patch("rfr.api.auth.AppConfig")
    async def test_non_admin_raises_403(
        self, mock_config: MagicMock, mock_apikey_cls: MagicMock, mock_create_session: MagicMock
    ) -> None:
        cfg = mock_config.return_value
        cfg.auth.enabled = True
        cfg.auth.admin_roles = ["admin"]
        mock_sess = MagicMock()
        mock_create_session.return_value.__enter__.return_value = mock_sess
        key_record = MagicMock()
        key_record.role = "user"
        mock_sess.query.return_value.filter.return_value.first.return_value = key_record

        req = MagicMock(spec=Request)
        req.headers = {"Authorization": "Bearer user_key"}
        with pytest.raises(HTTPException) as exc:
            await require_admin_role(request=req)
        assert exc.value.status_code == 403
