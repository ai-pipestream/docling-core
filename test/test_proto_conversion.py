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
    GroupItem,
    ImageRef,
    InlineGroup,
    KeyValueItem,
    KeywordsMetaField,
    LanguageMetaField,
    ListGroup,
    ListItem,
    OrderedList,
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
    GroupLabel,
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


def test_reverse_text_arm_dispatches_on_label():
    """Foreign producers emit all text items through the generic `text` arm,
    discriminated by label (as in the JSON dialect); the reverse converter
    must reconstruct the same classes the JSON loading path would produce."""
    from docling_core.types.doc.document import (
        ListItem as ListItemModel,
        SectionHeaderItem as SectionHeaderModel,
        TitleItem as TitleModel,
    )

    doc_msg = pb2.DoclingDocument(
        name="foreign",
        body=pb2.GroupItem(self_ref="#/body"),
        furniture=pb2.GroupItem(self_ref="#/furniture"),
    )
    for index, label in enumerate(
        (
            pb2.DOC_ITEM_LABEL_TITLE,
            pb2.DOC_ITEM_LABEL_SECTION_HEADER,
            pb2.DOC_ITEM_LABEL_LIST_ITEM,
            pb2.DOC_ITEM_LABEL_CODE,
            pb2.DOC_ITEM_LABEL_TEXT,
        )
    ):
        entry = doc_msg.texts.add()
        entry.text.base.self_ref = f"#/texts/{index}"
        entry.text.base.label = label
        entry.text.base.orig = "x"
        entry.text.base.text = "x"

    doc = proto_to_docling_document(doc_msg)
    assert type(doc.texts[0]) is TitleModel
    assert type(doc.texts[1]) is SectionHeaderModel
    assert doc.texts[1].level == 1
    assert type(doc.texts[2]) is ListItemModel
    assert type(doc.texts[3]) is CodeItem
    assert doc.texts[3].code_language == CodeLanguageLabel.UNKNOWN
    assert doc.texts[4].label == DocItemLabel.TEXT


# ---------------------------------------------------------------------------
# Nested list groups
#
# `DoclingDocument.groups` is typed `list[Union[ListGroup, InlineGroup,
# GroupItem]]`, and a group loaded from a mapping has an `ordered_list` label
# rewritten to `list` by `ListGroup.patch_ordered`. A JSON dump/load round trip
# therefore normalizes every legacy ordered-list group to a `ListGroup`, and no
# `ListItem` is ever left parented to a non-`ListGroup` node. The proto round
# trip must land on exactly the same document; that JSON round trip is the
# parity truth these tests pin.
# ---------------------------------------------------------------------------

def _assert_json_parity_round_trip(doc: DoclingDocument) -> DoclingDocument:
    """Assert the proto round trip agrees with a JSON dump/load round trip."""
    proto_round_trip = proto_to_docling_document(docling_document_to_proto(doc))
    json_round_trip = DoclingDocument.model_validate(doc.export_to_dict())
    assert proto_round_trip == json_round_trip
    assert proto_round_trip.export_to_dict() == json_round_trip.export_to_dict()
    return proto_round_trip


def _self_refs(doc: DoclingDocument) -> list[str]:
    return [group.self_ref for group in doc.groups] + [
        text.self_ref for text in doc.texts
    ]


def _add_group(doc: DoclingDocument, parent, factory, **kwargs):
    """Attach a group to `parent` without going through the add_* helpers.

    `add_list_group()` can only build a `ListGroup`, and `add_list_item()`
    silently wraps its item in a fresh list group when the parent is not one.
    Building the node directly is the only way to express a group carrying the
    legacy `ordered_list` label, which is what a foreign producer or an older
    document can put on the wire.
    """
    group = factory(
        self_ref=f"#/groups/{len(doc.groups)}", parent=parent.get_ref(), **kwargs
    )
    doc.groups.append(group)
    parent.children.append(group.get_ref())
    return group


def _add_list_item(doc: DoclingDocument, parent, text: str, **kwargs) -> ListItem:
    item = ListItem(
        self_ref=f"#/texts/{len(doc.texts)}",
        parent=parent.get_ref(),
        text=text,
        orig=text,
        **kwargs,
    )
    doc.texts.append(item)
    parent.children.append(item.get_ref())
    return item


def _ordered_group(**kwargs) -> GroupItem:
    with pytest.warns(DeprecationWarning):
        return OrderedList(**kwargs)


def test_round_trip_nested_list_groups():
    """A list group nested in a list group is already migration-stable and so
    must survive the proto round trip unchanged."""
    doc = DoclingDocument(name="nested_lists")
    outer = doc.add_list_group(name="outer")
    doc.add_list_item(text="a", parent=outer)
    inner = doc.add_list_group(name="inner", parent=outer)
    doc.add_list_item(text="b", parent=inner, enumerated=True, marker="1.")
    doc.add_list_item(text="c", parent=outer)

    round_tripped = _assert_round_trip(doc)
    assert [group.self_ref for group in round_tripped.groups] == [
        "#/groups/0",
        "#/groups/1",
    ]
    assert round_tripped.groups[1].parent.cref == "#/groups/0"


def test_round_trip_ordered_list_nested_in_list_group():
    """Regression: an ordered-list group nested inside a list group used to be
    rebuilt as the deprecated `OrderedList`, which kept its `ListItem` children
    "misplaced" and made the model synthesize replacement groups on load."""
    doc = DoclingDocument(name="ordered_in_list")
    outer = _add_group(doc, doc.body, ListGroup, name="outer")
    _add_list_item(doc, outer, "a")
    _add_list_item(doc, outer, "b")
    inner = _add_group(doc, outer, _ordered_group, name="inner")
    _add_list_item(doc, inner, "c", enumerated=True, marker="1.")
    _add_list_item(doc, inner, "d", enumerated=True, marker="2.")

    round_tripped = _assert_json_parity_round_trip(doc)

    refs = _self_refs(round_tripped)
    assert len(refs) == len(set(refs))
    # No group is synthesized: the two authored groups and four items survive.
    assert [group.self_ref for group in round_tripped.groups] == [
        "#/groups/0",
        "#/groups/1",
    ]
    assert [text.text for text in round_tripped.texts] == ["a", "b", "c", "d"]
    assert [child.cref for child in round_tripped.groups[1].children] == [
        "#/texts/2",
        "#/texts/3",
    ]
    # Model-consistent normalization: the union resolves `ordered_list` to a
    # `ListGroup`, exactly as a JSON load does.
    assert type(round_tripped.groups[1]) is ListGroup
    assert round_tripped.groups[1].label == GroupLabel.LIST
    assert round_tripped.groups[1].name == "inner"
    assert round_tripped.texts[2].enumerated is True
    assert round_tripped.texts[2].marker == "1."


def test_round_trip_list_nested_in_ordered_list_group():
    doc = DoclingDocument(name="list_in_ordered")
    outer = _add_group(doc, doc.body, _ordered_group, name="outer")
    _add_list_item(doc, outer, "a", enumerated=True, marker="1.")
    inner = _add_group(doc, outer, ListGroup, name="inner")
    _add_list_item(doc, inner, "b")
    _add_list_item(doc, outer, "c", enumerated=True, marker="2.")

    round_tripped = _assert_json_parity_round_trip(doc)

    refs = _self_refs(round_tripped)
    assert len(refs) == len(set(refs))
    assert [group.self_ref for group in round_tripped.groups] == [
        "#/groups/0",
        "#/groups/1",
    ]
    assert [text.text for text in round_tripped.texts] == ["a", "b", "c"]
    assert [child.cref for child in round_tripped.groups[0].children] == [
        "#/texts/0",
        "#/groups/1",
        "#/texts/2",
    ]
    assert round_tripped.groups[0].label == GroupLabel.LIST


def test_round_trip_two_sibling_nested_groups():
    doc = DoclingDocument(name="sibling_nested")
    outer = _add_group(doc, doc.body, ListGroup, name="outer")
    _add_list_item(doc, outer, "a")
    first = _add_group(doc, outer, _ordered_group, name="first")
    _add_list_item(doc, first, "b", enumerated=True, marker="1.")
    _add_list_item(doc, first, "c", enumerated=True, marker="2.")
    second = _add_group(doc, outer, _ordered_group, name="second")
    _add_list_item(doc, second, "d", enumerated=True, marker="1.")
    _add_list_item(doc, outer, "e")

    round_tripped = _assert_json_parity_round_trip(doc)

    refs = _self_refs(round_tripped)
    assert len(refs) == len(set(refs))
    assert [group.name for group in round_tripped.groups] == [
        "outer",
        "first",
        "second",
    ]
    assert [text.text for text in round_tripped.texts] == ["a", "b", "c", "d", "e"]
    assert [child.cref for child in round_tripped.groups[0].children] == [
        "#/texts/0",
        "#/groups/1",
        "#/groups/2",
        "#/texts/4",
    ]
    assert [child.cref for child in round_tripped.groups[1].children] == [
        "#/texts/1",
        "#/texts/2",
    ]
    assert [child.cref for child in round_tripped.groups[2].children] == ["#/texts/3"]


def test_round_trip_nested_group_with_meta_and_formatting():
    doc = DoclingDocument(name="nested_meta")
    outer = _add_group(doc, doc.body, ListGroup, name="outer")
    _add_list_item(doc, outer, "plain")
    inner = _add_group(
        doc,
        outer,
        _ordered_group,
        name="inner",
        meta=BaseMeta(summary=SummaryMetaField(text="inner summary")),
    )
    _add_list_item(
        doc,
        inner,
        "styled",
        enumerated=True,
        marker="1.",
        formatting=Formatting(bold=True, italic=True),
        hyperlink="https://example.com/nested",
    )
    rich = _add_list_item(doc, inner, "annotated", enumerated=True, marker="2.")
    rich.meta = BaseMeta(
        language=LanguageMetaField(code=HumanLanguageLabel.EN, confidence=0.75),
        keywords=KeywordsMetaField(values=["nested", "list"]),
    )
    rich.meta.set_custom_field(namespace="my_corp", name="rank", value={"n": 2})

    round_tripped = _assert_json_parity_round_trip(doc)

    styled = round_tripped.texts[1]
    assert styled.formatting is not None
    assert styled.formatting.bold is True
    assert styled.formatting.italic is True
    assert str(styled.hyperlink) == "https://example.com/nested"
    annotated = round_tripped.texts[2]
    assert annotated.meta.language.code == HumanLanguageLabel.EN
    assert annotated.meta.keywords.values == ["nested", "list"]
    assert annotated.meta.get_custom_part() == {"my_corp__rank": {"n": 2}}
    # Group meta rides along with the normalized nested group.
    assert round_tripped.groups[1].meta.summary.text == "inner summary"


def test_reverse_normalizes_ordered_list_group_label():
    """A foreign producer may still put `ordered_list` on the wire; the reverse
    converter must resolve it the way the JSON union does."""
    doc_msg = pb2.DoclingDocument(
        name="foreign_ordered",
        body=pb2.GroupItem(self_ref="#/body", name="_root_"),
        furniture=pb2.GroupItem(self_ref="#/furniture", name="_root_"),
    )
    doc_msg.body.children.add().ref = "#/groups/0"
    group = doc_msg.groups.add()
    group.self_ref = "#/groups/0"
    group.name = "legacy"
    group.label = pb2.GROUP_LABEL_ORDERED_LIST
    group.parent.ref = "#/body"
    group.children.add().ref = "#/texts/0"
    entry = doc_msg.texts.add()
    entry.list_item.base.self_ref = "#/texts/0"
    entry.list_item.base.label = pb2.DOC_ITEM_LABEL_LIST_ITEM
    entry.list_item.base.text = "one"
    entry.list_item.base.orig = "one"
    entry.list_item.base.parent.ref = "#/groups/0"
    entry.list_item.enumerated = True
    entry.list_item.marker = "1."

    doc = proto_to_docling_document(doc_msg)
    assert type(doc.groups[0]) is ListGroup
    assert doc.groups[0].label == GroupLabel.LIST
    assert len(doc.groups) == 1
    assert [child.cref for child in doc.groups[0].children] == ["#/texts/0"]
    assert doc.texts[0].parent.cref == "#/groups/0"


def test_inline_and_plain_groups_keep_their_class():
    doc = DoclingDocument(name="group_classes")
    inline = doc.add_inline_group(name="inl")
    doc.add_text(label=DocItemLabel.TEXT, text="x", parent=inline)
    plain = _add_group(doc, doc.body, GroupItem, name="chapter")
    doc.add_text(label=DocItemLabel.TEXT, text="y", parent=plain)

    round_tripped = _assert_round_trip(doc)
    assert type(round_tripped.groups[0]) is InlineGroup
    assert type(round_tripped.groups[1]) is GroupItem
    assert round_tripped.groups[1].label == GroupLabel.UNSPECIFIED


# ---------------------------------------------------------------------------
# Wire schema extensions
#
# The proto mirrors the canonical wire schema, which carries an additive
# extension set the Pydantic model has no slot for. Import absorbs those
# fields: a document that uses every one of them still converts, and dumps a
# document the dialect can express. The single active projection is the typed
# picture `barcode` annotation, which lands in the picture meta as the
# `pipestream__barcodes` custom field, byte for byte what the canonical
# exporter derives from the same annotations.
# ---------------------------------------------------------------------------

# The exporter's projection of the two barcodes built below, as it emits it:
# one object per annotation in annotation order, each with its keys in sorted
# order (`format`, `provenance`, `value`).
BARCODE_PROJECTION_JSON = (
    '[{"format": "QRCode", "provenance": "zxing", '
    '"value": "https://example.org/a"}, '
    '{"format": "Code128", "provenance": "opencv", "value": "0123456789"}]'
)


def _picture_doc_with_barcodes(*, meta: pb2.PictureMeta = None) -> pb2.DoclingDocument:
    doc_msg = pb2.DoclingDocument(
        name="barcodes",
        body=pb2.GroupItem(self_ref="#/body", children=[pb2.RefItem(ref="#/pictures/0")]),
        furniture=pb2.GroupItem(self_ref="#/furniture"),
    )
    picture = doc_msg.pictures.add()
    picture.self_ref = "#/pictures/0"
    picture.parent.ref = "#/body"
    picture.label = pb2.DOC_ITEM_LABEL_PICTURE
    if meta is not None:
        picture.meta.CopyFrom(meta)
    picture.annotations.add().barcode.CopyFrom(
        pb2.BarcodeAnnotation(
            format="QRCode", value="https://example.org/a", provenance="zxing"
        )
    )
    picture.annotations.add().barcode.CopyFrom(
        pb2.BarcodeAnnotation(
            format="Code128", value="0123456789", provenance="opencv"
        )
    )
    return doc_msg


def test_typed_barcodes_project_into_picture_meta():
    import json

    doc = proto_to_docling_document(_picture_doc_with_barcodes())
    meta = doc.pictures[0].meta
    assert meta is not None
    payloads = meta.model_extra["pipestream__barcodes"]
    # Key order is part of the contract, so compare the serialized fragment.
    assert json.dumps(payloads) == BARCODE_PROJECTION_JSON

    dumped = doc.export_to_dict()
    assert json.dumps(dumped["pictures"][0]["meta"]["pipestream__barcodes"]) == (
        BARCODE_PROJECTION_JSON
    )
    # A picture with no proto meta still gets one, carrying only the
    # projection: the same shape the exporter emits for that input.
    assert list(dumped["pictures"][0]["meta"]) == ["pipestream__barcodes"]
    # The dump is still a document the dialect can load.
    assert DoclingDocument.model_validate(dumped).export_to_dict() == dumped


def test_typed_barcodes_do_not_override_a_meta_carried_field():
    import json

    meta = pb2.PictureMeta()
    meta.custom_fields["pipestream__barcodes"].list_value.values.add().string_value = (
        "producer wrote this"
    )
    meta.custom_fields["pipestream__alpha"].string_value = "first"
    doc = proto_to_docling_document(_picture_doc_with_barcodes(meta=meta))

    dumped_meta = doc.export_to_dict()["pictures"][0]["meta"]
    assert dumped_meta["pipestream__barcodes"] == ["producer wrote this"]
    # Custom fields dump in sorted key order either way.
    assert list(dumped_meta) == ["pipestream__alpha", "pipestream__barcodes"]
    assert json.dumps(dumped_meta["pipestream__barcodes"]) != BARCODE_PROJECTION_JSON


def _every_extension_document() -> pb2.DoclingDocument:
    """A proto document that sets every field the model has no slot for."""
    from google.protobuf import timestamp_pb2

    stamp = timestamp_pb2.Timestamp(seconds=1_700_000_000)

    doc_msg = pb2.DoclingDocument(
        name="extensions",
        body=pb2.GroupItem(
            self_ref="#/body",
            children=[
                pb2.RefItem(ref="#/texts/0"),
                pb2.RefItem(ref="#/texts/1"),
                pb2.RefItem(ref="#/tables/0"),
                pb2.RefItem(ref="#/pictures/0"),
                pb2.RefItem(ref="#/groups/0"),
            ],
        ),
        furniture=pb2.GroupItem(self_ref="#/furniture"),
        origin=pb2.DocumentOrigin(
            mimetype="text/html",
            binary_hash=7,
            filename="page.html",
            uri="https://example.org/page.html",
            source_id="doc-42",
            mimetype_evidence="sniffed-magic",
            field_sources=[
                pb2.FieldSource(
                    field="web.canonical_uri",
                    source=pb2.CollectorSource(collector="grparse"),
                )
            ],
            web=pb2.WebMeta(
                target_uri="https://example.org/page.html",
                canonical_uri="https://example.org/",
                crawl_time=stamp,
                crawl_time_raw="Tue, 14 Nov 2023 22:13:20 GMT",
                http_status=200,
                content_language="en",
                headers={"content-type": "text/html"},
            ),
        ),
        source_meta=pb2.DocumentMeta(
            title="Extensions",
            authors=["A. Author"],
            created=stamp,
            modified=stamp,
            created_raw="2023-11-14T22:13:20Z",
            modified_raw="2023-11-14T22:13:20Z",
            language="en",
            generator="grparse",
            keywords=["wire", "schema"],
            schema_location="https://example.org/schema.xsd",
            extra={"department": "research"},
            identifiers=[
                pb2.Identifier(kind="doi", value="10.1000/xyz", scope="article")
            ],
            classifications=[
                pb2.Classification(
                    scheme="cpc", code="G06F", edition="2023.01", office="EP"
                )
            ],
            license=pb2.LicenseMeta(
                type_uri="https://creativecommons.org/licenses/by/4.0/",
                statement="CC BY 4.0",
                copyright_statement="(c) 2023 Example",
                copyright_year=2023,
                copyright_holder="Example",
            ),
            funding=[
                pb2.FundingAward(
                    funder="Example Foundation",
                    award_id="EF-1",
                    statement="Funded by EF-1.",
                )
            ],
            namespaces=[
                pb2.NamespaceBinding(prefix="dc", uri="http://purl.org/dc/elements/1.1/")
            ],
            schema_locations=[
                pb2.SchemaLocation(
                    namespace="http://purl.org/dc/elements/1.1/",
                    location="https://example.org/dc.xsd",
                )
            ],
            created_civil=pb2.CivilDateTime(year=2023, month=11, day=14),
            modified_civil=pb2.CivilDateTime(year=2023, month=11, day=15),
            subject="Extensions",
            modified_by="editor",
            printed=stamp,
            printed_raw="2023-11-14T22:13:20Z",
            printer="Example Printer",
            template="report.dotx",
            editing_cycles=3,
            editing_duration_seconds=7200,
            statistics=pb2.DocumentStatistics(
                pages=1,
                words=2,
                characters=10,
                paragraphs=1,
                tables=1,
                images=1,
                objects=1,
                cells=1,
                sheets=1,
            ),
            user_properties=[
                pb2.UserProperty(name="p_text", text="v"),
                pb2.UserProperty(name="p_number", number=1.5),
                pb2.UserProperty(name="p_boolean", boolean=True),
                pb2.UserProperty(name="p_instant", instant=stamp),
                pb2.UserProperty(
                    name="p_date", date=pb2.CivilDateTime(year=2023, month=11, day=14)
                ),
            ],
            format_version="1.7",
            structured=True,
            authoring_tool="Example Writer",
            protection=pb2.Protection(
                encrypted=True,
                handler="Standard",
                key_bits=256,
                opened_without_password=True,
                allows_extraction=True,
                allows_printing=True,
            ),
            raw_metadata=b"<x:xmpmeta/>",
            trapped=pb2.TRAPPED_UNKNOWN,
            field_sources=[
                pb2.FieldSource(
                    field="title",
                    source=pb2.CollectorSource(collector="libreoffice"),
                )
            ],
        ),
        attachments=[
            pb2.SubDocumentRef(
                id="part:1",
                name="attachment.pdf",
                media_type="application/pdf",
                size_bytes=1024,
                item_ref="#/texts/0",
                class_id="embedded",
                kind="attachment",
            )
        ],
        outline=[
            pb2.OutlineEntry(
                title="Chapter 1",
                level=1,
                page_no=1,
                target=pb2.FineRef(ref="#/texts/0"),
            )
        ],
        meta_tags=[pb2.MetaTag(name="description", content="a page")],
        structured_data=[pb2.StructuredData(kind="json-ld", json='{"@type":"Article"}')],
        media=pb2.MediaMeta(duration_ms=1200.0, speakers=["S1", "S2"], codec="opus"),
        changes=[
            pb2.ChangeRecord(
                id="c1",
                kind="insert",
                author="editor",
                timestamp=stamp,
                timestamp_raw="2023-11-14T22:13:20Z",
                target=pb2.FineRef(ref="#/texts/0", range=pb2.IntSpan(start=0, end=3)),
                content="was",
            )
        ],
        anchors=[pb2.NamedAnchor(name="top", target=pb2.FineRef(ref="#/texts/0"))],
        email=pb2.EmailMeta(
            **{
                "from": [pb2.EmailParty(name="Sender", address="s@example.org")],
                "to": [pb2.EmailParty(address="r@example.org")],
                "cc": [pb2.EmailParty(address="c@example.org")],
                "bcc": [pb2.EmailParty(address="b@example.org")],
            },
            message_id="<m1@example.org>",
            in_reply_to=["<m0@example.org>"],
            references=["<m0@example.org>"],
            conversation_topic="Extensions",
            conversation_index=b"\x01\x02",
            sent=stamp,
            sent_raw="Tue, 14 Nov 2023 22:13:20 GMT",
        ),
        page_styles=[
            pb2.PageStyle(
                name="Default",
                size=pb2.Size(width=612.0, height=792.0),
                margins=pb2.Margins(left=72.0, top=72.0, right=72.0, bottom=72.0),
                columns=1,
                variant="first",
            )
        ],
        named_ranges=[
            pb2.NamedRange(
                name="Data",
                range=pb2.GridSpan(
                    start=pb2.GridCell(row=0, col=0, sheet="Sheet1"),
                    end=pb2.GridCell(row=9, col=3, sheet="Sheet1"),
                ),
                has_headers=True,
                has_totals=True,
                kind="table",
                expression="Sheet1!$A$1:$D$10",
            )
        ],
        pivots=[
            pb2.PivotSpec(
                name="Pivot1",
                source=pb2.GridSpan(
                    start=pb2.GridCell(row=0, col=0), end=pb2.GridCell(row=9, col=3)
                ),
                output=pb2.GridSpan(
                    start=pb2.GridCell(row=0, col=5), end=pb2.GridCell(row=4, col=7)
                ),
                row_fields=["region"],
                column_fields=["quarter"],
                data_fields=["total"],
                page_fields=["year"],
            )
        ],
        claims=[
            pb2.CollectorClaim(
                source=pb2.CollectorSource(collector="libreoffice", version="24.2"),
                source_meta=pb2.DocumentMeta(title="Extensions (lost)"),
                origin=pb2.DocumentOrigin(
                    mimetype="application/pdf",
                    binary_hash=8,
                    filename="page.pdf",
                ),
                page_styles=[
                    pb2.PageStyle(name="Lost", size=pb2.Size(width=1.0, height=1.0))
                ],
                email=pb2.EmailMeta(message_id="<m2@example.org>"),
                media=pb2.MediaMeta(codec="aac"),
            )
        ],
    )

    # Every provenance arm on one item.
    prov = pb2.ProvenanceItem(
        page_no=1,
        bbox=pb2.BoundingBox(l=0, t=0, r=10, b=10),
        charspan=pb2.IntSpan(start=0, end=3),
        time=pb2.TimeSpan(start_ms=0.0, end_ms=500.0, track=0, speaker="S1"),
        byte_range=pb2.ByteSpan(start=0, end=64),
        grid=pb2.GridCell(row=2, col=3, sheet="Sheet1"),
        polygon=[
            pb2.Point(x=0.0, y=0.0),
            pb2.Point(x=10.0, y=0.0),
            pb2.Point(x=10.0, y=10.0),
        ],
        line_range=pb2.LineSpan(start=1, end=3),
    )
    span = pb2.InlineSpan(
        range=pb2.IntSpan(start=0, end=3),
        formatting=pb2.Formatting(
            bold=True,
            monospace=True,
            small_caps=True,
            math=True,
            mark=True,
            small=True,
            insertion=True,
            abbreviation=True,
            quote=True,
            overline=True,
        ),
        hyperlink="https://example.org/",
        target=pb2.FineRef(ref="#/texts/1"),
        font_family="Helvetica",
        font_size_pt=11.5,
        color="#112233",
        language="en",
        field_code="PAGE",
        reference_kind=pb2.REFERENCE_KIND_CITATION,
        reference="smith2023",
        link_title="Example",
        raw="<a href=...>",
        style_name="Emphasis",
        highlight_color="#ffff00",
        annotation="ruby",
    )
    collector = pb2.SourceType(
        collector=pb2.CollectorSource(
            collector="grparse",
            model="poppler-text",
            version="24.0",
            confidence=0.9,
            raw_score=-0.12,
            raw_score_kind="avg_logprob",
            raw_score_samples=512,
        )
    )
    alternatives = pb2.AlternativesMetaField(
        created_by="a-model",
        hypotheses=[
            pb2.Hypothesis(
                text="abd",
                raw_score=-1.4,
                raw_score_kind="avg_logprob",
                range=pb2.IntSpan(start=0, end=3),
            ),
            pb2.Hypothesis(text="obc"),
        ],
    )
    generation = pb2.SourceType(
        generation=pb2.GenerationSource(
            model="a-model",
            endpoint="https://example.org/v1",
            finish_reason="length",
            prompt_tokens=10,
            completion_tokens=20,
            temperature=0.2,
        )
    )

    text = doc_msg.texts.add()
    text.text.base.self_ref = "#/texts/0"
    text.text.base.parent.ref = "#/body"
    text.text.base.label = pb2.DOC_ITEM_LABEL_TEXT
    text.text.base.orig = "abc"
    text.text.base.text = "abc"
    text.text.base.prov.append(prov)
    text.text.base.spans.append(span)
    text.text.base.admonition_kind = "warning"
    text.text.base.label_raw = "future_label"
    text.text.base.style_name = "Body Text"
    text.text.base.raw = "<p>abc</p>"
    text.text.base.source_element_name = "p"
    text.text.base.source_namespace = "http://www.w3.org/1999/xhtml"
    text.text.base.source.extend([collector, generation])
    # The absorbed meta arm sits next to a mapped one, so the test pins that
    # absorbing it leaves the rest of the meta intact.
    text.text.base.meta.summary.text = "a summary"
    text.text.base.meta.alternatives.CopyFrom(alternatives)
    text.text.base.comment_meta.CopyFrom(
        pb2.CommentMeta(
            author="reviewer",
            initials="RV",
            timestamp=stamp,
            timestamp_raw="2023-11-14T22:13:20Z",
            resolved=True,
            parent=pb2.FineRef(ref="#/texts/1"),
            anchored_text="abc",
            shown=True,
        )
    )
    text.text.base.shape.CopyFrom(
        pb2.ShapeMeta(
            shape_type="textbox",
            name="TextBox 1",
            chain_next="TextBox 2",
            chain_prev="TextBox 0",
            z_order=3,
            rotation_degrees=90.0,
        )
    )
    text.text.base.footnote_meta.CopyFrom(
        pb2.FootnoteMeta(
            label="1", endnote=True, mark=pb2.FineRef(ref="#/texts/1")
        )
    )
    text.text.base.index_meta.CopyFrom(
        pb2.IndexMeta(service="index", title="Extensions, wire")
    )

    code = doc_msg.texts.add()
    code.code.self_ref = "#/texts/1"
    code.code.parent.ref = "#/body"
    code.code.label = pb2.DOC_ITEM_LABEL_CODE
    code.code.orig = "x = 1"
    code.code.text = "x = 1"
    code.code.label_raw = "future_label"
    code.code.source_element_name = "pre"
    code.code.source_namespace = "http://www.w3.org/1999/xhtml"
    code.code.source.append(collector)

    table = doc_msg.tables.add()
    table.self_ref = "#/tables/0"
    table.parent.ref = "#/body"
    table.label = pb2.DOC_ITEM_LABEL_TABLE
    table.meta.keywords.values.append("tabular")
    table.meta.alternatives.CopyFrom(alternatives)
    table.data.num_rows = 1
    table.data.num_cols = 1
    cell = table.data.table_cells.add()
    cell.text = "2023-11-14"
    cell.end_row_offset_idx = 1
    cell.end_col_offset_idx = 1
    cell.value.datetime.CopyFrom(
        pb2.CivilDateTime(
            year=2023, month=11, day=14, hour=22, minute=13, second=20, nanos=0
        )
    )
    cell.value.number_format = "yyyy-mm-dd"
    cell.spans.append(span)
    cell.align = pb2.ALIGNMENT_CENTER
    cell.valign = pb2.VERTICAL_ALIGNMENT_MIDDLE
    table.data.columns.append(
        pb2.TableColumnSchema(
            name="WHEN",
            declared_type="PIC X(10)",
            picture="X(10)",
            byte_offset=0,
            byte_size=10,
            level=5,
            occurs_index=1,
            width=64.0,
            width_raw="64pt",
            align=pb2.ALIGNMENT_RIGHT,
            valign=pb2.VERTICAL_ALIGNMENT_TOP,
            conditions=[
                pb2.ValueCondition(
                    name="VALID",
                    values=[pb2.ValueRange(low="A", high="Z")],
                )
            ],
        )
    )
    table.data.row_prov.append(prov)
    table.data.record_layout.CopyFrom(
        pb2.RecordLayoutMeta(
            encoding="cp037",
            record_length=80,
            header_bytes=0,
            footer_bytes=0,
            prefix_bytes=4,
            rows_truncated=0,
        )
    )

    picture = doc_msg.pictures.add()
    picture.self_ref = "#/pictures/0"
    picture.parent.ref = "#/body"
    picture.label = pb2.DOC_ITEM_LABEL_PICTURE
    picture.meta.topics.values.append("codes")
    picture.meta.alternatives.CopyFrom(alternatives)
    picture.meta.classification.predictions.add().class_name = "barcode"
    picture.meta.accessibility_title = "A QR code"
    picture.shape.CopyFrom(pb2.ShapeMeta(shape_type="picture", name="Picture 1"))
    picture.hyperlink = "https://example.org/figure"
    picture.target.CopyFrom(pb2.FineRef(ref="#/texts/0"))
    picture.chart.CopyFrom(
        pb2.ChartMeta(
            sources=[
                pb2.GridSpan(
                    start=pb2.GridCell(row=0, col=0, sheet="Sheet1"),
                    end=pb2.GridCell(row=9, col=1, sheet="Sheet1"),
                )
            ],
            has_row_headers=True,
            has_column_headers=True,
        )
    )
    picture.annotations.add().barcode.CopyFrom(
        pb2.BarcodeAnnotation(
            format="QRCode", value="https://example.org/a", provenance="zxing"
        )
    )
    picture.source_element_name = "img"
    picture.source_namespace = "http://www.w3.org/1999/xhtml"
    picture.image.CopyFrom(
        pb2.ImageRef(
            mimetype="image/png",
            dpi=72,
            size=pb2.Size(width=1.0, height=1.0),
            uri=_PNG_DATA_URI,
            size_raw="50%",
        )
    )

    group = doc_msg.groups.add()
    group.self_ref = "#/groups/0"
    group.parent.ref = "#/body"
    group.name = "chapter"
    group.label_raw = "future_group_label"
    group.sheet.CopyFrom(
        pb2.SheetMeta(
            index=0,
            visible=True,
            tab_color="#00ff00",
            print_areas=[
                pb2.GridSpan(
                    start=pb2.GridCell(row=0, col=0), end=pb2.GridCell(row=9, col=3)
                )
            ],
        )
    )

    field_item = doc_msg.field_items.add()
    field_item.self_ref = "#/field_items/0"
    field_item.parent.ref = "#/body"
    field_item.label = pb2.DOC_ITEM_LABEL_FIELD_ITEM
    field_item.field_name = "country"
    field_item.options.extend(["US", "DE"])
    field_item.selected_index = 1
    field_item.span.CopyFrom(pb2.FineRef(ref="#/texts/0"))
    field_item.parameters["required"] = "true"

    page = doc_msg.pages[1]
    page.page_no = 1
    page.size.width = 100.0
    page.size.height = 200.0
    page.unit = "pt"
    page.style_name = "Default"
    page.page_label = "iv"
    page.media_size.CopyFrom(pb2.Size(width=612.0, height=792.0))
    page.user_unit = 1.0
    page.quality.CopyFrom(
        pb2.PageQuality(
            garble_score=0.01,
            replacement_runs=0,
            ocr_recommended=False,
            rotation_degrees=0.0,
        )
    )
    return doc_msg


# Extension field names that must never surface in a dialect dump. The
# barcode projection is the one deliberate exception and is asserted
# separately.
_EXTENSION_KEYS = frozenset(
    {
        "source_meta",
        "attachments",
        "outline",
        "meta_tags",
        "structured_data",
        "media",
        "changes",
        "anchors",
        "email",
        "web",
        "time",
        "byte_range",
        "polygon",
        "spans",
        "admonition_kind",
        "style_name",
        "label_raw",
        "columns",
        "row_prov",
        "record_layout",
        "unit",
        "quality",
        "collector",
        "generation",
        "raw_score",
        "raw_score_kind",
        "raw_score_samples",
        "number_format",
        "barcode",
        "alternatives",
        "hypotheses",
        # Scholarly and declaration block.
        "identifiers",
        "classifications",
        "license",
        "funding",
        "namespaces",
        "schema_locations",
        "created_civil",
        "modified_civil",
        "reference_kind",
        "monospace",
        "small_caps",
        "math",
        # Markup block.
        "mark",
        "small",
        "insertion",
        "abbreviation",
        "quote",
        "width_raw",
        "align",
        "valign",
        "link_title",
        "highlight_color",
        # Office block.
        "comment_meta",
        "shape",
        "footnote_meta",
        "index_meta",
        "sheet",
        "page_styles",
        "named_ranges",
        "pivots",
        "subject",
        "modified_by",
        "printed",
        "printed_raw",
        "printer",
        "template",
        "editing_cycles",
        "editing_duration_seconds",
        "statistics",
        "user_properties",
        "class_id",
        "accessibility_title",
        "style_name",
        "overline",
        # PDF block.
        "format_version",
        "structured",
        "authoring_tool",
        "protection",
        "raw_metadata",
        "trapped",
        "source_id",
        "page_label",
        "media_size",
        "user_unit",
        "chart",
        # Office residuals.
        "field_name",
        "options",
        "selected_index",
        "parameters",
        # Collector claims and source identity block.
        "claims",
        "field_sources",
        "mimetype_evidence",
        "line_range",
        "size_raw",
        "annotation",
        "source_element_name",
        "source_namespace",
    }
)


def _keys_in(node) -> set:
    if isinstance(node, dict):
        found = set(node)
        for value in node.values():
            found |= _keys_in(value)
        return found
    if isinstance(node, list):
        found = set()
        for item in node:
            found |= _keys_in(item)
        return found
    return set()


def test_every_extension_field_is_absorbed_on_import():
    doc = proto_to_docling_document(_every_extension_document())
    dumped = doc.export_to_dict()

    # The absorbed extensions leave no trace, and the barcode projection is
    # the only thing the import synthesizes.
    leaked = _keys_in(dumped) & _EXTENSION_KEYS
    assert leaked == set()
    assert "pipestream__barcodes" in dumped["pictures"][0]["meta"]
    # Some extensions reuse a name the dialect already spends elsewhere
    # (`value`, `grid`, `hyperlink`, `target`, `span`, `raw`, `reference`),
    # so a whole-document key scan cannot judge them. They are checked where
    # the extension would have landed instead.
    cell = dumped["tables"][0]["data"]["table_cells"][0]
    assert "value" not in cell
    picture = dumped["pictures"][0]
    assert "hyperlink" not in picture
    assert "target" not in picture
    field_item = dumped["field_items"][0]
    assert "span" not in field_item
    text_dump = dumped["texts"][0]
    assert "raw" not in text_dump
    assert "reference" not in text_dump
    assert set(dumped["tables"][0]["data"]) == {
        "table_cells",
        "num_rows",
        "num_cols",
        "grid",
        "orientation",
    }
    assert "grid" not in dumped["texts"][0]["prov"][0]

    # What survives is a document the dialect can load and re-dump unchanged.
    assert DoclingDocument.model_validate(dumped).export_to_dict() == dumped

    # The model-side fields alongside the extensions still arrive.
    assert doc.texts[0].text == "abc"
    assert doc.texts[0].prov[0].bbox.r == 10
    assert doc.texts[0].prov[0].charspan == (0, 3)
    assert doc.texts[0].source == []
    assert doc.texts[1].text == "x = 1"
    # Absorbing the alternatives arm leaves the rest of each meta standing.
    assert doc.texts[0].meta.summary.text == "a summary"
    assert doc.tables[0].meta.keywords.values == ["tabular"]
    assert doc.pictures[0].meta.topics.values == ["codes"]
    assert "alternatives" not in dumped["texts"][0]["meta"]
    assert "alternatives" not in dumped["pictures"][0]["meta"]
    assert doc.tables[0].data.table_cells[0].text == "2023-11-14"
    assert doc.pages[1].size.width == 100.0
    assert doc.groups[0].name == "chapter"
    # Absorbing the image's size_raw leaves the mapped image intact, and the
    # resolved origin wins over the claim that lost.
    assert doc.pictures[0].image is not None
    assert doc.pictures[0].image.size.width == 1.0
    assert doc.origin is not None
    assert doc.origin.mimetype == "text/html"


def test_export_of_an_absorbed_document_stays_lossless_for_the_model():
    """The forward direction never emits extensions and must not choke on a
    document that came in carrying them."""
    doc = proto_to_docling_document(_every_extension_document())
    round_tripped = proto_to_docling_document(docling_document_to_proto(doc))
    assert round_tripped.export_to_dict() == doc.export_to_dict()


def test_alternatives_meta_field_numbers_match_the_wire_schema():
    """The alternates arm hangs off all three meta shapes, at the number the
    wire schema gave it in each."""
    for message_name, number in (
        ("BaseMeta", 6),
        ("FloatingMeta", 7),
        ("PictureMeta", 11),
    ):
        descriptor = pb2.DESCRIPTOR.message_types_by_name[message_name]
        field = descriptor.fields_by_name["alternatives"]
        assert field.number == number
        assert field.message_type.name == "AlternativesMetaField"
    hypothesis = pb2.DESCRIPTOR.message_types_by_name["Hypothesis"]
    assert [f.name for f in hypothesis.fields] == [
        "text",
        "raw_score",
        "raw_score_kind",
        "range",
    ]


def test_picture_classification_confidence_is_presence_tracked():
    """An engine that reports no probability leaves the field unset instead of
    claiming zero, so the wire field distinguishes the two."""
    field = pb2.PictureClassificationClass.DESCRIPTOR.fields_by_name["confidence"]
    assert field.number == 2
    assert field.type == field.TYPE_DOUBLE
    assert field.has_presence

    msg = pb2.PictureClassificationClass(class_name="qr")
    assert not msg.HasField("confidence")
    msg.confidence = 0.0
    assert msg.HasField("confidence")


def test_collector_source_carries_the_score_sample_count():
    field = pb2.CollectorSource.DESCRIPTOR.fields_by_name["raw_score_samples"]
    assert field.number == 7
    assert field.type == field.TYPE_UINT64
    assert field.has_presence


def _claimed_document() -> pb2.DoclingDocument:
    """A document whose two collectors disagreed on the title and the mimetype.

    The resolved view carries the winners and names them in `field_sources`;
    the loser keeps its whole account under `claims`.
    """
    grparse = pb2.CollectorSource(collector="grparse", version="1.4")
    libreoffice = pb2.CollectorSource(collector="libreoffice", version="24.2")
    return pb2.DoclingDocument(
        name="claimed",
        body=pb2.GroupItem(self_ref="#/body"),
        furniture=pb2.GroupItem(self_ref="#/furniture"),
        origin=pb2.DocumentOrigin(
            mimetype="application/vnd.oasis.opendocument.text",
            binary_hash=11,
            filename="letter.odt",
            mimetype_evidence="sniffed-magic",
            field_sources=[pb2.FieldSource(field="mimetype", source=libreoffice)],
        ),
        source_meta=pb2.DocumentMeta(
            title="Letter",
            field_sources=[
                pb2.FieldSource(field="title", source=libreoffice),
                pb2.FieldSource(field="generator", source=grparse),
            ],
        ),
        claims=[
            pb2.CollectorClaim(
                source=grparse,
                source_meta=pb2.DocumentMeta(title="letter.odt"),
                origin=pb2.DocumentOrigin(
                    mimetype="application/zip",
                    binary_hash=11,
                    filename="letter.odt",
                    mimetype_evidence="extension",
                ),
            ),
            pb2.CollectorClaim(
                source=libreoffice,
                source_meta=pb2.DocumentMeta(title="Letter"),
                page_styles=[
                    pb2.PageStyle(
                        name="Standard", size=pb2.Size(width=595.0, height=842.0)
                    )
                ],
                email=pb2.EmailMeta(message_id="<m1@example.org>"),
                media=pb2.MediaMeta(codec="aac"),
            ),
        ],
    )


def test_collector_claims_and_field_sources_round_trip():
    """Claims and field sources are absorbed on import; the resolved view
    they annotate survives untouched and re-exports losslessly."""
    doc = proto_to_docling_document(_claimed_document())
    dumped = doc.export_to_dict()

    assert "claims" not in dumped
    assert "source_meta" not in dumped
    assert "field_sources" not in dumped["origin"]
    assert "mimetype_evidence" not in dumped["origin"]
    assert _keys_in(dumped) & {"claims", "field_sources", "mimetype_evidence"} == set()

    # The resolved view wins, not the claim that lost the resolution.
    assert doc.origin is not None
    assert doc.origin.mimetype == "application/vnd.oasis.opendocument.text"
    assert doc.origin.binary_hash == 11
    assert doc.origin.filename == "letter.odt"

    # The dialect loads and re-dumps what survives unchanged, and a second
    # trip through the wire changes nothing.
    assert DoclingDocument.model_validate(dumped).export_to_dict() == dumped
    exported = docling_document_to_proto(doc)
    assert list(exported.claims) == []
    assert list(exported.origin.field_sources) == []
    assert not exported.origin.HasField("mimetype_evidence")
    assert proto_to_docling_document(exported).export_to_dict() == dumped


def test_collector_claim_and_field_source_numbers_match_the_wire_schema():
    """The claim block hangs off the document and both metadata messages at
    the numbers the wire schema gave it."""
    for message_name, field_name, number, type_name in (
        ("DoclingDocument", "claims", 28, "CollectorClaim"),
        ("DocumentOrigin", "field_sources", 8, "FieldSource"),
        ("DocumentMeta", "field_sources", 35, "FieldSource"),
    ):
        descriptor = pb2.DESCRIPTOR.message_types_by_name[message_name]
        field = descriptor.fields_by_name[field_name]
        assert field.number == number
        assert field.is_repeated
        assert field.message_type.name == type_name

    field_source = pb2.DESCRIPTOR.message_types_by_name["FieldSource"]
    assert [(f.name, f.number) for f in field_source.fields] == [
        ("field", 1),
        ("source", 2),
    ]
    assert field_source.fields_by_name["source"].message_type.name == (
        "CollectorSource"
    )

    claim = pb2.DESCRIPTOR.message_types_by_name["CollectorClaim"]
    assert [
        (f.name, f.number, f.message_type.name, f.has_presence)
        for f in claim.fields
    ] == [
        ("source", 1, "CollectorSource", True),
        ("source_meta", 2, "DocumentMeta", True),
        ("origin", 3, "DocumentOrigin", True),
        ("page_styles", 4, "PageStyle", False),
        ("email", 5, "EmailMeta", True),
        ("media", 6, "MediaMeta", True),
    ]


def test_source_identity_and_line_range_numbers_match_the_wire_schema():
    """The source element identity mirrors across the three item kinds that
    carry it, and the line-addressed provenance arm sits at its number."""
    for message_name, first in (
        ("TextItemBase", 23),
        ("CodeItem", 21),
        ("PictureItem", 20),
    ):
        descriptor = pb2.DESCRIPTOR.message_types_by_name[message_name]
        assert descriptor.fields_by_name["source_element_name"].number == first
        assert descriptor.fields_by_name["source_namespace"].number == first + 1
    text_base = pb2.DESCRIPTOR.message_types_by_name["TextItemBase"]
    assert text_base.fields_by_name["raw"].number == 22
    prov = pb2.DESCRIPTOR.message_types_by_name["ProvenanceItem"]
    line_range = prov.fields_by_name["line_range"]
    assert line_range.number == 8
    assert line_range.message_type.name == "LineSpan"
    line_span = pb2.DESCRIPTOR.message_types_by_name["LineSpan"]
    assert [(f.name, f.number, f.type) for f in line_span.fields] == [
        ("start", 1, line_span.fields[0].TYPE_UINT32),
        ("end", 2, line_span.fields[1].TYPE_UINT32),
    ]
    image_ref = pb2.DESCRIPTOR.message_types_by_name["ImageRef"]
    assert image_ref.fields_by_name["size_raw"].number == 5
    inline_span = pb2.DESCRIPTOR.message_types_by_name["InlineSpan"]
    assert inline_span.fields_by_name["annotation"].number == 16
    origin = pb2.DESCRIPTOR.message_types_by_name["DocumentOrigin"]
    assert origin.fields_by_name["mimetype_evidence"].number == 7


# ---------------------------------------------------------------------------
# Descriptor identity with the canonical wire schema.
#
# The vendored proto mirrors the canonical schema field for field. Four
# things differ by design (package, file path, Java options, root message
# name) and nothing else, so the sync is verified by comparing descriptors
# rather than by reading the diff.
# ---------------------------------------------------------------------------

# The fork's descriptor inventory, counted the way `_flatten_file` counts:
# map entry messages and their key/value fields included.
_WIRE_SCHEMA_MESSAGES = 141
_WIRE_SCHEMA_ENUMS = 14
_WIRE_SCHEMA_FIELDS = 749

# The root message is the one deliberate rename.
_ROOT_MESSAGE_RENAMES = {"Document": "DoclingDocument"}


def _flatten_file(file_proto, renames):
    """Reduce a FileDescriptorProto to comparable message, enum and field maps.

    Message and enum names are qualified by nesting, never by package, so
    the two files compare across their package difference. Field values
    carry everything that decides wire compatibility: number, label, type,
    the type name of message and enum fields, the oneof (if any) and whether
    the field is proto3 optional.
    """

    def local(type_name):
        name = type_name.rsplit(".", 1)[-1] if type_name else ""
        return renames.get(name, name)

    messages, enums, fields = {}, {}, {}

    def walk(message, prefix):
        name = prefix + renames.get(message.name, message.name)
        messages[name] = [o.name for o in message.oneof_decl]
        for field in message.field:
            oneof = (
                message.oneof_decl[field.oneof_index].name
                if field.HasField("oneof_index")
                else None
            )
            fields[f"{name}.{field.name}"] = (
                field.number,
                field.label,
                field.type,
                local(field.type_name),
                oneof,
                field.proto3_optional,
            )
        for enum in message.enum_type:
            enums[f"{name}.{enum.name}"] = [(v.name, v.number) for v in enum.value]
        for nested in message.nested_type:
            walk(nested, name + ".")

    for message in file_proto.message_type:
        walk(message, "")
    for enum in file_proto.enum_type:
        enums[enum.name] = [(v.name, v.number) for v in enum.value]
    return messages, enums, fields


def _fork_file_proto():
    from google.protobuf import descriptor_pb2

    return descriptor_pb2.FileDescriptorProto.FromString(pb2.DESCRIPTOR.serialized_pb)


def test_descriptor_inventory_is_pinned():
    """The counts move only when the canonical schema does; a change here
    without a matching canonical change is a drift, not a feature."""
    messages, enums, fields = _flatten_file(_fork_file_proto(), {})
    assert (len(messages), len(enums), len(fields)) == (
        _WIRE_SCHEMA_MESSAGES,
        _WIRE_SCHEMA_ENUMS,
        _WIRE_SCHEMA_FIELDS,
    )


def test_descriptor_is_identical_to_the_wire_schema():
    """Compile the canonical schema and compare descriptors: every message,
    enum, field number, name, type, label and oneof grouping must match.

    Set DOCLING_WIRE_SCHEMA_PROTO to the canonical `document.proto`; the test
    skips when it is unset, since the canonical file lives outside this
    repository.
    """
    import os
    import pathlib
    import subprocess
    import sys
    import tempfile

    from google.protobuf import descriptor_pb2

    location = os.environ.get("DOCLING_WIRE_SCHEMA_PROTO")
    if not location:
        pytest.skip("DOCLING_WIRE_SCHEMA_PROTO is unset")
    pytest.importorskip("grpc_tools")
    canonical = pathlib.Path(location)
    assert canonical.is_file(), canonical

    with tempfile.TemporaryDirectory() as tmp:
        out = pathlib.Path(tmp) / "canonical.pb"
        subprocess.check_call(
            [
                sys.executable,
                "-m",
                "grpc_tools.protoc",
                f"-I{canonical.parent}",
                f"--descriptor_set_out={out}",
                str(canonical),
            ]
        )
        file_set = descriptor_pb2.FileDescriptorSet.FromString(out.read_bytes())
    (canonical_proto,) = [f for f in file_set.file if f.name == canonical.name]

    theirs = _flatten_file(canonical_proto, _ROOT_MESSAGE_RENAMES)
    ours = _flatten_file(_fork_file_proto(), {})
    for label, a, b in zip(("messages", "enums", "fields"), theirs, ours):
        assert set(a) == set(b), (
            label,
            sorted(set(a) - set(b)),
            sorted(set(b) - set(a)),
        )
        assert a == b, [(k, a[k], b[k]) for k in sorted(a) if a[k] != b[k]]
    assert tuple(len(part) for part in ours) == (
        _WIRE_SCHEMA_MESSAGES,
        _WIRE_SCHEMA_ENUMS,
        _WIRE_SCHEMA_FIELDS,
    )
