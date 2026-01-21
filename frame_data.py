from dataclasses import dataclass
import numpy as np
from enum import IntEnum

class PhaseEnum(IntEnum):
    START = 0
    LIFT = 1
    PAUSE = 2
    LOWER = 3

class TempoEnum(IntEnum):
    OK = 0
    TOO_SLOW = 1
    TOO_FAST = 2

@dataclass(slots=True)
class FrameData:
    frame_index: int
    set_number: int
    repetition_number: int
    keypoints: np.ndarray
    keypoints_side: np.ndarray
    phase: int
    tempo: int
    percent_match: np.float32 # shape = (20, 3), dtype=np.float32
    key_position_flag: np.bool_
    joints_moving: np.ndarray # shape = (20,), dtype=np.bool_
    joints_wrong_angles: np.ndarray # shape = (20,), dtype=np.bool_
