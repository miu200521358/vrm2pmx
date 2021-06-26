# -*- coding: utf-8 -*-
#
from math import modf
import struct
from sys import maxsize
from mmd.PmxData import PmxModel, Bone, RigidBody, Vertex, Material, Morph, DisplaySlot, RigidBody, Joint, Ik, IkLink, Bdef1, Bdef2, Bdef4, Sdef, Qdef, VertexMorphOffset, GroupMorphData # noqa
from utils.MLogger import MLogger # noqa
import os
import glob
from pathlib import Path

logger = MLogger(__name__, level=1)

TYPE_FLOAT = '<f'
TYPE_BYTE = 'b'
TYPE_BOOL = '<b'
TYPE_UNSIGNED_BOOL = '<B'
TYPE_SHORT = '<h'
TYPE_UNSIGNED_SHORT = '<H'
TYPE_INT = '<i'
TYPE_UNSIGNED_INT = '<I'
TYPE_LONG = '<l'
TYPE_UNSIGNED_LONG = '<L'


class PmxWriter:
    def __init__(self):
        pass
    
    def write(self, pmx: PmxModel, output_path: str):
        with open(output_path, "wb") as fout:

            # 頂点の数
            vertex_cnt = 0
            for bone_idx, vertices in pmx.vertices.items():
                vertex_cnt += len(vertices)

            # シグニチャ
            fout.write(b'PMX ')
            fout.write(struct.pack(TYPE_FLOAT, float(2)))
            # 後続するデータ列のバイトサイズ  PMX2.0は 8 で固定
            fout.write(struct.pack(TYPE_BYTE, int(8)))
            # エンコード方式  | 0:UTF16
            fout.write(struct.pack(TYPE_BYTE, 0))
            # 追加UV数
            fout.write(struct.pack(TYPE_BYTE, 0))
            # 頂点Indexサイズ | 1,2,4 のいずれか
            vertex_idx_size, vertex_idx_type, vertex_idx_unsigned_type = self.define_index_size(vertex_cnt)
            fout.write(struct.pack(TYPE_BYTE, vertex_idx_size))
            # テクスチャIndexサイズ | 1,2,4 のいずれか
            texture_idx_size, texture_idx_type, texture_idx_unsigned_type = self.define_index_size(len(pmx.textures))
            fout.write(struct.pack(TYPE_BYTE, texture_idx_size))
            # 材質Indexサイズ | 1,2,4 のいずれか
            material_idx_size, material_idx_type, material_idx_unsigned_type = self.define_index_size(len(pmx.materials))
            fout.write(struct.pack(TYPE_BYTE, material_idx_size))
            # ボーンIndexサイズ | 1,2,4 のいずれか
            bone_idx_size, bone_idx_type, bone_idx_unsigned_type = self.define_index_size(len(pmx.bones))
            fout.write(struct.pack(TYPE_BYTE, bone_idx_size))
            # モーフIndexサイズ | 1,2,4 のいずれか
            morph_idx_size, morph_idx_type, morph_idx_unsigned_type = self.define_index_size(len(pmx.morphs))
            fout.write(struct.pack(TYPE_BYTE, morph_idx_size))
            # 剛体Indexサイズ | 1,2,4 のいずれか
            rigidbody_idx_size, rigidbody_idx_type, rigidbody_idx_unsigned_type = self.define_index_size(len(pmx.rigidbodies))
            fout.write(struct.pack(TYPE_BYTE, rigidbody_idx_size))

            # モデル名(日本語)
            self.write_text(fout, pmx.name, "Vrm Model")
            # モデル名(英語)
            self.write_text(fout, pmx.english_name, "Vrm Model")
            # コメント(日本語)
            self.write_text(fout, pmx.comment, "")
            # コメント(英語)
            self.write_text(fout, pmx.english_comment, "")

            fout.write(struct.pack(TYPE_INT, vertex_cnt))

            # 頂点データ
            vidx = 0
            for vertices in pmx.vertices.values():
                for vertex in vertices:
                    # position
                    fout.write(struct.pack(TYPE_FLOAT, float(vertex.position.x())))
                    fout.write(struct.pack(TYPE_FLOAT, float(vertex.position.y())))
                    fout.write(struct.pack(TYPE_FLOAT, float(vertex.position.z())))
                    # normal
                    fout.write(struct.pack(TYPE_FLOAT, float(vertex.normal.x())))
                    fout.write(struct.pack(TYPE_FLOAT, float(vertex.normal.y())))
                    fout.write(struct.pack(TYPE_FLOAT, float(vertex.normal.z())))
                    # uv
                    fout.write(struct.pack(TYPE_FLOAT, float(vertex.uv.x())))
                    fout.write(struct.pack(TYPE_FLOAT, float(vertex.uv.y())))

                    # deform
                    if type(vertex.deform) is Bdef1:
                        fout.write(struct.pack(TYPE_BYTE, 0))
                        fout.write(struct.pack(bone_idx_unsigned_type, int(vertex.deform.index0)))
                    elif type(vertex.deform) is Bdef2:
                        fout.write(struct.pack(TYPE_BYTE, 1))
                        fout.write(struct.pack(bone_idx_unsigned_type, int(vertex.deform.index0)))
                        fout.write(struct.pack(bone_idx_unsigned_type, int(vertex.deform.index1)))
                        fout.write(struct.pack(TYPE_FLOAT, vertex.deform.weight0))
                    elif type(vertex.deform) is Bdef4:
                        fout.write(struct.pack(TYPE_BYTE, 2))
                        fout.write(struct.pack(bone_idx_unsigned_type, int(vertex.deform.index0)))
                        fout.write(struct.pack(bone_idx_unsigned_type, int(vertex.deform.index1)))
                        fout.write(struct.pack(bone_idx_unsigned_type, int(vertex.deform.index2)))
                        fout.write(struct.pack(bone_idx_unsigned_type, int(vertex.deform.index3)))
                        fout.write(struct.pack(TYPE_FLOAT, vertex.deform.weight0))
                        fout.write(struct.pack(TYPE_FLOAT, vertex.deform.weight1))
                        fout.write(struct.pack(TYPE_FLOAT, vertex.deform.weight2))
                        fout.write(struct.pack(TYPE_FLOAT, vertex.deform.weight3))
                    else:
                        pass

                    fout.write(struct.pack(TYPE_FLOAT, float(vertex.edge_factor)))

                    if vidx > 0 and vidx % 50000 == 0:
                        logger.info(f"-- 頂点データ出力終了({round(vidx / vertex_cnt * 100, 2)}％)")
                        
                    vidx += 1

            logger.info(f"-- 頂点データ出力終了({vertex_cnt})")

            # 面の数
            fout.write(struct.pack(TYPE_INT, len(pmx.indices)))

            # 面データ
            for iidx, index in enumerate(pmx.indices):
                fout.write(struct.pack(vertex_idx_type, index))

            logger.info(f"-- 面データ出力終了({len(pmx.indices)})")

            # テクスチャの数
            fout.write(struct.pack(TYPE_INT, len(pmx.textures)))

            # テクスチャデータ
            for tex_path in pmx.textures:
                self.write_text(fout, tex_path, "")

            logger.info(f"-- テクスチャデータ出力終了({len(pmx.textures)})")

            # 材質の数
            fout.write(struct.pack(TYPE_INT, len(list(pmx.materials.values()))))

            # 材質データ
            for midx, material in enumerate(pmx.materials.values()):
                # 材質名
                self.write_text(fout, material.name, f"Material {midx}")
                self.write_text(fout, material.english_name, f"Material {midx}")
                # Diffuse
                fout.write(struct.pack(TYPE_FLOAT, float(material.diffuse_color.x())))
                fout.write(struct.pack(TYPE_FLOAT, float(material.diffuse_color.y())))
                fout.write(struct.pack(TYPE_FLOAT, float(material.diffuse_color.z())))
                fout.write(struct.pack(TYPE_FLOAT, float(material.alpha)))
                # Specular
                fout.write(struct.pack(TYPE_FLOAT, float(material.specular_color.x())))
                fout.write(struct.pack(TYPE_FLOAT, float(material.specular_color.y())))
                fout.write(struct.pack(TYPE_FLOAT, float(material.specular_color.z())))
                # Specular係数
                fout.write(struct.pack(TYPE_FLOAT, float(material.specular_factor)))
                # Ambient
                fout.write(struct.pack(TYPE_FLOAT, float(material.ambient_color.x())))
                fout.write(struct.pack(TYPE_FLOAT, float(material.ambient_color.y())))
                fout.write(struct.pack(TYPE_FLOAT, float(material.ambient_color.z())))
                # 描画フラグ(8bit)
                fout.write(struct.pack(TYPE_BYTE, material.flag))
                # エッジ色 (R,G,B,A)
                fout.write(struct.pack(TYPE_FLOAT, float(material.edge_color.x())))
                fout.write(struct.pack(TYPE_FLOAT, float(material.edge_color.y())))
                fout.write(struct.pack(TYPE_FLOAT, float(material.edge_color.z())))
                fout.write(struct.pack(TYPE_FLOAT, float(material.edge_color.w())))
                # エッジサイズ
                fout.write(struct.pack(TYPE_FLOAT, float(material.edge_size)))
                # 通常テクスチャ
                fout.write(struct.pack(texture_idx_type, material.texture_index))
                # スフィアテクスチャ
                fout.write(struct.pack(texture_idx_type, material.sphere_texture_index))
                # スフィアモード
                fout.write(struct.pack(TYPE_BYTE, material.sphere_mode))
                # 共有Toonフラグ
                fout.write(struct.pack(TYPE_BYTE, material.toon_sharing_flag))
                if material.toon_sharing_flag == 0:
                    # 共有Toonテクスチャ[0～9]
                    fout.write(struct.pack(texture_idx_type, material.toon_texture_index))
                else:
                    # 共有Toonテクスチャ[0～9]
                    fout.write(struct.pack(TYPE_BYTE, material.toon_texture_index))
                # コメント
                self.write_text(fout, material.comment, "")
                # 材質に対応する面(頂点)数
                fout.write(struct.pack(TYPE_INT, material.vertex_count))

            logger.info(f"-- 材質データ出力終了({len(list(pmx.materials.values()))})")

            # ボーンの数
            fout.write(struct.pack(TYPE_INT, len(list(pmx.bones.values()))))

            for bidx, bone in enumerate(pmx.bones.values()):
                # ボーン名
                self.write_text(fout, bone.name, f"Bone {bidx}")
                self.write_text(fout, bone.english_name, f"Bone {bidx}")
                # position
                fout.write(struct.pack(TYPE_FLOAT, float(bone.position.x())))
                fout.write(struct.pack(TYPE_FLOAT, float(bone.position.y())))
                fout.write(struct.pack(TYPE_FLOAT, float(bone.position.z())))
                # 親ボーンのボーンIndex
                fout.write(struct.pack(bone_idx_type, bone.parent_index))
                # 変形階層
                fout.write(struct.pack(TYPE_INT, bone.layer))
                # ボーンフラグ
                fout.write(struct.pack(TYPE_SHORT, bone.flag))

                if not bone.getConnectionFlag():
                    # 接続先位置
                    fout.write(struct.pack(TYPE_FLOAT, float(bone.tail_position.x())))
                    fout.write(struct.pack(TYPE_FLOAT, float(bone.tail_position.y())))
                    fout.write(struct.pack(TYPE_FLOAT, float(bone.tail_position.z())))
                elif bone.getConnectionFlag():
                    # 接続先ボーンのボーンIndex
                    fout.write(struct.pack(bone_idx_type, bone.tail_index))

                if bone.getExternalRotationFlag() or bone.getExternalTranslationFlag():
                    # 付与親指定ありの場合
                    fout.write(struct.pack(bone_idx_type, bone.effect_index))
                    fout.write(struct.pack(TYPE_FLOAT, bone.effect_factor))
                
                if bone.getFixedAxisFlag():
                    # 軸制限先
                    fout.write(struct.pack(TYPE_FLOAT, float(bone.fixed_axis.x())))
                    fout.write(struct.pack(TYPE_FLOAT, float(bone.fixed_axis.y())))
                    fout.write(struct.pack(TYPE_FLOAT, float(bone.fixed_axis.z())))

                if bone.getLocalCoordinateFlag():
                    # ローカルX
                    fout.write(struct.pack(TYPE_FLOAT, float(bone.local_x_vector.x())))
                    fout.write(struct.pack(TYPE_FLOAT, float(bone.local_x_vector.y())))
                    fout.write(struct.pack(TYPE_FLOAT, float(bone.local_x_vector.z())))
                    # ローカルZ
                    fout.write(struct.pack(TYPE_FLOAT, float(bone.local_z_vector.x())))
                    fout.write(struct.pack(TYPE_FLOAT, float(bone.local_z_vector.y())))
                    fout.write(struct.pack(TYPE_FLOAT, float(bone.local_z_vector.z())))

                if bone.getIkFlag():
                    # IKボーン
                    # n  : ボーンIndexサイズ  | IKターゲットボーンのボーンIndex
                    fout.write(struct.pack(bone_idx_type, bone.ik.target_index))
                    # 4  : int  	| IKループ回数
                    fout.write(struct.pack(TYPE_INT, bone.ik.loop))
                    # 4  : float	| IKループ計算時の1回あたりの制限角度 -> ラジアン角
                    fout.write(struct.pack(TYPE_FLOAT, bone.ik.limit_radian))
                    # 4  : int  	| IKリンク数 : 後続の要素数
                    fout.write(struct.pack(TYPE_INT, len(bone.ik.link)))

                    for link in bone.ik.link:
                        # n  : ボーンIndexサイズ  | リンクボーンのボーンIndex
                        fout.write(struct.pack(bone_idx_type, link.bone_index))
                        # 1  : byte	| 角度制限 0:OFF 1:ON
                        fout.write(struct.pack(TYPE_BYTE, link.limit_angle))

                        if link.limit_angle == 1:
                            fout.write(struct.pack(TYPE_FLOAT, float(link.limit_min.x())))
                            fout.write(struct.pack(TYPE_FLOAT, float(link.limit_min.y())))
                            fout.write(struct.pack(TYPE_FLOAT, float(link.limit_min.z())))

                            fout.write(struct.pack(TYPE_FLOAT, float(link.limit_max.x())))
                            fout.write(struct.pack(TYPE_FLOAT, float(link.limit_max.y())))
                            fout.write(struct.pack(TYPE_FLOAT, float(link.limit_max.z())))

            logger.info(f"-- ボーンデータ出力終了({len(list(pmx.bones.values()))})")

            # モーフの数
            fout.write(struct.pack(TYPE_INT, len(list(pmx.morphs.values()))))

            for midx, morph in enumerate(pmx.morphs.values()):
                # モーフ名
                self.write_text(fout, morph.name, f"Morph {midx}")
                self.write_text(fout, morph.english_name, f"Morph {midx}")
                # 操作パネル (PMD:カテゴリ) 1:眉(左下) 2:目(左上) 3:口(右上) 4:その他(右下)  | 0:システム予約
                fout.write(struct.pack(TYPE_BYTE, morph.panel))
                # モーフ種類 - 0:グループ, 1:頂点, 2:ボーン, 3:UV, 4:追加UV1, 5:追加UV2, 6:追加UV3, 7:追加UV4, 8:材質
                fout.write(struct.pack(TYPE_BYTE, morph.morph_type))
                # モーフのオフセット数 : 後続の要素数
                fout.write(struct.pack(TYPE_INT, len(morph.offsets)))

                for offset in morph.offsets:
                    if type(offset) is VertexMorphOffset:
                        # 頂点モーフ
                        fout.write(struct.pack(vertex_idx_type, offset.vertex_index))
                        fout.write(struct.pack(TYPE_FLOAT, float(offset.position_offset.x())))
                        fout.write(struct.pack(TYPE_FLOAT, float(offset.position_offset.y())))
                        fout.write(struct.pack(TYPE_FLOAT, float(offset.position_offset.z())))
                    elif type(offset) is GroupMorphData:
                        fout.write(struct.pack(morph_idx_type, offset.morph_index))
                        fout.write(struct.pack(TYPE_FLOAT, float(offset.value)))

            logger.info(f"-- モーフデータ出力終了({len(list(pmx.morphs.values()))})")

            # 表示枠の数
            fout.write(struct.pack(TYPE_INT, len(list(pmx.display_slots.values()))))

            for didx, display_slot in enumerate(pmx.display_slots.values()):
                # ボーン名
                self.write_text(fout, display_slot.name, f"Display {didx}")
                self.write_text(fout, display_slot.english_name, f"Display {didx}")
                # 特殊枠フラグ - 0:通常枠 1:特殊枠
                fout.write(struct.pack(TYPE_BYTE, display_slot.special_flag))
                # 枠内要素数
                fout.write(struct.pack(TYPE_INT, len(display_slot.references)))
                if display_slot.display_type == 0:
                    # ボーンの場合
                    for bone_idx in display_slot.references:
                        # 要素対象 0:ボーン 1:モーフ
                        fout.write(struct.pack(TYPE_BYTE, 0))
                        # ボーンIndex
                        fout.write(struct.pack(bone_idx_type, bone_idx))
                elif display_slot.display_type == 1:
                    # モーフの場合
                    for morph_idx in display_slot.references:
                        # 要素対象 0:ボーン 1:モーフ
                        fout.write(struct.pack(TYPE_BYTE, 1))
                        # ボーンIndex
                        fout.write(struct.pack(morph_idx_type, morph_idx))

            logger.info(f"-- 表示枠データ出力終了({len(list(pmx.display_slots.values()))})")

            # 剛体の数
            fout.write(struct.pack(TYPE_INT, len(list(pmx.rigidbodies.values()))))

            logger.info(f"-- 剛体データ出力終了({len(list(pmx.rigidbodies.values()))})")

            # ジョイントの数
            fout.write(struct.pack(TYPE_INT, len(list(pmx.joints.values()))))

            logger.info(f"-- ジョイントデータ出力終了({len(list(pmx.joints.values()))})")

    def define_index_size(self, size: int):
        if 32768 < size:
            idx_size = 4
            idx_type = TYPE_INT
            idx_unsigned_type = TYPE_UNSIGNED_INT
        elif 128 < size < 32767:
            idx_size = 2
            idx_type = TYPE_SHORT
            idx_unsigned_type = TYPE_UNSIGNED_SHORT
        else:
            idx_size = 1
            idx_type = TYPE_BOOL
            idx_unsigned_type = TYPE_UNSIGNED_BOOL

        return idx_size, idx_type, idx_unsigned_type

    def write_text(self, fout, text: str, default_text: str, type=TYPE_INT):
        try:
            btxt = text.encode("utf-16-le")
        except Exception:
            btxt = default_text.encode("utf-16-le")
        fout.write(struct.pack(type, len(btxt)))
        fout.write(btxt)



