# -*- coding: utf-8 -*-
#

from mmd.VrmData import VrmModel
from utils.MLogger import MLogger # noqa

logger = MLogger(__name__)


class MExportOptions:

    def __init__(self, version_name: str, logging_level: int, max_workers: int, vrm_model: VrmModel, output_path: str, bone_pairs: dict, \
                 physics_pairs: dict, monitor, is_file: bool, outout_datetime: str):
        self.version_name = version_name
        self.logging_level = logging_level
        self.vrm_model = vrm_model
        self.output_path = output_path
        self.bone_pairs = bone_pairs
        self.physics_pairs = physics_pairs
        self.monitor = monitor
        self.is_file = is_file
        self.outout_datetime = outout_datetime
        self.max_workers = max_workers


