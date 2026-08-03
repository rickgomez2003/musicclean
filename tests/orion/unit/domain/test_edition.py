from musicclean.orion.domain import Album, Edition


def test_edition_references_album_by_identity() -> None:
    album = Album("Album")
    edition = Edition(
        album_id=album.id,
        release_label="  2011 Remaster ",
        media_format=" CD ",
        catalog_number=" 12345 ",
        barcode=" 000111222 ",
    )

    assert edition.album_id == album.id
    assert edition.release_label == "2011 Remaster"
    assert edition.media_format == "CD"
    assert edition.catalog_number == "12345"
    assert edition.barcode == "000111222"


def test_blank_optional_edition_fields_become_none() -> None:
    album = Album("Album")
    edition = Edition(album_id=album.id, release_label=" ", media_format=" ")

    assert edition.release_label is None
    assert edition.media_format is None
