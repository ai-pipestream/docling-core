# DoclingDocument Parity Contract

This document explains how `DoclingDocument` parity is maintained between:

- **Pydantic model** (`docling_core.types.doc.document.DoclingDocument`) as semantic source of truth.
- **Protobuf IDL** (`docling_document.proto`) as wire contract source of truth.

## Invariants

1. New/updated Pydantic fields must be represented in protobuf with equivalent meaning.
2. Enums in Pydantic should map to protobuf enums (not downgraded to string fields).
3. gRPC payloads use protobuf as the primary document transport.
4. Any intentional difference must be documented and validated.

## Intentional Differences (Keep Small)


| Pattern                                                                                                             | Type                          | Reason                                                                                                                                                                                                                                                                                                                                            | Status      |
| ------------------------------------------------------------------------------------------------------------------- | ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------- |
| `*_raw` companion strings (e.g. `label_raw`, `code_language_raw`, `language_raw`, `code_raw`, `coord_origin_raw`, `script_raw`) | proto-only fallback field     | Preserves unrecognized values without breaking clients. The string carries the original source value when the enum tag is `*_UNSPECIFIED`. Companion name follows the enum field: `LanguageMetaField.code` uses `code_raw`; `CodeMetaField.language` uses `language_raw`.                                                                        | intentional |
| `TableData.grid` (and `*.chart_data.grid`)                                                                          | computed-field surfaced       | Pydantic `TableData.grid` is a `@computed_field` — derived from `table_cells` + cell row/col offsets. It IS in the Pydantic JSON dump, so proto surfaces it for parity. Not a divergence; the validator allowlists it because it doesn't appear in `model_fields`.                                                                                | intentional |
| `TrackSource.kind` (Pydantic-side only)                                                                             | discriminator absorbed        | Pydantic discriminated unions need a per-variant `kind: Literal[...]` field. Proto encodes the same information in the parent oneof tag (`SourceType.source.track`), so the per-variant string field is redundant on the wire.                                                                                                                    | intentional |
| `CodeItem` proto inlines `TextItemBase` fields instead of using `base = 1`                                          | inheritance-without-shadowing | All other text variants wrap a `TextItemBase base = 1` for shared fields. CodeItem is the only Pydantic text variant that overrides `meta` (FloatingMeta vs BaseMeta). Wrapping would surface two `meta` slots on the wire (`base.meta` AND `meta`) with no schema rule for which to populate. Inlining keeps a single, unambiguous `meta` field. | intentional |


Only fields matching a pattern listed here are allowed to differ intentionally. New `*_raw` patterns must be added to this table *and* registered in `_RAW_FALLBACK_SUFFIXES` in `docling_serve/grpc/schema_validator.py`. New discriminator-only fields must be registered in `_PYDANTIC_ONLY_DISCRIMINATORS` in the same file.

### `*_raw` Discriminator Contract

For every enum field that has a `*_raw` companion, the pair forms a single
two-field discriminator. There is no third sentinel enum value
(deliberately — see "Why no `*_UNKNOWN` sentinel" below). Consumers
distinguish the three valid states by inspecting both fields:


| Enum tag            | `*_raw` value    | Meaning                                              | Producer must                                                 |
| ------------------- | ---------------- | ---------------------------------------------------- | ------------------------------------------------------------- |
| `*_UNSPECIFIED` (0) | `""` (empty)     | Field was not set on the source.                     | Leave both unset.                                             |
| `*_UNSPECIFIED` (0) | non-empty string | Source had a value the converter does not recognize. | Set tag to 0 *and* populate `*_raw` with the original string. |
| any value `> 0`     | `""` (empty)     | Recognized value.                                    | Set tag only; do not populate `*_raw`.                        |


Producers must never set both a non-zero enum tag *and* a non-empty
`*_raw`. Consumers should treat that combination as a producer bug; if
they need to be defensive, the enum tag wins.

### Why no `*_UNKNOWN` Sentinel

We considered adding a named `*_UNKNOWN` enum value to mark the
"received but not recognized" case explicitly. We deliberately did not.
Rationale:

- Protobuf does not have this idiom. `*_UNSPECIFIED` at tag 0 plus a
companion fallback string is the conventional pattern (used by
Envoy, the gRPC ecosystem, and others). A second sentinel would be
a project-specific convention every client has to learn.
- It would expand every generated language's enum surface
(`DocItemLabel.UNKNOWN`, `CodeLanguageLabel.UNKNOWN`, …), forcing
every exhaustive switch in client code to add a new case for an
abstract concept rather than a real new value.
- It would create a request-side foot-gun: a client could send
`*_UNKNOWN` as input, which has no defined meaning.
- The two-field discriminator above already gives consumers complete,
unambiguous information. The sentinel only saves typing, not
semantics.

Forward compatibility of *new* enum values added by upstream is handled
by the `*_raw` companion when the producer is older than the source
schema, and by protobuf's runtime "unknown enum value" handling
(Python's `UnknownFieldSet`, Go's raw-int passthrough, etc.) when the
consumer is older than the producer. The `*_raw` companion is not a
substitute for either; it is the human-readable carry-along that makes
the unrecognized case observable in logs and clients.

## Wire Schema Extensions

The vendored proto is field-identical with the canonical wire schema this
branch bridges to. That schema mirrors the DoclingDocument v2 JSON schema and
then layers an additive extension set on top of it: shapes the fleet needs on
the wire that the dialect has no way to spell. Removing every extension yields
a document the dialect can express, which is what makes absorption safe.

Only four things differ between the two files, none of them a field: the
package, the file path, the Java options, and the root message name
(`DoclingDocument` here, `Document` there). Every message name, field name,
field number, field type, oneof grouping and enum tag is identical, and the
sync is verified by comparing descriptors, not by reading the diff. Extension
fields are appended after the numbers the Docling mirror occupies, never
interleaved with them, so a Docling addition still lands on the number Docling
chose.

The inventory comes in two halves. First, the mirrored messages that carry
extension fields alongside their mapped ones. These are the rows that matter
to the converter, because absorbing a field here must not disturb the mapped
members sitting next to it.


| Message              | Extension fields                                                                     |
| -------------------- | ------------------------------------------------------------------------------------ |
| `DoclingDocument`    | `source_meta` (`DocumentMeta`), `attachments` (`SubDocumentRef`), `outline` (`OutlineEntry`), `meta_tags` (`MetaTag`), `structured_data` (`StructuredData`), `media` (`MediaMeta`), `changes` (`ChangeRecord`), `anchors` (`NamedAnchor`), `email` (`EmailMeta`), `page_styles` (`PageStyle`), `named_ranges` (`NamedRange`), `pivots` (`PivotSpec`), `claims` (`CollectorClaim`) |
| `DocumentOrigin`     | `web` (`WebMeta`), `source_id`, `mimetype_evidence`, `field_sources` (`FieldSource`)  |
| `ProvenanceItem`     | `time` (`TimeSpan`), `byte_range` (`ByteSpan`), `grid` (`GridCell`), `polygon` (`Point`), `line_range` (`LineSpan`) |
| `TextItemBase`       | `spans` (`InlineSpan`), `admonition_kind`, `label_raw`, `style_name`, `comment_meta` (`CommentMeta`), `shape` (`ShapeMeta`), `footnote_meta` (`FootnoteMeta`), `index_meta` (`IndexMeta`), `raw`, `source_element_name`, `source_namespace` |
| `GroupItem`          | `label_raw`, `sheet` (`SheetMeta`)                                                    |
| `CodeItem`           | `label_raw`, `source_element_name`, `source_namespace`                                |
| `Formatting`         | `monospace`, `small_caps`, `math`, `mark`, `small`, `insertion`, `abbreviation`, `quote`, `overline` |
| `TableCell`          | `value` (`CellValue`, with `CivilDateTime`), `spans` (`InlineSpan`), `align`, `valign` |
| `TableData`          | `columns` (`TableColumnSchema`), `row_prov`, `record_layout` (`RecordLayoutMeta`)      |
| `PageItem`           | `unit`, `quality` (`PageQuality`), `style_name`, `page_label`, `media_size`, `user_unit` |
| `PictureItem`        | `shape` (`ShapeMeta`), `hyperlink`, `target`, `chart` (`ChartMeta`), `source_element_name`, `source_namespace` |
| `ImageRef`           | `size_raw`                                                                            |
| `PictureMeta`        | `accessibility_title`                                                                 |
| `FieldItem`          | `field_name`, `options`, `selected_index`, `span`, `parameters`                        |
| `SourceType`         | `collector` (`CollectorSource`), `generation` (`GenerationSource`)                     |
| `BaseMeta`, `FloatingMeta`, `PictureMeta` | `alternatives` (`AlternativesMetaField`, carrying `Hypothesis` entries) |
| `PictureAnnotation`  | `barcode` (`BarcodeAnnotation`)                                                        |


Second, the messages that exist only to hold extension data. Nothing in them
is mapped, so the converter never reaches them at all:

`AlternativesMetaField`, `BarcodeAnnotation`, `ByteSpan`, `CellValue`,
`ChangeRecord`, `ChartMeta`, `CivilDateTime`, `Classification`,
`CollectorClaim`, `CollectorSource`, `CommentMeta`, `DocumentMeta`,
`DocumentStatistics`, `EmailMeta`, `EmailParty`, `FieldSource`,
`FootnoteMeta`, `FundingAward`, `GenerationSource`, `GridCell`, `GridSpan`,
`Hypothesis`, `Identifier`, `IndexMeta`, `InlineSpan`, `LicenseMeta`,
`LineSpan`, `Margins`, `MediaMeta`, `MetaTag`, `NamedAnchor`, `NamedRange`,
`NamespaceBinding`, `OutlineEntry`, `PageQuality`, `PageStyle`, `PivotSpec`,
`Point`, `Protection`, `RecordLayoutMeta`, `SchemaLocation`, `ShapeMeta`,
`SheetMeta`, `StructuredData`, `SubDocumentRef`, `TableColumnSchema`,
`TimeSpan`, `UserProperty`, `ValueCondition`, `ValueRange`, `WebMeta`.

Four enums serve them and have no dialect counterpart: `ReferenceKind`,
`Alignment`, `VerticalAlignment` and `Trapped`.


### Presence Refinements

Not every canonical change adds a field. Two fields have moved from implicit
to explicit presence at the same number, name and type:

- `PictureClassificationClass.confidence` (2, `double`), so an engine that
  reports no probability leaves it unset rather than claiming zero.
- `TableColumnSchema.name` (1, `string`), so a column the source leaves
  unnamed is distinguishable from one named with the empty string.

The encoding is unchanged in both cases, so a consumer that reads the value
keeps working; what changed is that a deliberately-set zero value now
survives the round trip instead of vanishing. `buf breaking` reports each as
a cardinality change, which is expected and correct to accept here: the
vendored file mirrors the canonical schema, and the mirror is not the place
to argue with it. The converter is unaffected by either. The classification
one is only ever written on export, where the model's own field is a plain
required float and a value is always present; the column schema belongs to a
message the converter never reads.

### Absorption Rule

The Pydantic model is the dialect, and it has no slot for any of this. So:

**`proto_to_docling_document` absorbs every extension field. It does not
invent a model field for one, does not stash one in an extra, and does not
raise on one.** A document that used every extension converts cleanly and
dumps a valid dialect document; the extension data simply is not in the dump.

`docling_document_to_proto` emits no extension field, because the model never
holds one and there is nothing to read. It stays tolerant of them by
construction: it builds messages, it does not consume them.

Absorption is the deliberate posture, not an oversight. The wire carries more
than the dialect can say; the bridge's job is to yield the dialect document
the canonical exporter would emit from the same message, and that document
does not contain these fields. When upstream grows a real model slot for one
of them, the field graduates out of this list into an ordinary mapped field.

The one exception follows.

### The One Active Projection: `pipestream__barcodes`

`PictureAnnotation.barcode` is projected on import rather than absorbed,
because the canonical exporter projects it too and the two exports have to
agree byte for byte.

A picture's typed barcode annotations become a single picture-meta custom
field named `pipestream__barcodes`. Its value is a list with one object per
barcode annotation, in annotation order. Each object carries exactly three
string members, in sorted key order: `format`, `provenance`, `value`.

The rules match `picture_custom_fields` in the canonical renderer
(`src/render/canonical_json_renderer.cpp`) exactly:

- A picture whose proto meta already carries a `pipestream__barcodes` custom
  field keeps the producer's own value; the typed arm never overrides it, it
  only fills a gap.
- A picture that carries barcodes but no proto `meta` still gets a meta on
  import, holding just the projection.
- Custom fields dump in sorted key order, so the projected entry sorts in
  with the rest rather than being appended at the end.
- Every other annotation arm stays ignored on import. `meta` is the export
  contract and the annotation list is deprecated model-side; see
  `_from_table_item`.

The wire never carries an untyped copy of this data. Both sides synthesize the
custom field from the typed arm, which is what keeps them byte-equal.

## Enforcement

- Conversion logic: `docling_core/utils/conversion.py` — both directions:
  `docling_document_to_proto` (Pydantic to proto, `_to_*` helpers) and
  `proto_to_docling_document` (proto to Pydantic, mirror-image `_from_*`
  helpers). The reverse direction honors the `*_raw` two-field discriminator
  contract above on import: tag > 0 maps to the Pydantic enum; tag 0 with a
  non-empty raw falls back to the model's natural value where the strict
  field cannot carry a string (e.g. `CodeLanguageLabel.UNKNOWN`, otherwise
  the field default); both unset yields the model default/None so that
  exclude-none dumps stay byte-identical. `SourceType` entries with an unset
  oneof (foreign extension arms) are skipped silently on import.
  Import also mirrors the class the JSON loading path picks, not just the
  field values: `DoclingDocument.groups` is a `Union[ListGroup, InlineGroup,
  GroupItem]`, and resolving that union from a mapping rewrites a legacy
  `ordered_list` group label to `list` (`ListGroup.patch_ordered`). The
  reverse converter performs the same normalization, so a `GROUP_LABEL_ORDERED_LIST`
  group imports as a `ListGroup`. Reconstructing the deprecated `OrderedList`
  class instead would leave its `ListItem` children parented to a
  non-`ListGroup` node, which the model's `validate_misplaced_list_items`
  then "repairs" by synthesizing replacement groups and renumbering the
  `#/groups/*` and `#/texts/*` arenas. This is a model normalization, not a
  proto divergence: a JSON dump/load round trip of the same document does
  exactly the same thing.
- Startup validation (serve): `docling_serve/grpc/schema_validator.py`
- Tests:
  - `docling-core/test/test_proto_conversion.py` — includes round-trip
    acceptance: `proto_to_docling_document(docling_document_to_proto(doc))`
    must equal the original both by Pydantic equality and by strict
    `export_to_dict()` equality, plus targeted reverse-direction tests for
    the `*_raw` states, CodeItem meta, rich table cells, image data URIs,
    graph data, charspans, and empty-vs-absent lists. Where the model itself
    normalizes on load (legacy `ordered_list` groups, misplaced list items),
    the acceptance bar is instead parity with a JSON dump/load round trip of
    the same document: proto round trip and JSON round trip must agree by
    Pydantic equality and by `export_to_dict()` equality. The extension set
    has its own tests: a proto document that sets every extension field
    imports without error and dumps a document with no trace of them (while
    the mapped members sharing those messages survive intact; the names an
    extension shares with a dialect key are checked positionally, since a
    whole-document key scan cannot judge those), a picture
    carrying typed barcode annotations imports with the
    `pipestream__barcodes` projection fixtured as a JSON fragment so a change
    in key order or key set fails, descriptor-level tests pin the field
    numbers and presence rules the canonical schema chose, and a descriptor
    identity test pins the inventory (141 messages, 14 enums, 749 fields)
    and, when `DOCLING_WIRE_SCHEMA_PROTO` points at the canonical
    `document.proto`, compiles it and compares the two descriptors message
    by message and field by field.
  - `docling-serve/tests/test_schema_validator.py`

## Developer Workflow

When changing the model or IDL:

1. Update protobuf + converter for logical parity.
2. Regenerate stubs with `scripts/gen_proto.py`.
3. Update validator rules only for intentional, documented exceptions.
4. Update tests in `test/test_proto_conversion.py`.
5. Keep this file current if an intentional difference is added/removed.

When the canonical wire schema grows a field, port it here with its number
and name unchanged, regenerate, and verify the sync by comparing descriptors
rather than by reading the diff: message set, field numbers, names, types,
labels, oneof grouping and enum tags must match on both sides. That is what
`test_descriptor_is_identical_to_the_wire_schema` does when run with
`DOCLING_WIRE_SCHEMA_PROTO=/path/to/document.proto`; bump the pinned
inventory counts beside it in the same change. Then decide
the converter's posture: absorbed (the default, and correct whenever the
model has no slot), or projected (only when the canonical exporter projects
it too, and then the projection must match byte for byte).

## Keeping In Sync With Upstream `main`

The full procedure for bringing both `docling-core` and `docling-serve`
gRPC branches up to date with their respective `main` branches —
including how to detect and fix Pydantic↔proto drift mechanically — is
documented in the serve repo at `docs/grpc/upstream_sync_procedure.md`.

The short version for this repo:

1. `git fetch upstream && git merge upstream/main` on the gRPC branch.
2. `uv run python scripts/gen_proto.py` to regenerate stubs.
3. `uv run pytest test/test_proto_conversion.py -q` — must stay green.
4. Run the serve-side schema validator (see the serve procedure doc).
  That is what surfaces new Pydantic fields requiring a proto mirror.
5. For each new Pydantic field the validator reports, add a proto
  field, a converter helper, and a test, following the patterns
   already in `conversion.py` and `test_proto_conversion.py`.
6. For each new enum value, mirror it into the proto enum and the
  conversion map. Old proto enum tags are append-only — never renumber
   or remove tags, even if the upstream Pydantic enum is renamed.