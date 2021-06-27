# -*- coding: utf-8 -*-
#
import wx
import wx.lib.newevent
import csv
import copy
import traceback

from form.panel.BasePanel import BasePanel
from form.panel.BonePanel import BONE_PAIRS, RIGIDBODY_PAIRS
from utils.MLogger import MLogger # noqa

logger = MLogger(__name__)
TIMER_ID = wx.NewId()


class RigidbodyPanel(BasePanel):
        
    def __init__(self, frame: wx.Frame, export: wx.Notebook, tab_idx: int):
        super().__init__(frame, export, tab_idx)
        self.convert_export_worker = None

        self.header_panel = wx.Panel(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        self.header_sizer = wx.BoxSizer(wx.VERTICAL)

        self.description_txt = wx.StaticText(self.header_panel, wx.ID_ANY, "MMD準標準ボーンの剛体パラメーターを設定します。", wx.DefaultPosition, wx.DefaultSize, 0)
        self.header_sizer.Add(self.description_txt, 0, wx.ALL, 5)

        self.header_btn_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # インポートボタン
        self.import_btn_ctrl = wx.Button(self.header_panel, wx.ID_ANY, u"インポート ...", wx.DefaultPosition, wx.DefaultSize, 0)
        self.import_btn_ctrl.SetToolTip(u"剛体設定データをCSVファイルから読み込みます。\nファイル選択ダイアログが開きます。")
        self.import_btn_ctrl.Bind(wx.EVT_BUTTON, self.on_import)
        self.header_btn_sizer.Add(self.import_btn_ctrl, 0, wx.ALL, 5)

        # エクスポートボタン
        self.export_btn_ctrl = wx.Button(self.header_panel, wx.ID_ANY, u"エクスポート ...", wx.DefaultPosition, wx.DefaultSize, 0)
        self.export_btn_ctrl.SetToolTip(u"剛体設定データをCSVファイルに出力します。\nファイル出力先ダイアログが開きます。")
        self.export_btn_ctrl.Bind(wx.EVT_BUTTON, self.on_export)
        self.header_btn_sizer.Add(self.export_btn_ctrl, 0, wx.ALL, 5)

        self.header_sizer.Add(self.header_btn_sizer, 0, wx.ALIGN_RIGHT | wx.ALL, 5)

        # 行追加ボタン
        self.header_panel.SetSizer(self.header_sizer)
        self.header_panel.Layout()
        self.sizer.Add(self.header_panel, 0, wx.EXPAND | wx.ALL, 5)

        # モーフセット用基本Sizer
        self.rigidbody_set_list_sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.scrolled_window = wx.ScrolledWindow(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, \
                                                 wx.FULL_REPAINT_ON_RESIZE | wx.VSCROLL | wx.HSCROLL | wx.ALWAYS_SHOW_SB)
        self.scrolled_window.SetScrollRate(5, 5)

        self.rigidbody_set = RigidbodySet(self.frame, self, self.scrolled_window)
        self.rigidbody_set_list_sizer.Add(self.rigidbody_set.rigidbody_set_sizer, 0, wx.EXPAND | wx.ALL, 5)

        # スクロールバーの表示のためにサイズ調整
        self.scrolled_window.SetSizer(self.rigidbody_set_list_sizer)
        self.scrolled_window.Layout()
        self.sizer.Add(self.scrolled_window, 1, wx.ALL | wx.EXPAND | wx.FIXED_MINSIZE, 5)
        self.sizer.Layout()
        self.fit()
    
    def get_bone_pairs(self):
        bone_pairs = copy.deepcopy(BONE_PAIRS)
        for vrm_bone_txt, pmx_rigidbody_factor_txt, pmx_rigidbody_param_mass_txt, pmx_rigidbody_param_linear_damping_txt, \
            pmx_rigidbody_param_angular_damping_txt, pmx_rigidbody_param_restitution_txt, pmx_rigidbody_param_friction_txt \
            in zip(self.rigidbody_set.vrm_bone_txts, self.rigidbody_set.pmx_rigidbody_factor_txts, \
                   self.rigidbody_set.pmx_rigidbody_param_mass_txts, self.rigidbody_set.pmx_rigidbody_param_linear_damping_txts, \
                   self.rigidbody_set.pmx_rigidbody_param_angular_damping_txts, self.rigidbody_set.pmx_rigidbody_param_restitution_txts, \
                   self.rigidbody_set.pmx_rigidbody_param_friction_txts):
            bone_pairs[vrm_bone_txt]["rigidbodyFactor"] = pmx_rigidbody_factor_txt.GetValue()
            bone_pairs[vrm_bone_txt]["rigidbodyParam"][0] = pmx_rigidbody_param_mass_txt.GetValue()
            bone_pairs[vrm_bone_txt]["rigidbodyParam"][1] = pmx_rigidbody_param_linear_damping_txt.GetValue()
            bone_pairs[vrm_bone_txt]["rigidbodyParam"][2] = pmx_rigidbody_param_angular_damping_txt.GetValue()
            bone_pairs[vrm_bone_txt]["rigidbodyParam"][3] = pmx_rigidbody_param_restitution_txt.GetValue()
            bone_pairs[vrm_bone_txt]["rigidbodyParam"][4] = pmx_rigidbody_param_friction_txt.GetValue()
        return bone_pairs

    def on_import(self, event: wx.Event):
        with wx.FileDialog(self.frame, "剛体設定データCSVを読み込む", wildcard=u"CSVファイル (*.csv)|*.csv|すべてのファイル (*.*)|*.*",
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:

            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return     # the user changed their mind

            # Proceed loading the file chosen by the user
            target_morph_path = fileDialog.GetPath()
            try:
                with open(target_morph_path, 'r') as f:
                    cr = csv.reader(f, delimiter=",", quotechar='"')

                    for row in cr:
                        if row and row[0] in self.rigidbody_set.vrm_bone_txts:
                            rigidbody_idx = [i for i, r in enumerate(list(self.rigidbody_set.vrm_bone_txts)) if r == row[0]][0]
                            self.rigidbody_set.pmx_rigidbody_factor_txts[rigidbody_idx].SetValue(float(row[2]))
                            self.rigidbody_set.pmx_rigidbody_param_mass_txts[rigidbody_idx].SetValue(float(row[3]))
                            self.rigidbody_set.pmx_rigidbody_param_linear_damping_txts[rigidbody_idx].SetValue(float(row[4]))
                            self.rigidbody_set.pmx_rigidbody_param_angular_damping_txts[rigidbody_idx].SetValue(float(row[5]))
                            self.rigidbody_set.pmx_rigidbody_param_restitution_txts[rigidbody_idx].SetValue(float(row[6]))
                            self.rigidbody_set.pmx_rigidbody_param_friction_txts[rigidbody_idx].SetValue(float(row[7]))

            except Exception:
                dialog = wx.MessageDialog(self.frame, "CSVファイルが読み込めませんでした '%s'\n\n%s." % (target_morph_path, traceback.format_exc()), style=wx.OK)
                dialog.ShowModal()
                dialog.Destroy()

    def on_export(self, event: wx.Event):
        with wx.FileDialog(self.frame, "剛体設定データCSVを出力する", wildcard=u"CSVファイル (*.csv)|*.csv|すべてのファイル (*.*)|*.*",
                           style=wx.FLP_OVERWRITE_PROMPT | wx.FLP_SAVE | wx.FLP_USE_TEXTCTRL) as fileDialog:

            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return     # the user changed their mind

            # Proceed loading the file chosen by the user
            target_csv_path = fileDialog.GetPath()
            try:
                with open(target_csv_path, encoding='cp932', mode='w', newline='') as f:
                    cw = csv.writer(f, delimiter=",", quotechar='"', quoting=csv.QUOTE_ALL)

                    for vrm_bone_name, bone_dict in self.get_bone_pairs().items():
                        if bone_dict["rigidBody"]:
                            cw.writerow([vrm_bone_name, bone_dict["name"], bone_dict["rigidbodyFactor"], bone_dict["rigidbodyParam"][0], bone_dict["rigidbodyParam"][1], \
                                        bone_dict["rigidbodyParam"][2], bone_dict["rigidbodyParam"][3], bone_dict["rigidbodyParam"][4]])
                                    
                logger.info("出力成功: %s" % target_csv_path)

                dialog = wx.MessageDialog(self.frame, "剛体設定データCSVのエクスポートに成功しました \n'%s'" % (target_csv_path), style=wx.OK)
                dialog.ShowModal()
                dialog.Destroy()

            except Exception:
                fileDialog = wx.MessageDialog(self.frame, "剛体設定データCSVが出力できませんでした '%s'\n\n%s." % (target_csv_path, traceback.format_exc()), style=wx.OK)
                fileDialog.ShowModal()
                fileDialog.Destroy()


class RigidbodySet():

    def __init__(self, frame: wx.Frame, panel: wx.Panel, window: wx.Window):
        self.frame = frame
        self.panel = panel
        self.window = window

        self.vrm_bone_txts = []
        self.pmx_bone_txts = []
        self.pmx_rigidbody_factor_txts = []
        self.pmx_rigidbody_param_mass_txts = []
        self.pmx_rigidbody_param_linear_damping_txts = []
        self.pmx_rigidbody_param_angular_damping_txts = []
        self.pmx_rigidbody_param_restitution_txts = []
        self.pmx_rigidbody_param_friction_txts = []

        self.rigidbody_set_sizer = wx.BoxSizer(wx.VERTICAL)

        # タイトル部分
        self.grid_sizer = wx.FlexGridSizer(7, 0, 0)
        self.grid_sizer.SetFlexibleDirection(wx.BOTH)
        self.grid_sizer.SetNonFlexibleGrowMode(wx.FLEX_GROWMODE_SPECIFIED)

        for text, tooltip, width in [("PMXボーン名", "VRMモデルから変換したPMXボーン名（準標準まで）", 80), ("大きさ係数", "PMXモデルの剛体の大きさ", 65), \
                                     ("質量", "PMXモデルの剛体の質量", 65), ("移動減衰", "根元剛体の移動減衰（末端との線形補間）", 65), ("回転減衰", "根元剛体の回転減衰（末端との線形補間）", 65), \
                                     ("反発力", "根元剛体の反発力（末端との線形補間）", 65), ("摩擦力", "根元剛体の摩擦力（末端との線形補間）", 65)]:
            txt_ctrl = wx.StaticText(self.window, wx.ID_ANY, text, wx.DefaultPosition, (width, wx.DefaultSize[1]), 0)
            if tooltip:
                txt_ctrl.SetToolTip(tooltip)
            self.grid_sizer.Add(txt_ctrl, 0, wx.ALL, 5)

        for vrm_bone_name, bone_pair in BONE_PAIRS.items():
            if bone_pair["rigidBody"]:
                self.vrm_bone_txts.append(vrm_bone_name)

                self.pmx_bone_txts.append(wx.TextCtrl(self.window, id=wx.ID_ANY, value=bone_pair["name"], style=wx.TE_READONLY, size=(80, wx.DefaultSize[1])))
                self.grid_sizer.Add(self.pmx_bone_txts[-1], 0, wx.ALL, 5)

                self.pmx_rigidbody_factor_txts.append(wx.SpinCtrlDouble(self.window, id=wx.ID_ANY, size=wx.Size(65, -1), value=f"{bone_pair['rigidbodyFactor']}", \
                                                                        min=0, max=999, initial=bone_pair['rigidbodyFactor'], inc=0.001))
                self.grid_sizer.Add(self.pmx_rigidbody_factor_txts[-1], 0, wx.ALL, 5)

                self.pmx_rigidbody_param_mass_txts.append( \
                    wx.SpinCtrlDouble(self.window, id=wx.ID_ANY, size=wx.Size(65, -1), value=f"{bone_pair['rigidbodyParam'][0]}", \
                                      min=0, max=999, initial=bone_pair['rigidbodyParam'][0], inc=0.001))
                self.pmx_rigidbody_param_mass_txts[-1].Bind(wx.EVT_MOUSEWHEEL, lambda event: self.frame.on_wheel_spin_ctrl(event, 0.001))
                self.grid_sizer.Add(self.pmx_rigidbody_param_mass_txts[-1], 0, wx.ALL, 5)

                self.pmx_rigidbody_param_linear_damping_txts.append( \
                    wx.SpinCtrlDouble(self.window, id=wx.ID_ANY, size=wx.Size(65, -1), value=f"{bone_pair['rigidbodyParam'][1]}", \
                                      min=0, max=999, initial=bone_pair['rigidbodyParam'][1], inc=0.001))
                self.pmx_rigidbody_param_linear_damping_txts[-1].Bind(wx.EVT_MOUSEWHEEL, lambda event: self.frame.on_wheel_spin_ctrl(event, 0.001))
                self.grid_sizer.Add(self.pmx_rigidbody_param_linear_damping_txts[-1], 0, wx.ALL, 5)

                self.pmx_rigidbody_param_angular_damping_txts.append( \
                    wx.SpinCtrlDouble(self.window, id=wx.ID_ANY, size=wx.Size(65, -1), value=f"{bone_pair['rigidbodyParam'][2]}", \
                                      min=0, max=999, initial=bone_pair['rigidbodyParam'][2], inc=0.001))
                self.pmx_rigidbody_param_angular_damping_txts[-1].Bind(wx.EVT_MOUSEWHEEL, lambda event: self.frame.on_wheel_spin_ctrl(event, 0.001))
                self.grid_sizer.Add(self.pmx_rigidbody_param_angular_damping_txts[-1], 0, wx.ALL, 5)

                self.pmx_rigidbody_param_restitution_txts.append( \
                    wx.SpinCtrlDouble(self.window, id=wx.ID_ANY, size=wx.Size(65, -1), value=f"{bone_pair['rigidbodyParam'][3]}", \
                                      min=0, max=999, initial=bone_pair['rigidbodyParam'][3], inc=0.001))
                self.pmx_rigidbody_param_restitution_txts[-1].Bind(wx.EVT_MOUSEWHEEL, lambda event: self.frame.on_wheel_spin_ctrl(event, 0.001))
                self.grid_sizer.Add(self.pmx_rigidbody_param_restitution_txts[-1], 0, wx.ALL, 5)

                self.pmx_rigidbody_param_friction_txts.append( \
                    wx.SpinCtrlDouble(self.window, id=wx.ID_ANY, size=wx.Size(65, -1), value=f"{bone_pair['rigidbodyParam'][4]}", \
                                      min=0, max=999, initial=bone_pair['rigidbodyParam'][4], inc=0.001))
                self.pmx_rigidbody_param_friction_txts[-1].Bind(wx.EVT_MOUSEWHEEL, lambda event: self.frame.on_wheel_spin_ctrl(event, 0.001))
                self.grid_sizer.Add(self.pmx_rigidbody_param_friction_txts[-1], 0, wx.ALL, 5)

        self.rigidbody_set_sizer.Add(self.grid_sizer, 0, wx.ALL, 5)


