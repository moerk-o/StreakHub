"""Tests for StreakHub core logic.

These tests cover the pure functions in logic.py without any Home Assistant
dependencies. All functions are deterministic and take `today` as a parameter.
"""

from datetime import date

import pytest

from custom_components.streakhub.logic import (
    HistoryEntry,
    Top3Entry,
    TrackerData,
    calculate_rank,
    calculate_streak,
    calculate_top_3,
    create_initial_storage_data,
    create_initial_tracker_data,
    process_event,
    process_set_streak_start,
    validate_set_streak_start,
)


class TestCalculateStreak:
    """Tests for calculate_streak function."""

    def test_streak_on_start_day(self) -> None:
        """Streak is 1 on the first day."""
        streak_start = date(2025, 1, 15)
        today = date(2025, 1, 15)
        assert calculate_streak(streak_start, today) == 1

    def test_streak_after_multiple_days(self) -> None:
        """Streak counts days correctly."""
        streak_start = date(2025, 1, 15)
        today = date(2025, 1, 17)
        assert calculate_streak(streak_start, today) == 3

    def test_streak_on_event_day(self) -> None:
        """Streak is 0 when today is before streak_start (event day)."""
        streak_start = date(2025, 1, 16)  # New streak starts tomorrow
        today = date(2025, 1, 15)  # Event day
        assert calculate_streak(streak_start, today) == 0

    def test_streak_long_period(self) -> None:
        """Streak handles long periods correctly."""
        streak_start = date(2025, 1, 1)
        today = date(2025, 2, 10)  # 41 days
        assert calculate_streak(streak_start, today) == 41

    def test_streak_same_day_as_start(self) -> None:
        """Edge case: streak_start equals today."""
        streak_start = date(2025, 1, 20)
        today = date(2025, 1, 20)
        assert calculate_streak(streak_start, today) == 1


class TestCalculateTop3:
    """Tests for calculate_top_3 function."""

    def test_single_current_streak(self) -> None:
        """Top 3 with only current streak."""
        streak_start = date(2025, 1, 20)
        history: list[HistoryEntry] = []
        today = date(2025, 1, 25)

        top_3 = calculate_top_3(streak_start, history, today)

        assert len(top_3) == 1
        assert top_3[0]["rank"] == 1
        assert top_3[0]["days"] == 6
        assert top_3[0]["end"] is None  # Current streak marker

    def test_current_streak_is_record(self) -> None:
        """Current streak is longer than history entries."""
        streak_start = date(2025, 1, 1)
        history: list[HistoryEntry] = [
            HistoryEntry(start="2024-11-01", end="2024-11-10", days=10),
            HistoryEntry(start="2024-12-01", end="2024-12-05", days=5),
        ]
        today = date(2025, 1, 20)  # 20 days

        top_3 = calculate_top_3(streak_start, history, today)

        assert len(top_3) == 3
        assert top_3[0]["days"] == 20
        assert top_3[0]["end"] is None
        assert top_3[0]["rank"] == 1

    def test_current_streak_not_in_top_3(self) -> None:
        """Current streak is too short for top 3."""
        streak_start = date(2025, 1, 20)
        history: list[HistoryEntry] = [
            HistoryEntry(start="2024-01-01", end="2024-02-28", days=59),
            HistoryEntry(start="2024-05-01", end="2024-05-31", days=31),
            HistoryEntry(start="2024-08-01", end="2024-08-20", days=20),
        ]
        today = date(2025, 1, 22)  # Only 3 days

        top_3 = calculate_top_3(streak_start, history, today)

        assert len(top_3) == 3
        # Current streak should not be in top 3
        for entry in top_3:
            assert entry["end"] is not None

    def test_tie_breaking_newer_wins(self) -> None:
        """When days are equal, newer streak (later start) wins."""
        streak_start = date(2025, 1, 20)
        history: list[HistoryEntry] = [
            HistoryEntry(start="2024-01-01", end="2024-01-10", days=10),
            HistoryEntry(start="2024-06-01", end="2024-06-10", days=10),
        ]
        today = date(2025, 1, 29)  # 10 days - same as history entries

        top_3 = calculate_top_3(streak_start, history, today)

        # Current streak (newest) should be rank 1
        assert top_3[0]["end"] is None
        assert top_3[0]["rank"] == 1
        # June streak should be rank 2 (newer than January)
        assert top_3[1]["start"] == "2024-06-01"
        assert top_3[1]["rank"] == 2
        # January streak should be rank 3
        assert top_3[2]["start"] == "2024-01-01"
        assert top_3[2]["rank"] == 3

    def test_fewer_than_3_streaks(self) -> None:
        """Top 3 with fewer than 3 total streaks."""
        streak_start = date(2025, 1, 20)
        history: list[HistoryEntry] = [
            HistoryEntry(start="2024-01-01", end="2024-01-10", days=10),
        ]
        today = date(2025, 1, 25)

        top_3 = calculate_top_3(streak_start, history, today)

        assert len(top_3) == 2

    def test_zero_day_current_streak(self) -> None:
        """Current streak is 0 (event day)."""
        streak_start = date(2025, 1, 21)  # Starts tomorrow
        history: list[HistoryEntry] = [
            HistoryEntry(start="2024-01-01", end="2024-01-10", days=10),
        ]
        today = date(2025, 1, 20)  # Event day

        top_3 = calculate_top_3(streak_start, history, today)

        # Current streak with 0 days should still be included
        assert len(top_3) == 2
        # History entry should be rank 1
        assert top_3[0]["days"] == 10
        assert top_3[0]["rank"] == 1


class TestCalculateRank:
    """Tests for calculate_rank function."""

    def test_rank_1(self) -> None:
        """Current streak is rank 1."""
        top_3: list[Top3Entry] = [
            Top3Entry(rank=1, start="2025-01-01", end=None, days=20),
            Top3Entry(rank=2, start="2024-01-01", end="2024-01-10", days=10),
        ]
        assert calculate_rank(top_3) == 1

    def test_rank_2(self) -> None:
        """Current streak is rank 2."""
        top_3: list[Top3Entry] = [
            Top3Entry(rank=1, start="2024-01-01", end="2024-02-28", days=59),
            Top3Entry(rank=2, start="2025-01-01", end=None, days=20),
            Top3Entry(rank=3, start="2024-05-01", end="2024-05-10", days=10),
        ]
        assert calculate_rank(top_3) == 2

    def test_rank_3(self) -> None:
        """Current streak is rank 3."""
        top_3: list[Top3Entry] = [
            Top3Entry(rank=1, start="2024-01-01", end="2024-02-28", days=59),
            Top3Entry(rank=2, start="2024-05-01", end="2024-05-31", days=31),
            Top3Entry(rank=3, start="2025-01-01", end=None, days=5),
        ]
        assert calculate_rank(top_3) == 3

    def test_not_in_top_3(self) -> None:
        """Current streak is not in top 3."""
        top_3: list[Top3Entry] = [
            Top3Entry(rank=1, start="2024-01-01", end="2024-02-28", days=59),
            Top3Entry(rank=2, start="2024-05-01", end="2024-05-31", days=31),
            Top3Entry(rank=3, start="2024-08-01", end="2024-08-20", days=20),
        ]
        assert calculate_rank(top_3) == 0


class TestProcessEvent:
    """Tests for process_event function."""

    def test_normal_button_press(self) -> None:
        """Normal button press ends streak and starts new one."""
        data = TrackerData(streak_start="2025-01-01", history=[])
        event_day = date(2025, 1, 14)

        new_data, history_entry = process_event(data, event_day)

        # New streak starts day after event
        assert new_data["streak_start"] == "2025-01-15"
        # Old streak recorded in history
        assert history_entry is not None
        assert history_entry["start"] == "2025-01-01"
        assert history_entry["end"] == "2025-01-13"
        assert history_entry["days"] == 13
        # History appended to new data
        assert len(new_data["history"]) == 1

    def test_button_press_on_same_day_as_start(self) -> None:
        """Button pressed on streak start day results in 0-day streak."""
        data = TrackerData(streak_start="2025-01-15", history=[])
        event_day = date(2025, 1, 15)

        new_data, history_entry = process_event(data, event_day)

        # New streak starts tomorrow
        assert new_data["streak_start"] == "2025-01-16"
        # 0-day streak not saved
        assert history_entry is None
        assert len(new_data["history"]) == 0

    def test_consecutive_button_presses(self) -> None:
        """Two consecutive day button presses."""
        # First press
        data = TrackerData(streak_start="2025-01-10", history=[])
        event_day = date(2025, 1, 14)
        new_data, _ = process_event(data, event_day)

        # Second press next day
        event_day_2 = date(2025, 1, 15)
        final_data, history_entry = process_event(new_data, event_day_2)

        # New streak starts after second press
        assert final_data["streak_start"] == "2025-01-16"
        # Second press creates 0-day streak (not saved)
        assert history_entry is None
        # Only first streak in history
        assert len(final_data["history"]) == 1

    def test_does_not_mutate_input(self) -> None:
        """Input data is not mutated."""
        original_history: list[HistoryEntry] = [
            HistoryEntry(start="2024-01-01", end="2024-01-10", days=10)
        ]
        data = TrackerData(streak_start="2025-01-01", history=original_history)
        event_day = date(2025, 1, 14)

        new_data, _ = process_event(data, event_day)

        # Original data unchanged
        assert data["streak_start"] == "2025-01-01"
        assert len(data["history"]) == 1
        # New data has new entry
        assert len(new_data["history"]) == 2


class TestValidateSetStreakStart:
    """Tests for validate_set_streak_start function."""

    def test_valid_date(self) -> None:
        """Valid date returns None."""
        current_start = date(2025, 1, 10)
        new_start = date(2025, 1, 15)
        today = date(2025, 1, 20)

        assert validate_set_streak_start(current_start, new_start, today) is None

    def test_date_in_future(self) -> None:
        """Date in future returns error key."""
        current_start = date(2025, 1, 10)
        new_start = date(2025, 1, 25)  # Future
        today = date(2025, 1, 20)

        assert (
            validate_set_streak_start(current_start, new_start, today)
            == "date_in_future"
        )

    def test_date_tomorrow_is_valid(self) -> None:
        """Date of today + 1 is valid (event happened today)."""
        current_start = date(2025, 1, 10)
        new_start = date(2025, 1, 21)  # Tomorrow
        today = date(2025, 1, 20)

        assert validate_set_streak_start(current_start, new_start, today) is None

    def test_date_before_streak_start(self) -> None:
        """Date before current streak start returns error key."""
        current_start = date(2025, 1, 15)
        new_start = date(2025, 1, 10)  # Before current start
        today = date(2025, 1, 20)

        assert (
            validate_set_streak_start(current_start, new_start, today)
            == "date_before_streak_start"
        )

    def test_date_equal_to_streak_start(self) -> None:
        """Date equal to current streak start returns error key."""
        current_start = date(2025, 1, 15)
        new_start = date(2025, 1, 15)  # Same as current start
        today = date(2025, 1, 20)

        assert (
            validate_set_streak_start(current_start, new_start, today)
            == "date_before_streak_start"
        )


class TestProcessSetStreakStart:
    """Tests for process_set_streak_start function."""

    def test_set_streak_start(self) -> None:
        """Setting streak start creates correct history entry."""
        data = TrackerData(streak_start="2025-01-20", history=[])
        new_start = date(2025, 1, 25)

        new_data, history_entry = process_set_streak_start(data, new_start)

        # New streak start is set
        assert new_data["streak_start"] == "2025-01-25"
        # Old streak recorded
        assert history_entry is not None
        assert history_entry["start"] == "2025-01-20"
        assert history_entry["end"] == "2025-01-23"  # Day before event day (24th)
        assert history_entry["days"] == 4


class TestCreateInitialData:
    """Tests for create_initial_* functions."""

    def test_create_initial_tracker_data(self) -> None:
        """Initial tracker data has correct structure."""
        initial_date = date(2025, 1, 15)
        data = create_initial_tracker_data(initial_date)

        assert data["streak_start"] == "2025-01-15"
        assert data["history"] == []

    def test_create_initial_storage_data(self) -> None:
        """Initial storage data has correct structure."""
        data = create_initial_storage_data()

        assert data["trackers"] == {}


class TestEdgeCases:
    """Additional edge case tests."""

    def test_leap_year_streak(self) -> None:
        """Streak calculation across leap year boundary."""
        streak_start = date(2024, 2, 28)  # 2024 is leap year
        today = date(2024, 3, 1)

        assert calculate_streak(streak_start, today) == 3  # 28, 29, 1

    def test_year_boundary_streak(self) -> None:
        """Streak calculation across year boundary."""
        streak_start = date(2024, 12, 30)
        today = date(2025, 1, 2)

        assert calculate_streak(streak_start, today) == 4  # 30, 31, 1, 2

    def test_very_long_streak(self) -> None:
        """Very long streak calculation."""
        streak_start = date(2020, 1, 1)
        today = date(2025, 1, 1)  # 5 years

        # Days from 2020-01-01 to 2025-01-01 inclusive:
        # 2020: 366 days (leap year), 2021-2024: 365*4 = 1460 days
        # Total: 366 + 1460 + 1 (Jan 1, 2025) = 1827
        # But calculate_streak returns (today - streak_start).days + 1
        # (2025-01-01 - 2020-01-01).days = 1827, +1 = 1828
        expected_days = (today - streak_start).days + 1
        assert calculate_streak(streak_start, today) == expected_days

    def test_top_3_with_many_history_entries(self) -> None:
        """Top 3 correctly selects from many history entries."""
        streak_start = date(2025, 1, 20)
        history: list[HistoryEntry] = [
            HistoryEntry(start="2024-01-01", end="2024-01-05", days=5),
            HistoryEntry(start="2024-02-01", end="2024-02-10", days=10),
            HistoryEntry(start="2024-03-01", end="2024-03-30", days=30),
            HistoryEntry(start="2024-04-01", end="2024-04-20", days=20),
            HistoryEntry(start="2024-05-01", end="2024-05-02", days=2),
        ]
        today = date(2025, 1, 25)  # 6 days

        top_3 = calculate_top_3(streak_start, history, today)

        assert len(top_3) == 3
        assert top_3[0]["days"] == 30
        assert top_3[1]["days"] == 20
        assert top_3[2]["days"] == 10
