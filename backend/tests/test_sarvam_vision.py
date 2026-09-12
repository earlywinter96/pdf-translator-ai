import fitz

from app.services.sarvam_vision import _bbox_to_rect


def test_bbox_scales_when_orientation_matches():
    page = fitz.open().new_page(width=100, height=200)
    assert _bbox_to_rect([10, 20, 30, 60], page, 100, 200) == (10, 20, 30, 60)


def test_bbox_rotates_portrait_metadata_for_landscape_pdf():
    page = fitz.open().new_page(width=200, height=100)
    rect = _bbox_to_rect([10, 20, 30, 60], page, 100, 200)
    assert rect == (140.0, 10.0, 180.0, 30.0)
