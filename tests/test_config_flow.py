"""Test StreakHub config flow."""

from datetime import date, timedelta

import pytest
from freezegun import freeze_time
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType


@pytest.mark.asyncio
async def test_config_flow_name_required(hass: HomeAssistant) -> None:
    """Test that name is required in config flow."""
    from homeassistant.data_entry_flow import InvalidData

    result = await hass.config_entries.flow.async_init(
        "streakhub",
        context={"source": "user"},
    )
    assert result["type"] == FlowResultType.FORM

    # Try to submit without name - HA raises InvalidData exception
    with pytest.raises(InvalidData):
        await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={},
        )


@pytest.mark.asyncio
async def test_config_flow_date_optional(hass: HomeAssistant) -> None:
    """Test that date is optional and defaults to today."""
    with freeze_time("2025-01-15 12:00:00+00:00"):
        result = await hass.config_entries.flow.async_init(
            "streakhub",
            context={"source": "user"},
        )
        assert result["type"] == FlowResultType.FORM

        # Submit with only name (no date)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"name": "Test Tracker"},
        )

        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["data"]["name"] == "Test Tracker"
        # initial_date should default to today
        assert result["data"]["initial_date"] == "2025-01-15"


@pytest.mark.asyncio
async def test_config_flow_date_in_past(hass: HomeAssistant) -> None:
    """Test that dates in the past are allowed."""
    with freeze_time("2025-01-15 12:00:00+00:00"):
        result = await hass.config_entries.flow.async_init(
            "streakhub",
            context={"source": "user"},
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                "name": "Past Tracker",
                "initial_date": date(2024, 6, 1),
            },
        )

        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["data"]["initial_date"] == "2024-06-01"


@pytest.mark.asyncio
async def test_config_flow_date_today(hass: HomeAssistant) -> None:
    """Test that today's date is allowed."""
    with freeze_time("2025-01-15 12:00:00+00:00"):
        result = await hass.config_entries.flow.async_init(
            "streakhub",
            context={"source": "user"},
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                "name": "Today Tracker",
                "initial_date": date(2025, 1, 15),
            },
        )

        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["data"]["initial_date"] == "2025-01-15"


@pytest.mark.asyncio
async def test_config_flow_date_tomorrow(hass: HomeAssistant) -> None:
    """Test that tomorrow's date is allowed (event happened today)."""
    with freeze_time("2025-01-15 12:00:00+00:00"):
        result = await hass.config_entries.flow.async_init(
            "streakhub",
            context={"source": "user"},
        )

        tomorrow = date(2025, 1, 16)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                "name": "Tomorrow Tracker",
                "initial_date": tomorrow,
            },
        )

        # Tomorrow should be allowed per spec
        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["data"]["initial_date"] == "2025-01-16"


@pytest.mark.asyncio
async def test_config_flow_date_day_after_tomorrow(hass: HomeAssistant) -> None:
    """Test that date after tomorrow is rejected (today+2 not allowed)."""
    result = await hass.config_entries.flow.async_init(
        "streakhub",
        context={"source": "user"},
    )

    day_after_tomorrow = date.today() + timedelta(days=2)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            "name": "Future Tracker",
            "initial_date": day_after_tomorrow,
        },
    )

    # Should show form again with error
    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"initial_date": "date_in_future"}


@pytest.mark.asyncio
async def test_config_flow_date_far_future(hass: HomeAssistant) -> None:
    """Test that far future dates are rejected."""
    result = await hass.config_entries.flow.async_init(
        "streakhub",
        context={"source": "user"},
    )

    far_future = date.today() + timedelta(days=365)  # 1 year in future
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            "name": "Far Future Tracker",
            "initial_date": far_future,
        },
    )

    # Should show form again with error
    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"initial_date": "date_in_future"}


@pytest.mark.asyncio
async def test_config_flow_duplicate_name(hass: HomeAssistant) -> None:
    """Test that duplicate names are rejected."""
    # First entry
    result = await hass.config_entries.flow.async_init(
        "streakhub",
        context={"source": "user"},
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={"name": "Duplicate Test"},
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY

    # Try to create another with same name
    result = await hass.config_entries.flow.async_init(
        "streakhub",
        context={"source": "user"},
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={"name": "Duplicate Test"},
    )

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "already_configured"


@pytest.mark.asyncio
async def test_config_flow_unique_id_generation(hass: HomeAssistant) -> None:
    """Test that unique_id is generated correctly from slugified name."""
    result = await hass.config_entries.flow.async_init(
        "streakhub",
        context={"source": "user"},
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={"name": "Test With Spaces"},
    )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    # Unique ID should be slugified
    entry = hass.config_entries.async_get_entry(result["result"].entry_id)
    assert entry is not None
    assert entry.unique_id == "test_with_spaces"
