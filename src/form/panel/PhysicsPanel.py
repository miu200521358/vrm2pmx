# -*- coding: utf-8 -*-
#
import wx
import wx.lib.newevent

from form.panel.BasePanel import BasePanel
from form.panel.BonePanel import BONE_PAIRS, RIGIDBODY_PAIRS
from utils.MLogger import MLogger # noqa

logger = MLogger(__name__)
TIMER_ID = wx.NewId()


class PhysicsPanel(BasePanel):
        
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


