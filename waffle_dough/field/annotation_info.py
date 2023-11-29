from typing import ClassVar, Optional, Union

import numpy as np
from pydantic import BaseModel, Field, field_validator, validator

from waffle_dough.field.base_field import BaseField
from waffle_dough.field.validator.annotation_validator import (
    validate_area,
    validate_bbox,
    validate_caption,
    validate_is_prediction,
    validate_iscrowd,
    validate_keypoints,
    validate_num_keypoints,
    validate_score,
    validate_segmentation,
    validate_value,
)
from waffle_dough.math.box import convert_box, get_box_area
from waffle_dough.math.segmentation import (
    convert_segmentation,
    get_segmentation_area,
    get_segmentation_box,
)
from waffle_dough.type import BoxType, SegmentationType, TaskType


class AnnotationInfo(BaseField):
    image_id: str = Field(...)
    category_id: str = Field(None)
    bbox: Optional[list[float]] = Field(None)
    segmentation: Optional[Union[dict, list[list[float]]]] = Field(None)
    area: Optional[float] = Field(None)
    keypoints: Optional[list[float]] = Field(None)
    num_keypoints: Optional[int] = Field(None)
    caption: Optional[str] = Field(None)
    value: Optional[float] = Field(None)
    iscrowd: Optional[int] = Field(None)
    score: Optional[float] = Field(None)
    is_prediction: Optional[bool] = Field(False)

    extra_required_fields: ClassVar[dict[TaskType, list[str]]] = {
        TaskType.CLASSIFICATION: ["image_id", "category_id"],
        TaskType.OBJECT_DETECTION: ["image_id", "category_id", "bbox"],
        TaskType.SEMANTIC_SEGMENTATION: ["image_id", "category_id", "segmentation"],
        TaskType.INSTANCE_SEGMENTATION: ["image_id", "category_id", "segmentation"],
        TaskType.KEYPOINT_DETECTION: ["image_id", "category_id", "keypoints"],
        TaskType.TEXT_RECOGNITION: ["image_id", "caption"],
        TaskType.REGRESSION: ["image_id", "category_id", "value"],
    }

    @field_validator("bbox")
    def check_bbox(cls, v):
        return validate_bbox(v)

    @field_validator("segmentation")
    def check_segmentation(cls, v):
        return validate_segmentation(v)

    @field_validator("area")
    def check_area(cls, v):
        return validate_area(v)

    @field_validator("keypoints")
    def check_keypoints(cls, v):
        return validate_keypoints(v)

    @field_validator("num_keypoints")
    def check_num_keypoints(cls, v):
        return validate_num_keypoints(v)

    @field_validator("value")
    def check_value(cls, v):
        return validate_value(v)

    @field_validator("caption")
    def check_caption(cls, v):
        return validate_caption(v)

    @field_validator("iscrowd")
    def check_iscrowd(cls, v):
        return validate_iscrowd(v)

    @field_validator("score")
    def check_score(cls, v):
        return validate_score(v)

    @field_validator("is_prediction")
    def check_is_prediction(cls, v):
        return validate_is_prediction(v)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_default_values()

    def set_default_values(self):
        # init default values
        if self.bbox is None:
            if self.segmentation is not None:
                self.bbox = get_segmentation_box(self.segmentation, SegmentationType.POLYGON)

        if self.area is None:
            if self.segmentation is not None:
                self.area = get_segmentation_area(self.segmentation, SegmentationType.POLYGON)
            elif self.bbox is not None:
                self.area = get_box_area(self.bbox, BoxType.XYWH)

        if self.iscrowd is None and self.bbox is not None:
            self.iscrowd = 0

        if self.num_keypoints is None and self.keypoints is not None:
            self.num_keypoints = len(self.keypoints) // 3

        if self.score is not None:
            self.is_prediction = True

    @classmethod
    def classification(
        cls,
        image_id: str,
        category_id: str,
        score: float = None,
    ) -> "AnnotationInfo":
        """Classification Annotation Format

        Args:
            image_id (str): image id.
            category_id (str): category id.
            score (float, optional): prediction score. Default to None.

        Returns:
            Annotation: annotation class
        """
        return cls(
            task=TaskType.CLASSIFICATION,
            image_id=image_id,
            category_id=category_id,
            score=score,
        )

    @classmethod
    def object_detection(
        cls,
        image_id: str,
        category_id: str,
        bbox: list[float],
        area: int = None,
        iscrowd: int = 0,
        score: float = None,
    ) -> "AnnotationInfo":
        """Object Detection Annotation Format

        Args:
            image_id (str): image id.
            category_id (str): category id.
            bbox (list[float]): [x1, y1, w, h].
            area (int): bbox area.
            iscrowd (int, optional): is crowd or not. Default to 0.
            score (float, optional): prediction score. Default to None.

        Returns:
            Annotation: annotation class
        """
        return cls(
            task=TaskType.OBJECT_DETECTION,
            image_id=image_id,
            category_id=category_id,
            bbox=bbox,
            area=area,
            iscrowd=iscrowd,
            score=score,
        )

    @classmethod
    def semantic_segmentation(
        cls,
        image_id: str,
        category_id: str,
        segmentation: Union[list[list[float]], dict],
        bbox: list[float] = None,
        area: int = None,
        iscrowd: int = 0,
        score: float = None,
    ) -> "AnnotationInfo":
        """Segmentation Annotation Format

        Args:
            image_id (str): image id.
            category_id (str): category id.
            bbox (list[float]): [x1, y1, w, h].
            segmentation (Union[list[list[float]], dict]): [[x1, y1, x2, y2, x3, y3, ...], [polygon]] or RLE.
            area (int): segmentation segmentation area.
            iscrowd (int, optional): is crowd or not. Default to 0.
            score (float, optional): prediction score. Default to None.

        Returns:
            Annotation: annotation class
        """
        return cls(
            task=TaskType.SEMANTIC_SEGMENTATION,
            image_id=image_id,
            category_id=category_id,
            bbox=bbox,
            segmentation=segmentation,
            area=area,
            iscrowd=iscrowd,
            score=score,
        )

    @classmethod
    def instance_segmentation(
        cls,
        image_id: str,
        category_id: str,
        segmentation: Union[list[list[float]], dict],
        bbox: list[float] = None,
        area: int = None,
        iscrowd: int = 0,
        score: float = None,
    ) -> "AnnotationInfo":
        """Instance Annotation Format

        Args:
            image_id (str): image id.
            category_id (str): category id.
            bbox (list[float]): [x1, y1, w, h].
            segmentation (Union[list[list[float]], dict]): [[x1, y1, x2, y2, x3, y3, ...], [polygon]] or RLE.
            area (int): segmentation segmentation area.
            iscrowd (int, optional): is crowd or not. Default to 0.
            score (float, optional): prediction score. Default to None.

        Returns:
            Annotation: annotation class
        """
        return cls(
            task=TaskType.INSTANCE_SEGMENTATION,
            image_id=image_id,
            category_id=category_id,
            bbox=bbox,
            segmentation=segmentation,
            area=area,
            iscrowd=iscrowd,
            score=score,
        )

    @classmethod
    def keypoint_detection(
        cls,
        image_id: str,
        category_id: str,
        keypoints: list[float],
        bbox: list[float],
        num_keypoints: int = None,
        area: int = None,
        segmentation: list[list[float]] = None,
        iscrowd: int = 0,
        score: list[float] = None,
    ) -> "AnnotationInfo":
        """Keypoint Detection Annotation Format

        Args:
            image_id (str): image id.
            category_id (str): category id.
            bbox (list[float]): [x1, y1, w, h].
            keypoints (list[float]):
                [x1, y1, v1(visible flag), x2, y2, v2(visible flag), ...].
                visible flag is one of [0(Not labeled), 1(Labeled but not visible), 2(labeled and visible)]
            num_keypoints: number of labeled keypoints
            area (int): segmentation segmentation or bbox area.
            segmentation (list[list[float]], optional): [[x1, y1, x2, y2, x3, y3, ...], [polygon]].
            iscrowd (int, optional): is crowd or not. Default to 0.
            score (list[float], optional): prediction scores. Default to None.

        Returns:
            Annotation: annotation class
        """
        return cls(
            task=TaskType.KEYPOINT_DETECTION,
            image_id=image_id,
            category_id=category_id,
            bbox=bbox,
            keypoints=keypoints,
            num_keypoints=num_keypoints,
            segmentation=segmentation,
            area=area,
            iscrowd=iscrowd,
            score=score,
        )

    @classmethod
    def regression(cls, image_id: str, category_id: str, value: float) -> "AnnotationInfo":
        """Regression Annotation Format

        Args:
            image_id (str): image id.
            category_id (str): category id.
            value (float): regression value.

        Returns:
            Annotation: annotation class
        """
        return cls(
            task=TaskType.REGRESSION,
            image_id=image_id,
            category_id=category_id,
            value=value,
        )

    @classmethod
    def text_recognition(
        cls,
        image_id: str,
        category_id: str,
        caption: str,
        score: float = None,
    ) -> "AnnotationInfo":
        """Text Recognition Annotation Format

        Args:
            image_id (str): image id.
            category_id (str): category id.
            caption (str): string.
            score (float, optional): prediction score. Default to None.

        Returns:
            Annotation: annotation class
        """
        return cls(
            task=TaskType.TEXT_RECOGNITION,
            image_id=image_id,
            category_id=category_id,
            caption=caption,
            score=score,
        )


class UpdateAnnotationInfo(BaseModel):
    category_id: Optional[str] = Field(None)
    bbox: Optional[list[float]] = Field(None)
    segmentation: Optional[Union[dict, list[list[float]]]] = Field(None)
    area: Optional[float] = Field(None)
    keypoints: Optional[list[float]] = Field(None)
    num_keypoints: Optional[int] = Field(None)
    caption: Optional[str] = Field(None)
    value: Optional[float] = Field(None)
    iscrowd: Optional[int] = Field(None)
    score: Optional[float] = Field(None)
    is_prediction: Optional[bool] = Field(None)

    @field_validator("bbox")
    def check_bbox(cls, v):
        return validate_bbox(v)

    @field_validator("segmentation")
    def check_segmentation(cls, v):
        return validate_segmentation(v)

    @field_validator("area")
    def check_area(cls, v):
        return validate_area(v)

    @field_validator("keypoints")
    def check_keypoints(cls, v):
        return validate_keypoints(v)

    @field_validator("num_keypoints")
    def check_num_keypoints(cls, v):
        return validate_num_keypoints(v)

    @field_validator("value")
    def check_value(cls, v):
        return validate_value(v)

    @field_validator("caption")
    def check_caption(cls, v):
        return validate_caption(v)

    @field_validator("iscrowd")
    def check_iscrowd(cls, v):
        return validate_iscrowd(v)

    @field_validator("score")
    def check_score(cls, v):
        return validate_score(v)

    @field_validator("is_prediction")
    def check_is_prediction(cls, v):
        return validate_is_prediction(v)

    @classmethod
    def classification(
        cls,
        category_id: str = None,
        score: float = None,
    ) -> "UpdateAnnotationInfo":
        return cls(
            task=TaskType.CLASSIFICATION,
            category_id=category_id,
            score=score,
        )

    @classmethod
    def object_detection(
        cls,
        category_id: str = None,
        bbox: list[float] = None,
        area: int = None,
        iscrowd: int = None,
        score: float = None,
    ) -> "UpdateAnnotationInfo":
        return cls(
            task=TaskType.OBJECT_DETECTION,
            category_id=category_id,
            bbox=bbox,
            area=area,
            iscrowd=iscrowd,
            score=score,
        )

    @classmethod
    def semantic_segmentation(
        cls,
        category_id: str = None,
        segmentation: Union[list[list[float]], dict] = None,
        bbox: list[float] = None,
        area: int = None,
        iscrowd: int = None,
        score: float = None,
    ) -> "UpdateAnnotationInfo":
        return cls(
            task=TaskType.SEMANTIC_SEGMENTATION,
            category_id=category_id,
            segmentation=segmentation,
            bbox=bbox,
            area=area,
            iscrowd=iscrowd,
            score=score,
        )

    @classmethod
    def instance_segmentation(
        cls,
        category_id: str = None,
        segmentation: Union[list[list[float]], dict] = None,
        bbox: list[float] = None,
        area: int = None,
        iscrowd: int = None,
        score: float = None,
    ) -> "UpdateAnnotationInfo":
        return cls(
            task=TaskType.INSTANCE_SEGMENTATION,
            category_id=category_id,
            segmentation=segmentation,
            bbox=bbox,
            area=area,
            iscrowd=iscrowd,
            score=score,
        )

    @classmethod
    def keypoint_detection(
        cls,
        category_id: str = None,
        keypoints: list[float] = None,
        bbox: list[float] = None,
        num_keypoints: int = None,
        area: int = None,
        segmentation: list[list[float]] = None,
        iscrowd: int = None,
        score: list[float] = None,
    ) -> "UpdateAnnotationInfo":
        return cls(
            task=TaskType.KEYPOINT_DETECTION,
            category_id=category_id,
            keypoints=keypoints,
            bbox=bbox,
            num_keypoints=num_keypoints,
            area=area,
            segmentation=segmentation,
            iscrowd=iscrowd,
            score=score,
        )

    @classmethod
    def regression(
        cls,
        category_id: str = None,
        value: float = None,
    ) -> "UpdateAnnotationInfo":
        return cls(
            task=TaskType.REGRESSION,
            category_id=category_id,
            value=value,
        )

    @classmethod
    def text_recognition(
        cls,
        category_id: str = None,
        caption: str = None,
        score: float = None,
    ) -> "UpdateAnnotationInfo":
        return cls(
            task=TaskType.TEXT_RECOGNITION,
            category_id=category_id,
            caption=caption,
            score=score,
        )
