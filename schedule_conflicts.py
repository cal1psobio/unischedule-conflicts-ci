"""Schedule conflict validation module for UniSchedule (User Story UNI-16)."""

from dataclasses import dataclass

VALID_DAYS = {"Mon", "Tue", "Wed", "Thu", "Fri", "Sat"}
VALID_WEEK_TYPES = {"both", "numerator", "denominator"}


@dataclass(frozen=True)
class Lesson:
    """Represents a scheduled university lesson slot."""

    day: str
    pair: int
    week_type: str
    group: str
    teacher: str
    room: str
    subject: str
    students_count: int = 25
    is_lecture: bool = False


def validate_lesson(lesson: Lesson) -> None:
    """Validate lesson attributes and raise ValueError on invalid data."""
    if lesson.day not in VALID_DAYS:
        raise ValueError(f"Invalid day '{lesson.day}'. Expected one of {sorted(VALID_DAYS)}.")
    if not (1 <= lesson.pair <= 7):
        raise ValueError(f"Invalid pair {lesson.pair}. Pair must be between 1 and 7.")
    if lesson.week_type not in VALID_WEEK_TYPES:
        raise ValueError(
            f"Invalid week_type '{lesson.week_type}'. Expected one of {sorted(VALID_WEEK_TYPES)}."
        )
    if lesson.students_count <= 0:
        raise ValueError(f"Invalid students_count {lesson.students_count}. Must be positive.")
    for field_name in ("group", "teacher", "room", "subject"):
        value = getattr(lesson, field_name)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Field '{field_name}' must be a non-empty string.")


def weeks_overlap(w1: str, w2: str) -> bool:
    """Return True if two week types overlap in the semester schedule."""
    return w1 == w2


def _is_shared_stream_lecture(existing: Lesson, new_lesson: Lesson) -> bool:
    """Return True when two different groups attend the same stream lecture."""
    return (
        existing.is_lecture
        and new_lesson.is_lecture
        and existing.room == new_lesson.room
        and existing.teacher == new_lesson.teacher
        and existing.subject == new_lesson.subject
        and existing.group != new_lesson.group
    )


def find_conflicts(
    existing_lessons: list[Lesson],
    new_lesson: Lesson,
    room_capacities: dict[str, int] | None = None,
) -> list[str]:
    """Detect group, room, teacher, and room-capacity conflicts for a new lesson."""
    validate_lesson(new_lesson)
    for existing in existing_lessons:
        validate_lesson(existing)

    conflicts: list[str] = []
    overlapping = [
        lesson
        for lesson in existing_lessons
        if lesson.day == new_lesson.day
        and lesson.pair == new_lesson.pair
        and weeks_overlap(lesson.week_type, new_lesson.week_type)
    ]

    for existing in overlapping:
        if existing.group == new_lesson.group:
            conflicts.append(
                f"Group conflict: group {new_lesson.group} already has '{existing.subject}' "
                f"in room {existing.room} ({existing.day}, pair {existing.pair})."
            )

        if not _is_shared_stream_lecture(existing, new_lesson):
            if existing.room == new_lesson.room:
                conflicts.append(
                    f"Room conflict: room {new_lesson.room} is already occupied by "
                    f"group {existing.group} ({existing.subject})."
                )
            if existing.teacher == new_lesson.teacher:
                conflicts.append(
                    f"Teacher conflict: {new_lesson.teacher} is already teaching "
                    f"group {existing.group} in room {existing.room}."
                )

    if room_capacities is not None and new_lesson.room in room_capacities:
        capacity = room_capacities[new_lesson.room]
        target_weeks = (
            ("numerator", "denominator")
            if new_lesson.week_type == "both"
            else (new_lesson.week_type,)
        )
        max_occupancy = max(
            new_lesson.students_count
            + sum(
                lesson.students_count
                for lesson in overlapping
                if lesson.room == new_lesson.room and weeks_overlap(lesson.week_type, wk)
            )
            for wk in target_weeks
        )
        if max_occupancy > capacity:
            conflicts.append(
                f"Capacity conflict: room {new_lesson.room} capacity is {capacity}, "
                f"but scheduled total is {max_occupancy} students."
            )

    return conflicts
