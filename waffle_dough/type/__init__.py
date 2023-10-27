"""
Set of types for waffle_dough
"""
from .color_type import ColorType
from .data_type import DataType
from .split_type import SplitType
from .task_type import TaskType


def get_data_types():
    return list(map(lambda x: x.value, list(DataType)))


def get_task_types():
    return list(map(lambda x: x.value, list(TaskType)))


def get_color_types():
    return list(map(lambda x: x.value, list(ColorType)))


def get_split_types():
    return list(map(lambda x: x.value, list(SplitType)))


__all__ = [
    "DataType",
    "TaskType",
    "ColorType",
    "SplitType",
    "get_data_types",
    "get_task_types",
    "get_color_types",
    "get_split_types",
]
