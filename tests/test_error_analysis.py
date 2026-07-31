from musicclean.error_analysis import ErrorCategory, assess_metadata_error


def test_truncated_error() -> None:
    assessment = assess_metadata_error("unexpected end of file while reading frame")
    assert assessment.category is ErrorCategory.TRUNCATED_FILE


def test_access_error() -> None:
    assessment = assess_metadata_error("Permission denied")
    assert assessment.category is ErrorCategory.ACCESS_FAILURE


def test_unknown_error() -> None:
    assessment = assess_metadata_error("Something unusual happened")
    assert assessment.category is ErrorCategory.UNKNOWN
