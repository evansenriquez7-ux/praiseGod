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

class GridAreaParams(BaseVisualParams):
    rows: int
    cols: int
    title: Optional[str] = None

class FillInTableParams(BaseModel):
    columns: List[str] = Field(description="Column headers")
    rows: List[List[Any]] = Field(description="Table rows (values can be numbers, strings, or None for blank)")

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
        "GridArea": GridAreaParams,
        "FillInTable": FillInTableParams,
    }

    @classmethod
    def validate(cls, visual_type: str, params: Dict[str, Any]):
        if visual_type not in cls.SCHEMAS:
            raise ValueError(f"No schema defined for visual type: {visual_type}")
        return cls.SCHEMAS[visual_type](**params)
