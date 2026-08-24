import pytest
from docling_core.types.doc import (
    DoclingDocument,
    DocItemLabel,
    DocumentOrigin,
    PageItem,
    PictureClassificationLabel,
    PictureClassificationMetaField,
    PictureClassificationPrediction,
    PictureItem,
    PictureMeta,
    Size,
)
from docling_core.proto import docling_document_to_proto
from docling_core.proto.gen.ai.docling.core.v1 import docling_document_pb2 as pb2
from docling_core.utils import conversion

def test_minimal_doc_conversion():
    doc = DoclingDocument(name="test_doc")
    proto = docling_document_to_proto(doc)
    
    assert proto.name == "test_doc"
    assert proto.body.name == "_root_"
    assert proto.furniture.name == "_root_"

def test_doc_with_text_conversion():
    doc = DoclingDocument(name="test_doc")
    doc.add_text(label=DocItemLabel.PARAGRAPH, text="Hello world")
    
    proto = docling_document_to_proto(doc)
    
    assert len(proto.texts) == 1
    assert proto.texts[0].text.base.text == "Hello world"
    assert proto.texts[0].text.base.label == pb2.DOC_ITEM_LABEL_PARAGRAPH

def test_doc_with_title_conversion():
    doc = DoclingDocument(name="test_doc")
    doc.add_title(text="Main Title")
    
    proto = docling_document_to_proto(doc)
    
    assert len(proto.texts) == 1
    assert proto.texts[0].title.base.text == "Main Title"
    assert proto.texts[0].title.base.label == pb2.DOC_ITEM_LABEL_TITLE


def test_pages_map_keys_are_ints_in_proto():
    doc = DoclingDocument(name="test_doc")
    doc.pages = {
        1: PageItem(size=Size(width=100.0, height=200.0), page_no=1),
        2: PageItem(size=Size(width=300.0, height=400.0), page_no=2),
    }

    proto = docling_document_to_proto(doc)
    assert 1 in proto.pages
    assert 2 in proto.pages
    assert proto.pages[1].page_no == 1
    assert proto.pages[2].size.width == 300.0


def test_structural_item_labels_are_enum_with_raw_fallback():
    for message_name in ("PictureItem", "TableItem", "KeyValueItem", "FormItem"):
        descriptor = pb2.DESCRIPTOR.message_types_by_name[message_name]
        label_field = descriptor.fields_by_name["label"]
        assert label_field.enum_type is not None
        assert label_field.enum_type.name == "DocItemLabel"
        assert "label_raw" in descriptor.fields_by_name


def test_doc_item_label_fallback_mapping():
    enum_value, raw = conversion._to_doc_item_label_enum_and_raw(DocItemLabel.PICTURE)
    assert enum_value == pb2.DOC_ITEM_LABEL_PICTURE
    assert raw is None

    enum_value, raw = conversion._to_doc_item_label_enum_and_raw("future_new_label")
    assert enum_value == pb2.DOC_ITEM_LABEL_UNSPECIFIED
    assert raw == "future_new_label"


def test_document_origin_binary_hash_uses_uint64_proto_field():
    doc = DoclingDocument(
        name="test_doc",
        origin=DocumentOrigin(
            mimetype="application/pdf",
            binary_hash=18446744073709551615,
            filename="sample.pdf",
        ),
    )

    proto = docling_document_to_proto(doc)
    assert proto.origin.binary_hash == 18446744073709551615


def test_picture_meta_code_field_round_trip():
    from docling_core.types.doc.document import CodeMetaField, PictureMeta
    from docling_core.types.doc.labels import CodeLanguageLabel

    meta = PictureMeta(
        code=CodeMetaField(
            text="print('hi')",
            language=CodeLanguageLabel.PYTHON,
            confidence=0.9,
            created_by="ocr",
        )
    )
    proto_meta = conversion._to_picture_meta(meta)
    assert proto_meta is not None
    assert proto_meta.code.text == "print('hi')"
    assert proto_meta.code.language == pb2.CODE_LANGUAGE_LABEL_PYTHON
    assert proto_meta.code.language_raw == ""
    assert proto_meta.code.confidence == pytest.approx(0.9)
    assert proto_meta.code.created_by == "ocr"


def test_code_language_fallback_for_unknown_value():
    enum_value, raw = conversion._to_code_language_enum_and_raw("BrandNewLang")
    assert enum_value == pb2.CODE_LANGUAGE_LABEL_UNSPECIFIED
    assert raw == "BrandNewLang"


def test_table_data_orientation_conversion():
    from docling_core.types.doc.document import Orientation, TableData

    proto = conversion._to_table_data(
        TableData(num_rows=2, num_cols=3, orientation=Orientation.ROT_90)
    )
    assert proto.orientation == pb2.ORIENTATION_ROT_90
    assert proto.orientation_raw == ""

    enum_value, raw = conversion._to_orientation_enum_and_raw("rot_future")
    assert enum_value == pb2.ORIENTATION_UNSPECIFIED
    assert raw == "rot_future"


def test_code_language_label_proto_covers_latex_tikz_doclang():
    descriptor = pb2.CodeLanguageLabel.DESCRIPTOR
    names = {v.name for v in descriptor.values}
    assert "CODE_LANGUAGE_LABEL_LATEX" in names
    assert "CODE_LANGUAGE_LABEL_TIKZ" in names
    assert "CODE_LANGUAGE_LABEL_DOCLANG" in names


def test_base_meta_language_and_entities_conversion():
    from docling_core.types.doc.document import (
        BaseMeta,
        EntitiesMetaField,
        EntityMention,
        LanguageMetaField,
    )
    from docling_core.types.doc.labels import HumanLanguageLabel

    meta = BaseMeta(
        language=LanguageMetaField(
            code=HumanLanguageLabel.EN,
            confidence=0.95,
            created_by="lang-detector",
        ),
        entities=EntitiesMetaField(
            mentions=[
                EntityMention(
                    text="IBM",
                    orig="IBM",
                    label="ORG",
                    charspan=(0, 3),
                    confidence=0.88,
                )
            ]
        ),
    )
    proto_meta = conversion._to_base_meta(meta)
    assert proto_meta is not None
    assert proto_meta.language.code == pb2.HUMAN_LANGUAGE_LABEL_EN
    assert proto_meta.language.code_raw == ""
    assert proto_meta.language.confidence == pytest.approx(0.95)
    assert len(proto_meta.entities.mentions) == 1
    assert proto_meta.entities.mentions[0].text == "IBM"
    assert proto_meta.entities.mentions[0].charspan.start == 0
    assert proto_meta.entities.mentions[0].charspan.end == 3


def test_base_meta_keywords_and_topics_conversion():
    from docling_core.types.doc.document import (
        BaseMeta,
        KeywordsMetaField,
        TopicsMetaField,
    )

    meta = BaseMeta(
        keywords=KeywordsMetaField(values=["transformer", "attention mechanism"]),
        topics=TopicsMetaField(values=["natural language processing"]),
    )
    proto_meta = conversion._to_base_meta(meta)
    assert proto_meta is not None
    assert list(proto_meta.keywords.values) == ["transformer", "attention mechanism"]
    assert list(proto_meta.topics.values) == ["natural language processing"]


def test_human_language_fallback_for_unknown_value():
    enum_value, raw = conversion._to_human_language_enum_and_raw("xx")
    assert enum_value == pb2.HUMAN_LANGUAGE_LABEL_UNSPECIFIED
    assert raw == "xx"


def test_language_meta_field_has_code_raw_fallback():
    descriptor = pb2.LanguageMetaField.DESCRIPTOR
    code_field = descriptor.fields_by_name["code"]
    assert code_field.enum_type.name == "HumanLanguageLabel"
    assert "code_raw" in descriptor.fields_by_name


def test_picture_classification_other_chart_roundtrip():
    """OTHER_CHART survives proto conversion as its raw string value.

    ``PictureClassificationPrediction.class_name`` is a string field in the
    proto (not an enum), so newly added PictureClassificationLabel values such
    as ``other_chart`` flow through conversion without proto changes.
    """
    doc = DoclingDocument(name="chart_doc")
    doc.pictures = [
        PictureItem(
            self_ref="#/pictures/0",
            label=DocItemLabel.PICTURE,
            meta=PictureMeta(
                classification=PictureClassificationMetaField(
                    predictions=[
                        PictureClassificationPrediction(
                            class_name=PictureClassificationLabel.OTHER_CHART.value,
                            confidence=0.91,
                            created_by="figure-classifier-v2",
                        )
                    ]
                )
            ),
        )
    ]

    proto = docling_document_to_proto(doc)
    assert len(proto.pictures) == 1
    pred = proto.pictures[0].meta.classification.predictions[0]
    assert pred.class_name == "other_chart"
    assert pred.confidence == pytest.approx(0.91)
    assert pred.created_by == "figure-classifier-v2"


# ---------------------------------------------------------------------------
# Reverse direction: proto_to_docling_document
# ---------------------------------------------------------------------------

from docling_core.proto import proto_to_docling_document
from docling_core.types.doc.base import BoundingBox, CoordOrigin
from docling_core.types.doc.document import (
    BaseMeta,
    CodeItem,
    DescriptionMetaField,
    EntitiesMetaField,
    EntityMention,
    FloatingMeta,
    Formatting,
    GraphCell,
    GraphData,
    GraphLink,
    ImageRef,
    KeyValueItem,
    KeywordsMetaField,
    LanguageMetaField,
    Orientation,
    ProvenanceItem,
    RichTableCell,
    SummaryMetaField,
    TableCell,
    TableData,
    TableItem,
    TopicsMetaField,
    TrackSource,
)
from docling_core.types.doc.labels import (
    CodeLanguageLabel,
    GraphCellLabel,
    GraphLinkLabel,
    HumanLanguageLabel,
)

_PNG_DATA_URI = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


def _assert_round_trip(doc: DoclingDocument) -> DoclingDocument:
    roundtripped = proto_to_docling_document(docling_document_to_proto(doc))
    assert roundtripped == doc
    assert roundtripped.export_to_dict() == doc.export_to_dict()
    return roundtripped


def _fixture_minimal() -> DoclingDocument:
    return DoclingDocument(name="test_doc")


def _fixture_with_text() -> DoclingDocument:
    doc = DoclingDocument(name="test_doc")
    doc.add_text(label=DocItemLabel.PARAGRAPH, text="Hello world")
    return doc


def _fixture_with_title() -> DoclingDocument:
    doc = DoclingDocument(name="test_doc")
    doc.add_title(text="Main Title")
    return doc


def _fixture_with_pages() -> DoclingDocument:
    doc = DoclingDocument(name="test_doc")
    doc.pages = {
        1: PageItem(size=Size(width=100.0, height=200.0), page_no=1),
        2: PageItem(size=Size(width=300.0, height=400.0), page_no=2),
    }
    return doc


def _fixture_with_origin() -> DoclingDocument:
    return DoclingDocument(
        name="test_doc",
        origin=DocumentOrigin(
            mimetype="application/pdf",
            binary_hash=18446744073709551615,
            filename="sample.pdf",
        ),
    )


def _fixture_with_picture_classification() -> DoclingDocument:
    doc = DoclingDocument(name="chart_doc")
    doc.pictures = [
        PictureItem(
            self_ref="#/pictures/0",
            label=DocItemLabel.PICTURE,
            meta=PictureMeta(
                classification=PictureClassificationMetaField(
                    predictions=[
                        PictureClassificationPrediction(
                            class_name=PictureClassificationLabel.OTHER_CHART.value,
                            confidence=0.91,
                            created_by="figure-classifier-v2",
                        )
                    ]
                )
            ),
        )
    ]
    return doc


@pytest.mark.parametrize(
    "factory",
    [
        _fixture_minimal,
        _fixture_with_text,
        _fixture_with_title,
        _fixture_with_pages,
        _fixture_with_origin,
        _fixture_with_picture_classification,
    ],
)
def test_round_trip_of_fixture_documents(factory):
    _assert_round_trip(factory())


def test_round_trip_rich_document():
    doc = DoclingDocument(
        name="rich",
        origin=DocumentOrigin(
            mimetype="application/pdf", binary_hash=123, filename="a.pdf"
        ),
    )
    doc.pages = {1: PageItem(size=Size(width=100.0, height=200.0), page_no=1)}

    code = doc.add_code(text="print('x')", code_language=CodeLanguageLabel.PYTHON)
    code.meta = FloatingMeta(
        description=DescriptionMetaField(text="d", confidence=0.5, created_by="me")
    )

    prov = ProvenanceItem(
        page_no=1,
        bbox=BoundingBox(l=0, t=1, r=2, b=3, coord_origin=CoordOrigin.BOTTOMLEFT),
        charspan=(0, 5),
    )
    text = doc.add_text(
        label=DocItemLabel.TEXT,
        text="src",
        prov=prov,
        formatting=Formatting(bold=True),
        hyperlink="https://example.com/x",
    )
    text.source = [
        TrackSource(start_time=1.0, end_time=2.0, identifier="cue-1", voice="John")
    ]

    table = doc.add_table(data=TableData(table_cells=[], num_rows=1, num_cols=2))
    rich_target = doc.add_text(label=DocItemLabel.TEXT, text="cellbody", parent=table)
    table.data.table_cells = [
        TableCell(
            text="a",
            start_row_offset_idx=0,
            end_row_offset_idx=1,
            start_col_offset_idx=0,
            end_col_offset_idx=1,
        ),
        RichTableCell(
            text="",
            start_row_offset_idx=0,
            end_row_offset_idx=1,
            start_col_offset_idx=1,
            end_col_offset_idx=2,
            ref=rich_target.get_ref(),
        ),
    ]

    doc.key_value_items.append(
        KeyValueItem(
            self_ref="#/key_value_items/0",
            graph=GraphData(
                cells=[
                    GraphCell(label=GraphCellLabel.KEY, cell_id=0, text="k", orig="k"),
                    GraphCell(
                        label=GraphCellLabel.VALUE, cell_id=1, text="v", orig="v"
                    ),
                ],
                links=[
                    GraphLink(
                        label=GraphLinkLabel.TO_VALUE,
                        source_cell_id=0,
                        target_cell_id=1,
                    )
                ],
            ),
        )
    )

    doc.add_picture(
        image=ImageRef(
            mimetype="image/png",
            dpi=72,
            size=Size(width=1.0, height=1.0),
            uri=_PNG_DATA_URI,
        )
    )

    meta = BaseMeta(
        summary=SummaryMetaField(text="s"),
        language=LanguageMetaField(code=HumanLanguageLabel.EN, confidence=0.9),
        entities=EntitiesMetaField(mentions=[EntityMention(text="IBM", charspan=(0, 3))]),
        keywords=KeywordsMetaField(values=["k1", "k2"]),
        topics=TopicsMetaField(values=["t1"]),
    )
    meta.set_custom_field(
        namespace="my_corp", name="score", value={"a": [1, 2.5, None, True, "x"]}
    )
    doc.texts[1].meta = meta

    _assert_round_trip(doc)


def test_round_trip_groups():
    doc = DoclingDocument(name="groups")
    list_group = doc.add_list_group(name="mylist")
    doc.add_list_item(text="one", parent=list_group, enumerated=True, marker="1.")
    inline_group = doc.add_inline_group()
    doc.add_text(label=DocItemLabel.TEXT, text="inl", parent=inline_group)
    roundtripped = _assert_round_trip(doc)
    assert type(roundtripped.groups[0]) is type(doc.groups[0])
    assert type(roundtripped.groups[1]) is type(doc.groups[1])


def test_reverse_raw_fallback_states_table_label():
    # enum tag > 0: mapped enum value.
    msg = pb2.TableItem(
        self_ref="#/tables/0", label=pb2.DOC_ITEM_LABEL_DOCUMENT_INDEX
    )
    msg.data.num_rows = 0
    msg.data.num_cols = 0
    doc_msg = pb2.DoclingDocument(name="t", body=pb2.GroupItem(self_ref="#/body"),
                                  furniture=pb2.GroupItem(self_ref="#/furniture"))
    doc_msg.tables.append(msg)
    doc = proto_to_docling_document(doc_msg)
    assert doc.tables[0].label == DocItemLabel.DOCUMENT_INDEX

    # tag 0 + non-empty raw: strict Literal field, class default applies.
    doc_msg.tables[0].label = pb2.DOC_ITEM_LABEL_UNSPECIFIED
    doc_msg.tables[0].label_raw = "future_label"
    doc = proto_to_docling_document(doc_msg)
    assert doc.tables[0].label == DocItemLabel.TABLE

    # both unset: class default, no raw pollution anywhere in the dump.
    doc_msg.tables[0].ClearField("label_raw")
    doc = proto_to_docling_document(doc_msg)
    assert doc.tables[0].label == DocItemLabel.TABLE
    assert "future_label" not in str(doc.export_to_dict())


def test_reverse_raw_fallback_states_code_language():
    # CodeMetaField.language: tag 0 + raw -> the vocabulary catch-all UNKNOWN.
    meta_msg = pb2.CodeMetaField(
        text="x", language=pb2.CODE_LANGUAGE_LABEL_UNSPECIFIED, language_raw="zig"
    )
    meta = conversion._from_code_meta(meta_msg)
    assert meta.language == CodeLanguageLabel.UNKNOWN

    # tag 0, no raw -> None (field was not set on the source).
    meta = conversion._from_code_meta(pb2.CodeMetaField(text="x"))
    assert meta.language is None

    # tag > 0 -> mapped value.
    meta = conversion._from_code_meta(
        pb2.CodeMetaField(text="x", language=pb2.CODE_LANGUAGE_LABEL_PYTHON)
    )
    assert meta.language == CodeLanguageLabel.PYTHON


def test_reverse_orientation_and_coord_origin_fallbacks():
    data_msg = pb2.TableData(
        num_rows=1, num_cols=1, orientation=pb2.ORIENTATION_ROT_270
    )
    assert conversion._from_table_data(data_msg).orientation == Orientation.ROT_270

    data_msg = pb2.TableData(num_rows=1, num_cols=1, orientation_raw="rot_future")
    assert conversion._from_table_data(data_msg).orientation == Orientation.ROT_0

    bbox_msg = pb2.BoundingBox(
        l=1, t=2, r=3, b=4, coord_origin=pb2.COORD_ORIGIN_BOTTOMLEFT
    )
    assert conversion._from_bbox(bbox_msg).coord_origin == CoordOrigin.BOTTOMLEFT

    bbox_msg = pb2.BoundingBox(l=1, t=2, r=3, b=4, coord_origin_raw="CENTER")
    assert conversion._from_bbox(bbox_msg).coord_origin == CoordOrigin.TOPLEFT


def test_reverse_code_item_meta_is_floating_meta():
    doc = DoclingDocument(name="code_doc")
    code = doc.add_code(text="SELECT 1", code_language=CodeLanguageLabel.SQL)
    code.meta = FloatingMeta(description=DescriptionMetaField(text="query"))
    roundtripped = _assert_round_trip(doc)
    item = roundtripped.texts[0]
    assert isinstance(item, CodeItem)
    assert isinstance(item.meta, FloatingMeta)
    assert item.meta.description is not None
    assert item.meta.description.text == "query"
    assert item.code_language == CodeLanguageLabel.SQL


def test_reverse_skips_source_entries_with_unset_oneof():
    doc = DoclingDocument(name="src_doc")
    doc.add_text(label=DocItemLabel.TEXT, text="t")
    msg = docling_document_to_proto(doc)
    # Simulate a foreign producer using an extension arm this schema lacks:
    # the entry parses with the oneof unset and must be skipped silently.
    msg.texts[0].text.base.source.append(pb2.SourceType())
    roundtripped = proto_to_docling_document(msg)
    assert roundtripped.texts[0].source == []
    # An empty source list must serialize as absent, not as [].
    assert "source" not in roundtripped.export_to_dict()["texts"][0]
    assert roundtripped == doc
    assert roundtripped.export_to_dict() == doc.export_to_dict()


def test_reverse_track_source_kind_is_implicit():
    doc = DoclingDocument(name="track_doc")
    text = doc.add_text(label=DocItemLabel.TEXT, text="t")
    text.source = [TrackSource(start_time=0.5, end_time=1.5)]
    roundtripped = _assert_round_trip(doc)
    source = roundtripped.texts[0].source[0]
    assert isinstance(source, TrackSource)
    assert source.kind == "track"
    assert source.identifier is None
    assert source.voice is None


def test_reverse_charspan_tuples():
    doc = DoclingDocument(name="span_doc")
    doc.pages = {1: PageItem(size=Size(width=10.0, height=10.0), page_no=1)}
    prov = ProvenanceItem(
        page_no=1,
        bbox=BoundingBox(l=0, t=0, r=1, b=1),
        charspan=(3, 9),
    )
    text = doc.add_text(label=DocItemLabel.TEXT, text="abc", prov=prov)
    text.meta = BaseMeta(
        entities=EntitiesMetaField(
            mentions=[EntityMention(text="abc", charspan=(0, 3))]
        )
    )
    roundtripped = _assert_round_trip(doc)
    item = roundtripped.texts[0]
    assert item.prov[0].charspan == (3, 9)
    assert item.meta.entities.mentions[0].charspan == (0, 3)


def test_reverse_formatting_and_hyperlink_none_vs_set():
    doc = DoclingDocument(name="fmt_doc")
    doc.add_text(label=DocItemLabel.TEXT, text="plain")
    doc.add_text(
        label=DocItemLabel.TEXT,
        text="fancy",
        formatting=Formatting(bold=True, italic=True),
        hyperlink="https://example.com/a",
    )
    roundtripped = _assert_round_trip(doc)
    assert roundtripped.texts[0].formatting is None
    assert roundtripped.texts[0].hyperlink is None
    assert roundtripped.texts[1].formatting == Formatting(bold=True, italic=True)
    assert str(roundtripped.texts[1].hyperlink) == "https://example.com/a"
    dumped = roundtripped.export_to_dict()
    assert "formatting" not in dumped["texts"][0]
    assert "hyperlink" not in dumped["texts"][0]


def test_reverse_image_ref_data_uri():
    doc = DoclingDocument(name="img_doc")
    doc.add_picture(
        image=ImageRef(
            mimetype="image/png",
            dpi=144,
            size=Size(width=1.0, height=1.0),
            uri=_PNG_DATA_URI,
        )
    )
    roundtripped = _assert_round_trip(doc)
    image = roundtripped.pictures[0].image
    assert image is not None
    assert image.mimetype == "image/png"
    assert image.dpi == 144
    assert str(image.uri) == _PNG_DATA_URI


def test_reverse_rich_table_cell_refs():
    doc = DoclingDocument(name="rich_table")
    table = doc.add_table(data=TableData(table_cells=[], num_rows=1, num_cols=2))
    target = doc.add_text(label=DocItemLabel.TEXT, text="cell", parent=table)
    table.data.table_cells = [
        TableCell(
            text="plain",
            start_row_offset_idx=0,
            end_row_offset_idx=1,
            start_col_offset_idx=0,
            end_col_offset_idx=1,
        ),
        RichTableCell(
            text="",
            start_row_offset_idx=0,
            end_row_offset_idx=1,
            start_col_offset_idx=1,
            end_col_offset_idx=2,
            ref=target.get_ref(),
        ),
    ]
    roundtripped = _assert_round_trip(doc)
    cells = roundtripped.tables[0].data.table_cells
    assert type(cells[0]) is TableCell
    assert type(cells[1]) is RichTableCell
    assert cells[1].ref.cref == target.self_ref


def test_reverse_graph_data():
    doc = DoclingDocument(name="graph_doc")
    doc.key_value_items.append(
        KeyValueItem(
            self_ref="#/key_value_items/0",
            graph=GraphData(
                cells=[
                    GraphCell(
                        label=GraphCellLabel.KEY, cell_id=0, text="k", orig="K"
                    ),
                    GraphCell(
                        label=GraphCellLabel.VALUE,
                        cell_id=1,
                        text="v",
                        orig="V",
                        prov=ProvenanceItem(
                            page_no=1,
                            bbox=BoundingBox(l=0, t=0, r=1, b=1),
                            charspan=(0, 1),
                        ),
                    ),
                ],
                links=[
                    GraphLink(
                        label=GraphLinkLabel.TO_VALUE,
                        source_cell_id=0,
                        target_cell_id=1,
                    )
                ],
            ),
        )
    )
    doc.pages = {1: PageItem(size=Size(width=10.0, height=10.0), page_no=1)}
    roundtripped = _assert_round_trip(doc)
    graph = roundtripped.key_value_items[0].graph
    assert [cell.label for cell in graph.cells] == [
        GraphCellLabel.KEY,
        GraphCellLabel.VALUE,
    ]
    assert graph.cells[1].prov is not None
    assert graph.links[0].label == GraphLinkLabel.TO_VALUE


def test_reverse_empty_vs_absent_lists():
    doc = DoclingDocument(name="empty_doc")
    doc.add_text(label=DocItemLabel.TEXT, text="t")
    roundtripped = _assert_round_trip(doc)
    dumped = roundtripped.export_to_dict()
    text = dumped["texts"][0]
    # Empty comment/source lists are suppressed in the canonical dump.
    assert "comments" not in text
    assert "source" not in text
    # field_regions / field_items suppressed when empty.
    assert "field_regions" not in dumped
    assert "field_items" not in dumped
