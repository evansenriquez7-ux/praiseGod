from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Union, Dict, Any

class BaseVisualParams(BaseModel):
    """Base class for all visual problem parameters."""
    model_config = ConfigDict(extra="allow")

class NumberLineParams(BaseVisualParams):
    correct_position: int
    divisions: int
    content_type: str = Field(..., pattern="^(whole_number|fraction|integer|decimal)$")
    # Optional fields based on content_type
    numerator: Optional[int] = None
    denominator: Optional[int] = None
    decimal_value: Optional[float] = None
    value: Optional[int] = None
    # Equal jumps -- a run of `jump_count` hops of `jump_size` starting at `jump_from`,
    # which is the medium mat_g2_na_q3_1 names ("equal jumps on a number line") and the
    # one this payload could not express before 2026-09-11: the component drew a bare
    # dot while the stem described jumps nobody could see. Optional because every other
    # number-line item takes no jumps at all, and absent from a "set" payload on
    # purpose -- drawing the jumps there would draw the answer the pupil must place.
    jump_from: Optional[int] = None
    jump_size: Optional[int] = None
    jump_count: Optional[int] = None

class ClockParams(BaseVisualParams):
    hours: int
    minutes: int
    use_24: bool = False
    interaction_mode: str = Field(..., pattern="^(read|set)$")

class NumberBondParams(BaseVisualParams):
    whole: Optional[int] = None
    part1: Optional[int] = None
    part2: Optional[int] = None

class BarChartParams(BaseVisualParams):
    categories: List[str]
    values: Optional[List[int]] = None
    counts: Optional[List[int]] = None
    title: Optional[str] = None

class PictographParams(BaseVisualParams):
    categories: List[str]
    counts: List[int]
    scale: int
    symbol: str
    title: str
    ask_category: Optional[str] = None
    has_scale: bool

class EmojiPictorialParams(BaseVisualParams):
    emoji: str
    group_a: int
    group_b: int
    operation: str
    layout: str
    show_crossed: bool = False

class TenFrameParams(BaseVisualParams):
    filled: int
    total: int = 10

class FractionModelParams(BaseVisualParams):
    numerator: int
    denominator: int

class FractionShadeParams(BaseVisualParams):
    parts: Optional[int] = None
    shaded_parts: Optional[int] = None
    numerator: Optional[int] = None
    denominator: Optional[int] = None

class CalendarParams(BaseVisualParams):
    month: int
    year: int

class PesoMoneyParams(BaseVisualParams):
    coins: List[Dict[str, int]]
    bills: List[Dict[str, int]] = []
    total: int
    is_interactive: bool = False

class ShapeParams(BaseModel):
    type: str
    sides: int
    orientation_deg: int

class ShapeBoardParams(BaseVisualParams):
    shapes: List[ShapeParams]
    grid_size: int = 5

class PatternSequenceParams(BaseVisualParams):
    sequence: List[Union[int, str]]
    pattern_kind: str

class PlaceValueBlocksParams(BaseVisualParams):
    hundreds: int
    tens: int
    ones: int

class RulerMeasureParams(BaseVisualParams):
    length: float
    unit: str

class BalanceScaleParams(BaseVisualParams):
    left_side: Union[str, List[str]]
    right_side: Union[str, List[str]]
    blank_side: str
    is_balanced: bool

class ScaleReadParams(BaseVisualParams):
    """
    A graduated measuring instrument with its pointer at a reading.

    The mass/capacity analogue of RulerMeasureParams. `mass_capacity`'s
    `read_measurement` task asks "what is the mass of the object?", which is
    answerable only if the instrument is drawn -- before this existed the DNA
    carried the reading in `values["value"]` and nothing rendered it, so the
    stem named an object the learner could not see and the expected answer was
    underivable from anything on the page.

    `reading` must land exactly on a graduation (`reading % tick_interval == 0`)
    or the item is not exactly answerable; the formatter snaps it, the same way
    RulerMeasure's object spans a whole number of ruler units.
    """
    reading: int
    unit: str
    scale_max: int
    tick_interval: int
    instrument: str = Field(..., pattern="^(dial|cylinder)$")
    object_label: Optional[str] = None

class GeometryFigureParams(BaseVisualParams):
    """
    A drawn geometric model: a point, line, line segment, ray, or a pair of lines.

    MATATAG names the model explicitly on both nodes this serves -- "Recognize,
    USING MODELS, and draws a point, line, line segment, and ray" (mat_g3_mg_q1_4)
    and "Recognize and DRAW parallel, intersecting, and perpendicular lines"
    (mat_g3_mg_q1_5) -- and `geometric_lines` had no visual formatter at all, so
    the model lived as ASCII inside the stem: "Look at the model: <---A--------B--->
    (a straight path with arrowheads on both ends)." A stem that says "look at the
    model" and draws nothing is the defect class `dangling_visual_reference_1M`
    exists to catch; the parenthetical gloss made the item answerable in spite of
    the drawing rather than because of it.

    `kind` is what is drawn, not what the pupil must answer: a `recognize_model`
    item draws the figure its key NAMES, which is precisely why the drawing may
    not be described in words in the stem as well.
    """
    kind: str = Field(
        ...,
        pattern="^(point|line|segment|ray|parallel|perpendicular|intersecting|triangle|letter)$",
    )
    labels: List[str] = Field(
        default_factory=list,
        description="Point labels drawn on the figure, e.g. ['A', 'B']",
    )
    letter: Optional[str] = Field(
        default=None,
        description="For kind='letter': the capital letter whose strokes are the model",
    )

class TimetableParams(BaseVisualParams):
    """
    A drawn timetable: a class schedule or a bus timetable.

    mat_g2_mg_q4_2's competency is elapsed time "including TIMETABLES", and a timetable
    is a display. The stem used to carry it as a bulleted list after "Look at the class
    schedule:", so the item pointed at something the page never drew -- answerable,
    because the rows were in the sentence, but not a timetable-reading task. The rows
    come from the DNA, which is also what computes the key, so the drawing and the answer
    cannot disagree.
    """
    kind: str = Field(..., pattern="^(class|bus)$")
    columns: List[str]
    rows: List[Dict[str, Any]] = Field(
        description="[{'label': str, 'start': str, 'end': str}, ...]"
    )

class GridAreaParams(BaseVisualParams):
    rows: int
    cols: int
    title: Optional[str] = None

class FillInTableParams(BaseModel):
    columns: List[str] = Field(description="Column headers")
    rows: List[List[Any]] = Field(description="Table rows (values can be numbers, strings, or None for blank)")
    # The display the counts are to be READ FROM, when this table is the
    # destination of a transfer rather than the whole item.
    #
    # "Organize data in a pictograph without a scale into a table"
    # (mat_g1_dp_q3_3) is a transfer between TWO displays and only the
    # destination was ever drawn. An earlier session correctly rewrote the stem
    # to name the source ("Count the pictures in each row of the pictograph,
    # then write the counts ...") -- which made the item MORE explicitly
    # unanswerable, because it now instructs the pupil to look at something that
    # is not on the page. The pictograph was in the DNA's own visual_params the
    # whole time (symbol, counts, scale, title) and this formatter dropped it.
    #
    # Optional: a table that is not transferred from anywhere leaves it None and
    # renders exactly as before.
    source_pictograph: Optional[Dict[str, Any]] = Field(
        default=None,
        description="{'symbol': str, 'scale': int, 'title': str, "
                    "'rows': [{'category': str, 'count': int}]} — the stimulus to count",
    )

class VisualSchemaRegistry:
    """Registry to map visual types to their Pydantic schemas."""
    SCHEMAS = {
        "NumberLine": NumberLineParams,
        "ClockSet": ClockParams,
        "NumberBond": NumberBondParams,
        "BarChart": BarChartParams,
        "Pictograph": PictographParams,
        "EmojiPictorial": EmojiPictorialParams,
        "TenFrame": TenFrameParams,
        "FractionModel": FractionModelParams,
        "FractionShade": FractionShadeParams,
        "Calendar": CalendarParams,
        "PesoMoney": PesoMoneyParams,
        "ShapeBoard": ShapeBoardParams,
        "PlaceValueBlocks": PlaceValueBlocksParams,
        "PatternSequence": PatternSequenceParams,
        "RulerMeasure": RulerMeasureParams,
        "BalanceScale": BalanceScaleParams,
        "ScaleRead": ScaleReadParams,
        "GeometryFigure": GeometryFigureParams,
        "Timetable": TimetableParams,
        "GridArea": GridAreaParams,
        "FillInTable": FillInTableParams,
    }

    @classmethod
    def validate(cls, visual_type: str, params: Dict[str, Any]):
        if visual_type not in cls.SCHEMAS:
            raise ValueError(f"No schema defined for visual type: {visual_type}")
        return cls.SCHEMAS[visual_type](**params)
