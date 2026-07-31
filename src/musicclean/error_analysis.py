from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ErrorCategory(StrEnum):
    UNSUPPORTED_FORMAT = "unsupported_format"
    DAMAGED_OR_INVALID = "damaged_or_invalid"
    TRUNCATED_FILE = "truncated_file"
    TAG_PARSE_FAILURE = "tag_parse_failure"
    ACCESS_FAILURE = "access_failure"
    EMPTY_OR_UNREADABLE = "empty_or_unreadable"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class ErrorAssessment:
    category: ErrorCategory
    suggested_action: str


def assess_metadata_error(error: str) -> ErrorAssessment:
    normalized = error.casefold()

    if any(
        phrase in normalized
        for phrase in (
            "permission denied",
            "access is denied",
            "not permitted",
            "permissionerror",
        )
    ):
        return ErrorAssessment(
            ErrorCategory.ACCESS_FAILURE,
            "Verify share permissions, file ownership, and read access, then rescan.",
        )

    if any(
        phrase in normalized
        for phrase in (
            "truncated",
            "unexpected end",
            "end of file",
            "eof",
            "short read",
        )
    ):
        return ErrorAssessment(
            ErrorCategory.TRUNCATED_FILE,
            "Treat as potentially incomplete; verify against the source or re-download.",
        )

    if any(
        phrase in normalized
        for phrase in (
            "unsupported",
            "not a valid",
            "unknown format",
            "can't sync to",
            "cannot sync to",
            "no suitable tags",
        )
    ):
        return ErrorAssessment(
            ErrorCategory.UNSUPPORTED_FORMAT,
            "Confirm the extension matches the real codec and test with ffprobe.",
        )

    if any(
        phrase in normalized
        for phrase in (
            "header",
            "corrupt",
            "damaged",
            "invalid data",
            "invalid file",
            "not a",
            "bad",
        )
    ):
        return ErrorAssessment(
            ErrorCategory.DAMAGED_OR_INVALID,
            "Verify file integrity with the codec's native checker or ffmpeg.",
        )

    if any(
        phrase in normalized
        for phrase in (
            "tag",
            "id3",
            "vorbis comment",
            "metadata",
            "ape tag",
        )
    ):
        return ErrorAssessment(
            ErrorCategory.TAG_PARSE_FAILURE,
            "Back up the file, inspect tags in Picard, and rewrite malformed tags if needed.",
        )

    if any(
        phrase in normalized
        for phrase in (
            "empty",
            "zero length",
            "unreadable",
            "could not read",
            "cannot read",
        )
    ):
        return ErrorAssessment(
            ErrorCategory.EMPTY_OR_UNREADABLE,
            "Confirm the file is non-empty and readable, then compare with a known-good copy.",
        )

    return ErrorAssessment(
        ErrorCategory.UNKNOWN,
        "Review manually and test with ffprobe before changing or removing the file.",
    )
