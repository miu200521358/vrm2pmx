# -*- coding: utf-8 -*-
#
import logging
import os
import traceback
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor

from module.MOptions import MExportOptions
from mmd.VrmData import VrmModel # noqa
from mmd.VrmReader import VrmReader
from mmd.PmxData import PmxModel # noqa
from mmd.PmxWriter import PmxWriter
from module.MMath import MRect, MVector3D, MVector4D, MQuaternion, MMatrix4x4 # noqa
from utils.MLogger import MLogger # noqa
from utils.MException import SizingException, MKilledException

logger = MLogger(__name__, level=1)


class Vrm2PmxExportService():
    def __init__(self, options: MExportOptions):
        self.options = options

    def execute(self):
        logging.basicConfig(level=self.options.logging_level, format="%(message)s [%(module_name)s]")

        try:
            service_data_txt = "VRM2PMX変換処理実行\n------------------------\nexeバージョン: {version_name}\n".format(version_name=self.options.version_name) \

            service_data_txt = "{service_data_txt}　VRM: {vmd}\n".format(service_data_txt=service_data_txt,
                                    vmd=os.path.basename(self.options.vrm_model.path)) # noqa

            logger.info(service_data_txt, decoration=MLogger.DECORATION_BOX)

            pmx = PmxModel()

            # vrm展開
            logger.info("Vrm展開開始", decoration=MLogger.DECORATION_LINE)
            reader = VrmReader(self.options.vrm_model.path)
            result = reader.convert_glTF(self.options.vrm_model, pmx, self.options.output_path)
            
            # 最後に出力
            logger.info("PMX出力開始", decoration=MLogger.DECORATION_LINE)

            PmxWriter().write(pmx, self.options.output_path)

            logger.info("出力終了: %s", os.path.basename(self.options.output_path), decoration=MLogger.DECORATION_BOX, title="成功")

            return result
        except MKilledException:
            return False
        except SizingException as se:
            logger.error("全親移植処理が処理できないデータで終了しました。\n\n%s", se.message, decoration=MLogger.DECORATION_BOX)
        except Exception:
            logger.critical("全親移植処理が意図せぬエラーで終了しました。\n\n%s", traceback.format_exc(), decoration=MLogger.DECORATION_BOX)
        finally:
            logging.shutdown()

    # 全親移植処理実行
    def convert_pmx(self):
        vrm_model = self.options.vrm_model

