# -*- coding: utf-8 -*-
#
import os
import wx
import wx.lib.newevent
import csv
import traceback

from utils import MFileUtils
from utils.MLogger import MLogger # noqa

logger = MLogger(__name__)


class TargetBoneDialog(wx.Dialog):

    def __init__(self, frame: wx.Frame, panel: wx.Panel, direction: str, type: str):
        super().__init__(frame, id=wx.ID_ANY, title=f"{type}ボーン指定", pos=(-1, -1), size=(850, 450), style=wx.DEFAULT_DIALOG_STYLE, name="TargetBoneDialog")

        self.frame = frame
        self.panel = panel
        self.direction = direction
        self.vmd_digest = 0 if not self.panel.vmd_file_ctrl.data else self.panel.vmd_file_ctrl.data.digest
        self.pmx_digest = 0 if not self.panel.model_file_ctrl.data else self.panel.model_file_ctrl.data.digest
        self.org_bones = [""]  # 選択肢文言
        self.rep_bones = [""]
        self.org_choices = []   # 選択コントロール
        self.rep_mx_choices = []
        self.rep_my_choices = []
        self.rep_mz_choices = []
        self.rep_rx_choices = []
        self.rep_ry_choices = []
        self.rep_rz_choices = []

        self.sizer = wx.BoxSizer(wx.VERTICAL)

        # 説明文
        self.description_txt = wx.StaticText(self, wx.ID_ANY, f"多段{type}したいボーン名を選択・入力してください。プルダウン欄にボーン名の一部を入力して絞り込みをかける事ができます。\n" \
                                             + "プルダウン欄にボーン名を入力した場合、変換ENTERの後、もう一度ENTERを押すと、移動・回転の各ボーンに同ボーン名が入ります。\n" \
                                             + "多段ボーンは3つまで指定する事ができます。軸ごとに中身の成分が分かれていてもごちゃ混ぜでも、どちらでもOKです。", wx.DefaultPosition, wx.DefaultSize, 0)
        self.sizer.Add(self.description_txt, 0, wx.ALL, 5)

        # ボタン
        self.btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.ok_btn = wx.Button(self, wx.ID_OK, "OK")
        self.btn_sizer.Add(self.ok_btn, 0, wx.ALL, 5)

        self.calcel_btn = wx.Button(self, wx.ID_CANCEL, "キャンセル")
        self.btn_sizer.Add(self.calcel_btn, 0, wx.ALL, 5)

        # インポートボタン
        self.import_btn_ctrl = wx.Button(self, wx.ID_ANY, u"インポート ...", wx.DefaultPosition, wx.DefaultSize, 0)
        self.import_btn_ctrl.SetToolTip(u"ボーンデータをCSVファイルから読み込みます。\nファイル選択ダイアログが開きます。")
        self.import_btn_ctrl.Bind(wx.EVT_BUTTON, self.on_import)
        self.btn_sizer.Add(self.import_btn_ctrl, 0, wx.ALL, 5)

        # エクスポートボタン
        self.export_btn_ctrl = wx.Button(self, wx.ID_ANY, u"エクスポート ...", wx.DefaultPosition, wx.DefaultSize, 0)
        self.export_btn_ctrl.SetToolTip(u"ボーンデータをCSVファイルに出力します。\n調整対象VMDと同じフォルダに出力します。")
        self.export_btn_ctrl.Bind(wx.EVT_BUTTON, self.on_export)
        self.btn_sizer.Add(self.export_btn_ctrl, 0, wx.ALL, 5)

        # 行追加ボタン
        self.add_line_btn_ctrl = wx.Button(self, wx.ID_ANY, u"行追加", wx.DefaultPosition, wx.DefaultSize, 0)
        self.add_line_btn_ctrl.SetToolTip(u"ボーン{0}の組み合わせ行を追加します。\n上限はありません。".format(type))
        self.add_line_btn_ctrl.Bind(wx.EVT_BUTTON, self.on_add_line)
        self.btn_sizer.Add(self.add_line_btn_ctrl, 0, wx.ALL, 5)

        self.sizer.Add(self.btn_sizer, 0, wx.ALIGN_RIGHT | wx.ALL, 5)

        self.static_line01 = wx.StaticLine(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL)
        self.sizer.Add(self.static_line01, 0, wx.EXPAND | wx.ALL, 5)

        self.window = wx.ScrolledWindow(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.FULL_REPAINT_ON_RESIZE | wx.HSCROLL | wx.ALWAYS_SHOW_SB)
        self.window.SetScrollRate(5, 5)

        # セット用基本Sizer
        self.set_list_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # タイトル部分
        self.grid_sizer = wx.FlexGridSizer(0, 8, 0, 0)
        self.grid_sizer.SetFlexibleDirection(wx.BOTH)
        self.grid_sizer.SetNonFlexibleGrowMode(wx.FLEX_GROWMODE_SPECIFIED)

        # モデル名 ----------
        self.org_model_name_txt = wx.StaticText(self.window, wx.ID_ANY, "モデルなし", wx.DefaultPosition, wx.DefaultSize, 0)
        self.org_model_name_txt.Wrap(-1)
        self.grid_sizer.Add(self.org_model_name_txt, 0, wx.ALL, 5)

        self.name_arrow_txt = wx.StaticText(self.window, wx.ID_ANY, "　{0}　".format(self.direction), wx.DefaultPosition, wx.DefaultSize, 0)
        self.name_arrow_txt.Wrap(-1)
        self.grid_sizer.Add(self.name_arrow_txt, 0, wx.CENTER | wx.ALL, 5)

        self.rotate_x_txt = wx.StaticText(self.window, wx.ID_ANY, "回転(X)", wx.DefaultPosition, wx.DefaultSize, 0)
        self.rotate_x_txt.Wrap(-1)
        self.grid_sizer.Add(self.rotate_x_txt, 0, wx.ALL, 5)

        self.rotate_y_txt = wx.StaticText(self.window, wx.ID_ANY, "回転(Y)", wx.DefaultPosition, wx.DefaultSize, 0)
        self.rotate_y_txt.Wrap(-1)
        self.grid_sizer.Add(self.rotate_y_txt, 0, wx.ALL, 5)

        self.rotate_z_txt = wx.StaticText(self.window, wx.ID_ANY, "回転(Z)", wx.DefaultPosition, wx.DefaultSize, 0)
        self.rotate_z_txt.Wrap(-1)
        self.grid_sizer.Add(self.rotate_z_txt, 0, wx.ALL, 5)

        self.move_x_txt = wx.StaticText(self.window, wx.ID_ANY, "移動(X)", wx.DefaultPosition, wx.DefaultSize, 0)
        self.move_x_txt.Wrap(-1)
        self.grid_sizer.Add(self.move_x_txt, 0, wx.ALL, 5)

        self.move_y_txt = wx.StaticText(self.window, wx.ID_ANY, "移動(Y)", wx.DefaultPosition, wx.DefaultSize, 0)
        self.move_y_txt.Wrap(-1)
        self.grid_sizer.Add(self.move_y_txt, 0, wx.ALL, 5)

        self.move_z_txt = wx.StaticText(self.window, wx.ID_ANY, "移動(Z)", wx.DefaultPosition, wx.DefaultSize, 0)
        self.move_z_txt.Wrap(-1)
        self.grid_sizer.Add(self.move_z_txt, 0, wx.ALL, 5)

        self.set_list_sizer.Add(self.grid_sizer, 0, wx.ALL, 5)

        # スクロールバーの表示のためにサイズ調整
        self.window.SetSizer(self.set_list_sizer)
        self.window.Layout()
        self.sizer.Add(self.window, 1, wx.ALL | wx.EXPAND, 5)
        self.SetSizer(self.sizer)
        self.sizer.Layout()
        
        # 画面中央に表示
        self.CentreOnScreen()
        
        # 最初は隠しておく
        self.Hide()
    
    def initialize(self):
        if self.panel.model_file_ctrl.data:
            self.org_model_name_txt.SetLabel(self.panel.vmd_file_ctrl.data.model_name[:10])

            for bone_name, bone_data in self.panel.model_file_ctrl.data.bones.items():
                if bone_data.getVisibleFlag():
                    # 処理対象ボーン：有効なボーン
                    self.org_bones.append(bone_name)
                    # 処理対象ボーン：有効なボーン
                    self.rep_bones.append(bone_name)

            # 一行追加
            self.add_line()

    def on_import(self, event: wx.Event):
        input_bone_path = MFileUtils.get_output_split_bone_path(
            self.panel.vmd_file_ctrl.file_ctrl.GetPath(),
            self.panel.model_file_ctrl.file_ctrl.GetPath()
        )

        with wx.FileDialog(self.frame, "ボーン組み合わせCSVを読み込む", wildcard=u"CSVファイル (*.csv)|*.csv|すべてのファイル (*.*)|*.*",
                           defaultDir=os.path.dirname(input_bone_path),
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:

            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return     # the user changed their mind

            # Proceed loading the file chosen by the user
            target_bone_path = fileDialog.GetPath()
            try:
                with open(target_bone_path, 'r') as f:
                    cr = csv.reader(f, delimiter=",", quotechar='"')
                    bone_lines = [row for row in cr]

                    if len(bone_lines) == 0:
                        return

                    if not bone_lines[0]:
                        raise Exception("処理対象ボーン名指定なし")

                    org_choice_values = bone_lines[0]
                    if len(bone_lines) >= 4:
                        rep_rx_choice_values = bone_lines[1]
                        rep_ry_choice_values = bone_lines[2]
                        rep_rz_choice_values = bone_lines[3]
                    else:
                        rep_rx_choice_values = [""]
                        rep_ry_choice_values = [""]
                        rep_rz_choice_values = [""]
                        
                    if len(bone_lines) >= 7:
                        rep_mx_choice_values = bone_lines[4]
                        rep_my_choice_values = bone_lines[5]
                        rep_mz_choice_values = bone_lines[6]
                    else:
                        rep_mx_choice_values = [""]
                        rep_my_choice_values = [""]
                        rep_mz_choice_values = [""]

                    for (ov, rmxv, rmyv, rmzv, rrxv, rryv, rrzv) in zip(org_choice_values, rep_mx_choice_values, rep_my_choice_values, rep_mz_choice_values, \
                                                                        rep_rx_choice_values, rep_ry_choice_values, rep_rz_choice_values):
                        oc = self.org_choices[-1]
                        rrxc = self.rep_rx_choices[-1]
                        rryc = self.rep_ry_choices[-1]
                        rrzc = self.rep_rz_choices[-1]
                        rmxc = self.rep_mx_choices[-1]
                        rmyc = self.rep_my_choices[-1]
                        rmzc = self.rep_mz_choices[-1]

                        is_seted = False
                        for v, c in [(ov, oc), (rmxv, rmxc), (rmyv, rmyc), (rmzv, rmzc), (rrxv, rrxc), (rryv, rryc), (rrzv, rrzc)]:
                            logger.debug("v: %s, c: %s", v, c)
                            for n in range(c.GetCount()):
                                if c.GetString(n).strip() == v:
                                    c.SetSelection(n)
                                    is_seted = True
                            
                        if is_seted:
                            # 行追加
                            self.add_line()
                        else:
                            # ひとつも追加がなかった場合、終了
                            break

                # パス変更
                self.panel.set_output_vmd_path(event)

            except Exception:
                dialog = wx.MessageDialog(self.frame, "CSVファイルが読み込めませんでした '%s'\n\n%s." % (target_bone_path, traceback.format_exc()), style=wx.OK)
                dialog.ShowModal()
                dialog.Destroy()

    def on_export(self, event: wx.Event):
        org_choice_values = []
        rep_rx_choice_values = []
        rep_ry_choice_values = []
        rep_rz_choice_values = []
        rep_mx_choice_values = []
        rep_my_choice_values = []
        rep_mz_choice_values = []

        for m in self.get_bone_list():
            org_choice_values.append(m[0])
            rep_rx_choice_values.append(m[1])
            rep_ry_choice_values.append(m[2])
            rep_rz_choice_values.append(m[3])
            rep_mx_choice_values.append(m[4])
            rep_my_choice_values.append(m[5])
            rep_mz_choice_values.append(m[6])

        output_bone_path = MFileUtils.get_output_split_bone_path(
            self.panel.vmd_file_ctrl.file_ctrl.GetPath(),
            self.panel.model_file_ctrl.file_ctrl.GetPath()
        )

        try:
            with open(output_bone_path, encoding='cp932', mode='w', newline='') as f:
                cw = csv.writer(f, delimiter=",", quotechar='"', quoting=csv.QUOTE_ALL)

                cw.writerow(org_choice_values)
                cw.writerow(rep_rx_choice_values)
                cw.writerow(rep_ry_choice_values)
                cw.writerow(rep_rz_choice_values)
                cw.writerow(rep_mx_choice_values)
                cw.writerow(rep_my_choice_values)
                cw.writerow(rep_mz_choice_values)

            logger.info("出力成功: %s" % output_bone_path)

            dialog = wx.MessageDialog(self.frame, "多段ボーンデータのエクスポートに成功しました \n'%s'" % (output_bone_path), style=wx.OK)
            dialog.ShowModal()
            dialog.Destroy()

        except Exception:
            dialog = wx.MessageDialog(self.frame, "多段ボーンデータのエクスポートに失敗しました \n'%s'\n\n%s." % (output_bone_path, traceback.format_exc()), style=wx.OK)
            dialog.ShowModal()
            dialog.Destroy()

    def on_add_line(self, event: wx.Event):
        # 行追加
        self.add_line(len(self.org_choices) - 1)

    def get_bone_list(self):
        bone_list = []

        for midx, (oc, rmxc, rmyc, rmzc, rrxc, rryc, rrzc) in \
                enumerate(zip(self.org_choices, self.rep_mx_choices, self.rep_my_choices, self.rep_mz_choices, self.rep_rx_choices, self.rep_ry_choices, self.rep_rz_choices)):
            if oc.GetSelection() > 0 and (rmxc.GetSelection() > 0 or rmyc.GetSelection() > 0 or rmzc.GetSelection() > 0 \
                                          or rrxc.GetSelection() > 0 or rryc.GetSelection() > 0 or rrzc.GetSelection() > 0):
                
                ov = oc.GetString(oc.GetSelection())
                rrxv = rrxc.GetString(rrxc.GetSelection())
                rryv = rryc.GetString(rryc.GetSelection())
                rrzv = rrzc.GetString(rrzc.GetSelection())
                rmxv = rmxc.GetString(rmxc.GetSelection())
                rmyv = rmyc.GetString(rmyc.GetSelection())
                rmzv = rmzc.GetString(rmzc.GetSelection())

                if (ov, rrxv, rryv, rrzv, rmxv, rmyv, rmzv) not in bone_list:
                    # ボーンペアがまだ登録されてないければ登録
                    bone_list.append((ov, rrxv, rryv, rrzv, rmxv, rmyv, rmzv))

        # どれも設定されていなければFalse
        return bone_list

    def add_line(self, midx=0):
        # 置換前ボーン
        self.org_choices.append(wx.ComboBox(self.window, id=wx.ID_ANY, choices=self.org_bones, style=wx.CB_DROPDOWN | wx.TE_PROCESS_ENTER))
        self.org_choices[-1].Bind(wx.EVT_COMBOBOX, lambda event: self.on_change_choice(event, midx))
        self.org_choices[-1].Bind(wx.EVT_TEXT_ENTER, lambda event: self.on_enter_choice(event, midx))
        self.grid_sizer.Add(self.org_choices[-1], 0, wx.ALL, 5)

        # 矢印
        self.arrow_txt = wx.StaticText(self.window, wx.ID_ANY, "　{0}　".format(self.direction), wx.DefaultPosition, wx.DefaultSize, 0)
        self.arrow_txt.Wrap(-1)
        self.grid_sizer.Add(self.arrow_txt, 0, wx.CENTER | wx.ALL, 5)

        # 置換後ボーン(RX)
        self.rep_rx_choices.append(wx.ComboBox(self.window, id=wx.ID_ANY, choices=self.rep_bones, style=wx.CB_DROPDOWN | wx.TE_PROCESS_ENTER))
        # self.rep_rx_choices[-1].Bind(wx.EVT_COMBOBOX, lambda event: self.on_change_choice(event, midx))
        self.rep_rx_choices[-1].Bind(wx.EVT_TEXT_ENTER, lambda event: self.on_enter_choice(event, midx))
        self.grid_sizer.Add(self.rep_rx_choices[-1], 0, wx.ALL, 5)

        # 置換後ボーン(RY)
        self.rep_ry_choices.append(wx.ComboBox(self.window, id=wx.ID_ANY, choices=self.rep_bones, style=wx.CB_DROPDOWN | wx.TE_PROCESS_ENTER))
        # self.rep_ry_choices[-1].Bind(wx.EVT_COMBOBOX, lambda event: self.on_change_choice(event, midx))
        self.rep_ry_choices[-1].Bind(wx.EVT_TEXT_ENTER, lambda event: self.on_enter_choice(event, midx))
        self.grid_sizer.Add(self.rep_ry_choices[-1], 0, wx.ALL, 5)

        # 置換後ボーン(RZ)
        self.rep_rz_choices.append(wx.ComboBox(self.window, id=wx.ID_ANY, choices=self.rep_bones, style=wx.CB_DROPDOWN | wx.TE_PROCESS_ENTER))
        # self.rep_rz_choices[-1].Bind(wx.EVT_COMBOBOX, lambda event: self.on_change_choice(event, midx))
        self.rep_rz_choices[-1].Bind(wx.EVT_TEXT_ENTER, lambda event: self.on_enter_choice(event, midx))
        self.grid_sizer.Add(self.rep_rz_choices[-1], 0, wx.ALL, 5)

        # 置換後ボーン(MX)
        self.rep_mx_choices.append(wx.ComboBox(self.window, id=wx.ID_ANY, choices=self.rep_bones, style=wx.CB_DROPDOWN | wx.TE_PROCESS_ENTER))
        # self.rep_mx_choices[-1].Bind(wx.EVT_COMBOBOX, lambda event: self.on_change_choice(event, midx))
        self.rep_mx_choices[-1].Bind(wx.EVT_TEXT_ENTER, lambda event: self.on_enter_choice(event, midx))
        self.grid_sizer.Add(self.rep_mx_choices[-1], 0, wx.ALL, 5)

        # 置換後ボーン(MY)
        self.rep_my_choices.append(wx.ComboBox(self.window, id=wx.ID_ANY, choices=self.rep_bones, style=wx.CB_DROPDOWN | wx.TE_PROCESS_ENTER))
        # self.rep_my_choices[-1].Bind(wx.EVT_COMBOBOX, lambda event: self.on_change_choice(event, midx))
        self.rep_my_choices[-1].Bind(wx.EVT_TEXT_ENTER, lambda event: self.on_enter_choice(event, midx))
        self.grid_sizer.Add(self.rep_my_choices[-1], 0, wx.ALL, 5)

        # 置換後ボーン(MZ)
        self.rep_mz_choices.append(wx.ComboBox(self.window, id=wx.ID_ANY, choices=self.rep_bones, style=wx.CB_DROPDOWN | wx.TE_PROCESS_ENTER))
        # self.rep_mz_choices[-1].Bind(wx.EVT_COMBOBOX, lambda event: self.on_change_choice(event, midx))
        self.rep_mz_choices[-1].Bind(wx.EVT_TEXT_ENTER, lambda event: self.on_enter_choice(event, midx))
        self.grid_sizer.Add(self.rep_mz_choices[-1], 0, wx.ALL, 5)

        # スクロールバーの表示のためにサイズ調整
        self.set_list_sizer.Layout()
        self.set_list_sizer.FitInside(self.window)

    # ボーンが設定されているか
    def is_set_bone(self):
        for midx, (oc, rmxc, rmyc, rmzc, rrxc, rryc, rrzc) in \
                enumerate(zip(self.org_choices, self.rep_mx_choices, self.rep_my_choices, self.rep_mz_choices, self.rep_rx_choices, self.rep_ry_choices, self.rep_rz_choices)):
            if oc.GetSelection() > 0 and (rmxc.GetSelection() > 0 or rmyc.GetSelection() > 0 or rmzc.GetSelection() > 0 \
                                          or rrxc.GetSelection() > 0 or rryc.GetSelection() > 0 or rrzc.GetSelection() > 0):
                # なんか設定されていたらOK
                return True

        # どれも設定されていなければFalse
        return False
    
    # 文字列が入力された際、一致しているのがあれば適用
    def on_enter_choice(self, event: wx.Event, midx: int):
        idx = event.GetEventObject().FindString(event.GetEventObject().GetValue())
        if idx >= 0:
            event.GetEventObject().SetSelection(idx)
            self.on_change_choice(event, midx)

    # 選択肢が変更された場合
    def on_change_choice(self, event: wx.Event, midx: int):
        text = event.GetEventObject().GetStringSelection()

        # 同じ選択肢を初期設定
        if len(self.org_choices[midx].GetValue()) == 0 or len(text) == 0:
            self.org_choices[midx].ChangeValue(text)
            cidx = self.org_choices[midx].FindString(text)
            if cidx >= 0:
                self.org_choices[midx].SetSelection(cidx)

        if text in self.panel.model_file_ctrl.data.bones:
            bone_data = self.panel.model_file_ctrl.data.bones[text]

            if bone_data.getTranslatable():
                # 移動ボーン
                if len(self.rep_mx_choices[midx].GetValue()) == 0:
                    mxtext = f'{text}MX'
                    cidx = self.rep_mx_choices[midx].FindString(mxtext)
                    if cidx >= 0:
                        self.rep_mx_choices[midx].ChangeValue(mxtext)
                        self.rep_mx_choices[midx].SetSelection(cidx)
                    else:
                        self.rep_mx_choices[midx].ChangeValue(text)
                        cidx = self.rep_mx_choices[midx].FindString(text)
                        if cidx >= 0:
                            self.rep_mx_choices[midx].SetSelection(cidx)

                if len(self.rep_my_choices[midx].GetValue()) == 0:
                    mytext = f'{text}MY'
                    cidx = self.rep_my_choices[midx].FindString(mytext)
                    if cidx >= 0:
                        self.rep_my_choices[midx].ChangeValue(mytext)
                        self.rep_my_choices[midx].SetSelection(cidx)
                    else:
                        self.rep_my_choices[midx].ChangeValue(text)
                        cidx = self.rep_my_choices[midx].FindString(text)
                        if cidx >= 0:
                            self.rep_my_choices[midx].SetSelection(cidx)

                if len(self.rep_mz_choices[midx].GetValue()) == 0:
                    mztext = f'{text}MZ'
                    cidx = self.rep_mz_choices[midx].FindString(mztext)
                    if cidx >= 0:
                        self.rep_mz_choices[midx].ChangeValue(mztext)
                        self.rep_mz_choices[midx].SetSelection(cidx)
                    else:
                        self.rep_mz_choices[midx].ChangeValue(text)
                        cidx = self.rep_mz_choices[midx].FindString(text)
                        if cidx >= 0:
                            self.rep_mz_choices[midx].SetSelection(cidx)

            if bone_data.getRotatable():
                # 回転ボーン
                if len(self.rep_rx_choices[midx].GetValue()) == 0:
                    rxtext = f'{text}RX'
                    cidx = self.rep_rx_choices[midx].FindString(rxtext)
                    if cidx >= 0:
                        self.rep_rx_choices[midx].ChangeValue(rxtext)
                        self.rep_rx_choices[midx].SetSelection(cidx)
                    else:
                        self.rep_rx_choices[midx].ChangeValue(text)
                        cidx = self.rep_rx_choices[midx].FindString(text)
                        if cidx >= 0:
                            self.rep_rx_choices[midx].SetSelection(cidx)

                if len(self.rep_ry_choices[midx].GetValue()) == 0:
                    rytext = f'{text}RY'
                    cidx = self.rep_ry_choices[midx].FindString(rytext)
                    if cidx >= 0:
                        self.rep_ry_choices[midx].ChangeValue(rytext)
                        self.rep_ry_choices[midx].SetSelection(cidx)
                    else:
                        self.rep_ry_choices[midx].ChangeValue(text)
                        cidx = self.rep_ry_choices[midx].FindString(text)
                        if cidx >= 0:
                            self.rep_ry_choices[midx].SetSelection(cidx)

                if len(self.rep_rz_choices[midx].GetValue()) == 0:
                    rztext = f'{text}RZ'
                    cidx = self.rep_rz_choices[midx].FindString(rztext)
                    if cidx >= 0:
                        self.rep_rz_choices[midx].ChangeValue(rztext)
                        self.rep_rz_choices[midx].SetSelection(cidx)
                    else:
                        self.rep_rz_choices[midx].ChangeValue(text)
                        cidx = self.rep_rz_choices[midx].FindString(text)
                        if cidx >= 0:
                            self.rep_rz_choices[midx].SetSelection(cidx)

        elif len(text) == 0:
            # 空にした場合は空に
            self.org_choices[midx].ChangeValue("")
            self.org_choices[midx].SetSelection(-1)
            self.rep_mx_choices[midx].ChangeValue("")
            self.rep_mx_choices[midx].SetSelection(-1)
            self.rep_my_choices[midx].ChangeValue("")
            self.rep_my_choices[midx].SetSelection(-1)
            self.rep_mz_choices[midx].ChangeValue("")
            self.rep_mz_choices[midx].SetSelection(-1)
            self.rep_rx_choices[midx].ChangeValue("")
            self.rep_rx_choices[midx].SetSelection(-1)
            self.rep_ry_choices[midx].ChangeValue("")
            self.rep_ry_choices[midx].SetSelection(-1)
            self.rep_rz_choices[midx].ChangeValue("")
            self.rep_rz_choices[midx].SetSelection(-1)

        # 最後である場合、行追加
        if midx == len(self.org_choices) - 1 and self.org_choices[midx].GetSelection() > 0 and \
                (len(self.rep_mx_choices[midx].GetStringSelection()) > 0 or len(self.rep_my_choices[midx].GetStringSelection()) > 0 \
                    or len(self.rep_mz_choices[midx].GetStringSelection()) > 0 or len(self.rep_rx_choices[midx].GetStringSelection()) > 0 \
                    or len(self.rep_ry_choices[midx].GetStringSelection()) > 0 or len(self.rep_rz_choices[midx].GetStringSelection()) > 0):
            self.add_line(midx + 1)





