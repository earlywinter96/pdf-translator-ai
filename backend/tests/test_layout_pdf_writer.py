from app.services.layout_pdf_writer import TextBlock, has_usable_layout


def _block(page: int, text: str) -> TextBlock:
    return TextBlock(
        page_number=page,
        rect=(0, 0, 100, 20),
        text=text,
        font_size=12,
        color=(0, 0, 0),
        is_bold=False,
    )


def test_sparse_text_layer_is_not_treated_as_a_two_page_layout():
    # Scanner exports can leave a watermark/date layer on only one page. It
    # must be routed through Indic OCR instead of skipping OCR entirely.
    blocks = [_block(0, "2025 International drcspune@gmail.com")]

    assert not has_usable_layout(blocks, expected_pages=2)


def test_complete_two_page_text_layer_remains_layout_preserved():
    blocks = [
        _block(0, "Marathi notice content " * 3),
        _block(1, "Second Marathi page content " * 3),
    ]

    assert has_usable_layout(blocks, expected_pages=2)


def test_single_page_short_document_keeps_existing_layout_behavior():
    blocks = [_block(0, "A short digital page with enough text to preserve")]

    assert has_usable_layout(blocks, expected_pages=1)
