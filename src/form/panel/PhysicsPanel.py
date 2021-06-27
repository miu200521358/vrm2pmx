# -*- coding: utf-8 -*-
#
import wx
import wx.lib.newevent
import csv
import copy
import traceback

from form.panel.BasePanel import BasePanel
from form.panel.BonePanel import RIGIDBODY_PAIRS
from utils.MLogger import MLogger # noqa

logger = MLogger(__name__)
TIMER_ID = wx.NewId()


class PhysicsPanel(BasePanel):
        
    def __init__(self, frame: wx.Frame, export: wx.Notebook, tab_idx: int):
        super().__init__(frame, export, tab_idx)
        self.convert_export_worker = None

        self.header_panel = wx.Panel(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        self.header_sizer = wx.BoxSizer(wx.VERTICAL)

        self.description_txt = wx.StaticText(self.header_panel, wx.ID_ANY, "MMD準標準ボーンの以外の物理パラメーターを設定します。", wx.DefaultPosition, wx.DefaultSize, 0)
        self.header_sizer.Add(self.description_txt, 0, wx.ALL, 5)

        self.header_btn_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # インポートボタン
        self.import_btn_ctrl = wx.Button(self.header_panel, wx.ID_ANY, u"インポート ...", wx.DefaultPosition, wx.DefaultSize, 0)
        self.import_btn_ctrl.SetToolTip(u"物理設定データをCSVファイルから読み込みます。\nファイル選択ダイアログが開きます。")
        self.import_btn_ctrl.Bind(wx.EVT_BUTTON, self.on_import)
        self.header_btn_sizer.Add(self.import_btn_ctrl, 0, wx.ALL, 5)

        # エクスポートボタン
        self.export_btn_ctrl = wx.Button(self.header_panel, wx.ID_ANY, u"エクスポート ...", wx.DefaultPosition, wx.DefaultSize, 0)
        self.export_btn_ctrl.SetToolTip(u"物理設定データをCSVファイルに出力します。\nファイル出力先ダイアログが開きます。")
        self.export_btn_ctrl.Bind(wx.EVT_BUTTON, self.on_export)
        self.header_btn_sizer.Add(self.export_btn_ctrl, 0, wx.ALL, 5)

        self.header_sizer.Add(self.header_btn_sizer, 0, wx.ALIGN_RIGHT | wx.ALL, 5)

        self.header_panel.SetSizer(self.header_sizer)
        self.header_panel.Layout()
        self.sizer.Add(self.header_panel, 0, wx.EXPAND | wx.ALL, 5)

        # 物理セット用基本Sizer
        self.physics_set_list_sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.scrolled_window = wx.ScrolledWindow(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, \
                                                 wx.FULL_REPAINT_ON_RESIZE | wx.VSCROLL | wx.ALWAYS_SHOW_SB)
        self.scrolled_window.SetScrollRate(5, 5)

        self.physics_sets = {}
        for rigidbody_name, rigidbody_dict in RIGIDBODY_PAIRS.items():
            self.physics_sets[rigidbody_name] = PhysicsSet(self.frame, self, self.scrolled_window, rigidbody_name, rigidbody_dict)
            self.physics_set_list_sizer.Add(self.physics_sets[rigidbody_name].physics_set_sizer, 0, wx.EXPAND | wx.ALL, 5)

        # スクロールバーの表示のためにサイズ調整
        self.scrolled_window.SetSizer(self.physics_set_list_sizer)
        self.scrolled_window.Layout()
        self.sizer.Add(self.scrolled_window, 1, wx.ALL | wx.EXPAND | wx.FIXED_MINSIZE, 5)
        self.sizer.Layout()
        self.fit()
    
    def get_physics_pairs(self):
        rigidbody_pairs = copy.deepcopy(RIGIDBODY_PAIRS)

        for rigidbody_name, physics_set in self.physics_sets.items():
            rigidbody_cnt = 0
            if "rigidBody" in rigidbody_pairs[rigidbody_name]:
                rigidbody_pairs[rigidbody_name]["rigidbodySubdivision"] = physics_set.physics_ctrls[0].GetValue()
                rigidbody_pairs[rigidbody_name]["rigidbodyFactor"] = physics_set.physics_ctrls[1].GetValue()
                rigidbody_pairs[rigidbody_name]["rigidbodyParamFrom"][1] = physics_set.physics_ctrls[2].GetValue()
                rigidbody_pairs[rigidbody_name]["rigidbodyParamFrom"][2] = physics_set.physics_ctrls[3].GetValue()
                rigidbody_pairs[rigidbody_name]["rigidbodyParamFrom"][3] = physics_set.physics_ctrls[4].GetValue()
                rigidbody_pairs[rigidbody_name]["rigidbodyParamFrom"][4] = physics_set.physics_ctrls[5].GetValue()

                rigidbody_pairs[rigidbody_name]["rigidbodyParamTo"][0] = physics_set.physics_ctrls[6].GetValue()
                rigidbody_pairs[rigidbody_name]["rigidbodyCoefficient"] = physics_set.physics_ctrls[7].GetValue()
                rigidbody_pairs[rigidbody_name]["rigidbodyParamTo"][1] = physics_set.physics_ctrls[8].GetValue()
                rigidbody_pairs[rigidbody_name]["rigidbodyParamTo"][2] = physics_set.physics_ctrls[9].GetValue()
                rigidbody_pairs[rigidbody_name]["rigidbodyParamTo"][3] = physics_set.physics_ctrls[10].GetValue()
                rigidbody_pairs[rigidbody_name]["rigidbodyParamTo"][4] = physics_set.physics_ctrls[11].GetValue()
                rigidbody_cnt = 12

            rigidbody_pairs[rigidbody_name]["JointTLMin"][0] = physics_set.physics_ctrls[0 + rigidbody_cnt].GetValue()
            rigidbody_pairs[rigidbody_name]["JointTLMax"][0] = physics_set.physics_ctrls[1 + rigidbody_cnt].GetValue()
            rigidbody_pairs[rigidbody_name]["JointTLMin"][1] = physics_set.physics_ctrls[2 + rigidbody_cnt].GetValue()
            rigidbody_pairs[rigidbody_name]["JointTLMax"][1] = physics_set.physics_ctrls[3 + rigidbody_cnt].GetValue()
            rigidbody_pairs[rigidbody_name]["JointTLMin"][2] = physics_set.physics_ctrls[4 + rigidbody_cnt].GetValue()
            rigidbody_pairs[rigidbody_name]["JointTLMax"][2] = physics_set.physics_ctrls[5 + rigidbody_cnt].GetValue()

            rigidbody_pairs[rigidbody_name]["JointRLMin"][0] = physics_set.physics_ctrls[6 + rigidbody_cnt].GetValue()
            rigidbody_pairs[rigidbody_name]["JointRLMax"][0] = physics_set.physics_ctrls[7 + rigidbody_cnt].GetValue()
            rigidbody_pairs[rigidbody_name]["JointRLMin"][1] = physics_set.physics_ctrls[8 + rigidbody_cnt].GetValue()
            rigidbody_pairs[rigidbody_name]["JointRLMax"][1] = physics_set.physics_ctrls[9 + rigidbody_cnt].GetValue()
            rigidbody_pairs[rigidbody_name]["JointRLMin"][2] = physics_set.physics_ctrls[10 + rigidbody_cnt].GetValue()
            rigidbody_pairs[rigidbody_name]["JointRLMax"][2] = physics_set.physics_ctrls[11 + rigidbody_cnt].GetValue()

            rigidbody_pairs[rigidbody_name]["JointSCT"][0] = physics_set.physics_ctrls[12 + rigidbody_cnt].GetValue()
            rigidbody_pairs[rigidbody_name]["JointSCT"][1] = physics_set.physics_ctrls[13 + rigidbody_cnt].GetValue()
            rigidbody_pairs[rigidbody_name]["JointSCT"][2] = physics_set.physics_ctrls[14 + rigidbody_cnt].GetValue()
            rigidbody_pairs[rigidbody_name]["JointSCR"][0] = physics_set.physics_ctrls[15 + rigidbody_cnt].GetValue()
            rigidbody_pairs[rigidbody_name]["JointSCR"][1] = physics_set.physics_ctrls[16 + rigidbody_cnt].GetValue()
            rigidbody_pairs[rigidbody_name]["JointSCR"][2] = physics_set.physics_ctrls[17 + rigidbody_cnt].GetValue()

        return rigidbody_pairs

    def on_import(self, event: wx.Event):
        with wx.FileDialog(self.frame, "物理設定データCSVを読み込む", wildcard=u"CSVファイル (*.csv)|*.csv|すべてのファイル (*.*)|*.*",
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:

            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return     # the user changed their mind

            # Proceed loading the file chosen by the user
            target_morph_path = fileDialog.GetPath()
            try:
                with open(target_morph_path, 'r') as f:
                    cr = csv.reader(f, delimiter=",", quotechar='"')

                    for row in cr:
                        if row and row[0] in self.physics_sets:
                            for ri, r in enumerate(row):
                                if ri == 0:
                                    continue
                                elif ri == 1:
                                    self.physics_sets[row[0]].physics_ctrls[ri - 1].SetValue(int(float(r)))
                                else:
                                    self.physics_sets[row[0]].physics_ctrls[ri - 1].SetValue(float(r))
            except Exception:
                dialog = wx.MessageDialog(self.frame, "CSVファイルが読み込めませんでした '%s'\n\n%s." % (target_morph_path, traceback.format_exc()), style=wx.OK)
                dialog.ShowModal()
                dialog.Destroy()

    def on_export(self, event: wx.Event):
        with wx.FileDialog(self.frame, "物理設定データCSVを出力する", wildcard=u"CSVファイル (*.csv)|*.csv|すべてのファイル (*.*)|*.*",
                           style=wx.FLP_OVERWRITE_PROMPT | wx.FLP_SAVE | wx.FLP_USE_TEXTCTRL) as fileDialog:

            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return     # the user changed their mind

            # Proceed loading the file chosen by the user
            target_csv_path = fileDialog.GetPath()
            try:
                with open(target_csv_path, encoding='cp932', mode='w', newline='') as f:
                    cw = csv.writer(f, delimiter=",", quotechar='"', quoting=csv.QUOTE_ALL)

                    for vrm_bone_name, physics_dict in self.get_physics_pairs().items():
                        row = []
                        if "rigidBody" in physics_dict:
                            row = [vrm_bone_name, physics_dict["rigidbodySubdivision"], physics_dict["rigidbodyFactor"], physics_dict["rigidbodyParamFrom"][1], \
                                   physics_dict["rigidbodyParamFrom"][2], physics_dict["rigidbodyParamFrom"][3], \
                                   physics_dict["rigidbodyParamFrom"][4], physics_dict["rigidbodyParamTo"][0], physics_dict["rigidbodyCoefficient"], \
                                   physics_dict["rigidbodyParamTo"][1], physics_dict["rigidbodyParamTo"][2], \
                                   physics_dict["rigidbodyParamTo"][3], physics_dict["rigidbodyParamTo"][4]]
                        row += [physics_dict["JointTLMin"][0], physics_dict["JointTLMax"][0], physics_dict["JointTLMin"][1], \
                                physics_dict["JointTLMax"][1], physics_dict["JointTLMin"][2], physics_dict["JointTLMax"][2], \
                                physics_dict["JointRLMin"][0], physics_dict["JointRLMax"][0], physics_dict["JointRLMin"][1], \
                                physics_dict["JointRLMax"][1], physics_dict["JointRLMin"][2], physics_dict["JointRLMax"][2], \
                                physics_dict["JointSCT"][0], physics_dict["JointSCT"][1], physics_dict["JointSCT"][2], \
                                physics_dict["JointSCR"][0], physics_dict["JointSCR"][1], physics_dict["JointSCR"][2]]
                        cw.writerow(row)
                logger.info("出力成功: %s" % target_csv_path)

                dialog = wx.MessageDialog(self.frame, "物理設定データCSVのエクスポートに成功しました \n'%s'" % (target_csv_path), style=wx.OK)
                dialog.ShowModal()
                dialog.Destroy()

            except Exception:
                fileDialog = wx.MessageDialog(self.frame, "物理設定データCSVが出力できませんでした '%s'\n\n%s." % (target_csv_path, traceback.format_exc()), style=wx.OK)
                fileDialog.ShowModal()
                fileDialog.Destroy()


class PhysicsSet():

    def __init__(self, frame: wx.Frame, panel: wx.Panel, window: wx.Window, vrm_bone_name: str, rigidbody_dict: dict):
        self.frame = frame
        self.panel = panel
        self.window = window
        self.vrm_bone_name = vrm_bone_name
        self.physics_pair = copy.deepcopy(rigidbody_dict)

        self.physics_set_sizer = wx.StaticBoxSizer(wx.StaticBox(self.window, wx.ID_ANY, f"【{vrm_bone_name}】"), orient=wx.VERTICAL)

        # タイトル部分
        self.grid_sizer = wx.FlexGridSizer(6, 0, 0)
        self.grid_sizer.SetFlexibleDirection(wx.BOTH)
        self.grid_sizer.SetNonFlexibleGrowMode(wx.FLEX_GROWMODE_SPECIFIED)

        # 物理情報
        self.physics_ctrls = []
        
        if "rigidbodyFactor" in self.physics_pair:
            # 剛体根元ヘッダ --------------

            for text in ["根元剛体", "", "", "", "", ""]:
                self.grid_sizer.Add(wx.StaticText(self.window, wx.ID_ANY, text, wx.DefaultPosition, (75, wx.DefaultSize[1]), 0), 0, wx.ALL, 5)

            for text, tooltip in [("細分化", "ボーン間を細分化する個数"), ("大きさ", "一致する名称剛体すべての大きさ（均一）"), \
                                  ("移動減衰", "根元剛体の移動減衰（末端との線形補間）"), ("回転減衰", "根元剛体の回転減衰（末端との線形補間）"), \
                                  ("反発力", "根元剛体の反発力（末端との線形補間）"), ("摩擦力", "根元剛体の摩擦力（末端との線形補間）")]:
                txt_ctrl = wx.StaticText(self.window, wx.ID_ANY, text, wx.DefaultPosition, (75, wx.DefaultSize[1]), 0)
                if tooltip:
                    txt_ctrl.SetToolTip(tooltip)
                self.grid_sizer.Add(txt_ctrl, 0, wx.ALL, 5)

            # 剛体根元値 ---------

            self.physics_ctrls.append(wx.SpinCtrl(self.window, id=wx.ID_ANY, size=wx.Size(75, -1), value=f"{self.physics_pair['rigidbodySubdivision']}", \
                                                  min=1, max=3, initial=self.physics_pair['rigidbodySubdivision']))
            self.physics_ctrls[-1].Bind(wx.EVT_MOUSEWHEEL, lambda event: self.frame.on_wheel_spin_ctrl(event, 1))
            self.grid_sizer.Add(self.physics_ctrls[-1], 0, wx.ALL, 5)

            self.physics_ctrls.append(wx.SpinCtrlDouble(self.window, id=wx.ID_ANY, size=wx.Size(75, -1), value=f"{self.physics_pair['rigidbodyFactor']}", \
                                                        min=0, max=999, initial=self.physics_pair['rigidbodyFactor'], inc=0.001))
            self.physics_ctrls[-1].Bind(wx.EVT_MOUSEWHEEL, lambda event: self.frame.on_wheel_spin_ctrl(event, 0.001))
            self.grid_sizer.Add(self.physics_ctrls[-1], 0, wx.ALL, 5)

            self.physics_ctrls.append(wx.SpinCtrlDouble(self.window, id=wx.ID_ANY, size=wx.Size(75, -1), value=f"{self.physics_pair['rigidbodyParamFrom'][1]}", \
                                                        min=0, max=999, initial=self.physics_pair['rigidbodyParamFrom'][1], inc=0.001))
            self.physics_ctrls[-1].Bind(wx.EVT_MOUSEWHEEL, lambda event: self.frame.on_wheel_spin_ctrl(event, 0.001))
            self.grid_sizer.Add(self.physics_ctrls[-1], 0, wx.ALL, 5)

            self.physics_ctrls.append(wx.SpinCtrlDouble(self.window, id=wx.ID_ANY, size=wx.Size(75, -1), value=f"{self.physics_pair['rigidbodyParamFrom'][2]}", \
                                                        min=0, max=999, initial=self.physics_pair['rigidbodyParamFrom'][2], inc=0.001))
            self.physics_ctrls[-1].Bind(wx.EVT_MOUSEWHEEL, lambda event: self.frame.on_wheel_spin_ctrl(event, 0.001))
            self.grid_sizer.Add(self.physics_ctrls[-1], 0, wx.ALL, 5)

            self.physics_ctrls.append(wx.SpinCtrlDouble(self.window, id=wx.ID_ANY, size=wx.Size(75, -1), value=f"{self.physics_pair['rigidbodyParamFrom'][3]}", \
                                                        min=0, max=999, initial=self.physics_pair['rigidbodyParamFrom'][3], inc=0.001))
            self.physics_ctrls[-1].Bind(wx.EVT_MOUSEWHEEL, lambda event: self.frame.on_wheel_spin_ctrl(event, 0.001))
            self.grid_sizer.Add(self.physics_ctrls[-1], 0, wx.ALL, 5)

            self.physics_ctrls.append(wx.SpinCtrlDouble(self.window, id=wx.ID_ANY, size=wx.Size(75, -1), value=f"{self.physics_pair['rigidbodyParamFrom'][4]}", \
                                      min=0, max=999, initial=self.physics_pair['rigidbodyParamFrom'][4], inc=0.001))
            self.physics_ctrls[-1].Bind(wx.EVT_MOUSEWHEEL, lambda event: self.frame.on_wheel_spin_ctrl(event, 0.001))
            self.grid_sizer.Add(self.physics_ctrls[-1], 0, wx.ALL, 5)

            # 剛体根元ヘッダ --------------

            for text in ["末端剛体", "", "", "", "", ""]:
                self.grid_sizer.Add(wx.StaticText(self.window, wx.ID_ANY, text, wx.DefaultPosition, (75, wx.DefaultSize[1]), 0), 0, wx.ALL, 5)

            for text, tooltip in [("質量", "末端剛体の質量"), ("質量係数", "末端剛体の質量から根元にかけての増加係数"), \
                                  ("移動減衰", "末端交代の移動減衰（根元との線形補間）"), ("回転減衰", "末端交代の回転減衰（根元との線形補間）"), \
                                  ("反発力", "末端交代の反発力（根元との線形補間）"), ("摩擦力", "末端交代の摩擦力（根元との線形補間）")]:
                txt_ctrl = wx.StaticText(self.window, wx.ID_ANY, text, wx.DefaultPosition, (75, wx.DefaultSize[1]), 0)
                if tooltip:
                    txt_ctrl.SetToolTip(tooltip)
                self.grid_sizer.Add(txt_ctrl, 0, wx.ALL, 5)

            # 剛体末端値 ---------

            self.physics_ctrls.append(wx.SpinCtrlDouble(self.window, id=wx.ID_ANY, size=wx.Size(75, -1), value=f"{self.physics_pair['rigidbodyParamTo'][0]}", \
                                                        min=0, max=999, initial=self.physics_pair['rigidbodyParamTo'][0], inc=0.001))
            self.physics_ctrls[-1].Bind(wx.EVT_MOUSEWHEEL, lambda event: self.frame.on_wheel_spin_ctrl(event, 0.001))
            self.grid_sizer.Add(self.physics_ctrls[-1], 0, wx.ALL, 5)

            self.physics_ctrls.append(wx.SpinCtrlDouble(self.window, id=wx.ID_ANY, size=wx.Size(75, -1), value=f"{self.physics_pair['rigidbodyCoefficient']}", \
                                                        min=0, max=999, initial=self.physics_pair['rigidbodyCoefficient'], inc=0.001))
            self.physics_ctrls[-1].Bind(wx.EVT_MOUSEWHEEL, lambda event: self.frame.on_wheel_spin_ctrl(event, 0.001))
            self.grid_sizer.Add(self.physics_ctrls[-1], 0, wx.ALL, 5)

            self.physics_ctrls.append(wx.SpinCtrlDouble(self.window, id=wx.ID_ANY, size=wx.Size(75, -1), value=f"{self.physics_pair['rigidbodyParamTo'][1]}", \
                                                        min=0, max=999, initial=self.physics_pair['rigidbodyParamTo'][1], inc=0.001))
            self.physics_ctrls[-1].Bind(wx.EVT_MOUSEWHEEL, lambda event: self.frame.on_wheel_spin_ctrl(event, 0.001))
            self.grid_sizer.Add(self.physics_ctrls[-1], 0, wx.ALL, 5)

            self.physics_ctrls.append(wx.SpinCtrlDouble(self.window, id=wx.ID_ANY, size=wx.Size(75, -1), value=f"{self.physics_pair['rigidbodyParamTo'][2]}", \
                                                        min=0, max=999, initial=self.physics_pair['rigidbodyParamTo'][2], inc=0.001))
            self.physics_ctrls[-1].Bind(wx.EVT_MOUSEWHEEL, lambda event: self.frame.on_wheel_spin_ctrl(event, 0.001))
            self.grid_sizer.Add(self.physics_ctrls[-1], 0, wx.ALL, 5)

            self.physics_ctrls.append(wx.SpinCtrlDouble(self.window, id=wx.ID_ANY, size=wx.Size(75, -1), value=f"{self.physics_pair['rigidbodyParamTo'][3]}", \
                                                        min=0, max=999, initial=self.physics_pair['rigidbodyParamTo'][3], inc=0.001))
            self.physics_ctrls[-1].Bind(wx.EVT_MOUSEWHEEL, lambda event: self.frame.on_wheel_spin_ctrl(event, 0.001))
            self.grid_sizer.Add(self.physics_ctrls[-1], 0, wx.ALL, 5)

            self.physics_ctrls.append(wx.SpinCtrlDouble(self.window, id=wx.ID_ANY, size=wx.Size(75, -1), value=f"{self.physics_pair['rigidbodyParamTo'][4]}", \
                                                        min=0, max=999, initial=self.physics_pair['rigidbodyParamTo'][4], inc=0.001))
            self.physics_ctrls[-1].Bind(wx.EVT_MOUSEWHEEL, lambda event: self.frame.on_wheel_spin_ctrl(event, 0.001))
            self.grid_sizer.Add(self.physics_ctrls[-1], 0, wx.ALL, 5)

        # 移動制限ヘッダ --------------

        for text in ["ジョイント", "移動制限", "", "", "", ""]:
            self.grid_sizer.Add(wx.StaticText(self.window, wx.ID_ANY, text, wx.DefaultPosition, (75, wx.DefaultSize[1]), 0), 0, wx.ALL, 5)

        for text, tooltip in [("移動X最小", "移動Xの最小値"), ("移動X最大", "移動Xの最大値"), \
                              ("移動Y最小", "移動Yの最小値"), ("移動Y最大", "移動Yの最大値"), \
                              ("移動Z最小", "移動Zの最小値"), ("移動Z最大", "移動Zの最大値")]:
            txt_ctrl = wx.StaticText(self.window, wx.ID_ANY, text, wx.DefaultPosition, (75, wx.DefaultSize[1]), 0)
            if tooltip:
                txt_ctrl.SetToolTip(tooltip)
            self.grid_sizer.Add(txt_ctrl, 0, wx.ALL, 5)

        # 移動制限値 --------------

        self.physics_ctrls.append(wx.SpinCtrlDouble(self.window, id=wx.ID_ANY, size=wx.Size(75, -1), value=f"{self.physics_pair['JointTLMin'][0]}", \
                                                    min=-999, max=999, initial=self.physics_pair['JointTLMin'][0], inc=0.001))
        self.physics_ctrls[-1].Bind(wx.EVT_MOUSEWHEEL, lambda event: self.frame.on_wheel_spin_ctrl(event, 0.001))
        self.grid_sizer.Add(self.physics_ctrls[-1], 0, wx.ALL, 5)

        self.physics_ctrls.append(wx.SpinCtrlDouble(self.window, id=wx.ID_ANY, size=wx.Size(75, -1), value=f"{self.physics_pair['JointTLMax'][0]}", \
                                                    min=-999, max=999, initial=self.physics_pair['JointTLMax'][0], inc=0.001))
        self.physics_ctrls[-1].Bind(wx.EVT_MOUSEWHEEL, lambda event: self.frame.on_wheel_spin_ctrl(event, 0.001))
        self.grid_sizer.Add(self.physics_ctrls[-1], 0, wx.ALL, 5)

        self.physics_ctrls.append(wx.SpinCtrlDouble(self.window, id=wx.ID_ANY, size=wx.Size(75, -1), value=f"{self.physics_pair['JointTLMin'][1]}", \
                                                    min=-999, max=999, initial=self.physics_pair['JointTLMin'][1], inc=0.001))
        self.physics_ctrls[-1].Bind(wx.EVT_MOUSEWHEEL, lambda event: self.frame.on_wheel_spin_ctrl(event, 0.001))
        self.grid_sizer.Add(self.physics_ctrls[-1], 0, wx.ALL, 5)

        self.physics_ctrls.append(wx.SpinCtrlDouble(self.window, id=wx.ID_ANY, size=wx.Size(75, -1), value=f"{self.physics_pair['JointTLMax'][1]}", \
                                                    min=-999, max=999, initial=self.physics_pair['JointTLMax'][1], inc=0.001))
        self.physics_ctrls[-1].Bind(wx.EVT_MOUSEWHEEL, lambda event: self.frame.on_wheel_spin_ctrl(event, 0.001))
        self.grid_sizer.Add(self.physics_ctrls[-1], 0, wx.ALL, 5)

        self.physics_ctrls.append(wx.SpinCtrlDouble(self.window, id=wx.ID_ANY, size=wx.Size(75, -1), value=f"{self.physics_pair['JointTLMin'][2]}", \
                                                    min=-999, max=999, initial=self.physics_pair['JointTLMin'][2], inc=0.001))
        self.physics_ctrls[-1].Bind(wx.EVT_MOUSEWHEEL, lambda event: self.frame.on_wheel_spin_ctrl(event, 0.001))
        self.grid_sizer.Add(self.physics_ctrls[-1], 0, wx.ALL, 5)

        self.physics_ctrls.append(wx.SpinCtrlDouble(self.window, id=wx.ID_ANY, size=wx.Size(75, -1), value=f"{self.physics_pair['JointTLMax'][2]}", \
                                                    min=-999, max=999, initial=self.physics_pair['JointTLMax'][2], inc=0.001))
        self.physics_ctrls[-1].Bind(wx.EVT_MOUSEWHEEL, lambda event: self.frame.on_wheel_spin_ctrl(event, 0.001))
        self.grid_sizer.Add(self.physics_ctrls[-1], 0, wx.ALL, 5)

        # 回転制限ヘッダ --------------

        for text in ["ジョイント", "回転制限", "", "", "", ""]:
            self.grid_sizer.Add(wx.StaticText(self.window, wx.ID_ANY, text, wx.DefaultPosition, (75, wx.DefaultSize[1]), 0), 0, wx.ALL, 5)

        for text, tooltip in [("回転X最小", "回転Xの最小値"), ("回転X最大", "回転Xの最大値"), \
                              ("回転Y最小", "回転Yの最小値"), ("回転Y最大", "回転Yの最大値"), \
                              ("回転Z最小", "回転Zの最小値"), ("回転Z最大", "回転Zの最大値")]:
            txt_ctrl = wx.StaticText(self.window, wx.ID_ANY, text, wx.DefaultPosition, (75, wx.DefaultSize[1]), 0)
            if tooltip:
                txt_ctrl.SetToolTip(tooltip)
            self.grid_sizer.Add(txt_ctrl, 0, wx.ALL, 5)

        # 回転制限値 --------------

        self.physics_ctrls.append(wx.SpinCtrlDouble(self.window, id=wx.ID_ANY, size=wx.Size(75, -1), value=f"{self.physics_pair['JointRLMin'][0]}", \
                                                    min=-999, max=999, initial=self.physics_pair['JointRLMin'][0], inc=0.001))
        self.physics_ctrls[-1].Bind(wx.EVT_MOUSEWHEEL, lambda event: self.frame.on_wheel_spin_ctrl(event, 0.001))
        self.grid_sizer.Add(self.physics_ctrls[-1], 0, wx.ALL, 5)

        self.physics_ctrls.append(wx.SpinCtrlDouble(self.window, id=wx.ID_ANY, size=wx.Size(75, -1), value=f"{self.physics_pair['JointRLMax'][0]}", \
                                                    min=-999, max=999, initial=self.physics_pair['JointRLMax'][0], inc=0.001))
        self.physics_ctrls[-1].Bind(wx.EVT_MOUSEWHEEL, lambda event: self.frame.on_wheel_spin_ctrl(event, 0.001))
        self.grid_sizer.Add(self.physics_ctrls[-1], 0, wx.ALL, 5)

        self.physics_ctrls.append(wx.SpinCtrlDouble(self.window, id=wx.ID_ANY, size=wx.Size(75, -1), value=f"{self.physics_pair['JointRLMin'][1]}", \
                                                    min=-999, max=999, initial=self.physics_pair['JointRLMin'][1], inc=0.001))
        self.physics_ctrls[-1].Bind(wx.EVT_MOUSEWHEEL, lambda event: self.frame.on_wheel_spin_ctrl(event, 0.001))
        self.grid_sizer.Add(self.physics_ctrls[-1], 0, wx.ALL, 5)

        self.physics_ctrls.append(wx.SpinCtrlDouble(self.window, id=wx.ID_ANY, size=wx.Size(75, -1), value=f"{self.physics_pair['JointRLMax'][1]}", \
                                                    min=-999, max=999, initial=self.physics_pair['JointRLMax'][1], inc=0.001))
        self.physics_ctrls[-1].Bind(wx.EVT_MOUSEWHEEL, lambda event: self.frame.on_wheel_spin_ctrl(event, 0.001))
        self.grid_sizer.Add(self.physics_ctrls[-1], 0, wx.ALL, 5)

        self.physics_ctrls.append(wx.SpinCtrlDouble(self.window, id=wx.ID_ANY, size=wx.Size(75, -1), value=f"{self.physics_pair['JointRLMin'][2]}", \
                                                    min=-999, max=999, initial=self.physics_pair['JointRLMin'][2], inc=0.001))
        self.physics_ctrls[-1].Bind(wx.EVT_MOUSEWHEEL, lambda event: self.frame.on_wheel_spin_ctrl(event, 0.001))
        self.grid_sizer.Add(self.physics_ctrls[-1], 0, wx.ALL, 5)

        self.physics_ctrls.append(wx.SpinCtrlDouble(self.window, id=wx.ID_ANY, size=wx.Size(75, -1), value=f"{self.physics_pair['JointRLMax'][2]}", \
                                                    min=-999, max=999, initial=self.physics_pair['JointRLMax'][2], inc=0.001))
        self.physics_ctrls[-1].Bind(wx.EVT_MOUSEWHEEL, lambda event: self.frame.on_wheel_spin_ctrl(event, 0.001))
        self.grid_sizer.Add(self.physics_ctrls[-1], 0, wx.ALL, 5)

        # ばねヘッダ --------------

        for text in ["ジョイント", "ばね", "", "", "", ""]:
            self.grid_sizer.Add(wx.StaticText(self.window, wx.ID_ANY, text, wx.DefaultPosition, (75, wx.DefaultSize[1]), 0), 0, wx.ALL, 5)

        for text, tooltip in [("移動X", "移動Xのばね値"), ("移動Y", "移動Yのばね値"), ("移動Z", "移動Zのばね値"), \
                              ("回転X", "回転Xのばね値"), ("回転Y", "回転Yのばね値"), ("回転Z", "回転Zのばね値")]:
            txt_ctrl = wx.StaticText(self.window, wx.ID_ANY, text, wx.DefaultPosition, (75, wx.DefaultSize[1]), 0)
            if tooltip:
                txt_ctrl.SetToolTip(tooltip)
            self.grid_sizer.Add(txt_ctrl, 0, wx.ALL, 5)

        # ばね値 --------------

        self.physics_ctrls.append(wx.SpinCtrlDouble(self.window, id=wx.ID_ANY, size=wx.Size(75, -1), value=f"{self.physics_pair['JointSCT'][0]}", \
                                                    min=-999, max=999, initial=self.physics_pair['JointSCT'][0], inc=0.001))
        self.physics_ctrls[-1].Bind(wx.EVT_MOUSEWHEEL, lambda event: self.frame.on_wheel_spin_ctrl(event, 0.001))
        self.grid_sizer.Add(self.physics_ctrls[-1], 0, wx.ALL, 5)

        self.physics_ctrls.append(wx.SpinCtrlDouble(self.window, id=wx.ID_ANY, size=wx.Size(75, -1), value=f"{self.physics_pair['JointSCT'][1]}", \
                                                    min=-999, max=999, initial=self.physics_pair['JointSCT'][1], inc=0.001))
        self.physics_ctrls[-1].Bind(wx.EVT_MOUSEWHEEL, lambda event: self.frame.on_wheel_spin_ctrl(event, 0.001))
        self.grid_sizer.Add(self.physics_ctrls[-1], 0, wx.ALL, 5)

        self.physics_ctrls.append(wx.SpinCtrlDouble(self.window, id=wx.ID_ANY, size=wx.Size(75, -1), value=f"{self.physics_pair['JointSCT'][2]}", \
                                                    min=-999, max=999, initial=self.physics_pair['JointSCT'][2], inc=0.001))
        self.physics_ctrls[-1].Bind(wx.EVT_MOUSEWHEEL, lambda event: self.frame.on_wheel_spin_ctrl(event, 0.001))
        self.grid_sizer.Add(self.physics_ctrls[-1], 0, wx.ALL, 5)

        self.physics_ctrls.append(wx.SpinCtrlDouble(self.window, id=wx.ID_ANY, size=wx.Size(75, -1), value=f"{self.physics_pair['JointSCR'][0]}", \
                                                    min=-999, max=999, initial=self.physics_pair['JointSCR'][0], inc=0.001))
        self.physics_ctrls[-1].Bind(wx.EVT_MOUSEWHEEL, lambda event: self.frame.on_wheel_spin_ctrl(event, 0.001))
        self.grid_sizer.Add(self.physics_ctrls[-1], 0, wx.ALL, 5)

        self.physics_ctrls.append(wx.SpinCtrlDouble(self.window, id=wx.ID_ANY, size=wx.Size(75, -1), value=f"{self.physics_pair['JointSCR'][1]}", \
                                                    min=-999, max=999, initial=self.physics_pair['JointSCR'][1], inc=0.001))
        self.physics_ctrls[-1].Bind(wx.EVT_MOUSEWHEEL, lambda event: self.frame.on_wheel_spin_ctrl(event, 0.001))
        self.grid_sizer.Add(self.physics_ctrls[-1], 0, wx.ALL, 5)

        self.physics_ctrls.append(wx.SpinCtrlDouble(self.window, id=wx.ID_ANY, size=wx.Size(75, -1), value=f"{self.physics_pair['JointSCR'][2]}", \
                                                    min=-999, max=999, initial=self.physics_pair['JointSCR'][2], inc=0.001))
        self.physics_ctrls[-1].Bind(wx.EVT_MOUSEWHEEL, lambda event: self.frame.on_wheel_spin_ctrl(event, 0.001))
        self.grid_sizer.Add(self.physics_ctrls[-1], 0, wx.ALL, 5)

        # 追加 -----------------
        self.physics_set_sizer.Add(self.grid_sizer, 0, wx.ALL, 5)


