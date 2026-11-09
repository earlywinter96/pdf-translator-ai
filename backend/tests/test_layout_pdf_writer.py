from app.services.layout_pdf_writer import TextBlock, coalesce_ocr_blocks, has_usable_layout


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


def test_ocr_coalescing_keeps_blocks_bounded_for_scan_layouts():
    blocks = [
        TextBlock(0, (0, 0, 40, 10), "First", 10, (0, 0, 0), False),
        TextBlock(0, (42, 0, 82, 10), "line", 10, (0, 0, 0), False),
        TextBlock(0, (0, 14, 100, 24), "Second line", 10, (0, 0, 0), False),
    ]

    merged = coalesce_ocr_blocks(blocks, max_chars=700)

    assert len(merged) == 2
    assert merged[0].text == "First line"
    assert merged[1].text == "Second line"


def test_line_coalescing_groups_indic_word_spans_without_zero_width_markers():
    blocks = [
        TextBlock(0, (72, 100, 120, 118), "मॉड्यूल", 14, (0, 0, 0), False),
        TextBlock(0, (120, 100, 150, 118), "\u200c 2\u200c", 14, (0, 0, 0), False),
        TextBlock(0, (150, 100, 230, 118), "टेक्निकल", 14, (0, 0, 0), False),
    ]

    merged = coalesce_ocr_blocks(blocks)

    assert len(merged) == 1
    assert merged[0].text == "मॉड्यूल 2 टेक्निकल"
