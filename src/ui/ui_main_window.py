# Form implementation generated from reading ui file 'src/ui/main_window.ui'
#
# Created by: PyQt6 UI code generator 6.8.1
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1448, 862)
        self.centralwidget = QtWidgets.QWidget(parent=MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.fetchButton = QtWidgets.QPushButton(parent=self.centralwidget)
        self.fetchButton.setGeometry(QtCore.QRect(1060, 760, 101, 51))
        self.fetchButton.setObjectName("fetchButton")
        self.historyList = QtWidgets.QListWidget(parent=self.centralwidget)
        self.historyList.setGeometry(QtCore.QRect(1170, 10, 271, 821))
        self.historyList.setObjectName("historyList")
        self.songLabel = QtWidgets.QLabel(parent=self.centralwidget)
        self.songLabel.setGeometry(QtCore.QRect(610, 10, 401, 51))
        self.songLabel.setObjectName("songLabel")
        self.loginButton = QtWidgets.QPushButton(parent=self.centralwidget)
        self.loginButton.setGeometry(QtCore.QRect(500, 640, 301, 91))
        self.loginButton.setObjectName("loginButton")
        self.cancelButton = QtWidgets.QPushButton(parent=self.centralwidget)
        self.cancelButton.setGeometry(QtCore.QRect(610, 740, 81, 21))
        self.cancelButton.setObjectName("cancelButton")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(parent=MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1448, 21))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(parent=MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.fetchButton.setText(_translate("MainWindow", "Fetch Spotify Data"))
        self.songLabel.setText(_translate("MainWindow", "Now Playing: None"))
        self.loginButton.setText(_translate("MainWindow", "Login"))
        self.cancelButton.setText(_translate("MainWindow", "Cancel"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec())
