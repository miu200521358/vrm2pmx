# -*- coding: utf-8 -*-
#
import struct
import hashlib
import os
import json
from pathlib import Path

from mmd.VrmData import VrmModel # noqa
from mmd.PmxReader import PmxReader
from module.MMath import MRect, MVector3D, MVector4D, MQuaternion, MMatrix4x4 # noqa
from utils.MLogger import MLogger # noqa
from utils.MException import SizingException, MKilledException, MParseException

logger = MLogger(__name__, level=1)

MIME_TYPE = {
    'image/png': 'png',
    'image/jpeg': 'jpg',
    'image/ktx': 'ktx',
    'image/ktx2': 'ktx2',
    'image/webp': 'webp',
    'image/vnd-ms.dds': 'dds',
    'audio/wav': 'wav'
}


class VrmReader(PmxReader):
    def __init__(self, file_path, is_check=True):
        self.file_path = file_path
        self.is_check = is_check
        self.offset = 0
        self.buffer = None

    def read_model_name(self):
        return ""

    def read_data(self):
        # Pmxモデル生成
        vrm = VrmModel()
        vrm.path = self.file_path

        try:
            # UI側での読み込み処理はスキップ

            # ハッシュを設定
            vrm.digest = self.hexdigest()
            logger.test("vrm: %s, hash: %s", vrm.path, vrm.digest)

            return vrm
        except MKilledException as ke:
            # 終了命令
            raise ke
        except SizingException as se:
            logger.error("VRM2PMX処理が処理できないデータで終了しました。\n\n%s", se.message)
            return se
        except Exception as e:
            import traceback
            logger.error("VRM2PMX処理が意図せぬエラーで終了しました。\n\n%s", traceback.format_exc())
            raise e
    
    def convert_glTF(self, vrm: VrmModel, output_pmx_path: str):
        try:
            # 展開用ディレクトリ作成
            glft_dir_path = os.path.join(str(Path(output_pmx_path).resolve().parents[1]), "glTF")
            os.makedirs(glft_dir_path, exist_ok=True)

            with open(self.file_path, "rb") as f:
                self.buffer = f.read()

                signature = self.unpack(12, "12s")
                logger.test("signature: %s (%s)", signature, self.offset)

                # JSON文字列読み込み
                json_buf_size = self.unpack(8, "L")
                json_text = self.read_text(json_buf_size)

                vrm.json_data = json.loads(json_text)
                
                # JSON出力
                jf = open(os.path.join(glft_dir_path, "gltf.json"), "w")
                json.dump(vrm.json_data, jf, ensure_ascii=False, indent=4, sort_keys=True, separators=(',', ': '))

                # binデータ
                bin_buf_size = self.unpack(8, "L")
                logger.test(f'bin_buf_size: {bin_buf_size}')

                if "images" in vrm.json_data:
                    # jsonデータの中に画像データの指定がある場合
                    for image in vrm.json_data['images']:
                        if int(image["bufferView"]) < len(vrm.json_data['bufferViews']):
                            image_buffer = vrm.json_data['bufferViews'][int(image["bufferView"])]
                            # 画像の開始位置はオフセット分ずらす
                            image_start = self.offset + image_buffer["byteOffset"]
                            # 拡張子
                            ext = MIME_TYPE[image["mimeType"]]
                            with open(os.path.join(glft_dir_path, f"{image['name']}.{ext}"), "wb") as ibf:
                                ibf.write(self.buffer[image_start:(image_start + image_buffer["byteLength"])])
                
                if "shaders" in vrm.json_data:
                    # jsonデータの中にシェーダーの指定がある場合
                    pass

        except MKilledException as ke:
            # 終了命令
            raise ke
        except SizingException as se:
            logger.error("VRM2PMX処理が処理できないデータで終了しました。\n\n%s", se.message)
            return se
        except Exception as e:
            import traceback
            logger.error("VRM2PMX処理が意図せぬエラーで終了しました。\n\n%s", traceback.format_exc())
            raise e
    
    def read_text(self, format_size):
        bresult = self.unpack(format_size, "{0}s".format(format_size))
        return bresult.decode("UTF8")
