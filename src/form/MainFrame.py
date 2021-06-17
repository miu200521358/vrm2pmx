# -*- coding: utf-8 -*-
#
import os
import sys
import wx

from form.panel.ExportPanel import ExportPanel
from module.MMath import MRect, MVector3D, MVector4D, MQuaternion, MMatrix4x4 # noqa
from utils import MFormUtils, MFileUtils # noqa
from utils.MLogger import MLogger # noqa

if os.name == "nt":
    import winsound     # Windows版のみインポート

logger = MLogger(__name__)


# イベント
(SizingThreadEvent, EVT_SIZING_THREAD) = wx.lib.newevent.NewEvent()
(LoadThreadEvent, EVT_LOAD_THREAD) = wx.lib.newevent.NewEvent()


class MainFrame(wx.Frame):

    def __init__(self, parent, mydir_path: str, version_name: str, logging_level: int, is_saving: bool, is_out_log: bool):
        self.version_name = version_name
        self.logging_level = logging_level
        self.is_out_log = is_out_log
        self.is_saving = is_saving
        self.mydir_path = mydir_path
        self.elapsed_time = 0
        self.popuped_finger_warning = False
        
        self.worker = None
        self.load_worker = None

        wx.Frame.__init__(self, parent, id=wx.ID_ANY, title=u"Vrm2Pmxエクスポーター ローカル版 {0}".format(self.version_name), \
                          pos=wx.DefaultPosition, size=wx.Size(600, 650), style=wx.DEFAULT_FRAME_STYLE | wx.TAB_TRAVERSAL)

        # ファイル履歴読み込み
        self.file_hitories = MFileUtils.read_history(self.mydir_path)

        # ---------------------------------------------

        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)

        bSizer1 = wx.BoxSizer(wx.VERTICAL)

        self.note_ctrl = wx.Notebook(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0)
        if self.logging_level == MLogger.FULL or self.logging_level == MLogger.DEBUG_FULL:
            # フルデータの場合
            self.note_ctrl.SetBackgroundColour("RED")
        elif self.logging_level == MLogger.DEBUG:
            # テスト（デバッグ版）の場合
            self.note_ctrl.SetBackgroundColour("CORAL")
        elif self.logging_level == MLogger.TIMER:
            # 時間計測の場合
            self.note_ctrl.SetBackgroundColour("YELLOW")
        elif not is_saving:
            # ログありの場合、色変え
            self.note_ctrl.SetBackgroundColour("BLUE")
        elif is_out_log:
            # ログありの場合、色変え
            self.note_ctrl.SetBackgroundColour("AQUAMARINE")
        else:
            self.note_ctrl.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNSHADOW))

        # ---------------------------------------------

        # PMX変換タブ
        self.export_panel_ctrl = ExportPanel(self, self.note_ctrl, 9)
        self.note_ctrl.AddPage(self.export_panel_ctrl, u"PMX変換", False)

        # ---------------------------------------------

        # タブ押下時の処理
        self.note_ctrl.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.on_tab_change)

        # ---------------------------------------------

        bSizer1.Add(self.note_ctrl, 1, wx.EXPAND, 5)

        # デフォルトの出力先はファイルタブのコンソール
        sys.stdout = self.export_panel_ctrl.console_ctrl

        self.SetSizer(bSizer1)
        self.Layout()

        self.Centre(wx.BOTH)
    
    def on_idle(self, event: wx.Event):
        pass

    def on_tab_change(self, event: wx.Event):

        if self.export_panel_ctrl.is_fix_tab:
            self.note_ctrl.ChangeSelection(self.export_panel_ctrl.tab_idx)
            event.Skip()
            return

    # タブ移動可
    def release_tab(self):
        pass

    # フォーム入力可
    def enable(self):
        pass

    def show_worked_time(self):
        # 経過秒数を時分秒に変換
        td_m, td_s = divmod(self.elapsed_time, 60)

        if td_m == 0:
            worked_time = "{0:02d}秒".format(int(td_s))
        else:
            worked_time = "{0:02d}分{1:02d}秒".format(int(td_m), int(td_s))

        return worked_time

    def sound_finish(self):
        # 終了音を鳴らす
        if os.name == "nt":
            # Windows
            try:
                winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS)
            except Exception:
                pass

    def on_wheel_spin_ctrl(self, event: wx.Event, inc=0.1):
        # スピンコントロール変更時
        if event.GetWheelRotation() > 0:
            event.GetEventObject().SetValue(event.GetEventObject().GetValue() + inc)
        else:
            event.GetEventObject().SetValue(event.GetEventObject().GetValue() - inc)
