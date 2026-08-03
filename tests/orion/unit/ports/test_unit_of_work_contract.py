from musicclean.orion.ports import UnitOfWork


def test_unit_of_work_is_protocol() -> None:
    assert getattr(UnitOfWork, "_is_protocol", False) is True
