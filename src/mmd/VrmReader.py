# -*- coding: utf-8 -*-
#
from PIL import Image, ImageChops
import glob
import struct
import os
import json
from pathlib import Path
import shutil
import numpy as np
import re
import math

from mmd.VrmData import VrmModel # noqa
from mmd.PmxData import PmxModel, Bone, RigidBody, Vertex, Material, Morph, DisplaySlot, RigidBody, Joint, Ik, IkLink, Bdef1, Bdef2, Bdef4, Sdef, Qdef # noqa
from mmd.PmxReader import PmxReader
from module.MMath import MRect, MVector2D, MVector3D, MVector4D, MQuaternion, MMatrix4x4 # noqa
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

# MMDにおける1cm＝0.125(ミクセル)、1m＝12.5
MIKU_METER = 12.5


class VrmReader(PmxReader):
    def __init__(self, file_path, is_check=True):
        self.file_path = file_path
        self.is_check = is_check
        self.offset = 0
        self.buffer = None
        self.bone_pairs = {}

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
    
    def convert_glTF(self, vrm: VrmModel, pmx: PmxModel, output_pmx_path: str, bone_pairs: dict):
        try:
            self.bone_pairs = bone_pairs

            # テクスチャ用ディレクトリ
            tex_dir_path = os.path.join(str(Path(output_pmx_path).resolve().parents[0]), "tex")
            os.makedirs(tex_dir_path, exist_ok=True)
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
                logger.info("-- JSON出力終了")

                # binデータ
                bin_buf_size = self.unpack(8, "L")
                logger.test(f'bin_buf_size: {bin_buf_size}')

                with open(os.path.join(glft_dir_path, "data.bin"), "wb") as bf:
                    bf.write(self.buffer[self.offset:(self.offset + bin_buf_size)])

                # 空値をスフィア用に登録
                pmx.textures.append("")

                image_offset = 0
                if "images" in vrm.json_data:
                    # jsonデータの中に画像データの指定がある場合
                    for image in vrm.json_data['images']:
                        if int(image["bufferView"]) < len(vrm.json_data['bufferViews']):
                            image_buffer = vrm.json_data['bufferViews'][int(image["bufferView"])]
                            # 画像の開始位置はオフセット分ずらす
                            image_start = self.offset + image_buffer["byteOffset"]
                            # 拡張子
                            ext = MIME_TYPE[image["mimeType"]]
                            # 画像名
                            image_name = f"{image['name']}.{ext}"
                            with open(os.path.join(glft_dir_path, image_name), "wb") as ibf:
                                ibf.write(self.buffer[image_start:(image_start + image_buffer["byteLength"])])
                            # オフセット加算
                            image_offset += image_buffer["byteLength"]
                            # PMXに追記
                            pmx.textures.append(os.path.join("tex", image_name))
                            # テクスチャコピー
                            shutil.copy(os.path.join(glft_dir_path, image_name), os.path.join(tex_dir_path, image_name))
                
                logger.info("-- テクスチャデータ解析終了")

                vertex_idx = 0
                pmx.indices = []
                accessors = {}
                materials_by_type = {}
                indices_by_material = {}

                if "nodes" in vrm.json_data:
                    for nidx, node in enumerate(vrm.json_data["nodes"]):
                        self.define_bone(vrm, pmx, nidx, -1)
                
                # 全ての親とかMMD用ボーン調整
                bone_idx_offset = 0
                if "全ての親" in pmx.bones and pmx.bones["全ての親"].index > 0 and "センター" in pmx.bones and "上半身" in pmx.bones:
                    bone_idx_offset = pmx.bones["全ての親"].index
                    for bidx in range(bone_idx_offset):
                        # 全ての親より上を削除
                        del pmx.bones[pmx.bone_indexes[bidx]]
                    for bone in pmx.bones.values():
                        # 全ての親を上に動かした分をオフセット
                        bone.index -= bone_idx_offset
                        if bone.parent_index >= 0:
                            bone.parent_index -= bone_idx_offset
                        if bone.tail_index >= 0:
                            bone.tail_index -= bone_idx_offset
                    # 全ての親
                    pmx.bones["全ての親"].tail_index = pmx.bones["センター"].index
                    # センター
                    pmx.bones["センター"].parent_index = pmx.bones["全ての親"].index
                    pmx.bones["センター"].position.setY((pmx.bones["左足"].position.y() + pmx.bones["左ひざ"].position.y()) / 2)
                    pmx.bones["センター"].tail_index = -1
                    pmx.bones["センター"].tail_position = MVector3D(0, -pmx.bones["センター"].position.y(), 0)
                    pmx.bones["センター"].flag = 0x0000 | 0x0002 | 0x0004 | 0x0008 | 0x0010
                    # 上半身
                    pmx.bones["上半身"].parent_index = pmx.bones["センター"].index
                
                # 下半身の作成
                if "下半身" in pmx.bones and "下半身2" in pmx.bones:
                    # 0x0080  : ローカル付与 | 付与対象 0:ユーザー変形値／IKリンク／多重付与 1:親のローカル変形量
                    # 0x0100  : 回転付与
                    pmx.bones["下半身2"].flag |= 0x0081 | 0x0100
                    pmx.bones["下半身2"].effect_index = pmx.bones["下半身"].index
                    pmx.bones["下半身2"].effect_factor = 0.7
                
                # 足首の表示先はつま先
                if "右足首" in pmx.bones and "右つま先" in pmx.bones:
                    pmx.bones["右つま先"].parent_index = pmx.bones["右足首"].index
                    pmx.bones["右足首"].tail_index = pmx.bones["右つま先"].index
                if "左足首" in pmx.bones and "左つま先" in pmx.bones:
                    pmx.bones["左つま先"].parent_index = pmx.bones["左足首"].index
                    pmx.bones["左足首"].tail_index = pmx.bones["左つま先"].index
                if "rightToes" in pmx.bones:
                    pmx.bones["rightToes"].parent_index = -1
                    pmx.bones["rightToes"].tail_index = -1
                if "leftToes" in pmx.bones:
                    pmx.bones["leftToes"].parent_index = -1
                    pmx.bones["leftToes"].tail_index = -1
                
                # 足IK
                self.create_leg_ik(pmx, "右")
                self.create_leg_ik(pmx, "左")
                
                # 表示枠
                pmx.display_slots["Root"] = DisplaySlot("全ての親", "Root", 1, 0)
                pmx.display_slots["Root"].references.append(pmx.bones["全ての親"].index)
                pmx.display_slots["Morph"] = DisplaySlot("表情", "Morph", 1, 1)
                pmx.display_slots["Center"] = DisplaySlot("センター", "Center", 0, 0)
                pmx.display_slots["Center"].references.append(pmx.bones["センター"].index)
                pmx.display_slots["Trunk"] = DisplaySlot("体幹", "Trunk", 0, 0)
                pmx.display_slots["Trunk"].references.append(pmx.bones["頭"].index)
                pmx.display_slots["Trunk"].references.append(pmx.bones["首"].index)
                pmx.display_slots["Trunk"].references.append(pmx.bones["上半身2"].index)
                pmx.display_slots["Trunk"].references.append(pmx.bones["上半身"].index)
                pmx.display_slots["Trunk"].references.append(pmx.bones["下半身2"].index)
                pmx.display_slots["Trunk"].references.append(pmx.bones["下半身"].index)
                pmx.display_slots["LeftLeg"] = DisplaySlot("左足", "LeftLeg", 0, 0)
                pmx.display_slots["LeftLeg"].references.append(pmx.bones["左足"].index)
                pmx.display_slots["LeftLeg"].references.append(pmx.bones["左ひざ"].index)
                pmx.display_slots["LeftLeg"].references.append(pmx.bones["左足首"].index)
                pmx.display_slots["LeftLeg"].references.append(pmx.bones["左足ＩＫ"].index)
                pmx.display_slots["LeftLeg"].references.append(pmx.bones["左つま先ＩＫ"].index)
                pmx.display_slots["RightLeg"] = DisplaySlot("右足", "RightLeg", 0, 0)
                pmx.display_slots["RightLeg"].references.append(pmx.bones["右足"].index)
                pmx.display_slots["RightLeg"].references.append(pmx.bones["右ひざ"].index)
                pmx.display_slots["RightLeg"].references.append(pmx.bones["右足首"].index)
                pmx.display_slots["RightLeg"].references.append(pmx.bones["右足ＩＫ"].index)
                pmx.display_slots["RightLeg"].references.append(pmx.bones["右つま先ＩＫ"].index)
                pmx.display_slots["LeftHand"] = DisplaySlot("左手", "LeftHand", 0, 0)
                pmx.display_slots["LeftHand"].references.append(pmx.bones["左肩"].index)
                pmx.display_slots["LeftHand"].references.append(pmx.bones["左腕"].index)
                pmx.display_slots["LeftHand"].references.append(pmx.bones["左ひじ"].index)
                pmx.display_slots["LeftHand"].references.append(pmx.bones["左手首"].index)
                pmx.display_slots["RightHand"] = DisplaySlot("右手", "RightHand", 0, 0)
                pmx.display_slots["RightHand"].references.append(pmx.bones["右肩"].index)
                pmx.display_slots["RightHand"].references.append(pmx.bones["右腕"].index)
                pmx.display_slots["RightHand"].references.append(pmx.bones["右ひじ"].index)
                pmx.display_slots["RightHand"].references.append(pmx.bones["右手首"].index)
                pmx.display_slots["LeftFinger"] = DisplaySlot("左指", "LeftFinger", 0, 0)
                for bone in pmx.bones.values():
                    if bone.name[0] == "左" and bone.name[-2:-1] == "指" and bone.getManipulatable():
                        pmx.display_slots["LeftFinger"].references.append(bone.index)
                pmx.display_slots["RightFinger"] = DisplaySlot("右指", "RightFinger", 0, 0)
                for bone in pmx.bones.values():
                    if bone.name[0] == "右" and bone.name[-2:-1] == "指" and bone.getManipulatable():
                        pmx.display_slots["RightFinger"].references.append(bone.index)
                pmx.display_slots["Face"] = DisplaySlot("顔", "Face", 0, 0)
                pmx.display_slots["Face"].references.append(pmx.bones["左目"].index)
                pmx.display_slots["Face"].references.append(pmx.bones["右目"].index)
                pmx.display_slots["Others"] = DisplaySlot("その他", "Others", 0, 0)
                for bone in pmx.bones.values():
                    if bone.getManipulatable():
                        is_add = True
                        for ds in pmx.display_slots.values():
                            if bone.index in ds.references:
                                is_add = False
                                break
                    if is_add:
                        pmx.display_slots["Others"].references.append(bone.index)

                logger.info(f'-- ボーンデータ解析[{len(pmx.bones.keys())}]')

                if "meshes" in vrm.json_data:
                    for midx, mesh in enumerate(vrm.json_data["meshes"]):
                        if "primitives" in mesh:
                            for pidx, primitive in enumerate(mesh["primitives"]):
                                if "attributes" in primitive:
                                    # 頂点データ
                                    if primitive["attributes"]["POSITION"] not in accessors:
                                        # 位置データ
                                        positions = self.read_from_accessor(vrm, primitive["attributes"]["POSITION"])

                                        # 法線データ
                                        normals = self.read_from_accessor(vrm, primitive["attributes"]["NORMAL"])

                                        # UVデータ
                                        uvs = self.read_from_accessor(vrm, primitive["attributes"]["TEXCOORD_0"])

                                        # ジョイントデータ(MMDのジョイントとは異なる)
                                        joints = self.read_from_accessor(vrm, primitive["attributes"]["JOINTS_0"])
                                        
                                        # ウェイトデータ
                                        weights = self.read_from_accessor(vrm, primitive["attributes"]["WEIGHTS_0"])

                                        # # 対応するジョイントデータ
                                        skin_joints = vrm.json_data["skins"][[s for s in vrm.json_data["nodes"] if "mesh" in s and s["mesh"] == midx][0]["skin"]]["joints"]
                                        
                                        for vidx, (position, normal, uv, joint, weight) in enumerate(zip(positions, normals, uvs, joints, weights)):
                                            # 有効なINDEX番号と実際のボーンINDEXを取得
                                            valiable_joints, joint_idxs, weight_values = self.get_deform_index(pmx, joint, skin_joints, bone_idx_offset, weight)
                                            if len(joint_idxs) > 1:
                                                if len(joint_idxs) == 2:
                                                    # ウェイトが2つの場合、Bdef2
                                                    deform = Bdef2(joint_idxs[0], joint_idxs[1], weight_values[0])
                                                else:
                                                    # それ以上の場合、Bdef4
                                                    deform = Bdef4(joint_idxs[0], joint_idxs[1], joint_idxs[2], joint_idxs[3], \
                                                                   weight_values[0], weight_values[1], weight_values[2], weight_values[3])
                                            else:
                                                # ウェイトが1つのみの場合、Bdef1
                                                deform = Bdef1(joint_idxs[0])

                                            vertex = Vertex(vertex_idx, position * MIKU_METER * MVector3D(-1, 1, 1), normal * MVector3D(-1, 1, 1), uv, None, deform, 1)
                                            if vidx == 0:
                                                # ブロック毎の開始頂点INDEXを保持
                                                accessors[primitive["attributes"]["POSITION"]] = vertex_idx

                                            if primitive["material"] not in pmx.vertices:
                                                pmx.vertices[primitive["material"]] = []
                                            pmx.vertices[primitive["material"]].append(vertex)

                                            vertex_idx += 1

                                        logger.info(f'-- 頂点データ解析[{primitive["material"]}-{primitive["attributes"]["NORMAL"]}-{primitive["attributes"]["TEXCOORD_0"]}]')

                                        logger.debug(f'{midx}-{pidx}: start({pmx.vertices[primitive["material"]][0].index}): {[v.position.to_log() for v in pmx.vertices[primitive["material"]][:3]]}')
                                        logger.debug(f'{midx}-{pidx}: end({pmx.vertices[primitive["material"]][-1].index}): {[v.position.to_log() for v in pmx.vertices[primitive["material"]][-3:-1]]}')
                                    
                hair_regexp = r'((F\d+_\d+_Hair_\d+)_HAIR_\d+)'

                if "meshes" in vrm.json_data:
                    for midx, mesh in enumerate(vrm.json_data["meshes"]):
                        if "primitives" in mesh:
                            for pidx, primitive in enumerate(sorted(mesh["primitives"], key=lambda x: x["material"])):
                                if "material" in primitive and "materials" in vrm.json_data and primitive["material"] < len(vrm.json_data["materials"]):
                                    # 材質データ
                                    vrm_material = vrm.json_data["materials"][primitive["material"]]
                                    logger.debug(f'material: {primitive["material"]} -> {vrm_material["name"]}')

                                    if "indices" in primitive:
                                        # 面データ
                                        indices = self.read_from_accessor(vrm, primitive["indices"])
                                        for iidx, index in enumerate(indices):
                                            vertex_idx = index + accessors[primitive["attributes"]["POSITION"]]
                                            # 材質別に面を保持
                                            if vrm_material["name"] not in indices_by_material:
                                                indices_by_material[vrm_material["name"]] = []
                                            indices_by_material[vrm_material["name"]].append(vertex_idx)
                                            
                                            if iidx < 3 or iidx > len(indices) - 4:
                                                logger.debug(f'{iidx}: {index} -> {vertex_idx}')

                                        logger.info(f'-- 面データ解析[{primitive["indices"]}]')
                                        logger.debug(f'{midx}-{pidx}: indices: {primitive["indices"]} {indices[:9]} max: {max(indices)}, {len(indices)}/{len(indices_by_material[vrm_material["name"]])}')

                                    if vrm_material["alphaMode"] not in materials_by_type or vrm_material["name"] not in materials_by_type[vrm_material["alphaMode"]]:
                                        # 材質種別別に材質の存在がない場合

                                        # VRMの材質拡張情報
                                        material_ext = [m for m in vrm.json_data["extensions"]["VRM"]["materialProperties"] if m["name"] == vrm_material["name"]][0]
                                        # 拡散色
                                        diffuse_color_data = vrm_material["pbrMetallicRoughness"]["baseColorFactor"]
                                        diffuse_color = MVector3D(diffuse_color_data[:3])
                                        # 非透過度
                                        alpha = diffuse_color_data[3]
                                        # 反射色
                                        if "emissiveFactor" in vrm_material:
                                            specular_color_data = vrm_material["emissiveFactor"]
                                            specular_color = MVector3D(specular_color_data[:3])
                                        else:
                                            specular_color = MVector3D()
                                        specular_factor = 0
                                        # 環境色
                                        if "vectorProperties" in material_ext and "_ShadeColor" in material_ext["vectorProperties"]:
                                            ambient_color = MVector3D(material_ext["vectorProperties"]["_ShadeColor"][:3])
                                        else:
                                            ambient_color = diffuse_color / 2
                                        # 0x02:地面影, 0x04:セルフシャドウマップへの描画, 0x08:セルフシャドウの描画
                                        flag = 0x02 | 0x04 | 0x08
                                        if vrm_material["doubleSided"]:
                                            # 両面描画
                                            flag |= 0x01
                                        edge_color = MVector4D(material_ext["vectorProperties"]["_OutlineColor"])
                                        edge_size = material_ext["floatProperties"]["_OutlineWidth"]

                                        # 0番目は空テクスチャなので+1で設定
                                        m = re.search(hair_regexp, vrm_material["name"])
                                        if m is not None:
                                            # 髪材質の場合、合成
                                            hair_img_name = os.path.basename(pmx.textures[material_ext["textureProperties"]["_MainTex"] + 1])
                                            hair_spe_name = f'{m.groups()[1]}_spe.png'
                                            hair_blend_name = f'{m.groups()[0]}_blend.png'

                                            if os.path.exists(os.path.join(tex_dir_path, hair_img_name)) and os.path.exists(os.path.join(tex_dir_path, hair_spe_name)):
                                                # スペキュラファイルがある場合
                                                hair_img = Image.open(os.path.join(tex_dir_path, hair_img_name))
                                                hair_ary = np.array(hair_img)

                                                spe_img = Image.open(os.path.join(tex_dir_path, hair_spe_name))
                                                spe_ary = np.array(spe_img)

                                                # 拡散色の画像
                                                diffuse_ary = np.array(material_ext["vectorProperties"]["_Color"])
                                                diffuse_img = Image.fromarray(np.tile(diffuse_ary * 255, (hair_ary.shape[0], hair_ary.shape[1], 1)).astype(np.uint8))
                                                hair_diffuse_img = ImageChops.multiply(hair_img, diffuse_img)

                                                # 反射色の画像
                                                emissive_ary = np.array(vrm_material["emissiveFactor"])
                                                emissive_ary = np.append(emissive_ary, 1)
                                                emissive_img = Image.fromarray(np.tile(emissive_ary * 255, (spe_ary.shape[0], spe_ary.shape[1], 1)).astype(np.uint8))
                                                hair_emissive_img = ImageChops.multiply(spe_img, emissive_img)

                                                dest_img = ImageChops.screen(hair_diffuse_img, hair_emissive_img)
                                                dest_img.save(os.path.join(tex_dir_path, hair_blend_name))

                                                pmx.textures.append(os.path.join("tex", hair_blend_name))
                                                texture_index = len(pmx.textures) - 1

                                                # 拡散色と環境色は固定
                                                diffuse_color = MVector3D(1, 1, 1)
                                                ambient_color = diffuse_color / 2
                                            else:
                                                # スペキュラがない場合、ないし反映させない場合、そのまま設定
                                                texture_index = material_ext["textureProperties"]["_MainTex"] + 1
                                        else:
                                            # そのまま出力
                                            texture_index = material_ext["textureProperties"]["_MainTex"] + 1
                                        sphere_texture_index = material_ext["textureProperties"]["_SphereAdd"] + 1
                                        # 加算スフィア
                                        sphere_mode = 2

                                        if "vectorProperties" in material_ext and "_ShadeColor" in material_ext["vectorProperties"]:
                                            toon_sharing_flag = 0
                                            toon_img_name = f'{vrm_material["name"]}_TOON.bmp'
                                            
                                            toon_light_ary = np.tile(np.array([255, 255, 255, 255]), (24, 32, 1))
                                            toon_shadow_ary = np.tile(np.array(material_ext["vectorProperties"]["_ShadeColor"]) * 255, (8, 32, 1))
                                            toon_ary = np.concatenate((toon_light_ary, toon_shadow_ary), axis=0)
                                            toon_img = Image.fromarray(toon_ary.astype(np.uint8))

                                            toon_img.save(os.path.join(tex_dir_path, toon_img_name))
                                            pmx.textures.append(os.path.join("tex", toon_img_name))
                                            # 最後に追加したテクスチャをINDEXとして設定
                                            toon_texture_index = len(pmx.textures) - 1
                                        else:
                                            toon_sharing_flag = 1
                                            toon_texture_index = 1

                                        material = Material(vrm_material["name"], vrm_material["name"], diffuse_color, alpha, specular_factor, specular_color, \
                                                            ambient_color, flag, edge_color, edge_size, texture_index, sphere_texture_index, sphere_mode, toon_sharing_flag, \
                                                            toon_texture_index, "", len(indices))

                                        if vrm_material["alphaMode"] not in materials_by_type:
                                            materials_by_type[vrm_material["alphaMode"]] = {}
                                        materials_by_type[vrm_material["alphaMode"]][vrm_material["name"]] = material

                                        logger.info(f'-- 材質データ解析[{vrm_material["name"]}]')
                                    else:
                                        # 材質がある場合は、面数を加算する
                                        materials_by_type[vrm_material["alphaMode"]][vrm_material["name"]].vertex_count += len(indices)
                
                # モデル名
                pmx.name = vrm.json_data['extensions']['VRM']['meta']['title']

                # 材質を不透明(OPAQUE)→透明順(BLEND)に並べ替て設定
                for material_type in ["OPAQUE", "MASK", "BLEND"]:
                    if material_type in materials_by_type:
                        for material in materials_by_type[material_type].values():
                            pmx.materials[material.name] = material
                            for midx in range(0, len(indices_by_material[material.name]), 3):
                                # 面の貼り方がPMXは逆
                                pmx.indices.append(indices_by_material[material.name][midx + 2])
                                pmx.indices.append(indices_by_material[material.name][midx + 1])
                                pmx.indices.append(indices_by_material[material.name][midx])

            return True
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
        
    def create_leg_ik(self, pmx: PmxModel, direction: str):
        leg_name = f'{direction}足'
        knee_name = f'{direction}ひざ'
        ankle_name = f'{direction}足首'
        toe_name = f'{direction}つま先'
        leg_ik_name = f'{direction}足ＩＫ'
        toe_ik_name = f'{direction}つま先ＩＫ'

        if leg_name in pmx.bones and knee_name in pmx.bones and ankle_name in pmx.bones:
            # 足ＩＫ
            flag = 0x0002 | 0x0004 | 0x0008 | 0x0010 | 0x0020
            leg_ik_link = []
            leg_ik_link.append(IkLink(pmx.bones[knee_name].index, 1, MVector3D(math.radians(-180), 0, 0), MVector3D(math.radians(-0.5), 0, 0)))
            leg_ik_link.append(IkLink(pmx.bones[leg_name].index, 0))
            leg_ik = Ik(pmx.bones[ankle_name].index, 40, 2, leg_ik_link)
            leg_ik_bone = Bone(leg_ik_name, leg_ik_name, pmx.bones[ankle_name].position, pmx.bones["全ての親"].index, 1, flag, MVector3D(0, 0, 1), ik=leg_ik)
            leg_ik_bone.index = len(pmx.bones)
            pmx.bones[leg_ik_bone.name] = leg_ik_bone

            toe_ik_link = []
            toe_ik_link.append(IkLink(pmx.bones[ankle_name].index, 0))
            toe_ik = Ik(pmx.bones[toe_name].index, 3, 4, toe_ik_link)
            toe_ik_bone = Bone(toe_ik_name, toe_ik_name, pmx.bones[toe_name].position, pmx.bones[leg_ik_bone.name].index, 1, flag, MVector3D(0, -1, 0), ik=toe_ik)
            toe_ik_bone.index = len(pmx.bones)
            pmx.bones[toe_ik_bone.name] = toe_ik_bone
    
    def get_deform_index(self, pmx: PmxModel, joint: list, skin_joints: list, bone_idx_offset: int, org_weight: list):
        # まずは0じゃないデータ（何かしら有効なボーンINDEXがあるリスト）
        valiable_joints = np.where(joint.data() > 0)[0].tolist()
        # ジョイント添え字からジョイントINDEXを取得(floatになってるのでint)
        org_joint_idxs = joint.data()[valiable_joints].astype(np.int)
        # オフセットを加味したジョイント
        dest_joints = np.array(skin_joints)[org_joint_idxs] - bone_idx_offset

        # 足先EXに相当する箇所なので、足首に載せ替える
        right_joints = np.where(dest_joints == pmx.bones["rightToes"].index, pmx.bones["右足首"].index, dest_joints)
        target_joints = np.where(right_joints == pmx.bones["leftToes"].index, pmx.bones["左足首"].index, right_joints)

        # 有効なウェイト値
        target_weights = org_weight.data()[valiable_joints]

        # 足首を載せ替えた事で、ジョイントが重複している場合があるので、調整する
        joint_weights = {}
        for j, w in zip(target_joints, target_weights):
            if j not in joint_weights:
                joint_weights[j] = 0
            joint_weights[j] += w

        # 対象となるウェイト値
        joint_values = list(joint_weights.keys())
        # 正規化(合計して1になるように)
        total_weights = np.array(list(joint_weights.values()))
        weight_values = (total_weights / total_weights.sum(axis=0, keepdims=1)).tolist()

        if len(joint_values) == 3:
            # 3つの場合、0を入れ込む
            return valiable_joints, joint_values + [0], weight_values + [0]

        return valiable_joints, joint_values, weight_values
    
    def define_bone(self, vrm: VrmModel, pmx: PmxModel, node_idx: int, parent_idx: int):
        node = vrm.json_data["nodes"][node_idx]
        human_nodes = [b for b in vrm.json_data["extensions"]["VRM"]["humanoid"]["humanBones"] if b["node"] == node_idx]
        # 人体ボーンの場合のみ人体データ取得
        human_node = None if len(human_nodes) == 0 else human_nodes[0]
        bone_name = human_node["bone"] if human_node else node["name"]
        jp_bone_name = self.bone_pairs[bone_name] if bone_name in self.bone_pairs else bone_name

        if jp_bone_name in pmx.bones:
            return

        # 位置
        position = MVector3D(node["translation"]) * MIKU_METER * MVector3D(-1, 1, 1)

        if 0 < parent_idx:
            position += pmx.bones[pmx.bone_indexes[parent_idx]].position

        #  0x0001  : 接続先(PMD子ボーン指定)表示方法 -> 0:座標オフセットで指定 1:ボーンで指定
        #  0x0002  : 回転可能
        #  0x0004  : 移動可能
        #  0x0008  : 表示
        #  0x0010  : 操作可
        if bone_name in self.bone_pairs:
            if jp_bone_name.endswith("先"):
                flag = 0x0001 | 0x0002
            elif jp_bone_name in ["全ての親", "センター"]:
                flag = 0x0001 | 0x0002 | 0x0004 | 0x0008 | 0x0010
            else:
                flag = 0x0001 | 0x0002 | 0x0008 | 0x0010
        elif human_node or "mesh" in node:
            flag = 0x0001 | 0x0002 | 0x0004
        else:
            flag = 0x0001 | 0x0002 | 0x0004 | 0x0008 | 0x0010

        bone = Bone(jp_bone_name, node["name"], position, parent_idx, 0, flag)
        bone.index = node_idx
        pmx.bones[bone.name] = bone
        pmx.bone_indexes[node_idx] = bone.name

        if "children" in node:
            # 子ボーンがある場合
            for child_idx in node["children"]:
                # 子ボーンを取得
                self.define_bone(vrm, pmx, child_idx, node_idx)

                # 表示先を設定(最初のボーン系子ども)
                if pmx.bones[jp_bone_name].tail_index == -1 and (("Bip" in pmx.bones[pmx.bone_indexes[child_idx]].english_name and "Bip" in bone.english_name) or "Bip" not in bone.english_name):
                    pmx.bones[jp_bone_name].tail_index = child_idx

    # アクセサの数を取得する
    def count_from_accessor(self, vrm: VrmModel, accessor_idx: int):
        if accessor_idx < len(vrm.json_data['accessors']):
            accessor = vrm.json_data['accessors'][accessor_idx]
            if accessor['bufferView'] < len(vrm.json_data['bufferViews']):
                if 'count' in accessor:
                    return accessor['count']
        return 0

    # アクセサ経由で値を取得する
    # https://github.com/ft-lab/Documents_glTF/blob/master/structure.md
    def read_from_accessor(self, vrm: VrmModel, accessor_idx: int):
        bresult = None
        if accessor_idx < len(vrm.json_data['accessors']):
            accessor = vrm.json_data['accessors'][accessor_idx]
            acc_type = accessor['type']
            if accessor['bufferView'] < len(vrm.json_data['bufferViews']):
                buffer = vrm.json_data['bufferViews'][accessor['bufferView']]
                logger.debug('accessor: %s, %s', accessor_idx, buffer)
                if 'count' in accessor:
                    bresult = []
                    if acc_type == "VEC3":
                        buf_type, buf_num = self.define_buf_type(accessor['componentType'])

                        for n in range(accessor['count']):
                            buf_start = self.offset + buffer["byteOffset"] + ((buf_num * 3) * n)

                            # Vec3 / float
                            xresult = struct.unpack_from(buf_type, self.buffer, buf_start)
                            yresult = struct.unpack_from(buf_type, self.buffer, buf_start + buf_num)
                            zresult = struct.unpack_from(buf_type, self.buffer, buf_start + (buf_num * 2))

                            if buf_type == "f":
                                bresult.append(MVector3D(float(xresult[0]), float(yresult[0]), float(zresult[0])))
                            else:
                                bresult.append(MVector3D(int(xresult[0]), int(yresult[0]), int(zresult[0])))
                        logger.debug("-- -- Accessor[%s/Vec3/%s]", accessor_idx, buf_type)
                            
                    elif acc_type == "VEC2":
                        buf_type, buf_num = self.define_buf_type(accessor['componentType'])

                        for n in range(accessor['count']):
                            buf_start = self.offset + buffer["byteOffset"] + ((buf_num * 2) * n)

                            # Vec3 / float
                            xresult = struct.unpack_from(buf_type, self.buffer, buf_start)
                            yresult = struct.unpack_from(buf_type, self.buffer, buf_start + buf_num)

                            bresult.append(MVector2D(float(xresult[0]), float(yresult[0])))
                        logger.debug("-- -- Accessor[%s/Vec3/%s]", accessor_idx, buf_type)
                            
                    elif acc_type == "VEC4":
                        buf_type, buf_num = self.define_buf_type(accessor['componentType'])

                        for n in range(accessor['count']):
                            buf_start = self.offset + buffer["byteOffset"] + ((buf_num * 4) * n)

                            # Vec3 / float
                            xresult = struct.unpack_from(buf_type, self.buffer, buf_start)
                            yresult = struct.unpack_from(buf_type, self.buffer, buf_start + buf_num)
                            zresult = struct.unpack_from(buf_type, self.buffer, buf_start + (buf_num * 2))
                            wresult = struct.unpack_from(buf_type, self.buffer, buf_start + (buf_num * 3))

                            if buf_type == "f":
                                bresult.append(MVector4D(float(xresult[0]), float(yresult[0]), float(zresult[0]), float(wresult[0])))
                            else:
                                bresult.append(MVector4D(int(xresult[0]), int(yresult[0]), int(zresult[0]), int(wresult[0])))
                        logger.debug("-- -- Accessor[%s/Vec4/%s]", accessor_idx, buf_type)
                            
                    elif acc_type == "SCALAR":
                        buf_type, buf_num = self.define_buf_type(accessor['componentType'])

                        for n in range(accessor['count']):
                            buf_start = self.offset + buffer["byteOffset"] + (buf_num * n)
                            xresult = struct.unpack_from(buf_type, self.buffer, buf_start)

                            if buf_type == "f":
                                bresult.append(float(xresult[0]))
                            else:
                                bresult.append(int(xresult[0]))
                        logger.debug("-- -- Accessor[%s/Scalar/%s]", accessor_idx, buf_type)

        return bresult

    def define_buf_type(self, componentType: int):
        if componentType == 5120:
            return "b", 1
        elif componentType == 5121:
            return "B", 1
        elif componentType == 5122:
            return "h", 2
        elif componentType == 5123:
            return "H", 2
        elif componentType == 5124:
            return "i", 4
        elif componentType == 5125:
            return "I", 4
        
        return "f", 4
    
    def read_text(self, format_size):
        bresult = self.unpack(format_size, "{0}s".format(format_size))
        return bresult.decode("UTF8")
