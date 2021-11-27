import sys
from functools import partial

from PySide6.QtCore import Qt, QUrl, QEvent, QPoint
from PySide6.QtGui import QIcon, QMouseEvent, QGuiApplication, QDesktopServices, QPalette
from PySide6.QtWidgets import QButtonGroup, QToolButton, QLabel, QMainWindow, QMessageBox, QApplication

from component.dialog.loading_dialog import LoadingDialog
from component.label.msg_label import MsgLabel
from component.widget.frame_less_widget import FrameLessWidget
from config import config
from config.setting import Setting
from interface.ui_main_windows import Ui_MainWindow
from qt_owner import QtOwner
from server import req
from server.sql_server import SqlServer
from task.qt_task import QtTaskBase
from tools.log import Log
from tools.str import Str
from view.download.download_dir_view import DownloadDirView


class MainView(QMainWindow, Ui_MainWindow, QtTaskBase):
    """ 主窗口 """

    def __init__(self, parent=None):
        super().__init__(parent)
        QtTaskBase.__init__(self)
        QtOwner().SetOwner(self)
        self.setupUi(self)
        self.resize(600, 600)
        self.setWindowTitle("PicACG")
        self.setWindowIcon(QIcon(":/png/icon/logo_round.png"))
        # self.setAttribute(Qt.WA_TranslucentBackground)

        screens = QGuiApplication.screens()
        # print(screens[0].geometry(), screens[1].geometry())
        if Setting.ScreenIndex.value >= len(screens):
            desktop = QGuiApplication.primaryScreen().geometry()
        else:
            desktop = screens[Setting.ScreenIndex.value].geometry()
        self.resize(desktop.width() // 4 * 3, desktop.height() // 4 * 3)
        self.move(desktop.width() // 8+desktop.x(), desktop.height() // 8+desktop.y())

        # self.setAttribute(Qt.WA_StyledBackground, True)

        self.loadingDialog = LoadingDialog(self)
        self.__initWidget()

        # 窗口切换相关
        self.toolButtons = []
        self.toolLabels = []
        self.toolButtonGroup = QButtonGroup()
        self.toolButtonGroup.idClicked.connect(self.SwitchWidgetByIndex)
        self.menuButton.clicked.connect(self.CheckShowMenu)
        self.UpdateTabBar()

        self.subStackWidget.setCurrentIndex(0)
        self.settingView.LoadSetting()
        # self.readView.LoadSetting()


    @property
    def subStackList(self):
        return self.subStackWidget.subStackList

    @subStackList.setter
    def subStackList(self, value):
        self.subStackWidget.subStackList = value

    def __initWidget(self):
        self.navigationWidget.indexButton.clicked.connect(partial(self.SwitchWidgetAndClear, self.subStackWidget.indexOf(self.indexView)))
        self.navigationWidget.settingButton.clicked.connect(partial(self.SwitchWidgetAndClear, self.subStackWidget.indexOf(self.settingView)))
        self.navigationWidget.downloadButton.clicked.connect(partial(self.SwitchWidgetAndClear, self.subStackWidget.indexOf(self.downloadView)))
        self.navigationWidget.categoryButton.clicked.connect(partial(self.SwitchWidgetAndClear, self.subStackWidget.indexOf(self.categoryView)))
        self.navigationWidget.searchButton.clicked.connect(partial(self.SwitchWidgetAndClear, self.subStackWidget.indexOf(self.searchView)))
        self.navigationWidget.rankButton.clicked.connect(partial(self.SwitchWidgetAndClear, self.subStackWidget.indexOf(self.rankView)))
        self.navigationWidget.msgButton.clicked.connect(partial(self.SwitchWidgetAndClear, self.subStackWidget.indexOf(self.commentView)))
        self.navigationWidget.chatButton.clicked.connect(partial(self.SwitchWidgetAndClear, self.subStackWidget.indexOf(self.chatView)))
        self.navigationWidget.collectButton.clicked.connect(partial(self.SwitchWidgetAndClear, self.subStackWidget.indexOf(self.favorityView)))
        self.navigationWidget.lookButton.clicked.connect(partial(self.SwitchWidgetAndClear, self.subStackWidget.indexOf(self.historyView)))
        self.navigationWidget.myCommentButton.clicked.connect(partial(self.SwitchWidgetAndClear, self.subStackWidget.indexOf(self.myCommentView)))
        self.navigationWidget.gameButton.clicked.connect(partial(self.SwitchWidgetAndClear, self.subStackWidget.indexOf(self.gameView)))
        self.navigationWidget.helpButton.clicked.connect(partial(self.SwitchWidgetAndClear, self.subStackWidget.indexOf(self.helpView)))

    def RetranslateUi(self):
        Ui_MainWindow.retranslateUi(self, self)
        self.indexView.retranslateUi(self.indexView)
        self.settingView.retranslateUi(self.settingView)
        self.downloadView.retranslateUi(self.downloadView)
        self.categoryView.retranslateUi(self.categoryView)
        self.searchView.retranslateUi(self.searchView)
        self.rankView.retranslateUi(self.rankView)
        self.commentView.retranslateUi(self.commentView)
        self.chatView.retranslateUi(self.chatView)
        self.favorityView.retranslateUi(self.favorityView)
        self.readView.retranslateUi(self.readView)
        self.myCommentView.retranslateUi(self.myCommentView)
        self.gameCommentView.retranslateUi(self.gameCommentView)
        self.subCommentView.retranslateUi(self.subCommentView)
        self.gameView.retranslateUi(self.gameView)
        self.helpView.retranslateUi(self.helpView)
        self.waifu2xToolView.retranslateUi(self.waifu2xToolView)

    def Init(self):
        IsCanUse = False
        if config.CanWaifu2x:
            from waifu2x_vulkan import waifu2x_vulkan
            stat = waifu2x_vulkan.init()
            waifu2x_vulkan.setDebug(True)
            if stat < 0:
                pass
                # QtOwner().ShowMsg(self.tr("未发现支持VULKAN的GPU, Waiuf2x当前为CPU模式, " + ", code:{}".format(str(stat))))
                # CPU 模式，暂时不开放看图下的转换
                # config.IsOpenWaifu = 0
                # self.settingForm.checkBox.setEnabled(False)
                # self.qtReadImg.frame.qtTool.checkBox.setEnabled(False)

            IsCanUse = True
            gpuInfo = waifu2x_vulkan.getGpuInfo()
            self.settingView.SetGpuInfos(gpuInfo)
            # if not gpuInfo or (gpuInfo and config.Encode < 0) or (gpuInfo and config.Encode >= len(gpuInfo)):
            #     config.Encode = 0

            sts = waifu2x_vulkan.initSet(config.Encode, Setting.Waifu2xThread.value)
            Log.Info("waifu2x初始化: " + str(stat) + " encode: " + str(
                config.Encode) + " version:" + waifu2x_vulkan.getVersion() + " code:" + str(sts))
        else:
            pass
            # QtOwner().ShowError(self.tr("waifu2x无法启用, ") + config.ErrorMsg)

        if not IsCanUse:
            self.settingView.checkBox.setEnabled(False)
            self.readView.frame.qtTool.checkBox.setEnabled(False)
            Setting.DownloadAuto.SetValue(0)
            self.downloadView.radioButton.setEnabled(False)
            self.waifu2xToolView.checkBox.setEnabled(False)
            self.waifu2xToolView.changeButton.setEnabled(False)
            self.waifu2xToolView.changeButton.setEnabled(False)
            self.waifu2xToolView.comboBox.setEnabled(False)
            self.waifu2xToolView.SetStatus(False)
            Setting.IsOpenWaifu.SetValue(0)

        if Setting.IsUpdate.value:
            self.helpView.InitUpdate()

        self.searchView.InitWord()
        self.msgLabel = MsgLabel(self)
        self.msgLabel.hide()
        if not Setting.SavePath.value:
            view = DownloadDirView(self)
            view.exec()
        self.OpenLoginView()

    def ClearTabBar(self):
        for toolButton in self.toolButtons:
            self.menuLayout.removeWidget(toolButton)
            toolButton.setParent(None)
        for label in self.toolLabels:
            self.menuLayout.removeWidget(label)
            label.setParent(None)
        self.toolButtons = []
        self.toolLabels = []
        self.subStackList = []
        return

    def UpdateTabBar(self):
        for index, i in enumerate(self.subStackList):
            if index >= len(self.toolButtons):
                button = QToolButton()
                button.setCheckable(True)
                button.setText(self.subStackWidget.widget(i).windowTitle())

                if index == 0:
                    button.setChecked(True)
                else:
                    label = QLabel(">")
                    self.menuLayout.addWidget(label)
                    self.toolLabels.append(label)

                self.toolButtonGroup.addButton(button)
                self.toolButtonGroup.setId(button, i)
                self.menuLayout.addWidget(button)
                self.toolButtons.append(button)
        return

    def OpenLoginView(self):
        self.navigationWidget.OpenLoginView()

    def LoginSucBack(self):
        self.helpView.Init()
        self.favorityView.InitFavorite()
        self.SwitchWidget(self.indexView)

    def SwitchWidgetNext(self):
        index = self.subStackWidget.currentIndex()
        if index in self.subStackList:
            subIndex = self.subStackList.index(index)
            if subIndex >= len(self.subStackList) -1:
                return
            self.SwitchWidgetByIndex(self.subStackList[subIndex+1])

    def SwitchWidgetLast(self):
        index = self.subStackWidget.currentIndex()
        if index in self.subStackList:
            subIndex = self.subStackList.index(index)
            if subIndex <= 0:
                return
            self.SwitchWidgetByIndex(self.subStackList[subIndex-1])

    def SwitchWidget(self, widget, **kwargs):
        return self.SwitchWidgetByIndex(self.subStackWidget.indexOf(widget), **kwargs)

    def SwitchWidgetByIndex(self, index, **kwargs):
        if index == self.subStackWidget.currentIndex():
            self.subStackWidget.widget(index).SwitchCurrent(**kwargs)
            return
        if index not in self.subStackList:
            # 需要清除後面的界面
            currrentListIndex = self.subStackList.index(self.subStackWidget.currentIndex())
            subStackList = self.subStackList[:currrentListIndex+1]

            self.ClearTabBar()
            self.subStackList = subStackList
            self.subStackList.append(index)
            self.UpdateTabBar()
        self.subStackWidget.SwitchWidgetByIndex(index, **kwargs)
        # self.toolButtonGroup.id()
        for button in self.toolButtons:
            if self.toolButtonGroup.id(button) == index:
                button.setChecked(True)
        return

    def SwitchWidgetAndClear(self, index):
        self.ClearTabBar()
        self.subStackList = [index]
        kwargs = {"refresh": True}
        self.subStackWidget.SwitchWidgetByIndex(index, **kwargs)
        self.UpdateTabBar()
        return

    # def resizeEvent(self, e):
    #     super().resizeEvent(e)
    #     self.adjustWidgetGeometry()

    def closeEvent(self, a0) -> None:
        super().closeEvent(a0)
        # reply = QtOwner().ShowMsgBox(QMessageBox.Question, self.tr('提示'), self.tr('确定要退出吗？'))
        self.GetExitScreen()
        a0.accept()

    def GetExitScreen(self):
        screens = QGuiApplication.screens()
        # print(self.pos())
        # for screen in screens:
        #     print(screen.geometry())
        screen = QGuiApplication.screenAt(self.pos()+QPoint(self.width()//2, self.height()//2))
        if screen in screens:
            index = screens.index(screen)
            Setting.ScreenIndex.SetValue(index)
            Log.Info("Exit screen index:{}".format(str(index)))

    def CheckShowMenu(self):
        if self.navigationWidget.isHidden():
            self.navigationWidget.aniShow()
        else:
            self.navigationWidget.aniHide()
        return

    def keyReleaseEvent(self, event) -> None:
        if event.key() == Qt.Key_Escape:
            self.SwitchWidgetLast()
        return super(self.__class__, self).keyReleaseEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.ForwardButton:
            self.SwitchWidgetNext()
        elif event.button() == Qt.BackButton:
            self.SwitchWidgetLast()
        self.searchView.lineEdit.CheckClick(event.pos())
        return super(self.__class__, self).mousePressEvent(event)
    #
    # def changeEvent(self, ev):
    #     if sys.platform == 'darwin':
    #         OSX_LIGHT_MODE = 236
    #         OSX_DARK_MODE = 50
    #         if ev.type() == QEvent.PaletteChange:
    #             bg = self.palette().color(QPalette.Active, QPalette.Window)
    #             if bg.lightness() == OSX_LIGHT_MODE:
    #                 print("MacOS light theme")
    #                 return
    #             elif bg.lightness() == OSX_DARK_MODE:
    #                 print("MacOS dark theme")
    #                 return
    #     return super(self.__class__, self).changeEvent(ev)

    def nativeEvent(self, eventType, message):
        # print(eventType, message)
        if eventType == "windows_generic_MSG":
            try:
                from ctypes.wintypes import POINT
                import ctypes.wintypes
            except Exception as es:
                return super(self.__class__, self).nativeEvent(eventType, message)

            msg = ctypes.wintypes.MSG.from_address(message.__int__())
            # print(msg.message, self.GetWinSysColor())
            if msg.message == 26 and config.ThemeIndex == 0:
                self.settingView.SetTheme()

        return super(self.__class__, self).nativeEvent(eventType, message)

    def Close(self):
        # TODO 停止所有的定时器以及线程
        self.loadingDialog.close()
        self.downloadView.Close()
        SqlServer().Stop()
        # QtTask().Stop()

