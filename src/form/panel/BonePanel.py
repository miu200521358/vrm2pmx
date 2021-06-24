# -*- coding: utf-8 -*-
#
import wx
import wx.lib.newevent

from form.panel.BasePanel import BasePanel
from utils.MLogger import MLogger # noqa

logger = MLogger(__name__)
TIMER_ID = wx.NewId()

BONE_PAIRS = {
    "Root": {"name": "全ての親", "parent": None, "tail": "センター", "display": "全ての親"},
    "Center": {"name": "センター", "parent": "全ての親", "tail": -1, "display": "センター"},
    "Groove": {"name": "グルーブ", "parent": "センター", "tail": -1, "display": "センター"},
    "hips": {"name": "腰", "parent": "グルーブ", "tail": -1, "display": "体幹"},
    "spine": {"name": "下半身", "parent": "腰", "tail": -1, "display": "体幹"},
    "chest": {"name": "上半身", "parent": "腰", "tail": "上半身2", "display": "体幹"},
    "upperChest": {"name": "上半身2", "parent": "上半身", "tail": "首", "display": "体幹"},
    "neck": {"name": "首", "parent": "上半身2", "tail": "頭", "display": "体幹"},
    "head": {"name": "頭", "parent": "首", "tail": -1, "display": "体幹"},
    "leftEye": {"name": "左目", "parent": "頭", "tail": -1, "display": "顔"},
    "rightEye": {"name": "右目", "parent": "頭", "tail": -1, "display": "顔"},
    "shoulderP_L": {"name": "左肩P", "parent": "上半身2", "tail": -1, "display": "左手"},
    "leftShoulder": {"name": "左肩", "parent": "左肩P", "tail": "左腕", "display": "左手"},
    "shoulderC_L": {"name": "左肩C", "parent": "左肩", "tail": -1, "display": None},
    "leftUpperArm": {"name": "左腕", "parent": "左肩C", "tail": "左ひじ", "display": "左手"},
    "arm_twist_L": {"name": "左腕捩", "parent": "左腕", "tail": -1, "display": "左手"},
    "arm_twist_L1": {"name": "左腕捩1", "parent": "左腕", "tail": -1, "display": None},
    "arm_twist_L2": {"name": "左腕捩2", "parent": "左腕", "tail": -1, "display": None},
    "arm_twist_L3": {"name": "左腕捩3", "parent": "左腕", "tail": -1, "display": None},
    "leftLowerArm": {"name": "左ひじ", "parent": "左腕捩", "tail": "左手首", "display": "左手"},
    "wrist_twist_L": {"name": "左手捩", "parent": "左ひじ", "tail": -1, "display": "左手"},
    "leftHand": {"name": "左手首", "parent": "左手捩", "tail": -1, "display": "左手"},
    "leftThumbProximal": {"name": "左親指０", "parent": "左手首", "tail": "左親指１", "display": "左指"},
    "leftThumbIntermediate": {"name": "左親指１", "parent": "左親指０", "tail": "左親指２", "display": "左指"},
    "leftThumbDistal": {"name": "左親指２", "parent": "左親指１", "tail": "左親指先", "display": "左指"},
    "J_Bip_L_Thumb3_end": {"name": "左親指先", "parent": "左親指２", "tail": -1, "display": None},
    "leftIndexProximal": {"name": "左人指１", "parent": "左手首", "tail": "左人指２", "display": "左指"},
    "leftIndexIntermediate": {"name": "左人指２", "parent": "左人指１", "tail": "左人指３", "display": "左指"},
    "leftIndexDistal": {"name": "左人指３", "parent": "左人指２", "tail": "左人指先", "display": "左指"},
    "J_Bip_L_Index3_end": {"name": "左人指先", "parent": "左人指３", "tail": -1, "display": None},
    "leftMiddleProximal": {"name": "左中指１", "parent": "左手首", "tail": "左中指２", "display": "左指"},
    "leftMiddleIntermediate": {"name": "左中指２", "parent": "左中指１", "tail": "左中指３", "display": "左指"},
    "leftMiddleDistal": {"name": "左中指３", "parent": "左中指２", "tail": "左中指先", "display": "左指"},
    "J_Bip_L_Middle3_end": {"name": "左中指先", "parent": "左中指３", "tail": -1, "display": None},
    "leftRingProximal": {"name": "左薬指１", "parent": "左手首", "tail": "左薬指２", "display": "左指"},
    "leftRingIntermediate": {"name": "左薬指２", "parent": "左薬指１", "tail": "左薬指３", "display": "左指"},
    "leftRingDistal": {"name": "左薬指３", "parent": "左薬指２", "tail": "左薬指先", "display": "左指"},
    "J_Bip_L_Ring3_end": {"name": "左薬指先", "parent": "左薬指３", "tail": -1, "display": None},
    "leftLittleProximal": {"name": "左小指１", "parent": "左手首", "tail": "左小指２", "display": "左指"},
    "leftLittleIntermediate": {"name": "左小指２", "parent": "左小指１", "tail": "左小指３", "display": "左指"},
    "leftLittleDistal": {"name": "左小指３", "parent": "左小指２", "tail": "左小指先", "display": "左指"},
    "J_Bip_L_Little3_end": {"name": "左小指先", "parent": "左小指３", "tail": -1, "display": None},
    "shoulderP_R": {"name": "右肩P", "parent": "上半身2", "tail": -1, "display": "右手"},
    "rightShoulder": {"name": "右肩", "parent": "右肩P", "tail": "右腕", "display": "右手"},
    "shoulderC_R": {"name": "右肩C", "parent": "右肩", "tail": -1, "display": None},
    "rightUpperArm": {"name": "右腕", "parent": "右肩C", "tail": "右ひじ", "display": "右手"},
    "arm_twist_R": {"name": "右腕捩", "parent": "右腕", "tail": -1, "display": "右手"},
    "arm_twist_R1": {"name": "右腕捩1", "parent": "右腕", "tail": -1, "display": None},
    "arm_twist_R2": {"name": "右腕捩2", "parent": "右腕", "tail": -1, "display": None},
    "arm_twist_R3": {"name": "右腕捩3", "parent": "右腕", "tail": -1, "display": None},
    "rightLowerArm": {"name": "右ひじ", "parent": "右腕捩", "tail": "右手首", "display": "右手"},
    "wrist_twist_R": {"name": "右手捩", "parent": "右ひじ", "tail": -1, "display": "右手"},
    "rightHand": {"name": "右手首", "parent": "右手捩", "tail": -1, "display": "右手"},
    "rightThumbProximal": {"name": "右親指０", "parent": "右手首", "tail": "右親指１", "display": "右指"},
    "rightThumbIntermediate": {"name": "右親指１", "parent": "右親指０", "tail": "右親指２", "display": "右指"},
    "rightThumbDistal": {"name": "右親指２", "parent": "右親指１", "tail": "右親指先", "display": "右指"},
    "J_Bip_R_Thumb3_end": {"name": "右親指先", "parent": "右親指２", "tail": -1, "display": None},
    "rightIndexProximal": {"name": "右人指１", "parent": "右手首", "tail": "右人指２", "display": "右指"},
    "rightIndexIntermediate": {"name": "右人指２", "parent": "右人指１", "tail": "右人指３", "display": "右指"},
    "rightIndexDistal": {"name": "右人指３", "parent": "右人指２", "tail": "右人指先", "display": "右指"},
    "J_Bip_R_Index3_end": {"name": "右人指先", "parent": "右人指３", "tail": -1, "display": None},
    "rightMiddleProximal": {"name": "右中指１", "parent": "右手首", "tail": "右中指２", "display": "右指"},
    "rightMiddleIntermediate": {"name": "右中指２", "parent": "右中指１", "tail": "右中指３", "display": "右指"},
    "rightMiddleDistal": {"name": "右中指３", "parent": "右中指２", "tail": "右中指先", "display": "右指"},
    "J_Bip_R_Middle3_end": {"name": "右中指先", "parent": "右中指３", "tail": -1, "display": None},
    "rightRingProximal": {"name": "右薬指１", "parent": "右手首", "tail": "右薬指２", "display": "右指"},
    "rightRingIntermediate": {"name": "右薬指２", "parent": "右薬指１", "tail": "右薬指３", "display": "右指"},
    "rightRingDistal": {"name": "右薬指３", "parent": "右薬指２", "tail": "右薬指先", "display": "右指"},
    "J_Bip_R_Ring3_end": {"name": "右薬指先", "parent": "右薬指３", "tail": -1, "display": None},
    "rightLittleProximal": {"name": "右小指１", "parent": "右手首", "tail": "右小指２", "display": "右指"},
    "rightLittleIntermediate": {"name": "右小指２", "parent": "右小指１", "tail": "右小指３", "display": "右指"},
    "rightLittleDistal": {"name": "右小指３", "parent": "右小指２", "tail": "右小指先", "display": "右指"},
    "J_Bip_R_Little3_end": {"name": "右小指先", "parent": "右小指３", "tail": -1, "display": None},
    "leftWaistCancel": {"name": "腰キャンセル左", "parent": "下半身", "tail": -1, "display": None},
    "leftUpperLeg": {"name": "左足", "parent": "腰キャンセル左", "tail": "左ひざ", "display": "左足"},
    "leftLowerLeg": {"name": "左ひざ", "parent": "左足", "tail": "左足首", "display": "左足"},
    "leftFoot": {"name": "左足首", "parent": "左ひざ", "tail": "左つま先", "display": "左足"},
    "J_Bip_L_ToeBase_end": {"name": "左つま先", "parent": "左足首", "tail": -1, "display": None},
    "leg_IK_L": {"name": "左足ＩＫ", "parent": "全ての親", "tail": -1, "display": "左足"},
    "toe_IK_L": {"name": "左つま先ＩＫ", "parent": "左足ＩＫ", "tail": -1, "display": "左足"},
    "rightWaistCancel": {"name": "腰キャンセル右", "parent": "下半身", "tail": -1, "display": None},
    "rightUpperLeg": {"name": "右足", "parent": "腰キャンセル右", "tail": "右ひざ", "display": "右足"},
    "rightLowerLeg": {"name": "右ひざ", "parent": "右足", "tail": "右足首", "display": "右足"},
    "rightFoot": {"name": "右足首", "parent": "右ひざ", "tail": "右つま先", "display": "右足"},
    "J_Bip_R_ToeBase_end": {"name": "右つま先", "parent": "右足首", "tail": -1, "display": None},
    "leg_IK_R": {"name": "右足ＩＫ", "parent": "全ての親", "tail": -1, "display": "右足"},
    "toe_IK_R": {"name": "右つま先ＩＫ", "parent": "右足ＩＫ", "tail": -1, "display": "右足"},
    "leg_LD": {"name": "左足D", "parent": "腰キャンセル左", "tail": -1, "display": "左足"},
    "knee_LD": {"name": "左ひざD", "parent": "左足D", "tail": -1, "display": "左足"},
    "ankle_LD": {"name": "左足首D", "parent": "左ひざD", "tail": -1, "display": "左足"},
    "leftToes": {"name": "左足先EX", "parent": "左足首D", "tail": -1, "display": "左足"},
    "leg_RD": {"name": "右足D", "parent": "腰キャンセル右", "tail": -1, "display": "右足"},
    "knee_RD": {"name": "右ひざD", "parent": "右足D", "tail": -1, "display": "右足"},
    "ankle_RD": {"name": "右足首D", "parent": "右ひざD", "tail": -1, "display": "右足"},
    "rightToes": {"name": "右足先EX", "parent": "右足首D", "tail": -1, "display": "右足"},
}


class BonePanel(BasePanel):
        
    def __init__(self, frame: wx.Frame, export: wx.Notebook, tab_idx: int):
        super().__init__(frame, export, tab_idx)
        self.convert_export_worker = None

        self.header_panel = wx.Panel(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        self.header_sizer = wx.BoxSizer(wx.VERTICAL)

        self.description_txt = wx.StaticText(self.header_panel, wx.ID_ANY, "Vroid Studio のボーン命名をMMD用に設定します。", wx.DefaultPosition, wx.DefaultSize, 0)
        self.header_sizer.Add(self.description_txt, 0, wx.ALL, 5)

        self.header_panel.SetSizer(self.header_sizer)
        self.header_panel.Layout()
        self.sizer.Add(self.header_panel, 0, wx.EXPAND | wx.ALL, 5)

        # モーフセット用基本Sizer
        self.set_list_sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.scrolled_window = wx.ScrolledWindow(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, \
                                                 wx.FULL_REPAINT_ON_RESIZE | wx.VSCROLL | wx.ALWAYS_SHOW_SB)
        self.scrolled_window.SetScrollRate(5, 5)

        self.bone_set = BoneSet(self.frame, self, self.scrolled_window)
        self.set_list_sizer.Add(self.bone_set.set_sizer, 0, wx.EXPAND | wx.ALL, 5)

        # スクロールバーの表示のためにサイズ調整
        self.scrolled_window.SetSizer(self.set_list_sizer)
        self.scrolled_window.Layout()
        self.sizer.Add(self.scrolled_window, 1, wx.ALL | wx.EXPAND | wx.FIXED_MINSIZE, 5)
        self.sizer.Layout()
        self.fit()
    
    def get_bone_pairs(self):
        bone_pairs = {}
        for vrm_bone_txt, pmx_bone_txt in zip(self.bone_set.vrm_bone_txts, self.bone_set.pmx_bone_txts):
            bone_pairs[vrm_bone_txt.GetValue()] = pmx_bone_txt.GetValue()
        return bone_pairs


class BoneSet():

    def __init__(self, frame: wx.Frame, panel: wx.Panel, window: wx.Window):
        self.frame = frame
        self.panel = panel
        self.window = window

        self.vrm_bone_txts = []
        self.arrow_txts = []
        self.pmx_bone_txts = []

        self.set_sizer = wx.BoxSizer(wx.VERTICAL)

        # タイトル部分
        self.grid_sizer = wx.FlexGridSizer(0, 3, 0, 0)
        self.grid_sizer.SetFlexibleDirection(wx.BOTH)
        self.grid_sizer.SetNonFlexibleGrowMode(wx.FLEX_GROWMODE_SPECIFIED)

        self.vrm_bone_header_txt = wx.StaticText(self.window, wx.ID_ANY, u"VRMボーン名", wx.DefaultPosition, (180, wx.DefaultSize[1]), 0)
        self.vrm_bone_header_txt.SetToolTip(u"VRMモデルのボーン名")
        self.vrm_bone_header_txt.Wrap(-1)
        self.grid_sizer.Add(self.vrm_bone_header_txt, 0, wx.ALL, 5)

        self.arrow_header_txt = wx.StaticText(self.window, wx.ID_ANY, u"　→　", wx.DefaultPosition, wx.DefaultSize, 0)
        self.arrow_header_txt.Wrap(-1)
        self.grid_sizer.Add(self.arrow_header_txt, 0, wx.CENTER | wx.ALL, 5)

        self.pmx_bone_header_txt = wx.StaticText(self.window, wx.ID_ANY, u"PMXボーン名", wx.DefaultPosition, (180, wx.DefaultSize[1]), 0)
        self.pmx_bone_header_txt.SetToolTip(u"PMXモデルのボーン名。任意ボーン名に変換可能です。")
        self.pmx_bone_header_txt.Wrap(-1)
        self.grid_sizer.Add(self.pmx_bone_header_txt, 0, wx.ALL, 5)

        for bone_pair in BONE_PAIRS:
            self.vrm_bone_txts.append(wx.TextCtrl(self.window, id=wx.ID_ANY, value=bone_pair[0], style=wx.TE_READONLY, size=(180, wx.DefaultSize[1])))
            self.grid_sizer.Add(self.vrm_bone_txts[-1], 0, wx.ALL, 5)

            self.arrow_txts.append(wx.StaticText(self.window, wx.ID_ANY, u"　→　", wx.DefaultPosition, wx.DefaultSize, 0))
            self.grid_sizer.Add(self.arrow_txts[-1], 0, wx.ALL, 5)

            self.pmx_bone_txts.append(wx.TextCtrl(self.window, id=wx.ID_ANY, value=bone_pair[1], size=(180, wx.DefaultSize[1])))
            self.grid_sizer.Add(self.pmx_bone_txts[-1], 0, wx.ALL, 5)

        self.set_sizer.Add(self.grid_sizer, 0, wx.ALL, 5)


