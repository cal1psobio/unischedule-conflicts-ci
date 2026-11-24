"""Unit tests for UniSchedule conflict checker (User Story UNI-16)."""

import pytest
from schedule_conflicts import Lesson, find_conflicts


def test_empty_schedule_no_conflicts():
    new_lesson = Lesson(
        day="Mon",
        pair=1,
        week_type="both",
        group="B-126-23-1-IT",
        teacher="Bondar O. A.",
        room="1.305",
        subject="Agile Development",
    )
    assert find_conflicts([], new_lesson) == []


def test_different_week_types_no_conflict():
    existing = [
        Lesson(
            day="Tue",
            pair=2,
            week_type="numerator",
            group="B-126-23-1-IT",
            teacher="Bondar O. A.",
            room="1.305",
            subject="Agile Development",
        )
    ]
    new_lesson = Lesson(
        day="Tue",
        pair=2,
        week_type="denominator",
        group="B-126-23-1-IT",
        teacher="Bondar O. A.",
        room="1.305",
        subject="System Analysis",
    )
    assert find_conflicts(existing, new_lesson) == []


def test_both_weeks_conflicts_with_numerator():
    existing = [
        Lesson(
            day="Wed",
            pair=3,
            week_type="numerator",
            group="B-126-23-2-IT",
            teacher="Kovalenko I. V.",
            room="1.402",
            subject="Databases",
        )
    ]
    new_lesson = Lesson(
        day="Wed",
        pair=3,
        week_type="both",
        group="B-126-23-1-IT",
        teacher="Bondar O. A.",
        room="1.402",
        subject="Agile Development",
    )
    conflicts = find_conflicts(existing, new_lesson)
    assert len(conflicts) == 1
    assert "Room conflict" in conflicts[0]


def test_group_conflict_same_slot():
    existing = [
        Lesson(
            day="Thu",
            pair=1,
            week_type="both",
            group="B-126-23-1-IT",
            teacher="Bondar O. A.",
            room="1.305",
            subject="Agile Development",
        )
    ]
    new_lesson = Lesson(
        day="Thu",
        pair=1,
        week_type="denominator",
        group="B-126-23-1-IT",
        teacher="Ivanenko P. M.",
        room="2.104",
        subject="DevOps",
    )
    conflicts = find_conflicts(existing, new_lesson)
    assert len(conflicts) == 1
    assert "Group conflict" in conflicts[0]


def test_teacher_conflict_different_rooms():
    existing = [
        Lesson(
            day="Fri",
            pair=4,
            week_type="both",
            group="B-126-23-1-IT",
            teacher="Bondar O. A.",
            room="1.305",
            subject="Agile Development",
        )
    ]
    new_lesson = Lesson(
        day="Fri",
        pair=4,
        week_type="both",
        group="B-126-23-2-IT",
        teacher="Bondar O. A.",
        room="1.308",
        subject="Software Architecture",
    )
    conflicts = find_conflicts(existing, new_lesson)
    assert len(conflicts) == 1
    assert "Teacher conflict" in conflicts[0]


def test_shared_stream_lecture_allowed():
    existing = [
        Lesson(
            day="Mon",
            pair=2,
            week_type="both",
            group="B-126-23-1-IT",
            teacher="Bondar O. A.",
            room="1.101",
            subject="Agile Development",
            students_count=28,
            is_lecture=True,
        )
    ]
    new_lesson = Lesson(
        day="Mon",
        pair=2,
        week_type="both",
        group="B-126-23-2-IT",
        teacher="Bondar O. A.",
        room="1.101",
        subject="Agile Development",
        students_count=27,
        is_lecture=True,
    )
    assert find_conflicts(existing, new_lesson, room_capacities={"1.101": 60}) == []


def test_room_capacity_boundary_and_exceeded():
    existing = [
        Lesson(
            day="Mon",
            pair=2,
            week_type="both",
            group="B-126-23-1-IT",
            teacher="Bondar O. A.",
            room="1.101",
            subject="Agile Development",
            students_count=30,
            is_lecture=True,
        )
    ]
    boundary_lesson = Lesson(
        day="Mon",
        pair=2,
        week_type="both",
        group="B-126-23-2-IT",
        teacher="Bondar O. A.",
        room="1.101",
        subject="Agile Development",
        students_count=30,
        is_lecture=True,
    )
    assert find_conflicts(existing, boundary_lesson, room_capacities={"1.101": 60}) == []

    exceeding_lesson = Lesson(
        day="Mon",
        pair=2,
        week_type="both",
        group="B-126-23-2-IT",
        teacher="Bondar O. A.",
        room="1.101",
        subject="Agile Development",
        students_count=31,
        is_lecture=True,
    )
    conflicts = find_conflicts(existing, exceeding_lesson, room_capacities={"1.101": 60})
    assert len(conflicts) == 1
    assert "Capacity conflict" in conflicts[0]


@pytest.mark.parametrize(
    "bad_kwargs",
    [
        {"pair": 0},
        {"pair": 8},
        {"day": "Sun"},
        {"week_type": "monthly"},
        {"students_count": 0},
    ],
)
def test_invalid_inputs_raise_value_error(bad_kwargs):
    base = {
        "day": "Mon",
        "pair": 1,
        "week_type": "both",
        "group": "B-126-23-1-IT",
        "teacher": "Bondar O. A.",
        "room": "1.305",
        "subject": "Agile Development",
        "students_count": 25,
    }
    base.update(bad_kwargs)
    bad_lesson = Lesson(**base)
    with pytest.raises(ValueError):
        find_conflicts([], bad_lesson)
