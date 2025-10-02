"""Unit tests for authentication service."""

from unittest.mock import MagicMock, patch

import pytest

from src.config import HeysolConfig
from src.services.auth_service import AuthService
from src.utils.exceptions import AuthenticationError


class TestAuthService:
    """Test AuthService functionality."""

    def test_auth_service_init_with_api_key(self, mock_heysol_client):
        """Test AuthService initialization with API key."""
        config = HeysolConfig(
            api_key="test-key", base_url="https://test.heysol.ai/api/v1"
        )

        with patch("src.services.auth_service.HeySolClient") as mock_client_class:
            mock_client_class.return_value = mock_heysol_client
            service = AuthService(config)

            assert service._api_key == "test-key"
            assert service._client is not None
            assert service.is_authenticated is True
            mock_client_class.assert_called_once_with(
                api_key="test-key",
                base_url="https://test.heysol.ai/api/v1",
                prefer_mcp=False,
                skip_mcp_init=False,
            )

    def test_auth_service_init_without_api_key(self):
        """Test AuthService initialization without API key."""
        config = HeysolConfig(api_key=None, base_url="https://test.heysol.ai/api/v1")

        service = AuthService(config)

        assert service._api_key is None
        assert service._client is None
        assert service.is_authenticated is False

    def test_auth_service_init_client_creation_failure(self):
        """Test AuthService initialization when client creation fails."""
        config = HeysolConfig(
            api_key="invalid-key", base_url="https://test.heysol.ai/api/v1"
        )

        with patch("src.services.auth_service.HeySolClient") as mock_client_class:
            mock_client_class.side_effect = Exception("Client creation failed")

            # Should not raise, but log warning and set client to None
            with patch("builtins.print") as mock_print:
                service = AuthService(config)

                assert service._api_key == "invalid-key"
                assert service._client is None
                assert service.is_authenticated is False
                mock_print.assert_called_once()
                assert (
                    "Failed to initialize HeySol client" in mock_print.call_args[0][0]
                )

    def test_auth_service_client_property_authenticated(self, mock_auth_service):
        """Test client property when authenticated."""
        client = mock_auth_service.client
        assert client is not None

    def test_auth_service_client_property_not_authenticated(self):
        """Test client property when not authenticated."""
        config = HeysolConfig(api_key=None, base_url="https://test.com")
        service = AuthService(config)

        with pytest.raises(AuthenticationError) as exc_info:
            _ = service.client

        assert "not authenticated" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_auth_service_authenticate_success(self):
        """Test successful authentication."""
        config = HeysolConfig(api_key=None, base_url="https://test.heysol.ai/api/v1")
        service = AuthService(config)

        mock_client = MagicMock()
        with patch("src.services.auth_service.HeySolClient") as mock_client_class:
            mock_client_class.return_value = mock_client

            result = await service.authenticate("new-api-key")

            assert result is True
            assert service._api_key == "new-api-key"
            assert service._client == mock_client
            assert service.is_authenticated is True

            mock_client_class.assert_called_once_with(
                api_key="new-api-key",
                base_url="https://test.heysol.ai/api/v1",
                prefer_mcp=False,
                skip_mcp_init=False,
            )

    @pytest.mark.asyncio
    async def test_auth_service_authenticate_failure(self):
        """Test failed authentication."""
        config = HeysolConfig(api_key=None, base_url="https://test.heysol.ai/api/v1")
        service = AuthService(config)

        with patch("src.services.auth_service.HeySolClient") as mock_client_class:
            mock_client_class.side_effect = Exception("Authentication failed")

            with patch("builtins.print") as mock_print:
                result = await service.authenticate("invalid-key")

                assert result is False
                assert service._api_key is None
                assert service._client is None
                assert service.is_authenticated is False

                mock_print.assert_called_once()
                assert "Authentication failed" in mock_print.call_args[0][0]

    def test_auth_service_logout(self, mock_auth_service):
        """Test logout functionality."""
        assert mock_auth_service.is_authenticated is True
        assert mock_auth_service._client is not None
        assert mock_auth_service._api_key is not None

        mock_auth_service.logout()

        assert mock_auth_service._client is None
        assert mock_auth_service._api_key is None
        assert mock_auth_service.is_authenticated is False

    def test_auth_service_headers_authenticated(self, mock_auth_service):
        """Test headers generation when authenticated."""
        headers = mock_auth_service.headers()

        expected = {
            "Authorization": f"Bearer {mock_auth_service._api_key}",
            "Content-Type": "application/json",
        }
        assert headers == expected

    def test_auth_service_headers_not_authenticated(self):
        """Test headers generation when not authenticated."""
        config = HeysolConfig(api_key=None, base_url="https://test.com")
        service = AuthService(config)

        with pytest.raises(AuthenticationError) as exc_info:
            service.headers()

        assert "not authenticated" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_auth_service_reauthentication(self, mock_auth_service):
        """Test re-authentication with different API key."""
        original_client = mock_auth_service._client

        # Mock new client creation
        new_mock_client = MagicMock()
        with patch("src.services.auth_service.HeySolClient") as mock_client_class:
            mock_client_class.return_value = new_mock_client

            result = await mock_auth_service.authenticate("new-api-key")

            assert result is True
            assert mock_auth_service._api_key == "new-api-key"
            assert mock_auth_service._client == new_mock_client
            assert mock_auth_service._client != original_client

    @pytest.mark.asyncio
    async def test_auth_service_multiple_logins_logouts(self):
        """Test multiple login/logout cycles."""
        config = HeysolConfig(api_key=None, base_url="https://test.heysol.ai/api/v1")
        service = AuthService(config)

        # Initially not authenticated
        assert not service.is_authenticated

        # First authentication
        mock_client1 = MagicMock()
        with patch("src.services.auth_service.HeySolClient") as mock_client_class:
            mock_client_class.return_value = mock_client1
            result = await service.authenticate("key1")
            assert result is True
            assert service.is_authenticated
            assert service._client == mock_client1

        # Logout
        service.logout()
        assert not service.is_authenticated
        assert service._client is None

        # Second authentication
        mock_client2 = MagicMock()
        with patch("src.services.auth_service.HeySolClient") as mock_client_class:
            mock_client_class.return_value = mock_client2
            result = await service.authenticate("key2")
            assert result is True
            assert service.is_authenticated
            assert service._client == mock_client2
            assert service._client != mock_client1

    @pytest.mark.asyncio
    async def test_auth_service_is_authenticated_property(self):
        """Test is_authenticated property behavior."""
        config = HeysolConfig(api_key=None, base_url="https://test.heysol.ai/api/v1")
        service = AuthService(config)

        # Initially not authenticated
        assert service.is_authenticated is False

        # Mock successful authentication
        mock_client = MagicMock()
        with patch("src.services.auth_service.HeySolClient") as mock_client_class:
            mock_client_class.return_value = mock_client
            await service.authenticate("test-key")

            assert service.is_authenticated is True

        # After logout
        service.logout()
        assert service.is_authenticated is False

    def test_auth_service_client_initialization_error_handling(self):
        """Test error handling during client initialization."""
        config = HeysolConfig(
            api_key="problematic-key", base_url="https://test.heysol.ai/api/v1"
        )

        # Test various exception types during initialization
        for exception_type in [ValueError, RuntimeError, ConnectionError]:
            with patch("src.services.auth_service.HeySolClient") as mock_client_class:
                mock_client_class.side_effect = exception_type("Init failed")

                with patch("builtins.print") as mock_print:
                    service = AuthService(config)

                    assert service._client is None
                    assert service._api_key == "problematic-key"
                    mock_print.assert_called_once()

    def test_auth_service_import_error_handling(self):
        """Test graceful handling when heysol module import fails."""
        config = HeysolConfig(
            api_key="test-key", base_url="https://test.heysol.ai/api/v1"
        )

        # Mock the import error at the module level
        with patch.dict("sys.modules", {"heysol": None}):
            with patch("builtins.__import__", side_effect=ModuleNotFoundError):
                # Should handle import error gracefully
                service = AuthService(config)
                assert service._client is None
                assert not service.is_authenticated
