import urllib
from copy import deepcopy

from PySide6 import QtWidgets
from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices

from config import config
from config.setting import Setting
from interface.ui_login_proxy_widget import Ui_LoginProxyWidget
from qt_owner import QtOwner
from server import req, Log
from server.server import Server
from task.qt_task import QtTaskBase
from tools.str import Str


class LoginProxyWidget(QtWidgets.QWidget, Ui_LoginProxyWidget, QtTaskBase):
    def __init__(self):
        self.isShowProxy5 = Setting.IsShowProxy5.value
        super(self.__class__, self).__init__()
        Ui_LoginProxyWidget.__init__(self)
        QtTaskBase.__init__(self)
        self.setupUi(self)
        self.speedTest = []
        self.speedIndex = 0
        self.speedPingNum = 0
        self.pingBackNumCnt = {}
        self.pingBackNumDict = {}
        self.needBackNum = 0
        self.radioApiGroup.setId(self.radioButton_1, 1)
        self.radioApiGroup.setId(self.radioButton_2, 2)
        self.radioApiGroup.setId(self.radioButton_3, 3)
        self.radioApiGroup.setId(self.radioButton_4, 4)
        self.radioApiGroup.setId(self.radioButton_5, 5)
        self.radioApiGroup.setId(self.radioButton_6, 6)

        self.radioImgGroup.setId(self.radio_img_1, 1)
        self.radioImgGroup.setId(self.radio_img_2, 2)
        self.radioImgGroup.setId(self.radio_img_3, 3)
        self.radioImgGroup.setId(self.radio_img_4, 4)
        self.radioImgGroup.setId(self.radio_img_5, 5)
        self.radioImgGroup.setId(self.radio_img_6, 6)
        config.Address[1] = Setting.SaveCacheAddress.value

        self.LoadSetting()
        self.UpdateServer()
        self.commandLinkButton.clicked.connect(self.OpenUrl)

        self.radioProxyGroup.setId(self.proxy_0, 0)
        self.radioProxyGroup.setId(self.proxy_1, 1)
        self.radioProxyGroup.setId(self.proxy_2, 2)
        self.radioProxyGroup.setId(self.proxy_3, 3)
        if not self.isShowProxy5:
            self.radio_img_5.setEnabled(False)
        if Setting.ProxyImgSelectIndex.value == 5:
            self.radio_img_5.setEnabled(True)

        self.maxNum = 6

    def Init(self):
        self.LoadSetting()
        proxy = urllib.request.getproxies()
        if isinstance(proxy, dict) and proxy.get("http"):
            self.checkLabel.setVisible(False)
        else:
            self.checkLabel.setVisible(True)

    def ClickButton(self):
        self.SaveSetting()

    def SetEnabled(self, enabled):
        self.testSpeedButton.setEnabled(enabled)
        self.proxy_0.setEnabled(enabled)
        self.proxy_1.setEnabled(enabled)
        self.proxy_2.setEnabled(enabled)
        self.proxy_3.setEnabled(enabled)
        self.httpLine.setEnabled(enabled)
        self.sockEdit.setEnabled(enabled)
        self.cdn_img_ip.setEnabled(enabled)
        self.cdn_api_ip.setEnabled(enabled)
        self.radioButton_1.setEnabled(enabled)
        self.radioButton_2.setEnabled(enabled)
        self.radioButton_3.setEnabled(enabled)
        self.radioButton_4.setEnabled(enabled)
        self.radioButton_5.setEnabled(enabled)
        self.radioButton_6.setEnabled(enabled)
        self.radio_img_1.setEnabled(enabled)
        self.radio_img_2.setEnabled(enabled)
        self.radio_img_3.setEnabled(enabled)
        self.radio_img_4.setEnabled(enabled)
        self.radio_img_5.setEnabled(enabled)
        self.radio_img_6.setEnabled(enabled)
        self.httpsBox.setEnabled(enabled)
        self.ipv6Check.setEnabled(enabled)
        
        if not self.isShowProxy5:
            self.radio_img_5.setEnabled(False)
        else:
            self.radio_img_5.setEnabled(enabled)

    def SpeedTest(self):
        self.speedIndex = 0
        # self.speedPingNum = 0
        self.speedTest = []

        for i in range(1, self.maxNum+1):
            label = getattr(self, "label_api_" + str(i))
            label.setText("")
            label = getattr(self, "label_img_" + str(i))
            label.setText("")

        self.speedTest = [("", "", False, False, 1)]
        i = 2
        adress = config.AddressIpv6[0] if self.ipv6Check.isChecked() else config.Address[0]
        self.speedTest.append((adress, config.ImageServer2, False, False, i))
        i += 1
        adress1 = config.AddressIpv6[1] if self.ipv6Check.isChecked() else config.Address[1]
        self.speedTest.append((adress1, config.ImageServer3, False, False, i))
        i += 1

        PreferCDNIP = self.cdn_api_ip.text()
        if PreferCDNIP:
            self.speedTest.append((PreferCDNIP, PreferCDNIP, False, False, i))
            i += 1
        else:
            i += 1

        self.speedTest.append(("", "", False, (config.ProxyApiDomain, config.ProxyImgDomain), i))
        i += 1

        self.speedTest.append(("", "", False, (config.ProxyApiDomain2, config.ProxyImgDomain2), i))
        i += 1

        self.SetEnabled(False)
        self.needBackNum = 0
        self.speedPingNum = 0
        self.StartSpeedPing()

    def StartSpeedPing(self):
        if len(self.speedTest) <= self.speedPingNum:
            self.StartSpeedTest()
            return
        # for v in self.speedTest:
        address, imageProxy, isHttpProxy, isProxyUrl, i = self.speedTest[self.speedPingNum]
        httpProxy = self.httpLine.text()
        isHttpProxy = True

        if ((self.radioProxyGroup.checkedId() == 1 and not self.httpLine.text()) or
                            (self.radioProxyGroup.checkedId() == 2 and not self.sockEdit.text())):
            label = getattr(self, "label_api_"+str(i))
            label.setText(Str.GetStr(Str.NoProxy))
            self.speedPingNum += 1
            self.StartSpeedPing()
            return

        request = req.SpeedTestPingReq()
        request.isUseHttps = self.httpsBox.isChecked()

        if self.radioProxyGroup.checkedId() == 1:
            request.proxy = {"http": httpProxy, "https": httpProxy}
        elif self.radioProxyGroup.checkedId() == 3:
            request.proxy = ""
        else:
            request.proxy = {"http": None, "https": None}

        if isProxyUrl:
            if "user-agent" in request.headers:
                request.headers.pop("user-agent")
            request.proxyUrl = isProxyUrl[0]
        else:
            request.proxyUrl = ""

        if self.radioProxyGroup.checkedId() == 2:
            self.SetSock5Proxy(True)
        else:
            self.SetSock5Proxy(False)

        Server().UpdateDns(address, imageProxy)
        self.pingBackNumCnt[i] = 0
        self.pingBackNumDict[i] = [0, 0, 0]
        request1 = deepcopy(request)
        request2 = deepcopy(request)
        self.AddHttpTask(lambda x: Server().TestSpeedPing(request, x), self.SpeedTestPingBack, (i, 0))
        self.AddHttpTask(lambda x: Server().TestSpeedPing(request1, x), self.SpeedTestPingBack, (i, 1))
        self.AddHttpTask(lambda x: Server().TestSpeedPing(request2, x), self.SpeedTestPingBack, (i, 2))
        self.needBackNum += 1
        return

    def SpeedTestPingBack(self, raw, v):
        i, backNum = v
        data = raw["data"]
        st = raw["st"]
        label = getattr(self, "label_api_" + str(i))
        if float(data) > 0.0:
            self.pingBackNumDict[i][backNum] = int(float(data))
            label.setText("<font color=#7fb80e>{}</font>".format(str(int(float(data))) + "ms"))
        else:
            self.pingBackNumDict[i][backNum] = str(st)
            label.setText("<font color=#d71345>{}</font>".format(Str.GetStr(st)))
        self.pingBackNumCnt[i] += 1

        if self.pingBackNumCnt[i] >= 3:
            sumData = 0
            sumCnt = 0
            sumSt = 0
            for data in self.pingBackNumDict[i]:
                if isinstance(data, int):
                   sumData += data
                   sumCnt += 1
                else:
                    sumSt = data
            if sumCnt >= 1:
                label.setText("<font color=#7fb80e>{}</font>".format(str(int(float(sumData/sumCnt))) + "ms") )
            else:
                label.setText("<font color=#d71345>{}</font>".format(Str.GetStr(int(sumSt))) )

            self.speedPingNum += 1
            self.StartSpeedPing()
            return

    def CheckShow5(self):
        isShow = True
        for i in range(1, 5):
            label = getattr(self, "label_img_" + str(i))
            if label.text().count("7fb80e") == 1:
                isShow = False
        if isShow and not self.isShowProxy5:
            self.isShowProxy5 = True
            self.radio_img_5.setEnabled(True)

    def StartSpeedTest(self):
        if len(self.speedTest) <= self.speedIndex:
            self.UpdateServer()
            self.SetEnabled(True)
            self.CheckShow5()
            return

        address, imageProxy, isHttpProxy, isProxyUrl, i = self.speedTest[self.speedIndex]
        httpProxy = self.httpLine.text()
        if ((self.radioProxyGroup.checkedId() == 1 and not self.httpLine.text()) or
                            (self.radioProxyGroup.checkedId() == 2 and not self.sockEdit.text())):
            label = getattr(self, "label_img_" + str(i))
            label.setText(Str.GetStr(Str.NoProxy))
            self.speedIndex += 1
            self.StartSpeedTest()
            return

        request = req.SpeedTestReq()
        request.isUseHttps = self.httpsBox.isChecked()

        if self.radioProxyGroup.checkedId() == 1:
            request.proxy = {"http": httpProxy, "https": httpProxy}
        elif self.radioProxyGroup.checkedId() == 3:
            request.proxy = ""
        else:
            request.proxy = {"http": None, "https": None}

        if isProxyUrl:
            if "user-agent" in request.headers:
                request.headers.pop("user-agent")
            request.proxyUrl = isProxyUrl[1]
        else:
            request.proxyUrl = ""

        if self.radioProxyGroup.checkedId() == 2:
            self.SetSock5Proxy(True)
        else:
            self.SetSock5Proxy(False)

        Server().UpdateDns(address, imageProxy)
        self.AddHttpTask(lambda x: Server().TestSpeed(request, x), self.SpeedTestBack, i)
        return

    def SpeedTestBack(self, raw, i):
        data = raw["data"]
        st = raw["st"]
        if not data:
            data = "<font color=#d71345>{}</font>".format(Str.GetStr(st))
        else:
            data = "<font color=#7fb80e>{}</font>".format(data)
        label = getattr(self, "label_img_" + str(i))
        label.setText(data)
        self.speedIndex += 1
        self.StartSpeedTest()
        return

    def LoadSetting(self):
        # config.PreferCDNIP = QtOwner().settingView.GetSettingV("Proxy/PreferCDNIP", config.PreferCDNIP)
        # config.ProxySelectIndex = QtOwner().settingView.GetSettingV("Proxy/ProxySelectIndex", config.ProxySelectIndex)
        # config.IsUseHttps = QtOwner().settingView.GetSettingV("Proxy/IsUseHttps", config.IsUseHttps)
        # httpProxy = QtOwner().settingView.GetSettingV("Proxy/Http", config.HttpProxy)
        IsCanIpv6 = True
        try:
            from urllib3.util.connection import  HAS_IPV6
            IsCanIpv6 = HAS_IPV6
        except Exception as es:
            Log.Error(es)
            IsCanIpv6 = False

        if not IsCanIpv6:
            self.ipv6Check.setChecked(False)
            self.ipv6Check.setEnabled(False)
            Setting.PreIpv6.SetValue(0)

        self.ipv6Check.setChecked(Setting.PreIpv6.value)
        self.httpsBox.setChecked(Setting.IsUseHttps.value)
        self.httpLine.setText(Setting.HttpProxy.value)
        self.sockEdit.setText(Setting.Sock5Proxy.value)
        button = getattr(self, "radioButton_{}".format(Setting.ProxySelectIndex.value))
        button.setChecked(True)
        button = getattr(self, "proxy_{}".format(int(Setting.IsHttpProxy.value)))
        button.setChecked(True)
        button = getattr(self, "radio_img_{}".format(int(Setting.ProxyImgSelectIndex.value)))
        button.setChecked(True)

        self.cdn_api_ip.setText(Setting.PreferCDNIP.value)
        self.cdn_img_ip.setText(Setting.PreferCDNIPImg.value)

        if Setting.ProxyImgSelectIndex.value == 5:
            self.isShowProxy5 = True

        if not self.isShowProxy5:
            self.radio_img_5.setEnabled(False)
        else:
            self.radio_img_5.setEnabled(True)

    def UpdateServer(self):
        if Setting.ProxySelectIndex.value == 1:
            address = ""
        elif Setting.ProxySelectIndex.value == 2:
            address = config.AddressIpv6[0] if Setting.PreIpv6.value > 0 else config.Address[0]
        elif Setting.ProxySelectIndex.value == 3:
            address = config.AddressIpv6[1] if Setting.PreIpv6.value > 0 else config.Address[1]
        elif Setting.ProxySelectIndex.value == 5:
            address = ""
        elif Setting.ProxySelectIndex.value == 6:
            address = ""
        else:
            address = Setting.PreferCDNIP.value

        if Setting.ProxyImgSelectIndex.value == 1:
            imageServer = ""
        elif Setting.ProxyImgSelectIndex.value == 2:
            imageServer = config.ImageServer2
        elif Setting.ProxyImgSelectIndex.value == 3:
            imageServer = config.ImageServer3
        elif Setting.ProxyImgSelectIndex.value == 5:
            imageServer = ""
        elif Setting.ProxyImgSelectIndex.value == 6:
            imageServer = ""
        else:
            imageServer = Setting.PreferCDNIPImg.value

        QtOwner().settingView.SetSock5Proxy()
        Server().UpdateDns(address, imageServer)
        Log.Info("update proxy, apiSetId:{}, imgSetID:{}, image server:{}, address:{}".format(Setting.ProxySelectIndex.value, Setting.ProxyImgSelectIndex.value, Server().imageServer, Server().address))

    def SaveSetting(self):
        Setting.PreferCDNIP.SetValue(self.cdn_api_ip.text())
        Setting.PreferCDNIPImg.SetValue(self.cdn_img_ip.text())
        Setting.IsHttpProxy.SetValue(int(self.radioProxyGroup.checkedId()))
        Setting.Sock5Proxy.SetValue(self.sockEdit.text())
        Setting.HttpProxy.SetValue(self.httpLine.text())
        Setting.ProxySelectIndex.SetValue(self.radioApiGroup.checkedId())
        Setting.ProxyImgSelectIndex.SetValue(self.radioImgGroup.checkedId())
        Setting.IsUseHttps.SetValue(int(self.httpsBox.isChecked()))
        Setting.PreIpv6.SetValue(int(self.ipv6Check.isChecked()))

        # QtOwner().settingView.SetSettingV("Proxy/ProxySelectIndex", config.ProxySelectIndex)
        # QtOwner().settingView.SetSettingV("Proxy/PreferCDNIP", config.PreferCDNIP)
        # QtOwner().settingView.SetSettingV("Proxy/Http", httpProxy)
        # QtOwner().settingView.SetSettingV("Proxy/IsHttp", config.IsHttpProxy)
        # QtOwner().settingView.SetSettingV("Proxy/IsUseHttps", config.IsUseHttps)

        self.UpdateServer()
        QtOwner().ShowMsg(Str.GetStr(Str.SaveSuc))
        return

    def OpenUrl(self):
        QtOwner().owner.helpView.OpenProxyUrl()

    def SetSock5Proxy(self, isProxy):
        import socket
        import socks
        if not QtOwner().backSock:
            QtOwner().backSock = socket.socket
        if isProxy:
            data = self.sockEdit.text().replace("http://", "").replace("https://", "").replace("sock5://", "")
            data = data.split(":")
            if len(data) == 2:
                host = data[0]
                port = data[1]
                socks.set_default_proxy(socks.SOCKS5, host, int(port))
                socket.socket = socks.socksocket
        else:
            socks.set_default_proxy()
            socket.socket = QtOwner().backSock