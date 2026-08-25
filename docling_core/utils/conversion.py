from __future__ import annotations

import warnings
from enum import Enum
from typing import Any, Optional

from google.protobuf import struct_pb2

from docling_core.types.doc.base import CoordOrigin
from docling_core.types.doc.document import (
    BaseMeta,
    BaseSource,
    BoundingBox,
    CodeItem,
    CodeMetaField,
    ContentLayer,
    DescriptionAnnotation,
    DescriptionMetaField,
    DoclingDocument,
    DocumentOrigin,
    FieldHeadingItem,
    FieldItem,
    FieldRegionItem,
    FieldValueItem,
    FineRef,
    FloatingMeta,
    Formatting,
    FormItem,
    FormulaItem,
    GraphCell,
    GraphData,
    GraphLink,
    GroupItem,
    ImageRef,
    KeyValueItem,
    ListItem,
    MiscAnnotation,
    MoleculeMetaField,
    PageItem,
    PictureBarChartData,
    PictureClassificationClass,
    PictureClassificationData,
    PictureClassificationMetaField,
    PictureClassificationPrediction,
    PictureItem,
    PictureLineChartData,
    PictureMeta,
    PictureMoleculeData,
    PicturePieChartData,
    PictureScatterChartData,
    PictureStackedBarChartData,
    PictureTabularChartData,
    ProvenanceItem,
    RefItem,
    RichTableCell,
    Script,
    SectionHeaderItem,
    Size,
    SummaryMetaField,
    LanguageMetaField,
    EntitiesMetaField,
    KeywordsMetaField,
    TopicsMetaField,
    EntityMention,
    TableCell,
    TableData,
    TableItem,
    Orientation,
    TabularChartMetaField,
    InlineGroup,
    ListGroup,
    OrderedList,
    TextItem,
    TitleItem,
    TrackSource,
)
from docling_core.types.doc.labels import (
    CodeLanguageLabel,
    DocItemLabel,
    HumanLanguageLabel,
    GraphCellLabel,
    GraphLinkLabel,
    GroupLabel,
)
from docling_core.proto.gen.ai.docling.core.v1 import docling_document_pb2 as pb2


def _enum_value(value: Enum | str | None, mapping: dict[str, int], default: int) -> int:
    if value is None:
        return default
    if isinstance(value, Enum):
        key = value.value
    else:
        key = value
    return mapping.get(str(key), default)


_CONTENT_LAYER_MAP = {
    ContentLayer.BODY.value: pb2.CONTENT_LAYER_BODY,
    ContentLayer.FURNITURE.value: pb2.CONTENT_LAYER_FURNITURE,
    ContentLayer.BACKGROUND.value: pb2.CONTENT_LAYER_BACKGROUND,
    ContentLayer.INVISIBLE.value: pb2.CONTENT_LAYER_INVISIBLE,
    ContentLayer.NOTES.value: pb2.CONTENT_LAYER_NOTES,
}

_GROUP_LABEL_MAP = {
    GroupLabel.UNSPECIFIED.value: pb2.GROUP_LABEL_UNSPECIFIED,
    GroupLabel.LIST.value: pb2.GROUP_LABEL_LIST,
    GroupLabel.ORDERED_LIST.value: pb2.GROUP_LABEL_ORDERED_LIST,
    GroupLabel.CHAPTER.value: pb2.GROUP_LABEL_CHAPTER,
    GroupLabel.SECTION.value: pb2.GROUP_LABEL_SECTION,
    GroupLabel.SHEET.value: pb2.GROUP_LABEL_SHEET,
    GroupLabel.SLIDE.value: pb2.GROUP_LABEL_SLIDE,
    GroupLabel.FORM_AREA.value: pb2.GROUP_LABEL_FORM_AREA,
    GroupLabel.KEY_VALUE_AREA.value: pb2.GROUP_LABEL_KEY_VALUE_AREA,
    GroupLabel.COMMENT_SECTION.value: pb2.GROUP_LABEL_COMMENT_SECTION,
    GroupLabel.INLINE.value: pb2.GROUP_LABEL_INLINE,
    GroupLabel.PICTURE_AREA.value: pb2.GROUP_LABEL_PICTURE_AREA,
}

_DOC_ITEM_LABEL_MAP = {
    DocItemLabel.CAPTION.value: pb2.DOC_ITEM_LABEL_CAPTION,
    DocItemLabel.CHART.value: pb2.DOC_ITEM_LABEL_CHART,
    DocItemLabel.CHECKBOX_SELECTED.value: pb2.DOC_ITEM_LABEL_CHECKBOX_SELECTED,
    DocItemLabel.CHECKBOX_UNSELECTED.value: pb2.DOC_ITEM_LABEL_CHECKBOX_UNSELECTED,
    DocItemLabel.CODE.value: pb2.DOC_ITEM_LABEL_CODE,
    DocItemLabel.DOCUMENT_INDEX.value: pb2.DOC_ITEM_LABEL_DOCUMENT_INDEX,
    DocItemLabel.EMPTY_VALUE.value: pb2.DOC_ITEM_LABEL_EMPTY_VALUE,
    DocItemLabel.FOOTNOTE.value: pb2.DOC_ITEM_LABEL_FOOTNOTE,
    DocItemLabel.FORM.value: pb2.DOC_ITEM_LABEL_FORM,
    DocItemLabel.FORMULA.value: pb2.DOC_ITEM_LABEL_FORMULA,
    DocItemLabel.GRADING_SCALE.value: pb2.DOC_ITEM_LABEL_GRADING_SCALE,
    DocItemLabel.HANDWRITTEN_TEXT.value: pb2.DOC_ITEM_LABEL_HANDWRITTEN_TEXT,
    DocItemLabel.KEY_VALUE_REGION.value: pb2.DOC_ITEM_LABEL_KEY_VALUE_REGION,
    DocItemLabel.LIST_ITEM.value: pb2.DOC_ITEM_LABEL_LIST_ITEM,
    DocItemLabel.PAGE_FOOTER.value: pb2.DOC_ITEM_LABEL_PAGE_FOOTER,
    DocItemLabel.PAGE_HEADER.value: pb2.DOC_ITEM_LABEL_PAGE_HEADER,
    DocItemLabel.PARAGRAPH.value: pb2.DOC_ITEM_LABEL_PARAGRAPH,
    DocItemLabel.PICTURE.value: pb2.DOC_ITEM_LABEL_PICTURE,
    DocItemLabel.REFERENCE.value: pb2.DOC_ITEM_LABEL_REFERENCE,
    DocItemLabel.SECTION_HEADER.value: pb2.DOC_ITEM_LABEL_SECTION_HEADER,
    DocItemLabel.TABLE.value: pb2.DOC_ITEM_LABEL_TABLE,
    DocItemLabel.TEXT.value: pb2.DOC_ITEM_LABEL_TEXT,
    DocItemLabel.TITLE.value: pb2.DOC_ITEM_LABEL_TITLE,
    DocItemLabel.FIELD_REGION.value: pb2.DOC_ITEM_LABEL_FIELD_REGION,
    DocItemLabel.FIELD_HEADING.value: pb2.DOC_ITEM_LABEL_FIELD_HEADING,
    DocItemLabel.FIELD_ITEM.value: pb2.DOC_ITEM_LABEL_FIELD_ITEM,
    DocItemLabel.FIELD_KEY.value: pb2.DOC_ITEM_LABEL_FIELD_KEY,
    DocItemLabel.FIELD_VALUE.value: pb2.DOC_ITEM_LABEL_FIELD_VALUE,
    DocItemLabel.FIELD_HINT.value: pb2.DOC_ITEM_LABEL_FIELD_HINT,
    DocItemLabel.MARKER.value: pb2.DOC_ITEM_LABEL_MARKER,
}


def _to_doc_item_label_enum_and_raw(
    value: Enum | str | None,
) -> tuple[int, Optional[str]]:
    if value is None:
        return pb2.DOC_ITEM_LABEL_UNSPECIFIED, None
    key = value.value if isinstance(value, Enum) else str(value)
    enum_val = _DOC_ITEM_LABEL_MAP.get(str(key))
    if enum_val is None:
        return pb2.DOC_ITEM_LABEL_UNSPECIFIED, str(key)
    return enum_val, None


def _to_code_language_enum_and_raw(
    value: Enum | str | None,
) -> tuple[int, Optional[str]]:
    if value is None:
        return pb2.CODE_LANGUAGE_LABEL_UNSPECIFIED, None
    key = value.value if isinstance(value, Enum) else str(value)
    enum_val = _CODE_LANGUAGE_MAP.get(str(key))
    if enum_val is None:
        return pb2.CODE_LANGUAGE_LABEL_UNSPECIFIED, str(key)
    return enum_val, None

_SCRIPT_MAP = {
    Script.BASELINE.value: pb2.SCRIPT_BASELINE,
    Script.SUB.value: pb2.SCRIPT_SUB,
    Script.SUPER.value: pb2.SCRIPT_SUPER,
}

_GRAPH_CELL_LABEL_MAP = {
    GraphCellLabel.UNSPECIFIED.value: pb2.GRAPH_CELL_LABEL_UNSPECIFIED,
    GraphCellLabel.KEY.value: pb2.GRAPH_CELL_LABEL_KEY,
    GraphCellLabel.VALUE.value: pb2.GRAPH_CELL_LABEL_VALUE,
    GraphCellLabel.CHECKBOX.value: pb2.GRAPH_CELL_LABEL_CHECKBOX,
}

_GRAPH_LINK_LABEL_MAP = {
    GraphLinkLabel.UNSPECIFIED.value: pb2.GRAPH_LINK_LABEL_UNSPECIFIED,
    GraphLinkLabel.TO_VALUE.value: pb2.GRAPH_LINK_LABEL_TO_VALUE,
    GraphLinkLabel.TO_KEY.value: pb2.GRAPH_LINK_LABEL_TO_KEY,
    GraphLinkLabel.TO_PARENT.value: pb2.GRAPH_LINK_LABEL_TO_PARENT,
    GraphLinkLabel.TO_CHILD.value: pb2.GRAPH_LINK_LABEL_TO_CHILD,
}

_COORD_ORIGIN_MAP = {
    CoordOrigin.TOPLEFT.value: pb2.COORD_ORIGIN_TOPLEFT,
    CoordOrigin.BOTTOMLEFT.value: pb2.COORD_ORIGIN_BOTTOMLEFT,
}

_ORIENTATION_MAP = {
    Orientation.ROT_0.value: pb2.ORIENTATION_ROT_0,
    Orientation.ROT_90.value: pb2.ORIENTATION_ROT_90,
    Orientation.ROT_180.value: pb2.ORIENTATION_ROT_180,
    Orientation.ROT_270.value: pb2.ORIENTATION_ROT_270,
}


def _to_orientation_enum_and_raw(
    value: Enum | str | None,
) -> tuple[int, Optional[str]]:
    if value is None:
        return pb2.ORIENTATION_UNSPECIFIED, None
    key = value.value if isinstance(value, Enum) else str(value)
    enum_val = _ORIENTATION_MAP.get(str(key))
    if enum_val is None:
        return pb2.ORIENTATION_UNSPECIFIED, str(key)
    return enum_val, None

_CODE_LANGUAGE_MAP = {
    CodeLanguageLabel.ADA.value: pb2.CODE_LANGUAGE_LABEL_ADA,
    CodeLanguageLabel.AWK.value: pb2.CODE_LANGUAGE_LABEL_AWK,
    CodeLanguageLabel.BASH.value: pb2.CODE_LANGUAGE_LABEL_BASH,
    CodeLanguageLabel.BC.value: pb2.CODE_LANGUAGE_LABEL_BC,
    CodeLanguageLabel.C.value: pb2.CODE_LANGUAGE_LABEL_C,
    CodeLanguageLabel.C_SHARP.value: pb2.CODE_LANGUAGE_LABEL_C_SHARP,
    CodeLanguageLabel.C_PLUS_PLUS.value: pb2.CODE_LANGUAGE_LABEL_C_PLUS_PLUS,
    CodeLanguageLabel.CMAKE.value: pb2.CODE_LANGUAGE_LABEL_CMAKE,
    CodeLanguageLabel.COBOL.value: pb2.CODE_LANGUAGE_LABEL_COBOL,
    CodeLanguageLabel.CSS.value: pb2.CODE_LANGUAGE_LABEL_CSS,
    CodeLanguageLabel.CEYLON.value: pb2.CODE_LANGUAGE_LABEL_CEYLON,
    CodeLanguageLabel.CLOJURE.value: pb2.CODE_LANGUAGE_LABEL_CLOJURE,
    CodeLanguageLabel.CRYSTAL.value: pb2.CODE_LANGUAGE_LABEL_CRYSTAL,
    CodeLanguageLabel.CUDA.value: pb2.CODE_LANGUAGE_LABEL_CUDA,
    CodeLanguageLabel.CYTHON.value: pb2.CODE_LANGUAGE_LABEL_CYTHON,
    CodeLanguageLabel.D.value: pb2.CODE_LANGUAGE_LABEL_D,
    CodeLanguageLabel.DART.value: pb2.CODE_LANGUAGE_LABEL_DART,
    CodeLanguageLabel.DC.value: pb2.CODE_LANGUAGE_LABEL_DC,
    CodeLanguageLabel.DOCKERFILE.value: pb2.CODE_LANGUAGE_LABEL_DOCKERFILE,
    CodeLanguageLabel.ELIXIR.value: pb2.CODE_LANGUAGE_LABEL_ELIXIR,
    CodeLanguageLabel.ERLANG.value: pb2.CODE_LANGUAGE_LABEL_ERLANG,
    CodeLanguageLabel.FORTRAN.value: pb2.CODE_LANGUAGE_LABEL_FORTRAN,
    CodeLanguageLabel.FORTH.value: pb2.CODE_LANGUAGE_LABEL_FORTH,
    CodeLanguageLabel.GO.value: pb2.CODE_LANGUAGE_LABEL_GO,
    CodeLanguageLabel.HTML.value: pb2.CODE_LANGUAGE_LABEL_HTML,
    CodeLanguageLabel.HASKELL.value: pb2.CODE_LANGUAGE_LABEL_HASKELL,
    CodeLanguageLabel.HAXE.value: pb2.CODE_LANGUAGE_LABEL_HAXE,
    CodeLanguageLabel.JAVA.value: pb2.CODE_LANGUAGE_LABEL_JAVA,
    CodeLanguageLabel.JAVASCRIPT.value: pb2.CODE_LANGUAGE_LABEL_JAVASCRIPT,
    CodeLanguageLabel.JSON.value: pb2.CODE_LANGUAGE_LABEL_JSON,
    CodeLanguageLabel.JULIA.value: pb2.CODE_LANGUAGE_LABEL_JULIA,
    CodeLanguageLabel.KOTLIN.value: pb2.CODE_LANGUAGE_LABEL_KOTLIN,
    CodeLanguageLabel.LISP.value: pb2.CODE_LANGUAGE_LABEL_LISP,
    CodeLanguageLabel.LUA.value: pb2.CODE_LANGUAGE_LABEL_LUA,
    CodeLanguageLabel.MATLAB.value: pb2.CODE_LANGUAGE_LABEL_MATLAB,
    CodeLanguageLabel.MOONSCRIPT.value: pb2.CODE_LANGUAGE_LABEL_MOONSCRIPT,
    CodeLanguageLabel.NIM.value: pb2.CODE_LANGUAGE_LABEL_NIM,
    CodeLanguageLabel.OCAML.value: pb2.CODE_LANGUAGE_LABEL_OCAML,
    CodeLanguageLabel.OBJECTIVEC.value: pb2.CODE_LANGUAGE_LABEL_OBJECTIVEC,
    CodeLanguageLabel.OCTAVE.value: pb2.CODE_LANGUAGE_LABEL_OCTAVE,
    CodeLanguageLabel.PHP.value: pb2.CODE_LANGUAGE_LABEL_PHP,
    CodeLanguageLabel.PASCAL.value: pb2.CODE_LANGUAGE_LABEL_PASCAL,
    CodeLanguageLabel.PERL.value: pb2.CODE_LANGUAGE_LABEL_PERL,
    CodeLanguageLabel.PROLOG.value: pb2.CODE_LANGUAGE_LABEL_PROLOG,
    CodeLanguageLabel.PYTHON.value: pb2.CODE_LANGUAGE_LABEL_PYTHON,
    CodeLanguageLabel.RACKET.value: pb2.CODE_LANGUAGE_LABEL_RACKET,
    CodeLanguageLabel.RUBY.value: pb2.CODE_LANGUAGE_LABEL_RUBY,
    CodeLanguageLabel.RUST.value: pb2.CODE_LANGUAGE_LABEL_RUST,
    CodeLanguageLabel.SML.value: pb2.CODE_LANGUAGE_LABEL_SML,
    CodeLanguageLabel.SQL.value: pb2.CODE_LANGUAGE_LABEL_SQL,
    CodeLanguageLabel.SCALA.value: pb2.CODE_LANGUAGE_LABEL_SCALA,
    CodeLanguageLabel.SCHEME.value: pb2.CODE_LANGUAGE_LABEL_SCHEME,
    CodeLanguageLabel.SWIFT.value: pb2.CODE_LANGUAGE_LABEL_SWIFT,
    CodeLanguageLabel.TYPESCRIPT.value: pb2.CODE_LANGUAGE_LABEL_TYPESCRIPT,
    CodeLanguageLabel.UNKNOWN.value: pb2.CODE_LANGUAGE_LABEL_UNKNOWN,
    CodeLanguageLabel.VISUALBASIC.value: pb2.CODE_LANGUAGE_LABEL_VISUALBASIC,
    CodeLanguageLabel.XML.value: pb2.CODE_LANGUAGE_LABEL_XML,
    CodeLanguageLabel.YAML.value: pb2.CODE_LANGUAGE_LABEL_YAML,
    CodeLanguageLabel.LATEX.value: pb2.CODE_LANGUAGE_LABEL_LATEX,
    CodeLanguageLabel.TIKZ.value: pb2.CODE_LANGUAGE_LABEL_TIKZ,
    CodeLanguageLabel.DOCLANG.value: pb2.CODE_LANGUAGE_LABEL_DOCLANG,
}



_HUMAN_LANGUAGE_MAP = {
    HumanLanguageLabel.AA.value: pb2.HUMAN_LANGUAGE_LABEL_AA,
    HumanLanguageLabel.AB.value: pb2.HUMAN_LANGUAGE_LABEL_AB,
    HumanLanguageLabel.AE.value: pb2.HUMAN_LANGUAGE_LABEL_AE,
    HumanLanguageLabel.AF.value: pb2.HUMAN_LANGUAGE_LABEL_AF,
    HumanLanguageLabel.AK.value: pb2.HUMAN_LANGUAGE_LABEL_AK,
    HumanLanguageLabel.AM.value: pb2.HUMAN_LANGUAGE_LABEL_AM,
    HumanLanguageLabel.AN.value: pb2.HUMAN_LANGUAGE_LABEL_AN,
    HumanLanguageLabel.AR.value: pb2.HUMAN_LANGUAGE_LABEL_AR,
    HumanLanguageLabel.AS.value: pb2.HUMAN_LANGUAGE_LABEL_AS,
    HumanLanguageLabel.AV.value: pb2.HUMAN_LANGUAGE_LABEL_AV,
    HumanLanguageLabel.AY.value: pb2.HUMAN_LANGUAGE_LABEL_AY,
    HumanLanguageLabel.AZ.value: pb2.HUMAN_LANGUAGE_LABEL_AZ,
    HumanLanguageLabel.BA.value: pb2.HUMAN_LANGUAGE_LABEL_BA,
    HumanLanguageLabel.BE.value: pb2.HUMAN_LANGUAGE_LABEL_BE,
    HumanLanguageLabel.BG.value: pb2.HUMAN_LANGUAGE_LABEL_BG,
    HumanLanguageLabel.BH.value: pb2.HUMAN_LANGUAGE_LABEL_BH,
    HumanLanguageLabel.BI.value: pb2.HUMAN_LANGUAGE_LABEL_BI,
    HumanLanguageLabel.BM.value: pb2.HUMAN_LANGUAGE_LABEL_BM,
    HumanLanguageLabel.BN.value: pb2.HUMAN_LANGUAGE_LABEL_BN,
    HumanLanguageLabel.BO.value: pb2.HUMAN_LANGUAGE_LABEL_BO,
    HumanLanguageLabel.BR.value: pb2.HUMAN_LANGUAGE_LABEL_BR,
    HumanLanguageLabel.BS.value: pb2.HUMAN_LANGUAGE_LABEL_BS,
    HumanLanguageLabel.CA.value: pb2.HUMAN_LANGUAGE_LABEL_CA,
    HumanLanguageLabel.CE.value: pb2.HUMAN_LANGUAGE_LABEL_CE,
    HumanLanguageLabel.CH.value: pb2.HUMAN_LANGUAGE_LABEL_CH,
    HumanLanguageLabel.CO.value: pb2.HUMAN_LANGUAGE_LABEL_CO,
    HumanLanguageLabel.CR.value: pb2.HUMAN_LANGUAGE_LABEL_CR,
    HumanLanguageLabel.CS.value: pb2.HUMAN_LANGUAGE_LABEL_CS,
    HumanLanguageLabel.CU.value: pb2.HUMAN_LANGUAGE_LABEL_CU,
    HumanLanguageLabel.CV.value: pb2.HUMAN_LANGUAGE_LABEL_CV,
    HumanLanguageLabel.CY.value: pb2.HUMAN_LANGUAGE_LABEL_CY,
    HumanLanguageLabel.DA.value: pb2.HUMAN_LANGUAGE_LABEL_DA,
    HumanLanguageLabel.DE.value: pb2.HUMAN_LANGUAGE_LABEL_DE,
    HumanLanguageLabel.DV.value: pb2.HUMAN_LANGUAGE_LABEL_DV,
    HumanLanguageLabel.DZ.value: pb2.HUMAN_LANGUAGE_LABEL_DZ,
    HumanLanguageLabel.EE.value: pb2.HUMAN_LANGUAGE_LABEL_EE,
    HumanLanguageLabel.EL.value: pb2.HUMAN_LANGUAGE_LABEL_EL,
    HumanLanguageLabel.EN.value: pb2.HUMAN_LANGUAGE_LABEL_EN,
    HumanLanguageLabel.EO.value: pb2.HUMAN_LANGUAGE_LABEL_EO,
    HumanLanguageLabel.ES.value: pb2.HUMAN_LANGUAGE_LABEL_ES,
    HumanLanguageLabel.ET.value: pb2.HUMAN_LANGUAGE_LABEL_ET,
    HumanLanguageLabel.EU.value: pb2.HUMAN_LANGUAGE_LABEL_EU,
    HumanLanguageLabel.FA.value: pb2.HUMAN_LANGUAGE_LABEL_FA,
    HumanLanguageLabel.FF.value: pb2.HUMAN_LANGUAGE_LABEL_FF,
    HumanLanguageLabel.FI.value: pb2.HUMAN_LANGUAGE_LABEL_FI,
    HumanLanguageLabel.FJ.value: pb2.HUMAN_LANGUAGE_LABEL_FJ,
    HumanLanguageLabel.FO.value: pb2.HUMAN_LANGUAGE_LABEL_FO,
    HumanLanguageLabel.FR.value: pb2.HUMAN_LANGUAGE_LABEL_FR,
    HumanLanguageLabel.FY.value: pb2.HUMAN_LANGUAGE_LABEL_FY,
    HumanLanguageLabel.GA.value: pb2.HUMAN_LANGUAGE_LABEL_GA,
    HumanLanguageLabel.GD.value: pb2.HUMAN_LANGUAGE_LABEL_GD,
    HumanLanguageLabel.GL.value: pb2.HUMAN_LANGUAGE_LABEL_GL,
    HumanLanguageLabel.GN.value: pb2.HUMAN_LANGUAGE_LABEL_GN,
    HumanLanguageLabel.GU.value: pb2.HUMAN_LANGUAGE_LABEL_GU,
    HumanLanguageLabel.GV.value: pb2.HUMAN_LANGUAGE_LABEL_GV,
    HumanLanguageLabel.HA.value: pb2.HUMAN_LANGUAGE_LABEL_HA,
    HumanLanguageLabel.HE.value: pb2.HUMAN_LANGUAGE_LABEL_HE,
    HumanLanguageLabel.HI.value: pb2.HUMAN_LANGUAGE_LABEL_HI,
    HumanLanguageLabel.HO.value: pb2.HUMAN_LANGUAGE_LABEL_HO,
    HumanLanguageLabel.HR.value: pb2.HUMAN_LANGUAGE_LABEL_HR,
    HumanLanguageLabel.HT.value: pb2.HUMAN_LANGUAGE_LABEL_HT,
    HumanLanguageLabel.HU.value: pb2.HUMAN_LANGUAGE_LABEL_HU,
    HumanLanguageLabel.HY.value: pb2.HUMAN_LANGUAGE_LABEL_HY,
    HumanLanguageLabel.HZ.value: pb2.HUMAN_LANGUAGE_LABEL_HZ,
    HumanLanguageLabel.IA.value: pb2.HUMAN_LANGUAGE_LABEL_IA,
    HumanLanguageLabel.ID.value: pb2.HUMAN_LANGUAGE_LABEL_ID,
    HumanLanguageLabel.IE.value: pb2.HUMAN_LANGUAGE_LABEL_IE,
    HumanLanguageLabel.IG.value: pb2.HUMAN_LANGUAGE_LABEL_IG,
    HumanLanguageLabel.II.value: pb2.HUMAN_LANGUAGE_LABEL_II,
    HumanLanguageLabel.IK.value: pb2.HUMAN_LANGUAGE_LABEL_IK,
    HumanLanguageLabel.IO.value: pb2.HUMAN_LANGUAGE_LABEL_IO,
    HumanLanguageLabel.IS.value: pb2.HUMAN_LANGUAGE_LABEL_IS,
    HumanLanguageLabel.IT.value: pb2.HUMAN_LANGUAGE_LABEL_IT,
    HumanLanguageLabel.IU.value: pb2.HUMAN_LANGUAGE_LABEL_IU,
    HumanLanguageLabel.JA.value: pb2.HUMAN_LANGUAGE_LABEL_JA,
    HumanLanguageLabel.JV.value: pb2.HUMAN_LANGUAGE_LABEL_JV,
    HumanLanguageLabel.KA.value: pb2.HUMAN_LANGUAGE_LABEL_KA,
    HumanLanguageLabel.KG.value: pb2.HUMAN_LANGUAGE_LABEL_KG,
    HumanLanguageLabel.KI.value: pb2.HUMAN_LANGUAGE_LABEL_KI,
    HumanLanguageLabel.KJ.value: pb2.HUMAN_LANGUAGE_LABEL_KJ,
    HumanLanguageLabel.KK.value: pb2.HUMAN_LANGUAGE_LABEL_KK,
    HumanLanguageLabel.KL.value: pb2.HUMAN_LANGUAGE_LABEL_KL,
    HumanLanguageLabel.KM.value: pb2.HUMAN_LANGUAGE_LABEL_KM,
    HumanLanguageLabel.KN.value: pb2.HUMAN_LANGUAGE_LABEL_KN,
    HumanLanguageLabel.KO.value: pb2.HUMAN_LANGUAGE_LABEL_KO,
    HumanLanguageLabel.KR.value: pb2.HUMAN_LANGUAGE_LABEL_KR,
    HumanLanguageLabel.KS.value: pb2.HUMAN_LANGUAGE_LABEL_KS,
    HumanLanguageLabel.KU.value: pb2.HUMAN_LANGUAGE_LABEL_KU,
    HumanLanguageLabel.KV.value: pb2.HUMAN_LANGUAGE_LABEL_KV,
    HumanLanguageLabel.KW.value: pb2.HUMAN_LANGUAGE_LABEL_KW,
    HumanLanguageLabel.KY.value: pb2.HUMAN_LANGUAGE_LABEL_KY,
    HumanLanguageLabel.LA.value: pb2.HUMAN_LANGUAGE_LABEL_LA,
    HumanLanguageLabel.LB.value: pb2.HUMAN_LANGUAGE_LABEL_LB,
    HumanLanguageLabel.LG.value: pb2.HUMAN_LANGUAGE_LABEL_LG,
    HumanLanguageLabel.LI.value: pb2.HUMAN_LANGUAGE_LABEL_LI,
    HumanLanguageLabel.LN.value: pb2.HUMAN_LANGUAGE_LABEL_LN,
    HumanLanguageLabel.LO.value: pb2.HUMAN_LANGUAGE_LABEL_LO,
    HumanLanguageLabel.LT.value: pb2.HUMAN_LANGUAGE_LABEL_LT,
    HumanLanguageLabel.LU.value: pb2.HUMAN_LANGUAGE_LABEL_LU,
    HumanLanguageLabel.LV.value: pb2.HUMAN_LANGUAGE_LABEL_LV,
    HumanLanguageLabel.MG.value: pb2.HUMAN_LANGUAGE_LABEL_MG,
    HumanLanguageLabel.MH.value: pb2.HUMAN_LANGUAGE_LABEL_MH,
    HumanLanguageLabel.MI.value: pb2.HUMAN_LANGUAGE_LABEL_MI,
    HumanLanguageLabel.MK.value: pb2.HUMAN_LANGUAGE_LABEL_MK,
    HumanLanguageLabel.ML.value: pb2.HUMAN_LANGUAGE_LABEL_ML,
    HumanLanguageLabel.MN.value: pb2.HUMAN_LANGUAGE_LABEL_MN,
    HumanLanguageLabel.MR.value: pb2.HUMAN_LANGUAGE_LABEL_MR,
    HumanLanguageLabel.MS.value: pb2.HUMAN_LANGUAGE_LABEL_MS,
    HumanLanguageLabel.MT.value: pb2.HUMAN_LANGUAGE_LABEL_MT,
    HumanLanguageLabel.MY.value: pb2.HUMAN_LANGUAGE_LABEL_MY,
    HumanLanguageLabel.NA.value: pb2.HUMAN_LANGUAGE_LABEL_NA,
    HumanLanguageLabel.NB.value: pb2.HUMAN_LANGUAGE_LABEL_NB,
    HumanLanguageLabel.ND.value: pb2.HUMAN_LANGUAGE_LABEL_ND,
    HumanLanguageLabel.NE.value: pb2.HUMAN_LANGUAGE_LABEL_NE,
    HumanLanguageLabel.NG.value: pb2.HUMAN_LANGUAGE_LABEL_NG,
    HumanLanguageLabel.NL.value: pb2.HUMAN_LANGUAGE_LABEL_NL,
    HumanLanguageLabel.NN.value: pb2.HUMAN_LANGUAGE_LABEL_NN,
    HumanLanguageLabel.NO.value: pb2.HUMAN_LANGUAGE_LABEL_NO,
    HumanLanguageLabel.NR.value: pb2.HUMAN_LANGUAGE_LABEL_NR,
    HumanLanguageLabel.NV.value: pb2.HUMAN_LANGUAGE_LABEL_NV,
    HumanLanguageLabel.NY.value: pb2.HUMAN_LANGUAGE_LABEL_NY,
    HumanLanguageLabel.OC.value: pb2.HUMAN_LANGUAGE_LABEL_OC,
    HumanLanguageLabel.OJ.value: pb2.HUMAN_LANGUAGE_LABEL_OJ,
    HumanLanguageLabel.OM.value: pb2.HUMAN_LANGUAGE_LABEL_OM,
    HumanLanguageLabel.OR.value: pb2.HUMAN_LANGUAGE_LABEL_OR,
    HumanLanguageLabel.OS.value: pb2.HUMAN_LANGUAGE_LABEL_OS,
    HumanLanguageLabel.PA.value: pb2.HUMAN_LANGUAGE_LABEL_PA,
    HumanLanguageLabel.PI.value: pb2.HUMAN_LANGUAGE_LABEL_PI,
    HumanLanguageLabel.PL.value: pb2.HUMAN_LANGUAGE_LABEL_PL,
    HumanLanguageLabel.PS.value: pb2.HUMAN_LANGUAGE_LABEL_PS,
    HumanLanguageLabel.PT.value: pb2.HUMAN_LANGUAGE_LABEL_PT,
    HumanLanguageLabel.QU.value: pb2.HUMAN_LANGUAGE_LABEL_QU,
    HumanLanguageLabel.RM.value: pb2.HUMAN_LANGUAGE_LABEL_RM,
    HumanLanguageLabel.RN.value: pb2.HUMAN_LANGUAGE_LABEL_RN,
    HumanLanguageLabel.RO.value: pb2.HUMAN_LANGUAGE_LABEL_RO,
    HumanLanguageLabel.RU.value: pb2.HUMAN_LANGUAGE_LABEL_RU,
    HumanLanguageLabel.RW.value: pb2.HUMAN_LANGUAGE_LABEL_RW,
    HumanLanguageLabel.SA.value: pb2.HUMAN_LANGUAGE_LABEL_SA,
    HumanLanguageLabel.SC.value: pb2.HUMAN_LANGUAGE_LABEL_SC,
    HumanLanguageLabel.SD.value: pb2.HUMAN_LANGUAGE_LABEL_SD,
    HumanLanguageLabel.SE.value: pb2.HUMAN_LANGUAGE_LABEL_SE,
    HumanLanguageLabel.SG.value: pb2.HUMAN_LANGUAGE_LABEL_SG,
    HumanLanguageLabel.SH.value: pb2.HUMAN_LANGUAGE_LABEL_SH,
    HumanLanguageLabel.SI.value: pb2.HUMAN_LANGUAGE_LABEL_SI,
    HumanLanguageLabel.SK.value: pb2.HUMAN_LANGUAGE_LABEL_SK,
    HumanLanguageLabel.SL.value: pb2.HUMAN_LANGUAGE_LABEL_SL,
    HumanLanguageLabel.SM.value: pb2.HUMAN_LANGUAGE_LABEL_SM,
    HumanLanguageLabel.SN.value: pb2.HUMAN_LANGUAGE_LABEL_SN,
    HumanLanguageLabel.SO.value: pb2.HUMAN_LANGUAGE_LABEL_SO,
    HumanLanguageLabel.SQ.value: pb2.HUMAN_LANGUAGE_LABEL_SQ,
    HumanLanguageLabel.SR.value: pb2.HUMAN_LANGUAGE_LABEL_SR,
    HumanLanguageLabel.SS.value: pb2.HUMAN_LANGUAGE_LABEL_SS,
    HumanLanguageLabel.ST.value: pb2.HUMAN_LANGUAGE_LABEL_ST,
    HumanLanguageLabel.SU.value: pb2.HUMAN_LANGUAGE_LABEL_SU,
    HumanLanguageLabel.SV.value: pb2.HUMAN_LANGUAGE_LABEL_SV,
    HumanLanguageLabel.SW.value: pb2.HUMAN_LANGUAGE_LABEL_SW,
    HumanLanguageLabel.TA.value: pb2.HUMAN_LANGUAGE_LABEL_TA,
    HumanLanguageLabel.TE.value: pb2.HUMAN_LANGUAGE_LABEL_TE,
    HumanLanguageLabel.TG.value: pb2.HUMAN_LANGUAGE_LABEL_TG,
    HumanLanguageLabel.TH.value: pb2.HUMAN_LANGUAGE_LABEL_TH,
    HumanLanguageLabel.TI.value: pb2.HUMAN_LANGUAGE_LABEL_TI,
    HumanLanguageLabel.TK.value: pb2.HUMAN_LANGUAGE_LABEL_TK,
    HumanLanguageLabel.TL.value: pb2.HUMAN_LANGUAGE_LABEL_TL,
    HumanLanguageLabel.TN.value: pb2.HUMAN_LANGUAGE_LABEL_TN,
    HumanLanguageLabel.TO.value: pb2.HUMAN_LANGUAGE_LABEL_TO,
    HumanLanguageLabel.TR.value: pb2.HUMAN_LANGUAGE_LABEL_TR,
    HumanLanguageLabel.TS.value: pb2.HUMAN_LANGUAGE_LABEL_TS,
    HumanLanguageLabel.TT.value: pb2.HUMAN_LANGUAGE_LABEL_TT,
    HumanLanguageLabel.TW.value: pb2.HUMAN_LANGUAGE_LABEL_TW,
    HumanLanguageLabel.TY.value: pb2.HUMAN_LANGUAGE_LABEL_TY,
    HumanLanguageLabel.UG.value: pb2.HUMAN_LANGUAGE_LABEL_UG,
    HumanLanguageLabel.UK.value: pb2.HUMAN_LANGUAGE_LABEL_UK,
    HumanLanguageLabel.UR.value: pb2.HUMAN_LANGUAGE_LABEL_UR,
    HumanLanguageLabel.UZ.value: pb2.HUMAN_LANGUAGE_LABEL_UZ,
    HumanLanguageLabel.VE.value: pb2.HUMAN_LANGUAGE_LABEL_VE,
    HumanLanguageLabel.VI.value: pb2.HUMAN_LANGUAGE_LABEL_VI,
    HumanLanguageLabel.VO.value: pb2.HUMAN_LANGUAGE_LABEL_VO,
    HumanLanguageLabel.WA.value: pb2.HUMAN_LANGUAGE_LABEL_WA,
    HumanLanguageLabel.WO.value: pb2.HUMAN_LANGUAGE_LABEL_WO,
    HumanLanguageLabel.XH.value: pb2.HUMAN_LANGUAGE_LABEL_XH,
    HumanLanguageLabel.YI.value: pb2.HUMAN_LANGUAGE_LABEL_YI,
    HumanLanguageLabel.YO.value: pb2.HUMAN_LANGUAGE_LABEL_YO,
    HumanLanguageLabel.ZA.value: pb2.HUMAN_LANGUAGE_LABEL_ZA,
    HumanLanguageLabel.ZH.value: pb2.HUMAN_LANGUAGE_LABEL_ZH,
    HumanLanguageLabel.ZU.value: pb2.HUMAN_LANGUAGE_LABEL_ZU,
}


def _to_human_language_enum_and_raw(
    value: Enum | str | None,
) -> tuple[int, Optional[str]]:
    if value is None:
        return pb2.HUMAN_LANGUAGE_LABEL_UNSPECIFIED, None
    key = value.value if isinstance(value, Enum) else str(value)
    enum_val = _HUMAN_LANGUAGE_MAP.get(str(key))
    if enum_val is None:
        return pb2.HUMAN_LANGUAGE_LABEL_UNSPECIFIED, str(key)
    return enum_val, None

def _to_ref(ref: Optional[RefItem]) -> Optional[pb2.RefItem]:
    if ref is None:
        return None
    return pb2.RefItem(ref=ref.cref)


def _to_struct_value(value: Any) -> struct_pb2.Value:
    msg = struct_pb2.Value()
    if value is None:
        msg.null_value = struct_pb2.NullValue.NULL_VALUE
        return msg
    if isinstance(value, bool):
        msg.bool_value = value
        return msg
    if isinstance(value, (int, float)):
        msg.number_value = float(value)
        return msg
    if isinstance(value, str):
        msg.string_value = value
        return msg
    if isinstance(value, dict):
        struct_msg = struct_pb2.Struct()
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError("Custom field keys must be strings.")
            struct_msg.fields[key].CopyFrom(_to_struct_value(item))
        msg.struct_value.CopyFrom(struct_msg)
        return msg
    if isinstance(value, (list, tuple)):
        list_msg = struct_pb2.ListValue()
        for item in value:
            list_msg.values.add().CopyFrom(_to_struct_value(item))
        msg.list_value.CopyFrom(list_msg)
        return msg
    raise TypeError(f"Unsupported custom field type: {type(value)!r}")


def _apply_custom_fields(msg: Any, model: Any) -> None:
    if model is None or not hasattr(model, "get_custom_part"):
        return
    custom = model.get_custom_part()
    if not custom:
        return
    for key, value in custom.items():
        msg.custom_fields[key].CopyFrom(_to_struct_value(value))


def _to_fine_ref(ref: FineRef) -> pb2.FineRef:
    msg = pb2.FineRef(ref=ref.cref)
    if ref.range is not None:
        msg.range.CopyFrom(pb2.IntSpan(start=int(ref.range[0]), end=int(ref.range[1])))
    return msg


def _to_track_source(source: TrackSource) -> pb2.TrackSource:
    # `source.kind` is the Pydantic discriminator (Literal["track"]).
    # On the wire, the SourceType oneof tag selects the variant — no need
    # to also serialize the discriminator string.
    msg = pb2.TrackSource(start_time=source.start_time, end_time=source.end_time)
    if source.identifier is not None:
        msg.identifier = source.identifier
    if source.voice is not None:
        msg.voice = source.voice
    return msg


def _to_source_type(source: BaseSource) -> pb2.SourceType:
    msg = pb2.SourceType()
    if isinstance(source, TrackSource):
        msg.track.CopyFrom(_to_track_source(source))
    else:
        raise TypeError(f"Unsupported source type: {type(source)!r}")
    return msg



def _to_language_meta(meta: LanguageMetaField) -> pb2.LanguageMetaField:
    enum_val, raw = _to_human_language_enum_and_raw(meta.code)
    msg = pb2.LanguageMetaField(code=enum_val)
    if raw is not None:
        msg.code_raw = raw
    if meta.confidence is not None:
        msg.confidence = meta.confidence
    if meta.created_by is not None:
        msg.created_by = str(meta.created_by)
    _apply_custom_fields(msg, meta)
    return msg


def _to_entity_mention(mention: EntityMention) -> pb2.EntityMention:
    msg = pb2.EntityMention(text=mention.text)
    if mention.orig is not None:
        msg.orig = mention.orig
    if mention.label is not None:
        msg.label = mention.label
    if mention.charspan is not None:
        msg.charspan.CopyFrom(
            pb2.IntSpan(start=int(mention.charspan[0]), end=int(mention.charspan[1]))
        )
    if mention.confidence is not None:
        msg.confidence = mention.confidence
    if mention.created_by is not None:
        msg.created_by = str(mention.created_by)
    _apply_custom_fields(msg, mention)
    return msg


def _to_entities_meta(meta: EntitiesMetaField) -> pb2.EntitiesMetaField:
    msg = pb2.EntitiesMetaField()
    msg.mentions.extend([_to_entity_mention(m) for m in meta.mentions])
    _apply_custom_fields(msg, meta)
    return msg


def _to_keywords_meta(meta: KeywordsMetaField) -> pb2.KeywordsMetaField:
    msg = pb2.KeywordsMetaField()
    msg.values.extend(meta.values)
    _apply_custom_fields(msg, meta)
    return msg


def _to_topics_meta(meta: TopicsMetaField) -> pb2.TopicsMetaField:
    msg = pb2.TopicsMetaField()
    msg.values.extend(meta.values)
    _apply_custom_fields(msg, meta)
    return msg


def _apply_inherited_meta_fields(msg: Any, meta: BaseMeta) -> None:
    if meta.summary is not None:
        msg.summary.CopyFrom(_to_summary_meta(meta.summary))
    if meta.language is not None:
        msg.language.CopyFrom(_to_language_meta(meta.language))
    if meta.entities is not None:
        msg.entities.CopyFrom(_to_entities_meta(meta.entities))
    if meta.keywords is not None:
        msg.keywords.CopyFrom(_to_keywords_meta(meta.keywords))
    if meta.topics is not None:
        msg.topics.CopyFrom(_to_topics_meta(meta.topics))

def _to_summary_meta(meta: SummaryMetaField) -> pb2.SummaryMetaField:
    msg = pb2.SummaryMetaField(text=meta.text)
    if meta.confidence is not None:
        msg.confidence = meta.confidence
    if meta.created_by is not None:
        msg.created_by = str(meta.created_by)
    _apply_custom_fields(msg, meta)
    return msg


def _to_base_meta(meta: Optional[BaseMeta]) -> Optional[pb2.BaseMeta]:
    if meta is None:
        return None
    if (
        meta.summary is None
        and meta.language is None
        and meta.entities is None
        and meta.keywords is None
        and meta.topics is None
        and not meta.get_custom_part()
    ):
        return None
    msg = pb2.BaseMeta()
    _apply_inherited_meta_fields(msg, meta)
    _apply_custom_fields(msg, meta)
    return msg


def _to_description_meta(meta: DescriptionMetaField) -> pb2.DescriptionMetaField:
    msg = pb2.DescriptionMetaField(text=meta.text)
    if meta.confidence is not None:
        msg.confidence = meta.confidence
    if meta.created_by is not None:
        msg.created_by = str(meta.created_by)
    _apply_custom_fields(msg, meta)
    return msg


def _to_picture_classification_prediction(
    pred: PictureClassificationPrediction,
) -> pb2.PictureClassificationPrediction:
    msg = pb2.PictureClassificationPrediction(class_name=pred.class_name)
    if pred.confidence is not None:
        msg.confidence = pred.confidence
    if pred.created_by is not None:
        msg.created_by = str(pred.created_by)
    _apply_custom_fields(msg, pred)
    return msg


def _to_picture_classification_meta(
    meta: PictureClassificationMetaField,
) -> pb2.PictureClassificationMetaField:
    msg = pb2.PictureClassificationMetaField()
    msg.predictions.extend(
        [_to_picture_classification_prediction(p) for p in meta.predictions]
    )
    _apply_custom_fields(msg, meta)
    return msg


def _to_molecule_meta(meta: MoleculeMetaField) -> pb2.MoleculeMetaField:
    msg = pb2.MoleculeMetaField(smi=meta.smi)
    if meta.confidence is not None:
        msg.confidence = meta.confidence
    if meta.created_by is not None:
        msg.created_by = str(meta.created_by)
    _apply_custom_fields(msg, meta)
    return msg


def _to_tabular_chart_meta(meta: TabularChartMetaField) -> pb2.TabularChartMetaField:
    msg = pb2.TabularChartMetaField()
    if meta.confidence is not None:
        msg.confidence = meta.confidence
    if meta.created_by is not None:
        msg.created_by = str(meta.created_by)
    if meta.title is not None:
        msg.title = meta.title
    msg.chart_data.CopyFrom(_to_table_data(meta.chart_data))
    _apply_custom_fields(msg, meta)
    return msg


def _to_code_meta(meta: CodeMetaField) -> pb2.CodeMetaField:
    enum_val, raw = _to_code_language_enum_and_raw(meta.language)
    msg = pb2.CodeMetaField(text=meta.text, language=enum_val)
    if raw is not None:
        msg.language_raw = raw
    if meta.confidence is not None:
        msg.confidence = meta.confidence
    if meta.created_by is not None:
        msg.created_by = str(meta.created_by)
    _apply_custom_fields(msg, meta)
    return msg


def _to_floating_meta(meta: Optional[FloatingMeta]) -> Optional[pb2.FloatingMeta]:
    if meta is None:
        return None
    msg = pb2.FloatingMeta()
    _apply_inherited_meta_fields(msg, meta)
    if meta.description is not None:
        msg.description.CopyFrom(_to_description_meta(meta.description))
    _apply_custom_fields(msg, meta)
    return msg


def _to_picture_meta(meta: Optional[PictureMeta]) -> Optional[pb2.PictureMeta]:
    if meta is None:
        return None
    msg = pb2.PictureMeta()
    _apply_inherited_meta_fields(msg, meta)
    if meta.description is not None:
        msg.description.CopyFrom(_to_description_meta(meta.description))
    if meta.classification is not None:
        msg.classification.CopyFrom(
            _to_picture_classification_meta(meta.classification)
        )
    if meta.molecule is not None:
        msg.molecule.CopyFrom(_to_molecule_meta(meta.molecule))
    if meta.tabular_chart is not None:
        msg.tabular_chart.CopyFrom(_to_tabular_chart_meta(meta.tabular_chart))
    if meta.code is not None:
        msg.code.CopyFrom(_to_code_meta(meta.code))
    _apply_custom_fields(msg, meta)
    return msg


def _to_float_pair(pair: tuple) -> pb2.FloatPair:
    return pb2.FloatPair(first=float(pair[0]), second=float(pair[1]))


def _to_string_int_pair(pair: tuple) -> pb2.StringIntPair:
    return pb2.StringIntPair(key=str(pair[0]), value=int(pair[1]))


def _to_picture_annotation(annotation) -> pb2.PictureAnnotation:
    """Convert a Pydantic picture annotation to its proto oneof wrapper."""
    msg = pb2.PictureAnnotation()
    if isinstance(annotation, DescriptionAnnotation):
        msg.description.CopyFrom(
            pb2.DescriptionAnnotation(
                kind=annotation.kind,
                text=annotation.text,
                provenance=annotation.provenance,
            )
        )
    elif isinstance(annotation, MiscAnnotation):
        misc = pb2.MiscAnnotation(kind=annotation.kind)
        if annotation.content:
            struct = struct_pb2.Struct()
            for k, v in annotation.content.items():
                struct.fields[str(k)].CopyFrom(_to_struct_value(v))
            misc.content.CopyFrom(struct)
        msg.misc.CopyFrom(misc)
    elif isinstance(annotation, PictureClassificationData):
        msg.classification.CopyFrom(
            pb2.PictureClassificationData(
                kind=annotation.kind,
                provenance=annotation.provenance,
                predicted_classes=[
                    pb2.PictureClassificationClass(
                        class_name=c.class_name,
                        confidence=c.confidence,
                    )
                    for c in annotation.predicted_classes
                ],
            )
        )
    elif isinstance(annotation, PictureMoleculeData):
        mol = pb2.PictureMoleculeData(
            kind=annotation.kind,
            smi=annotation.smi,
            confidence=annotation.confidence,
            class_name=annotation.class_name,
            provenance=annotation.provenance,
        )
        if annotation.segmentation:
            mol.segmentation.extend(
                [_to_float_pair(p) for p in annotation.segmentation]
            )
        msg.molecule.CopyFrom(mol)
    elif isinstance(annotation, PictureTabularChartData):
        msg.tabular_chart.CopyFrom(
            pb2.PictureTabularChartData(
                kind=annotation.kind,
                title=annotation.title,
                chart_data=_to_table_data(annotation.chart_data),
            )
        )
    elif isinstance(annotation, PictureLineChartData):
        msg.line_chart.CopyFrom(
            pb2.PictureLineChartData(
                kind=annotation.kind,
                title=annotation.title,
                x_axis_label=annotation.x_axis_label,
                y_axis_label=annotation.y_axis_label,
                lines=[
                    pb2.ChartLine(
                        label=line.label,
                        values=[_to_float_pair(v) for v in line.values],
                    )
                    for line in annotation.lines
                ],
            )
        )
    elif isinstance(annotation, PictureBarChartData):
        msg.bar_chart.CopyFrom(
            pb2.PictureBarChartData(
                kind=annotation.kind,
                title=annotation.title,
                x_axis_label=annotation.x_axis_label,
                y_axis_label=annotation.y_axis_label,
                bars=[
                    pb2.ChartBar(label=bar.label, values=bar.values)
                    for bar in annotation.bars
                ],
            )
        )
    elif isinstance(annotation, PictureStackedBarChartData):
        msg.stacked_bar_chart.CopyFrom(
            pb2.PictureStackedBarChartData(
                kind=annotation.kind,
                title=annotation.title,
                x_axis_label=annotation.x_axis_label,
                y_axis_label=annotation.y_axis_label,
                stacked_bars=[
                    pb2.ChartStackedBar(
                        label=list(sb.label),
                        values=[_to_string_int_pair(v) for v in sb.values],
                    )
                    for sb in annotation.stacked_bars
                ],
            )
        )
    elif isinstance(annotation, PicturePieChartData):
        msg.pie_chart.CopyFrom(
            pb2.PicturePieChartData(
                kind=annotation.kind,
                title=annotation.title,
                slices=[
                    pb2.ChartSlice(label=s.label, value=s.value)
                    for s in annotation.slices
                ],
            )
        )
    elif isinstance(annotation, PictureScatterChartData):
        msg.scatter_chart.CopyFrom(
            pb2.PictureScatterChartData(
                kind=annotation.kind,
                title=annotation.title,
                x_axis_label=annotation.x_axis_label,
                y_axis_label=annotation.y_axis_label,
                points=[
                    pb2.ChartPoint(value=_to_float_pair(p.value))
                    for p in annotation.points
                ],
            )
        )
    else:
        raise TypeError(f"Unsupported picture annotation type: {type(annotation)!r}")
    return msg


def _to_table_annotation(annotation) -> pb2.TableAnnotation:
    """Convert a Pydantic table annotation to its proto oneof wrapper."""
    msg = pb2.TableAnnotation()
    if isinstance(annotation, DescriptionAnnotation):
        msg.description.CopyFrom(
            pb2.DescriptionAnnotation(
                kind=annotation.kind,
                text=annotation.text,
                provenance=annotation.provenance,
            )
        )
    elif isinstance(annotation, MiscAnnotation):
        misc = pb2.MiscAnnotation(kind=annotation.kind)
        if annotation.content:
            struct = struct_pb2.Struct()
            for k, v in annotation.content.items():
                struct.fields[str(k)].CopyFrom(_to_struct_value(v))
            misc.content.CopyFrom(struct)
        msg.misc.CopyFrom(misc)
    else:
        raise TypeError(f"Unsupported table annotation type: {type(annotation)!r}")
    return msg


def _annotations_from_floating_meta(
    meta: Optional[FloatingMeta],
) -> list[DescriptionAnnotation]:
    """Build table annotation list from meta (avoids deprecated item.annotations)."""
    if meta is None:
        return []
    out: list[DescriptionAnnotation] = []
    if meta.description is not None:
        out.append(
            DescriptionAnnotation(
                kind="description",
                text=meta.description.text,
                provenance=meta.description.created_by or "",
            )
        )
    return out


def _annotations_from_picture_meta(
    meta: Optional[PictureMeta],
) -> list[
    DescriptionAnnotation
    | PictureClassificationData
    | PictureMoleculeData
    | PictureTabularChartData
]:
    """Build picture annotation list from meta (avoids deprecated item.annotations)."""
    if meta is None:
        return []
    out: list[
        DescriptionAnnotation
        | PictureClassificationData
        | PictureMoleculeData
        | PictureTabularChartData
    ] = []
    if meta.description is not None:
        out.append(
            DescriptionAnnotation(
                kind="description",
                text=meta.description.text,
                provenance=meta.description.created_by or "",
            )
        )
    if meta.classification is not None:
        out.append(
            PictureClassificationData(
                kind="classification",
                provenance="",
                predicted_classes=[
                    PictureClassificationClass(
                        class_name=p.class_name,
                        confidence=getattr(p, "confidence", 0.0) or 0.0,
                    )
                    for p in meta.classification.predictions
                ],
            )
        )
    if meta.molecule is not None:
        out.append(
            PictureMoleculeData(
                kind="molecule_data",
                smi=meta.molecule.smi,
                confidence=meta.molecule.confidence or 0.0,
                class_name="",
                segmentation=[],
                provenance=meta.molecule.created_by or "",
            )
        )
    if meta.tabular_chart is not None:
        out.append(
            PictureTabularChartData(
                kind="tabular_chart_data",
                title=meta.tabular_chart.title or "",
                chart_data=meta.tabular_chart.chart_data,
            )
        )
    return out


def _to_formatting(fmt: Optional[Formatting]) -> Optional[pb2.Formatting]:
    if fmt is None:
        return None
    msg = pb2.Formatting(
        bold=fmt.bold,
        italic=fmt.italic,
        underline=fmt.underline,
        strikethrough=fmt.strikethrough,
    )
    if fmt.script is not None:
        key = fmt.script.value if isinstance(fmt.script, Enum) else str(fmt.script)
        enum_val = _SCRIPT_MAP.get(str(key))
        if enum_val is None:
            msg.script = pb2.SCRIPT_UNSPECIFIED
            msg.script_raw = str(key)
        else:
            msg.script = enum_val
    return msg


def _to_bbox(bbox: Optional[BoundingBox]) -> Optional[pb2.BoundingBox]:
    if bbox is None:
        return None
    msg = pb2.BoundingBox(l=bbox.l, t=bbox.t, r=bbox.r, b=bbox.b)
    if bbox.coord_origin is not None:
        key = (
            bbox.coord_origin.value
            if isinstance(bbox.coord_origin, Enum)
            else str(bbox.coord_origin)
        )
        enum_val = _COORD_ORIGIN_MAP.get(str(key))
        if enum_val is None:
            msg.coord_origin = pb2.COORD_ORIGIN_UNSPECIFIED
            msg.coord_origin_raw = str(key)
        else:
            msg.coord_origin = enum_val
    return msg


def _to_size(size: Size) -> pb2.Size:
    return pb2.Size(width=size.width, height=size.height)


def _to_image_ref(image: Optional[ImageRef]) -> Optional[pb2.ImageRef]:
    if image is None:
        return None
    msg = pb2.ImageRef(
        mimetype=image.mimetype,
        dpi=image.dpi,
        size=_to_size(image.size),
        uri=str(image.uri),
    )
    return msg


def _to_provenance_item(prov: ProvenanceItem) -> pb2.ProvenanceItem:
    msg = pb2.ProvenanceItem(page_no=prov.page_no)
    msg.bbox.CopyFrom(_to_bbox(prov.bbox))
    msg.charspan.CopyFrom(
        pb2.IntSpan(start=int(prov.charspan[0]), end=int(prov.charspan[1]))
    )
    return msg


def _to_text_item_base(item: TextItem) -> pb2.TextItemBase:
    msg = pb2.TextItemBase(
        self_ref=item.self_ref,
        content_layer=_enum_value(
            item.content_layer, _CONTENT_LAYER_MAP, pb2.CONTENT_LAYER_UNSPECIFIED
        ),
        label=_enum_value(
            item.label, _DOC_ITEM_LABEL_MAP, pb2.DOC_ITEM_LABEL_UNSPECIFIED
        ),
        orig=item.orig,
        text=item.text,
    )
    if item.parent is not None:
        msg.parent.CopyFrom(_to_ref(item.parent))
    if item.children:
        msg.children.extend([_to_ref(child) for child in item.children])
    meta = _to_base_meta(item.meta)
    if meta is not None:
        msg.meta.CopyFrom(meta)
    if item.prov:
        msg.prov.extend([_to_provenance_item(p) for p in item.prov])
    if item.source:
        msg.source.extend([_to_source_type(src) for src in item.source])
    if item.comments:
        msg.comments.extend([_to_fine_ref(ref) for ref in item.comments])
    fmt = _to_formatting(item.formatting)
    if fmt is not None:
        msg.formatting.CopyFrom(fmt)
    if item.hyperlink is not None:
        msg.hyperlink = str(item.hyperlink)
    return msg


def _to_title_item(item: TitleItem) -> pb2.TitleItem:
    return pb2.TitleItem(base=_to_text_item_base(item))


def _to_section_header_item(item: SectionHeaderItem) -> pb2.SectionHeaderItem:
    return pb2.SectionHeaderItem(base=_to_text_item_base(item), level=item.level)


def _to_field_heading_item(item: FieldHeadingItem) -> pb2.FieldHeadingItem:
    return pb2.FieldHeadingItem(base=_to_text_item_base(item), level=item.level)


def _to_field_value_item(item: FieldValueItem) -> pb2.FieldValueItem:
    return pb2.FieldValueItem(base=_to_text_item_base(item), kind=item.kind)


def _to_list_item(item: ListItem) -> pb2.ListItem:
    msg = pb2.ListItem(base=_to_text_item_base(item), enumerated=item.enumerated)
    if item.marker is not None:
        msg.marker = item.marker
    return msg


def _to_code_item(item: CodeItem) -> pb2.CodeItem:
    msg = pb2.CodeItem(
        self_ref=item.self_ref,
        content_layer=_enum_value(
            item.content_layer, _CONTENT_LAYER_MAP, pb2.CONTENT_LAYER_UNSPECIFIED
        ),
        label=_enum_value(
            item.label, _DOC_ITEM_LABEL_MAP, pb2.DOC_ITEM_LABEL_UNSPECIFIED
        ),
        orig=item.orig,
        text=item.text,
    )
    if item.parent is not None:
        msg.parent.CopyFrom(_to_ref(item.parent))
    if item.children:
        msg.children.extend([_to_ref(child) for child in item.children])
    meta = _to_floating_meta(item.meta)
    if meta is not None:
        msg.meta.CopyFrom(meta)
    if item.prov:
        msg.prov.extend([_to_provenance_item(p) for p in item.prov])
    fmt = _to_formatting(item.formatting)
    if fmt is not None:
        msg.formatting.CopyFrom(fmt)
    if item.hyperlink is not None:
        msg.hyperlink = str(item.hyperlink)
    if item.source:
        msg.source.extend([_to_source_type(src) for src in item.source])
    if item.comments:
        msg.comments.extend([_to_fine_ref(ref) for ref in item.comments])
    if item.captions:
        msg.captions.extend([_to_ref(ref) for ref in item.captions])
    if item.references:
        msg.references.extend([_to_ref(ref) for ref in item.references])
    if item.footnotes:
        msg.footnotes.extend([_to_ref(ref) for ref in item.footnotes])
    image = _to_image_ref(item.image)
    if image is not None:
        msg.image.CopyFrom(image)
    if item.code_language is not None:
        enum_val, raw = _to_code_language_enum_and_raw(item.code_language)
        msg.code_language = enum_val
        if raw is not None:
            msg.code_language_raw = raw
    return msg


def _to_formula_item(item: FormulaItem) -> pb2.FormulaItem:
    return pb2.FormulaItem(base=_to_text_item_base(item))


def _to_text_item(item: TextItem) -> pb2.TextItem:
    return pb2.TextItem(base=_to_text_item_base(item))


def _to_base_text_item(item: TextItem) -> pb2.BaseTextItem:
    msg = pb2.BaseTextItem()
    if isinstance(item, TitleItem):
        msg.title.CopyFrom(_to_title_item(item))
    elif isinstance(item, SectionHeaderItem):
        msg.section_header.CopyFrom(_to_section_header_item(item))
    elif isinstance(item, FieldHeadingItem):
        msg.field_heading.CopyFrom(_to_field_heading_item(item))
    elif isinstance(item, FieldValueItem):
        msg.field_value.CopyFrom(_to_field_value_item(item))
    elif isinstance(item, ListItem):
        msg.list_item.CopyFrom(_to_list_item(item))
    elif isinstance(item, CodeItem):
        msg.code.CopyFrom(_to_code_item(item))
    elif isinstance(item, FormulaItem):
        msg.formula.CopyFrom(_to_formula_item(item))
    else:
        msg.text.CopyFrom(_to_text_item(item))
    return msg


def _to_table_cell(cell: TableCell | RichTableCell) -> pb2.TableCell:
    msg = pb2.TableCell(
        row_span=cell.row_span,
        col_span=cell.col_span,
        start_row_offset_idx=cell.start_row_offset_idx,
        end_row_offset_idx=cell.end_row_offset_idx,
        start_col_offset_idx=cell.start_col_offset_idx,
        end_col_offset_idx=cell.end_col_offset_idx,
        text=cell.text,
        column_header=cell.column_header,
        row_header=cell.row_header,
        row_section=cell.row_section,
        fillable=cell.fillable,
    )
    bbox = _to_bbox(cell.bbox)
    if bbox is not None:
        msg.bbox.CopyFrom(bbox)
    if getattr(cell, "ref", None) is not None:
        msg.ref.CopyFrom(_to_ref(cell.ref))
    return msg


def _to_table_data(data: TableData) -> pb2.TableData:
    orientation_enum, orientation_raw = _to_orientation_enum_and_raw(data.orientation)
    msg = pb2.TableData(
        num_rows=data.num_rows,
        num_cols=data.num_cols,
        orientation=orientation_enum,
    )
    if orientation_raw is not None:
        msg.orientation_raw = orientation_raw
    if data.table_cells:
        msg.table_cells.extend([_to_table_cell(cell) for cell in data.table_cells])
    for row in data.grid:
        row_msg = pb2.TableRow()
        row_msg.cells.extend([_to_table_cell(cell) for cell in row])
        msg.grid.append(row_msg)
    return msg


def _to_table_item_base(item: TableItem) -> pb2.TableItem:
    label_enum, label_raw = _to_doc_item_label_enum_and_raw(item.label)
    msg = pb2.TableItem(
        self_ref=item.self_ref,
        content_layer=_enum_value(
            item.content_layer, _CONTENT_LAYER_MAP, pb2.CONTENT_LAYER_UNSPECIFIED
        ),
        label=label_enum,
    )
    if label_raw is not None:
        msg.label_raw = label_raw
    if item.parent is not None:
        msg.parent.CopyFrom(_to_ref(item.parent))
    if item.children:
        msg.children.extend([_to_ref(ref) for ref in item.children])
    meta = _to_floating_meta(item.meta)
    if meta is not None:
        msg.meta.CopyFrom(meta)
    if item.prov:
        msg.prov.extend([_to_provenance_item(p) for p in item.prov])
    if item.source:
        msg.source.extend([_to_source_type(src) for src in item.source])
    if item.comments:
        msg.comments.extend([_to_fine_ref(ref) for ref in item.comments])
    if item.captions:
        msg.captions.extend([_to_ref(ref) for ref in item.captions])
    if item.references:
        msg.references.extend([_to_ref(ref) for ref in item.references])
    if item.footnotes:
        msg.footnotes.extend([_to_ref(ref) for ref in item.footnotes])
    image = _to_image_ref(item.image)
    if image is not None:
        msg.image.CopyFrom(image)
    return msg


def _to_table_item(item: TableItem) -> pb2.TableItem:
    msg = _to_table_item_base(item)
    msg.data.CopyFrom(_to_table_data(item.data))
    for ann in _annotations_from_floating_meta(item.meta):
        msg.annotations.append(_to_table_annotation(ann))
    return msg


def _to_picture_item(item: PictureItem) -> pb2.PictureItem:
    label_enum, label_raw = _to_doc_item_label_enum_and_raw(item.label)
    msg = pb2.PictureItem(
        self_ref=item.self_ref,
        content_layer=_enum_value(
            item.content_layer, _CONTENT_LAYER_MAP, pb2.CONTENT_LAYER_UNSPECIFIED
        ),
        label=label_enum,
    )
    if label_raw is not None:
        msg.label_raw = label_raw
    if item.parent is not None:
        msg.parent.CopyFrom(_to_ref(item.parent))
    if item.children:
        msg.children.extend([_to_ref(ref) for ref in item.children])
    meta = _to_picture_meta(item.meta)
    if meta is not None:
        msg.meta.CopyFrom(meta)
    if item.prov:
        msg.prov.extend([_to_provenance_item(p) for p in item.prov])
    if item.source:
        msg.source.extend([_to_source_type(src) for src in item.source])
    if item.comments:
        msg.comments.extend([_to_fine_ref(ref) for ref in item.comments])
    if item.captions:
        msg.captions.extend([_to_ref(ref) for ref in item.captions])
    if item.references:
        msg.references.extend([_to_ref(ref) for ref in item.references])
    if item.footnotes:
        msg.footnotes.extend([_to_ref(ref) for ref in item.footnotes])
    image = _to_image_ref(item.image)
    if image is not None:
        msg.image.CopyFrom(image)
    for ann in _annotations_from_picture_meta(item.meta):
        msg.annotations.append(_to_picture_annotation(ann))
    return msg


def _to_graph_cell(cell: GraphCell) -> pb2.GraphCell:
    msg = pb2.GraphCell(
        label=_enum_value(
            cell.label, _GRAPH_CELL_LABEL_MAP, pb2.GRAPH_CELL_LABEL_UNSPECIFIED
        ),
        cell_id=cell.cell_id,
        text=cell.text,
        orig=cell.orig,
    )
    if cell.prov is not None:
        msg.prov.CopyFrom(_to_provenance_item(cell.prov))
    if cell.item_ref is not None:
        msg.item_ref.CopyFrom(_to_ref(cell.item_ref))
    return msg


def _to_graph_link(link: GraphLink) -> pb2.GraphLink:
    msg = pb2.GraphLink(
        label=_enum_value(
            link.label, _GRAPH_LINK_LABEL_MAP, pb2.GRAPH_LINK_LABEL_UNSPECIFIED
        ),
        source_cell_id=link.source_cell_id,
        target_cell_id=link.target_cell_id,
    )
    return msg


def _to_graph_data(data: GraphData) -> pb2.GraphData:
    msg = pb2.GraphData()
    if data.cells:
        msg.cells.extend([_to_graph_cell(cell) for cell in data.cells])
    if data.links:
        msg.links.extend([_to_graph_link(link) for link in data.links])
    return msg


def _to_key_value_item(item: KeyValueItem) -> pb2.KeyValueItem:
    label_enum, label_raw = _to_doc_item_label_enum_and_raw(item.label)
    msg = pb2.KeyValueItem(
        self_ref=item.self_ref,
        content_layer=_enum_value(
            item.content_layer, _CONTENT_LAYER_MAP, pb2.CONTENT_LAYER_UNSPECIFIED
        ),
        label=label_enum,
    )
    if label_raw is not None:
        msg.label_raw = label_raw
    if item.parent is not None:
        msg.parent.CopyFrom(_to_ref(item.parent))
    if item.children:
        msg.children.extend([_to_ref(ref) for ref in item.children])
    meta = _to_floating_meta(item.meta)
    if meta is not None:
        msg.meta.CopyFrom(meta)
    if item.prov:
        msg.prov.extend([_to_provenance_item(p) for p in item.prov])
    if item.source:
        msg.source.extend([_to_source_type(src) for src in item.source])
    if item.comments:
        msg.comments.extend([_to_fine_ref(ref) for ref in item.comments])
    if item.captions:
        msg.captions.extend([_to_ref(ref) for ref in item.captions])
    if item.references:
        msg.references.extend([_to_ref(ref) for ref in item.references])
    if item.footnotes:
        msg.footnotes.extend([_to_ref(ref) for ref in item.footnotes])
    image = _to_image_ref(item.image)
    if image is not None:
        msg.image.CopyFrom(image)
    msg.graph.CopyFrom(_to_graph_data(item.graph))
    return msg


def _to_form_item(item: FormItem) -> pb2.FormItem:
    label_enum, label_raw = _to_doc_item_label_enum_and_raw(item.label)
    msg = pb2.FormItem(
        self_ref=item.self_ref,
        content_layer=_enum_value(
            item.content_layer, _CONTENT_LAYER_MAP, pb2.CONTENT_LAYER_UNSPECIFIED
        ),
        label=label_enum,
    )
    if label_raw is not None:
        msg.label_raw = label_raw
    if item.parent is not None:
        msg.parent.CopyFrom(_to_ref(item.parent))
    if item.children:
        msg.children.extend([_to_ref(ref) for ref in item.children])
    meta = _to_floating_meta(item.meta)
    if meta is not None:
        msg.meta.CopyFrom(meta)
    if item.prov:
        msg.prov.extend([_to_provenance_item(p) for p in item.prov])
    if item.source:
        msg.source.extend([_to_source_type(src) for src in item.source])
    if item.comments:
        msg.comments.extend([_to_fine_ref(ref) for ref in item.comments])
    if item.captions:
        msg.captions.extend([_to_ref(ref) for ref in item.captions])
    if item.references:
        msg.references.extend([_to_ref(ref) for ref in item.references])
    if item.footnotes:
        msg.footnotes.extend([_to_ref(ref) for ref in item.footnotes])
    image = _to_image_ref(item.image)
    if image is not None:
        msg.image.CopyFrom(image)
    msg.graph.CopyFrom(_to_graph_data(item.graph))
    return msg


def _to_field_region_item(item: FieldRegionItem) -> pb2.FieldRegionItem:
    msg = pb2.FieldRegionItem(
        self_ref=item.self_ref,
        content_layer=_enum_value(
            item.content_layer, _CONTENT_LAYER_MAP, pb2.CONTENT_LAYER_UNSPECIFIED
        ),
        label=_enum_value(
            item.label, _DOC_ITEM_LABEL_MAP, pb2.DOC_ITEM_LABEL_UNSPECIFIED
        ),
    )
    if item.parent is not None:
        msg.parent.CopyFrom(_to_ref(item.parent))
    if item.children:
        msg.children.extend([_to_ref(ref) for ref in item.children])
    meta = _to_base_meta(item.meta)
    if meta is not None:
        msg.meta.CopyFrom(meta)
    if item.prov:
        msg.prov.extend([_to_provenance_item(p) for p in item.prov])
    if item.source:
        msg.source.extend([_to_source_type(src) for src in item.source])
    if item.comments:
        msg.comments.extend([_to_fine_ref(ref) for ref in item.comments])
    return msg


def _to_field_item(item: FieldItem) -> pb2.FieldItem:
    msg = pb2.FieldItem(
        self_ref=item.self_ref,
        content_layer=_enum_value(
            item.content_layer, _CONTENT_LAYER_MAP, pb2.CONTENT_LAYER_UNSPECIFIED
        ),
        label=_enum_value(
            item.label, _DOC_ITEM_LABEL_MAP, pb2.DOC_ITEM_LABEL_UNSPECIFIED
        ),
    )
    if item.parent is not None:
        msg.parent.CopyFrom(_to_ref(item.parent))
    if item.children:
        msg.children.extend([_to_ref(ref) for ref in item.children])
    meta = _to_base_meta(item.meta)
    if meta is not None:
        msg.meta.CopyFrom(meta)
    if item.prov:
        msg.prov.extend([_to_provenance_item(p) for p in item.prov])
    if item.source:
        msg.source.extend([_to_source_type(src) for src in item.source])
    if item.comments:
        msg.comments.extend([_to_fine_ref(ref) for ref in item.comments])
    return msg


def _to_group_item(group: GroupItem) -> pb2.GroupItem:
    msg = pb2.GroupItem(
        self_ref=group.self_ref,
        content_layer=_enum_value(
            group.content_layer, _CONTENT_LAYER_MAP, pb2.CONTENT_LAYER_UNSPECIFIED
        ),
        label=_enum_value(group.label, _GROUP_LABEL_MAP, pb2.GROUP_LABEL_UNSPECIFIED),
        name=group.name,
    )
    if group.parent is not None:
        msg.parent.CopyFrom(_to_ref(group.parent))
    if group.children:
        msg.children.extend([_to_ref(ref) for ref in group.children])
    meta = _to_base_meta(group.meta)
    if meta is not None:
        msg.meta.CopyFrom(meta)
    return msg


def _to_page_item(page: PageItem) -> pb2.PageItem:
    msg = pb2.PageItem(size=_to_size(page.size), page_no=page.page_no)
    image = _to_image_ref(page.image)
    if image is not None:
        msg.image.CopyFrom(image)
    return msg


def _to_document_origin(origin: DocumentOrigin) -> pb2.DocumentOrigin:
    msg = pb2.DocumentOrigin(
        mimetype=origin.mimetype,
        binary_hash=int(origin.binary_hash),
        filename=origin.filename,
    )
    if origin.uri is not None:
        msg.uri = str(origin.uri)
    return msg


def docling_document_to_proto(doc: DoclingDocument) -> pb2.DoclingDocument:
    """Convert a DoclingDocument to its protobuf representation."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=DeprecationWarning)
        furniture = doc.furniture
    msg = pb2.DoclingDocument(
        name=doc.name,
        body=_to_group_item(doc.body),
        furniture=_to_group_item(furniture),
    )
    if doc.schema_name is not None:
        msg.schema_name = doc.schema_name
    if doc.version is not None:
        msg.version = doc.version
    if doc.origin is not None:
        msg.origin.CopyFrom(_to_document_origin(doc.origin))
    if doc.groups:
        msg.groups.extend([_to_group_item(group) for group in doc.groups])
    if doc.texts:
        msg.texts.extend([_to_base_text_item(text) for text in doc.texts])
    if doc.pictures:
        msg.pictures.extend([_to_picture_item(pic) for pic in doc.pictures])
    if doc.tables:
        msg.tables.extend([_to_table_item(tbl) for tbl in doc.tables])
    if doc.key_value_items:
        msg.key_value_items.extend(
            [_to_key_value_item(item) for item in doc.key_value_items]
        )
    if doc.form_items:
        msg.form_items.extend([_to_form_item(item) for item in doc.form_items])
    if doc.field_regions:
        msg.field_regions.extend(
            [_to_field_region_item(item) for item in doc.field_regions]
        )
    if doc.field_items:
        msg.field_items.extend([_to_field_item(item) for item in doc.field_items])
    for key, page in doc.pages.items():
        msg.pages[int(key)].CopyFrom(_to_page_item(page))
    return msg


# ---------------------------------------------------------------------------
# Reverse direction: protobuf -> Pydantic
#
# Every `_from_*` helper below is the mirror image of the `_to_*` helper of
# the same name above. The `*_raw` two-field discriminator contract
# (see proto/ai/docling/core/v1/PARITY.md) is honored as follows:
#   - enum tag > 0                -> the mapped Pydantic enum value.
#   - tag 0 + non-empty `*_raw`   -> the raw string where the Pydantic field
#     accepts one; otherwise the model's natural fallback (e.g.
#     CodeLanguageLabel.UNKNOWN) or the field default.
#   - tag 0 + empty `*_raw`       -> field default / None (never zero-value
#     pollution, so exclude-none dumps stay identical).
# ---------------------------------------------------------------------------


def _invert_enum_map(mapping: dict[str, int]) -> dict[int, str]:
    return {tag: key for key, tag in mapping.items()}


_CONTENT_LAYER_REVERSE = _invert_enum_map(_CONTENT_LAYER_MAP)
_GROUP_LABEL_REVERSE = _invert_enum_map(_GROUP_LABEL_MAP)
_DOC_ITEM_LABEL_REVERSE = _invert_enum_map(_DOC_ITEM_LABEL_MAP)
_SCRIPT_REVERSE = _invert_enum_map(_SCRIPT_MAP)
_GRAPH_CELL_LABEL_REVERSE = _invert_enum_map(_GRAPH_CELL_LABEL_MAP)
_GRAPH_LINK_LABEL_REVERSE = _invert_enum_map(_GRAPH_LINK_LABEL_MAP)
_COORD_ORIGIN_REVERSE = _invert_enum_map(_COORD_ORIGIN_MAP)
_ORIENTATION_REVERSE = _invert_enum_map(_ORIENTATION_MAP)
_CODE_LANGUAGE_REVERSE = _invert_enum_map(_CODE_LANGUAGE_MAP)
_HUMAN_LANGUAGE_REVERSE = _invert_enum_map(_HUMAN_LANGUAGE_MAP)


def _from_doc_item_label(tag: int) -> Optional[DocItemLabel]:
    if tag == 0:
        return None
    value = _DOC_ITEM_LABEL_REVERSE.get(tag)
    return DocItemLabel(value) if value is not None else None


def _from_code_language(tag: int, raw: str) -> Optional[CodeLanguageLabel]:
    if tag > 0:
        value = _CODE_LANGUAGE_REVERSE.get(tag)
        if value is not None:
            return CodeLanguageLabel(value)
    if raw:
        # The model field is a strict enum, so an unrecognized raw string
        # falls back to the vocabulary's own catch-all value.
        return CodeLanguageLabel.UNKNOWN
    return None


def _from_struct_value(msg: struct_pb2.Value) -> Any:
    kind = msg.WhichOneof("kind")
    if kind is None or kind == "null_value":
        return None
    if kind == "bool_value":
        return msg.bool_value
    if kind == "number_value":
        number = msg.number_value
        if number.is_integer():
            return int(number)
        return number
    if kind == "string_value":
        return msg.string_value
    if kind == "struct_value":
        return {
            key: _from_struct_value(value)
            for key, value in msg.struct_value.fields.items()
        }
    if kind == "list_value":
        return [_from_struct_value(item) for item in msg.list_value.values]
    raise TypeError(f"Unsupported struct value kind: {kind!r}")


def _custom_fields_kwargs(msg: Any) -> dict[str, Any]:
    # Sorted so the Pydantic extras' insertion order (which is the dump
    # order) is deterministic; protobuf map iteration order is not.
    return {
        key: _from_struct_value(msg.custom_fields[key])
        for key in sorted(msg.custom_fields)
    }


def _from_ref(msg: pb2.RefItem) -> RefItem:
    return RefItem(cref=msg.ref)


def _opt_ref(msg: Any, field: str) -> Optional[RefItem]:
    return _from_ref(getattr(msg, field)) if msg.HasField(field) else None


def _from_fine_ref(msg: pb2.FineRef) -> FineRef:
    kwargs: dict[str, Any] = {"cref": msg.ref}
    if msg.HasField("range"):
        kwargs["range"] = (msg.range.start, msg.range.end)
    return FineRef(**kwargs)


def _from_track_source(msg: pb2.TrackSource) -> TrackSource:
    # `kind="track"` is supplied by the Pydantic model default; on the wire
    # the SourceType oneof tag carried that information.
    kwargs: dict[str, Any] = {
        "start_time": msg.start_time,
        "end_time": msg.end_time,
    }
    if msg.HasField("identifier"):
        kwargs["identifier"] = msg.identifier
    if msg.HasField("voice"):
        kwargs["voice"] = msg.voice
    return TrackSource(**kwargs)


def _from_source_list(msgs: Any) -> list[BaseSource]:
    # Entries whose oneof arm is unset (e.g. an extension arm from a foreign
    # producer that this schema does not know) are skipped silently.
    out: list[BaseSource] = []
    for msg in msgs:
        arm = msg.WhichOneof("source")
        if arm == "track":
            out.append(_from_track_source(msg.track))
    return out


def _from_summary_meta(msg: pb2.SummaryMetaField) -> SummaryMetaField:
    kwargs: dict[str, Any] = {"text": msg.text}
    if msg.HasField("confidence"):
        kwargs["confidence"] = msg.confidence
    if msg.HasField("created_by"):
        kwargs["created_by"] = msg.created_by
    return SummaryMetaField(**kwargs, **_custom_fields_kwargs(msg))


def _from_language_meta(msg: pb2.LanguageMetaField) -> Optional[LanguageMetaField]:
    value = _HUMAN_LANGUAGE_REVERSE.get(msg.code) if msg.code > 0 else None
    if value is None:
        # `code` is required and strictly typed; a language whose code cannot
        # be represented (tag 0, raw-only) cannot be reconstructed.
        return None
    kwargs: dict[str, Any] = {"code": HumanLanguageLabel(value)}
    if msg.HasField("confidence"):
        kwargs["confidence"] = msg.confidence
    if msg.HasField("created_by"):
        kwargs["created_by"] = msg.created_by
    return LanguageMetaField(**kwargs, **_custom_fields_kwargs(msg))


def _from_entity_mention(msg: pb2.EntityMention) -> EntityMention:
    kwargs: dict[str, Any] = {"text": msg.text}
    if msg.HasField("orig"):
        kwargs["orig"] = msg.orig
    if msg.HasField("label"):
        kwargs["label"] = msg.label
    if msg.HasField("charspan"):
        kwargs["charspan"] = (msg.charspan.start, msg.charspan.end)
    if msg.HasField("confidence"):
        kwargs["confidence"] = msg.confidence
    if msg.HasField("created_by"):
        kwargs["created_by"] = msg.created_by
    return EntityMention(**kwargs, **_custom_fields_kwargs(msg))


def _from_entities_meta(msg: pb2.EntitiesMetaField) -> Optional[EntitiesMetaField]:
    if not msg.mentions:
        return None
    return EntitiesMetaField(
        mentions=[_from_entity_mention(m) for m in msg.mentions],
        **_custom_fields_kwargs(msg),
    )


def _from_keywords_meta(msg: pb2.KeywordsMetaField) -> Optional[KeywordsMetaField]:
    if not msg.values:
        return None
    return KeywordsMetaField(values=list(msg.values), **_custom_fields_kwargs(msg))


def _from_topics_meta(msg: pb2.TopicsMetaField) -> Optional[TopicsMetaField]:
    if not msg.values:
        return None
    return TopicsMetaField(values=list(msg.values), **_custom_fields_kwargs(msg))


def _inherited_meta_kwargs(msg: Any) -> dict[str, Any]:
    kwargs: dict[str, Any] = {}
    if msg.HasField("summary"):
        kwargs["summary"] = _from_summary_meta(msg.summary)
    if msg.HasField("language"):
        language = _from_language_meta(msg.language)
        if language is not None:
            kwargs["language"] = language
    if msg.HasField("entities"):
        entities = _from_entities_meta(msg.entities)
        if entities is not None:
            kwargs["entities"] = entities
    if msg.HasField("keywords"):
        keywords = _from_keywords_meta(msg.keywords)
        if keywords is not None:
            kwargs["keywords"] = keywords
    if msg.HasField("topics"):
        topics = _from_topics_meta(msg.topics)
        if topics is not None:
            kwargs["topics"] = topics
    return kwargs


def _from_base_meta(msg: pb2.BaseMeta) -> BaseMeta:
    return BaseMeta(**_inherited_meta_kwargs(msg), **_custom_fields_kwargs(msg))


def _from_description_meta(msg: pb2.DescriptionMetaField) -> DescriptionMetaField:
    kwargs: dict[str, Any] = {"text": msg.text}
    if msg.HasField("confidence"):
        kwargs["confidence"] = msg.confidence
    if msg.HasField("created_by"):
        kwargs["created_by"] = msg.created_by
    return DescriptionMetaField(**kwargs, **_custom_fields_kwargs(msg))


def _from_picture_classification_prediction(
    msg: pb2.PictureClassificationPrediction,
) -> PictureClassificationPrediction:
    kwargs: dict[str, Any] = {"class_name": msg.class_name}
    if msg.HasField("confidence"):
        kwargs["confidence"] = msg.confidence
    if msg.HasField("created_by"):
        kwargs["created_by"] = msg.created_by
    return PictureClassificationPrediction(**kwargs, **_custom_fields_kwargs(msg))


def _from_picture_classification_meta(
    msg: pb2.PictureClassificationMetaField,
) -> PictureClassificationMetaField:
    kwargs: dict[str, Any] = {}
    if msg.predictions:
        kwargs["predictions"] = [
            _from_picture_classification_prediction(p) for p in msg.predictions
        ]
    return PictureClassificationMetaField(**kwargs, **_custom_fields_kwargs(msg))


def _from_molecule_meta(msg: pb2.MoleculeMetaField) -> MoleculeMetaField:
    kwargs: dict[str, Any] = {"smi": msg.smi}
    if msg.HasField("confidence"):
        kwargs["confidence"] = msg.confidence
    if msg.HasField("created_by"):
        kwargs["created_by"] = msg.created_by
    return MoleculeMetaField(**kwargs, **_custom_fields_kwargs(msg))


def _from_tabular_chart_meta(msg: pb2.TabularChartMetaField) -> TabularChartMetaField:
    kwargs: dict[str, Any] = {"chart_data": _from_table_data(msg.chart_data)}
    if msg.HasField("confidence"):
        kwargs["confidence"] = msg.confidence
    if msg.HasField("created_by"):
        kwargs["created_by"] = msg.created_by
    if msg.HasField("title"):
        kwargs["title"] = msg.title
    return TabularChartMetaField(**kwargs, **_custom_fields_kwargs(msg))


def _from_code_meta(msg: pb2.CodeMetaField) -> CodeMetaField:
    kwargs: dict[str, Any] = {"text": msg.text}
    language = _from_code_language(msg.language, msg.language_raw)
    if language is not None:
        kwargs["language"] = language
    if msg.HasField("confidence"):
        kwargs["confidence"] = msg.confidence
    if msg.HasField("created_by"):
        kwargs["created_by"] = msg.created_by
    return CodeMetaField(**kwargs, **_custom_fields_kwargs(msg))


def _from_floating_meta(msg: pb2.FloatingMeta) -> FloatingMeta:
    kwargs = _inherited_meta_kwargs(msg)
    if msg.HasField("description"):
        kwargs["description"] = _from_description_meta(msg.description)
    return FloatingMeta(**kwargs, **_custom_fields_kwargs(msg))


def _from_picture_meta(msg: pb2.PictureMeta) -> PictureMeta:
    kwargs = _inherited_meta_kwargs(msg)
    if msg.HasField("description"):
        kwargs["description"] = _from_description_meta(msg.description)
    if msg.HasField("classification"):
        kwargs["classification"] = _from_picture_classification_meta(
            msg.classification
        )
    if msg.HasField("molecule"):
        kwargs["molecule"] = _from_molecule_meta(msg.molecule)
    if msg.HasField("tabular_chart"):
        kwargs["tabular_chart"] = _from_tabular_chart_meta(msg.tabular_chart)
    if msg.HasField("code"):
        kwargs["code"] = _from_code_meta(msg.code)
    return PictureMeta(**kwargs, **_custom_fields_kwargs(msg))


def _from_formatting(msg: pb2.Formatting) -> Formatting:
    kwargs: dict[str, Any] = {
        "bold": msg.bold,
        "italic": msg.italic,
        "underline": msg.underline,
        "strikethrough": msg.strikethrough,
    }
    if msg.script > 0:
        value = _SCRIPT_REVERSE.get(msg.script)
        if value is not None:
            kwargs["script"] = Script(value)
    # tag 0 (with or without script_raw): the strict enum field keeps its
    # default (Script.BASELINE).
    return Formatting(**kwargs)


def _from_bbox(msg: pb2.BoundingBox) -> BoundingBox:
    kwargs: dict[str, Any] = {"l": msg.l, "t": msg.t, "r": msg.r, "b": msg.b}
    if msg.HasField("coord_origin") and msg.coord_origin > 0:
        value = _COORD_ORIGIN_REVERSE.get(msg.coord_origin)
        if value is not None:
            kwargs["coord_origin"] = CoordOrigin(value)
    # tag 0 (with or without coord_origin_raw): the strict enum field keeps
    # its default (CoordOrigin.TOPLEFT).
    return BoundingBox(**kwargs)


def _from_size(msg: pb2.Size) -> Size:
    return Size(width=msg.width, height=msg.height)


def _from_image_ref(msg: pb2.ImageRef) -> ImageRef:
    return ImageRef(
        mimetype=msg.mimetype,
        dpi=msg.dpi,
        size=_from_size(msg.size),
        uri=msg.uri,
    )


def _from_provenance_item(msg: pb2.ProvenanceItem) -> ProvenanceItem:
    return ProvenanceItem(
        page_no=msg.page_no,
        bbox=_from_bbox(msg.bbox),
        charspan=(msg.charspan.start, msg.charspan.end),
    )


def _text_item_base_kwargs(msg: pb2.TextItemBase) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "self_ref": msg.self_ref,
        "parent": _opt_ref(msg, "parent"),
        "children": [_from_ref(child) for child in msg.children],
        "orig": msg.orig,
        "text": msg.text,
        "prov": [_from_provenance_item(p) for p in msg.prov],
        "source": _from_source_list(msg.source),
        "comments": [_from_fine_ref(ref) for ref in msg.comments],
    }
    content_layer = _CONTENT_LAYER_REVERSE.get(msg.content_layer)
    if content_layer is not None:
        kwargs["content_layer"] = ContentLayer(content_layer)
    label = _from_doc_item_label(msg.label)
    if label is not None:
        kwargs["label"] = label
    if msg.HasField("meta"):
        kwargs["meta"] = _from_base_meta(msg.meta)
    if msg.HasField("formatting"):
        kwargs["formatting"] = _from_formatting(msg.formatting)
    if msg.HasField("hyperlink"):
        kwargs["hyperlink"] = msg.hyperlink
    return kwargs


def _from_title_item(msg: pb2.TitleItem) -> TitleItem:
    return TitleItem(**_text_item_base_kwargs(msg.base))


def _from_section_header_item(msg: pb2.SectionHeaderItem) -> SectionHeaderItem:
    kwargs = _text_item_base_kwargs(msg.base)
    if msg.level:
        kwargs["level"] = msg.level
    return SectionHeaderItem(**kwargs)


def _from_field_heading_item(msg: pb2.FieldHeadingItem) -> FieldHeadingItem:
    kwargs = _text_item_base_kwargs(msg.base)
    if msg.level:
        kwargs["level"] = msg.level
    return FieldHeadingItem(**kwargs)


def _from_field_value_item(msg: pb2.FieldValueItem) -> FieldValueItem:
    kwargs = _text_item_base_kwargs(msg.base)
    if msg.kind:
        kwargs["kind"] = msg.kind
    return FieldValueItem(**kwargs)


def _from_list_item(msg: pb2.ListItem) -> ListItem:
    kwargs = _text_item_base_kwargs(msg.base)
    kwargs["enumerated"] = msg.enumerated
    if msg.HasField("marker"):
        kwargs["marker"] = msg.marker
    return ListItem(**kwargs)


def _from_code_item(msg: pb2.CodeItem) -> CodeItem:
    kwargs: dict[str, Any] = {
        "self_ref": msg.self_ref,
        "parent": _opt_ref(msg, "parent"),
        "children": [_from_ref(child) for child in msg.children],
        "orig": msg.orig,
        "text": msg.text,
        "prov": [_from_provenance_item(p) for p in msg.prov],
        "source": _from_source_list(msg.source),
        "comments": [_from_fine_ref(ref) for ref in msg.comments],
        "captions": [_from_ref(ref) for ref in msg.captions],
        "references": [_from_ref(ref) for ref in msg.references],
        "footnotes": [_from_ref(ref) for ref in msg.footnotes],
    }
    content_layer = _CONTENT_LAYER_REVERSE.get(msg.content_layer)
    if content_layer is not None:
        kwargs["content_layer"] = ContentLayer(content_layer)
    label = _from_doc_item_label(msg.label)
    if label is not None:
        kwargs["label"] = label
    if msg.HasField("meta"):
        # The inlined CodeItem carries a single, unambiguous FloatingMeta.
        kwargs["meta"] = _from_floating_meta(msg.meta)
    if msg.HasField("formatting"):
        kwargs["formatting"] = _from_formatting(msg.formatting)
    if msg.HasField("hyperlink"):
        kwargs["hyperlink"] = msg.hyperlink
    if msg.HasField("image"):
        kwargs["image"] = _from_image_ref(msg.image)
    if msg.HasField("code_language"):
        code_language = _from_code_language(msg.code_language, msg.code_language_raw)
        if code_language is not None:
            kwargs["code_language"] = code_language
    return CodeItem(**kwargs)


def _from_formula_item(msg: pb2.FormulaItem) -> FormulaItem:
    return FormulaItem(**_text_item_base_kwargs(msg.base))


_TEXT_ARM_LABEL_CLASSES: dict[DocItemLabel, type[TextItem]] = {
    DocItemLabel.TITLE: TitleItem,
    DocItemLabel.SECTION_HEADER: SectionHeaderItem,
    DocItemLabel.LIST_ITEM: ListItem,
    DocItemLabel.FORMULA: FormulaItem,
    DocItemLabel.FIELD_HEADING: FieldHeadingItem,
    DocItemLabel.FIELD_VALUE: FieldValueItem,
}


def _from_text_item(msg: pb2.TextItem) -> TextItem:
    kwargs = _text_item_base_kwargs(msg.base)
    # This converter's forward direction routes every TextItem subclass to
    # its dedicated oneof arm, but the JSON dialect discriminates text items
    # by `label` alone, and foreign producers mirror that by emitting all
    # text items through the generic `text` arm. Dispatch on the label so
    # such documents reconstruct the same classes the JSON loading path
    # would produce (subclass-only fields keep their model defaults).
    label = kwargs.get("label")
    if label == DocItemLabel.CODE:
        if msg.base.HasField("meta"):
            kwargs["meta"] = FloatingMeta(
                **_inherited_meta_kwargs(msg.base.meta),
                **_custom_fields_kwargs(msg.base.meta),
            )
        return CodeItem(**kwargs)
    subclass = _TEXT_ARM_LABEL_CLASSES.get(label) if label is not None else None
    if subclass is not None:
        return subclass(**kwargs)
    kwargs.setdefault("label", DocItemLabel.TEXT)
    return TextItem(**kwargs)


def _from_base_text_item(msg: pb2.BaseTextItem) -> TextItem:
    arm = msg.WhichOneof("item")
    if arm == "title":
        return _from_title_item(msg.title)
    if arm == "section_header":
        return _from_section_header_item(msg.section_header)
    if arm == "field_heading":
        return _from_field_heading_item(msg.field_heading)
    if arm == "field_value":
        return _from_field_value_item(msg.field_value)
    if arm == "list_item":
        return _from_list_item(msg.list_item)
    if arm == "code":
        return _from_code_item(msg.code)
    if arm == "formula":
        return _from_formula_item(msg.formula)
    if arm == "text":
        return _from_text_item(msg.text)
    # A texts-arena entry with an unset oneof cannot be skipped: dropping it
    # would shift arena indices and corrupt every subsequent reference.
    raise ValueError("BaseTextItem with unset item oneof cannot be converted")


def _from_table_cell(msg: pb2.TableCell) -> TableCell:
    kwargs: dict[str, Any] = {
        "row_span": msg.row_span,
        "col_span": msg.col_span,
        "start_row_offset_idx": msg.start_row_offset_idx,
        "end_row_offset_idx": msg.end_row_offset_idx,
        "start_col_offset_idx": msg.start_col_offset_idx,
        "end_col_offset_idx": msg.end_col_offset_idx,
        "text": msg.text,
        "column_header": msg.column_header,
        "row_header": msg.row_header,
        "row_section": msg.row_section,
        "fillable": msg.fillable,
    }
    if msg.HasField("bbox"):
        kwargs["bbox"] = _from_bbox(msg.bbox)
    if msg.HasField("ref"):
        return RichTableCell(ref=_from_ref(msg.ref), **kwargs)
    return TableCell(**kwargs)


def _from_table_data(msg: pb2.TableData) -> TableData:
    kwargs: dict[str, Any] = {
        "table_cells": [_from_table_cell(cell) for cell in msg.table_cells],
        "num_rows": msg.num_rows,
        "num_cols": msg.num_cols,
    }
    if msg.orientation > 0:
        value = _ORIENTATION_REVERSE.get(msg.orientation)
        if value is not None:
            kwargs["orientation"] = Orientation(value)
    # tag 0 (with or without orientation_raw): the strict enum field keeps
    # its default (Orientation.ROT_0).
    # `grid` is a computed field derived from table_cells + num_rows/num_cols;
    # the serialized proto grid is redundant and is ignored on import.
    return TableData(**kwargs)


def _doc_item_kwargs(msg: Any) -> dict[str, Any]:
    """Shared reverse kwargs for the structural (non-text) item messages."""
    kwargs: dict[str, Any] = {
        "self_ref": msg.self_ref,
        "parent": _opt_ref(msg, "parent"),
        "children": [_from_ref(child) for child in msg.children],
        "prov": [_from_provenance_item(p) for p in msg.prov],
        "source": _from_source_list(msg.source),
        "comments": [_from_fine_ref(ref) for ref in msg.comments],
    }
    content_layer = _CONTENT_LAYER_REVERSE.get(msg.content_layer)
    if content_layer is not None:
        kwargs["content_layer"] = ContentLayer(content_layer)
    label = _from_doc_item_label(msg.label)
    if label is not None:
        kwargs["label"] = label
    # tag 0 with a non-empty label_raw: the label fields are strict Literal
    # types, so the raw string cannot be carried; the class default applies.
    return kwargs


def _floating_item_kwargs(msg: Any) -> dict[str, Any]:
    kwargs = _doc_item_kwargs(msg)
    kwargs.update(
        captions=[_from_ref(ref) for ref in msg.captions],
        references=[_from_ref(ref) for ref in msg.references],
        footnotes=[_from_ref(ref) for ref in msg.footnotes],
    )
    if msg.HasField("meta"):
        kwargs["meta"] = _from_floating_meta(msg.meta)
    if msg.HasField("image"):
        kwargs["image"] = _from_image_ref(msg.image)
    return kwargs


def _from_table_item(msg: pb2.TableItem) -> TableItem:
    # The proto `annotations` list is derived from `meta` on export and is
    # deprecated on the Pydantic side; `meta` is the source of truth.
    kwargs = _floating_item_kwargs(msg)
    kwargs["data"] = _from_table_data(msg.data)
    return TableItem(**kwargs)


def _from_picture_item(msg: pb2.PictureItem) -> PictureItem:
    # See _from_table_item for why proto `annotations` are ignored on import.
    kwargs = _floating_item_kwargs(msg)
    if msg.HasField("meta"):
        kwargs["meta"] = _from_picture_meta(msg.meta)
    return PictureItem(**kwargs)


def _from_graph_cell(msg: pb2.GraphCell) -> GraphCell:
    kwargs: dict[str, Any] = {
        "label": GraphCellLabel(
            _GRAPH_CELL_LABEL_REVERSE.get(msg.label, GraphCellLabel.UNSPECIFIED.value)
        ),
        "cell_id": msg.cell_id,
        "text": msg.text,
        "orig": msg.orig,
    }
    if msg.HasField("prov"):
        kwargs["prov"] = _from_provenance_item(msg.prov)
    if msg.HasField("item_ref"):
        kwargs["item_ref"] = _from_ref(msg.item_ref)
    return GraphCell(**kwargs)


def _from_graph_link(msg: pb2.GraphLink) -> GraphLink:
    return GraphLink(
        label=GraphLinkLabel(
            _GRAPH_LINK_LABEL_REVERSE.get(msg.label, GraphLinkLabel.UNSPECIFIED.value)
        ),
        source_cell_id=msg.source_cell_id,
        target_cell_id=msg.target_cell_id,
    )


def _from_graph_data(msg: pb2.GraphData) -> GraphData:
    return GraphData(
        cells=[_from_graph_cell(cell) for cell in msg.cells],
        links=[_from_graph_link(link) for link in msg.links],
    )


def _from_key_value_item(msg: pb2.KeyValueItem) -> KeyValueItem:
    kwargs = _floating_item_kwargs(msg)
    kwargs["graph"] = _from_graph_data(msg.graph)
    return KeyValueItem(**kwargs)


def _from_form_item(msg: pb2.FormItem) -> FormItem:
    kwargs = _floating_item_kwargs(msg)
    kwargs["graph"] = _from_graph_data(msg.graph)
    return FormItem(**kwargs)


def _base_meta_item_kwargs(msg: Any) -> dict[str, Any]:
    kwargs = _doc_item_kwargs(msg)
    if msg.HasField("meta"):
        kwargs["meta"] = _from_base_meta(msg.meta)
    return kwargs


def _from_field_region_item(msg: pb2.FieldRegionItem) -> FieldRegionItem:
    return FieldRegionItem(**_base_meta_item_kwargs(msg))


def _from_field_item(msg: pb2.FieldItem) -> FieldItem:
    return FieldItem(**_base_meta_item_kwargs(msg))


def _from_group_item(msg: pb2.GroupItem) -> GroupItem:
    kwargs: dict[str, Any] = {
        "self_ref": msg.self_ref,
        "parent": _opt_ref(msg, "parent"),
        "children": [_from_ref(child) for child in msg.children],
    }
    content_layer = _CONTENT_LAYER_REVERSE.get(msg.content_layer)
    if content_layer is not None:
        kwargs["content_layer"] = ContentLayer(content_layer)
    if msg.HasField("meta"):
        kwargs["meta"] = _from_base_meta(msg.meta)
    if msg.HasField("name"):
        kwargs["name"] = msg.name
    label = GroupLabel(
        _GROUP_LABEL_REVERSE.get(msg.label, GroupLabel.UNSPECIFIED.value)
    )
    # Mirror the class the JSON loading path would pick for this label.
    if label == GroupLabel.LIST:
        return ListGroup(**kwargs)
    if label == GroupLabel.ORDERED_LIST:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=DeprecationWarning)
            return OrderedList(**kwargs)
    if label == GroupLabel.INLINE:
        return InlineGroup(**kwargs)
    return GroupItem(label=label, **kwargs)


def _from_page_item(msg: pb2.PageItem) -> PageItem:
    kwargs: dict[str, Any] = {
        "size": _from_size(msg.size),
        "page_no": msg.page_no,
    }
    if msg.HasField("image"):
        kwargs["image"] = _from_image_ref(msg.image)
    return PageItem(**kwargs)


def _from_document_origin(msg: pb2.DocumentOrigin) -> DocumentOrigin:
    kwargs: dict[str, Any] = {
        "mimetype": msg.mimetype,
        "binary_hash": msg.binary_hash,
        "filename": msg.filename,
    }
    if msg.HasField("uri"):
        kwargs["uri"] = msg.uri
    return DocumentOrigin(**kwargs)


def proto_to_docling_document(msg: pb2.DoclingDocument) -> DoclingDocument:
    """Convert a protobuf DoclingDocument back to its Pydantic representation.

    Exact inverse of :func:`docling_document_to_proto`.
    """
    kwargs: dict[str, Any] = {
        "name": msg.name,
        "body": _from_group_item(msg.body),
        "furniture": _from_group_item(msg.furniture),
        "groups": [_from_group_item(group) for group in msg.groups],
        "texts": [_from_base_text_item(text) for text in msg.texts],
        "pictures": [_from_picture_item(pic) for pic in msg.pictures],
        "tables": [_from_table_item(tbl) for tbl in msg.tables],
        "key_value_items": [
            _from_key_value_item(item) for item in msg.key_value_items
        ],
        "form_items": [_from_form_item(item) for item in msg.form_items],
        "field_regions": [
            _from_field_region_item(item) for item in msg.field_regions
        ],
        "field_items": [_from_field_item(item) for item in msg.field_items],
        "pages": {
            int(key): _from_page_item(page) for key, page in msg.pages.items()
        },
    }
    if msg.HasField("schema_name"):
        kwargs["schema_name"] = msg.schema_name
    if msg.HasField("version"):
        kwargs["version"] = msg.version
    if msg.HasField("origin"):
        kwargs["origin"] = _from_document_origin(msg.origin)
    return DoclingDocument(**kwargs)
