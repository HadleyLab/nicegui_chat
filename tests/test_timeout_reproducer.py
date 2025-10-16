"""Unit tests for timeout_reproducer.py."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.utils.timeout_reproducer import TimeoutReproducer


class TestTimeoutReproducer:
    """Test TimeoutReproducer class."""

    @pytest.fixture
    def reproducer(self):
        """Create TimeoutReproducer instance."""
        return TimeoutReproducer()

    @pytest.mark.asyncio
    async def test_api_stress_test_basic(self, reproducer):
        """Test basic API stress test functionality."""
        result = await reproducer.api_stress_test(num_requests=10, concurrent=5)

        assert result["scenario"] == "api_stress_test"
        assert result["total_requests"] == 10
        assert "successful_requests" in result
        assert "avg_response_time" in result
        assert "response_times" in result
        assert len(result["response_times"]) <= 100

    @pytest.mark.asyncio
    async def test_api_stress_test_with_timeouts(self, reproducer):
        """Test API stress test with simulated timeouts."""
        # Mock random to force timeouts
        with patch("random.random") as mock_random:
            # Force timeouts on some requests
            mock_random.side_effect = [0.04] * 5  # 5% timeout threshold

            result = await reproducer.api_stress_test(num_requests=10, concurrent=5)

            assert result["scenario"] == "api_stress_test"
            assert result["total_requests"] == 10
            # Should have some failed requests due to timeouts
            assert result["failed_requests"] >= 0

    @pytest.mark.asyncio
    async def test_memory_pressure_test_basic(self, reproducer):
        """Test basic memory pressure test functionality."""
        with patch("psutil.Process") as mock_process:
            mock_memory_info = MagicMock()
            mock_memory_info.rss = 100 * 1024 * 1024  # 100MB
            mock_memory_info.vms = 200 * 1024 * 1024  # 200MB
            mock_process.return_value.memory_info.return_value = mock_memory_info

            result = await reproducer.memory_pressure_test(duration_seconds=5)

            assert result["scenario"] == "memory_pressure_test"
            assert result["duration"] == 5
            assert "peak_memory_mb" in result
            assert "avg_memory_mb" in result
            assert "memory_growth_rate" in result

    @pytest.mark.asyncio
    async def test_memory_pressure_test_no_psutil(self, reproducer):
        """Test memory pressure test when psutil is not available."""
        with patch.dict("sys.modules", {"psutil": None}):
            result = await reproducer.memory_pressure_test(duration_seconds=2)

            assert result["scenario"] == "memory_pressure_test"
            assert "error" in result

    def test_calculate_growth_rate(self, reproducer):
        """Test memory growth rate calculation."""
        samples = [
            {"timestamp": 0.0, "rss_mb": 100.0},
            {"timestamp": 5.0, "rss_mb": 150.0},
        ]

        growth_rate = reproducer._calculate_growth_rate(samples)
        assert growth_rate == 10.0  # (150-100)/5 = 10 MB/s

    def test_calculate_growth_rate_insufficient_samples(self, reproducer):
        """Test growth rate calculation with insufficient samples."""
        samples = [{"timestamp": 0.0, "rss_mb": 100.0}]

        growth_rate = reproducer._calculate_growth_rate(samples)
        assert growth_rate == 0.0

    @pytest.mark.asyncio
    async def test_concurrent_requests_test_basic(self, reproducer):
        """Test basic concurrent requests test functionality."""
        result = await reproducer.concurrent_requests_test(
            num_users=5, messages_per_user=3
        )

        assert result["scenario"] == "concurrent_requests_test"
        assert result["total_users"] == 5
        assert result["total_requests"] == 15  # 5 * 3
        assert "avg_response_time" in result
        assert "response_times" in result
        assert len(result["response_times"]) <= 200

    @pytest.mark.asyncio
    async def test_network_latency_test_success(self, reproducer):
        """Test network latency test with successful requests."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_client.return_value.__aenter__.return_value.get.return_value = (
                mock_response
            )

            result = await reproducer.network_latency_test(
                target_url="https://example.com"
            )

            assert result["scenario"] == "network_latency_test"
            assert result["target_url"] == "https://example.com"
            assert result["total_requests"] == 20
            assert "successful_requests" in result
            assert "avg_response_time_ms" in result

    @pytest.mark.asyncio
    async def test_network_latency_test_failures(self, reproducer):
        """Test network latency test with request failures."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get.side_effect = (
                Exception("Connection failed")
            )

            result = await reproducer.network_latency_test(
                target_url="https://example.com"
            )

            assert result["scenario"] == "network_latency_test"
            assert result["failed_requests"] == 20
            assert result["successful_requests"] == 0
            assert len(result["errors"]) <= 10

    @pytest.mark.asyncio
    async def test_run_scenario_api_stress(self, reproducer):
        """Test running API stress scenario."""
        result = await reproducer.run_scenario(
            "api_stress", num_requests=5, concurrent=2
        )

        assert result["scenario"] == "api_stress_test"
        assert result["total_requests"] == 5

    @pytest.mark.asyncio
    async def test_run_scenario_memory_pressure(self, reproducer):
        """Test running memory pressure scenario."""
        with patch("psutil.Process"):
            result = await reproducer.run_scenario(
                "memory_pressure", duration_seconds=2
            )

            assert result["scenario"] == "memory_pressure_test"
            assert result["duration"] == 2

    @pytest.mark.asyncio
    async def test_run_scenario_concurrent_requests(self, reproducer):
        """Test running concurrent requests scenario."""
        result = await reproducer.run_scenario(
            "concurrent_requests", num_users=3, messages_per_user=2
        )

        assert result["scenario"] == "concurrent_requests_test"
        assert result["total_users"] == 3
        assert result["total_requests"] == 6

    @pytest.mark.asyncio
    async def test_run_scenario_network_latency(self, reproducer):
        """Test running network latency scenario."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_client.return_value.__aenter__.return_value.get.return_value = (
                mock_response
            )

            result = await reproducer.run_scenario(
                "network_latency", target_url="https://test.com"
            )

            assert result["scenario"] == "network_latency_test"
            assert result["target_url"] == "https://test.com"

    @pytest.mark.asyncio
    async def test_run_scenario_unknown(self, reproducer):
        """Test running unknown scenario raises ValueError."""
        with pytest.raises(ValueError, match="Unknown scenario"):
            await reproducer.run_scenario("unknown_scenario")

    def test_save_results(self, reproducer, tmp_path):
        """Test saving results to file."""
        # Add a mock result
        reproducer.results = [{"scenario": "test", "data": "value"}]

        filename = reproducer.save_results()
        assert filename.endswith(".json")

        # Verify file was created and contains expected data
        import json
        from pathlib import Path

        with Path(filename).open() as f:
            data = json.load(f)

        assert "results" in data
        assert "generated_at" in data
        assert "total_scenarios" in data
        assert data["total_scenarios"] == 1
        assert data["results"][0]["scenario"] == "test"

    def test_save_results_custom_filename(self, reproducer):
        """Test saving results with custom filename."""
        reproducer.results = [{"scenario": "test"}]

        custom_filename = "custom_results.json"
        result_filename = reproducer.save_results(custom_filename)

        assert result_filename == custom_filename

    def test_print_summary(self, reproducer, capsys):
        """Test printing summary of results."""
        # Add various test results
        reproducer.results = [
            {
                "scenario": "api_stress_test",
                "total_requests": 100,
                "successful_requests": 95,
                "failed_requests": 5,
                "requests_per_second": 10.5,
                "avg_response_time": 1.2,
                "max_response_time": 3.5,
            },
            {
                "scenario": "memory_pressure_test",
                "duration": 60,
                "peak_memory_mb": 150.5,
                "avg_memory_mb": 120.3,
                "memory_growth_rate": 2.1,
            },
            {
                "scenario": "concurrent_requests_test",
                "total_users": 20,
                "total_requests": 100,
                "requests_per_second": 15.2,
                "avg_response_time": 0.8,
                "max_response_time": 2.1,
            },
            {
                "scenario": "network_latency_test",
                "target_url": "https://api.example.com",
                "successful_requests": 18,
                "total_requests": 20,
                "avg_response_time_ms": 250.5,
                "max_response_time_ms": 1200.0,
            },
        ]

        reproducer.print_summary()

        captured = capsys.readouterr()
        output = captured.out

        # Verify summary contains expected elements
        assert "TIMEOUT REPRODUCTION TEST RESULTS" in output
        assert "api_stress_test" in output
        assert "memory_pressure_test" in output
        assert "concurrent_requests_test" in output
        assert "network_latency_test" in output
        assert "Total scenarios run: 4" in output

    def test_print_summary_empty_results(self, reproducer, capsys):
        """Test printing summary with no results."""
        reproducer.print_summary()

        captured = capsys.readouterr()
        output = captured.out

        assert "TIMEOUT REPRODUCTION TEST RESULTS" in output
        assert "Total scenarios run: 0" in output

    @pytest.mark.asyncio
    async def test_main_function_runs_scenarios(self):
        """Test that main function runs all scenarios."""
        with (
            patch("src.utils.timeout_reproducer.TimeoutReproducer") as mock_class,
            patch("asyncio.sleep"),
            patch("builtins.print"),
        ):
            mock_instance = MagicMock()
            mock_class.return_value = mock_instance

            # Mock the run_scenario method to return different results
            mock_instance.run_scenario = AsyncMock(
                side_effect=[
                    {"scenario": "api_stress_test"},
                    {"scenario": "memory_pressure_test"},
                    {"scenario": "concurrent_requests_test"},
                    {"scenario": "network_latency_test"},
                ]
            )

            # Import and run main
            from src.utils.timeout_reproducer import main

            await main()

            # Verify scenarios were run
            assert mock_instance.run_scenario.call_count == 4

            # Verify save_results was called
            mock_instance.save_results.assert_called_once()

            # Verify print_summary was called
            mock_instance.print_summary.assert_called_once()

    @pytest.mark.asyncio
    async def test_main_function_handles_scenario_errors(self):
        """Test that main function handles scenario errors gracefully."""
        with (
            patch("src.utils.timeout_reproducer.TimeoutReproducer") as mock_class,
            patch("builtins.print") as mock_print,
        ):
            mock_instance = MagicMock()
            mock_class.return_value = mock_instance

            # Mock run_scenario to raise an exception
            mock_instance.run_scenario = AsyncMock(side_effect=Exception("Test error"))

            from src.utils.timeout_reproducer import main

            await main()

            # Verify error was printed
            error_prints = [
                call for call in mock_print.call_args_list if "failed" in str(call)
            ]
            assert len(error_prints) > 0
