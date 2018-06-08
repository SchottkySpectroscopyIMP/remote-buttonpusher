#! /usr/bin/env python3
# -*- coding:utf-8 -*-

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

import socket, sys, time
from multithread import Worker, WorkerSignals

class ControlClient():
    def __init__(self, IP, port):
        self.IP = IP
        self.port = port
        self.connect()
    
    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.IP, self.port))

    def disconnect(self):
        self.sock.close()

    def write(self, cmd):
        self.sock.send(cmd.encode("utf-8"))

    def read(self):
        data = self.sock.recv(4096)
        return data.decode("utf-8").strip()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.title = "Controller for Button Pusher"
        self.left = 650
        self.top = 30
        self.width = 200
        self.height = 200

        # the default parameters
        self.workMode = "2"     # default workMode: short press
        self.step = "5"         # default steps of movement(free mode): 5
        self.direct = "1"       # default direction of movement(free mode): forward
        self.stepDiff = 0       # step difference with the starting point

        # the default operation parameters
        self.hide = True
        self.exit = False

        # the default color setting
        self.bgcolor = "#FAFAFA"
        self.fgcolor = "#23373B"
        self.green = "#1B813E"
        self.orange = "#E98B2A"
        self.red = "#AB3B3A"

        # style for the state 
        self.off_style = """
        QProgressBar{{
            border-radius: 5px;
            border: 1px groove silver;
            color: {0:s};
            text-align: center
            }}
        QProgressBar::chunk{{
            border-radius: 5px;
            background-color: #80{1:s};
            }}
        """.format(self.fgcolor, self.red[1:])
        self.on_style = """
        QProgressBar{{
            border-radius: 5px;
            border: 1px groove silver;
            color: {0:s};
            text-align: center
            }}
        QProgressBar::chunk{{
            border-radius: 5px;
            background-color: #80{1:s};
            }}
        """.format(self.fgcolor, self.green[1:])
        self.init_style = """
        QProgressBar{{
            border-radius: 5px;
            border: 1px groove silver;
            color: {0:s};
            text-align: center
            }}
        QProgressBar::chunk{{
            border-radius: 5px;
            background-color: #80{1:s};
            }}
        """.format(self.fgcolor, self.orange[1:])

        # set the font of label
        self.fontStat = QFont("RobotoCondensed", 12)
        self.fontLab = QFont("RobotoCondensed", 14)

        # set the style for input bar
        self.stop_style = """
        QLineEdit{{
            color: {:s};
            }}
        """.format(self.fgcolor)
        self.run_style = """
        QLineEdit{{
            color: {:s};
            background-color: lightgray
            }}
        """.format(self.fgcolor)

        # set the style for radio button
        self.able_style = """
        QRadioButton{{
            color: {:s};
            }}
        """.format(self.fgcolor)
        self.inable_style = """
        QRadioButton{{
            color: {:s};
            background-color: lightgray
            }}
        """.format(self.fgcolor)

        # set the Icon
        self.iconPress = QIcon("./userManual.png")

        self.initUI()

    def QLineEdit_StopStyle(self, lineEdit):
        lineEdit.setStyleSheet(self.stop_style)
        lineEdit.setReadOnly(False)

    def QLineEdit_RunStyle(self, lineEdit):
        lineEdit.setStyleSheet(self.run_style)
        lineEdit.setReadOnly(True)

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.setStyleSheet("QLabel{{color: {0:s} }} QRadioButton{{background-color: {1:s}; color: {0:s}}} QTextEdit{{color: {0:s}}} QMainWindow{{ background-color: {1:s} }} QCentralWidget{{ background-color: {1:s} }} QGroupBox{{ background-color: {1:s} }}".format(self.fgcolor, self.bgcolor))

        self.threadPool = QThreadPool()

        self.setDisplayPanel()
        self.buildConnection()

        self.statusBar().showMessage("choose the press mode before run")

    def setDisplayPanel(self):
        # set the mode radio button - visiable
        self.modeLongButton = QRadioButton("turn off")
        self.modeLongButton.setFont(self.fontLab)
        self.modeShortButton = QRadioButton("turn on ")
        self.modeShortButton.setFont(self.fontLab)
        self.modeShortButton.setChecked(True)

        # set IQR power label & status
        self.IQRstatusLab = QLabel("IQR Power")
        self.IQRstatusLab.setFont(self.fontStat)
        self.IQRstatus = QProgressBar()
        self.IQRstatus.setFont(self.fontLab)
        self.IQRstatus.setStyleSheet(self.init_style)
        self.IQRstatus.setFormat("waiting")
        self.IQRstatus.setValue(100)

        # set the working status button
        self.statusButton = QPushButton()
        self.statusButton.setIcon(self.iconPress)
        self.statusButton.setFixedSize(40, 40)
        self.statusButton.setIconSize(QSize(25, 25))

        # set the free mode buttons - invisiable
        self.operatForwardButton = QRadioButton("forward")
        self.operatForwardButton.setFont(self.fontLab)
        self.operatForwardButton.setChecked(True)
        self.operatBackwardButton = QRadioButton("backward")
        self.operatBackwardButton.setFont(self.fontLab)
        # set the step setting and information
        self.stepLab = QLabel("steps")
        self.stepLab.setFont(self.fontLab)
        self.stepInput = QLineEdit(self.step)
        self.stepInput.setFont(self.fontStat)
        self.stepInput.setFixedWidth(55)
        self.QLineEdit_RunStyle(self.stepInput)
        self.stepChangeLab = QLabel("position:")
        self.stepChangeLab.setFont(self.fontLab)
        self.stepChange = QLabel(str(self.stepDiff))
        self.stepChange.setFont(self.fontLab)

        # set the normal panel
        visiableGrid = QGridLayout()
        visiableGrid.setSpacing(5)
        visiableGrid.addWidget(self.modeShortButton, 0, 0, 1, 2, Qt.AlignLeft)
        visiableGrid.addWidget(self.modeLongButton, 1, 0, 1, 2, Qt.AlignLeft)
        visiableGrid.addWidget(self.IQRstatusLab, 0, 2, 1, 2, Qt.AlignHCenter)
        visiableGrid.addWidget(self.IQRstatus, 1, 2, 1, 2)
        visiableGrid.addWidget(self.statusButton, 0, 4, 2, 2)
        
        self.visiablePanel = QGroupBox()
        self.visiablePanel.setStyleSheet("QGroupBox{border: 1px groove silver; margin: 1px; padding-top: 0}")
        self.visiablePanel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        self.visiablePanel.setLayout(visiableGrid)

        # set the hidden panel
        invisiableGrid = QGridLayout()
        invisiableGrid.setSpacing(5)
        invisiableGrid.addWidget(self.operatForwardButton, 0, 0, 1, 2, Qt.AlignHCenter)
        invisiableGrid.addWidget(self.operatBackwardButton, 0, 2, 1, 2, Qt.AlignHCenter)
        invisiableGrid.addWidget(self.stepLab, 1, 0, 1, 1, Qt.AlignRight)
        invisiableGrid.addWidget(self.stepInput, 1, 1, 1, 1, Qt.AlignLeft)
        invisiableGrid.addWidget(self.stepChangeLab, 1, 2, 1, 1, Qt.AlignRight)
        invisiableGrid.addWidget(self.stepChange, 1, 3, 1, 1, Qt.AlignHCenter)
        
        self.invisiablePanel = QGroupBox()
        self.invisiablePanel.setStyleSheet("QGroupBox{border: 1px groove silver; margin: 1px; padding-top: 0}")
        self.invisiablePanel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        self.invisiablePanel.setLayout(invisiableGrid)
        self.invisiablePanel.setVisible(False)


        windowLayout = QVBoxLayout()
        windowLayout.setSpacing(5)
        windowLayout.addWidget(self.visiablePanel)
        windowLayout.addWidget(self.invisiablePanel)
        wid = QWidget()
        self.setCentralWidget(wid)
        wid.setLayout(windowLayout)

    def buildConnection(self):
        # build connection with mode
        def check_mode(b):
            if b.text() == "turn on " and b.isChecked() == True:
                self.statusBar().showMessage("turn on the IQ recorder")
                self.workMode = "2"
            if b.text() == "turn off" and b.isChecked() == True:
                self.statusBar().showMessage("turn off the IQ recorder")
                self.workMode = "1"
        self.modeShortButton.toggled.connect(lambda:check_mode(self.modeShortButton))
        self.modeLongButton.toggled.connect(lambda:check_mode(self.modeLongButton))

        # build connection with forward or backward
        def button_direction(b):
            if self.invisiablePanel.isVisible():
                if b.text() == "forward" and b.isChecked() == True:
                    self.direct = "1"
                if b.text() == "backward" and b.isChecked() == True:
                    self.direct = "2"
            else:
                return
        self.operatForwardButton.toggled.connect(lambda:button_direction(self.operatForwardButton))
        self.operatBackwardButton.toggled.connect(lambda:button_direction(self.operatBackwardButton))

        # build connection with play or pause
        def button_status():
            if self.statusButton.isChecked():
                if not self.invisiablePanel.isVisible():
                    self.current_worker = Worker(Press_work, self.workMode)
                    self.current_worker.signals.finished.connect(ready)
                    self.current_worker.signals.progress.connect(process)
                    self.current_worker.signals.result.connect(result)
                    self.statusButton.setEnabled(False)
                    self.threadPool.start(self.current_worker)
                else:
                    self.step = self.stepInput.text()
                    if int(self.step) <= 0:
                        self.statusBar.showMessage("step input invaild! input again...")
                        return
                    self.current_worker = Worker(Debug_work, self.direct, self.step, self.stepDiff)
                    self.current_worker.signals.finished.connect(ready)
                    self.current_worker.signals.progress.connect(process)
                    self.current_worker.signals.result.connect(result)
                    self.statusButton.setEnabled(False)
                    self.QLineEdit_RunStyle(self.stepInput)
                    self.threadPool.start(self.current_worker)
                self.statusBar().showMessage("start press!")
        self.statusButton.setCheckable(True)
        self.statusButton.toggled.connect(button_status)
        self.statusButton.setEnabled(False)

        # short/long press work
        def Press_work(mode, stdscr):
            self.control.write(mode)
            while True:
                msg = self.control.read()
                stdscr.emit(int(msg))
                if msg == "10" or msg == "11":
                    break
            return self.stepDiff
        # free press work
        def Debug_work(direction, step, stepDiff, stdscr):
            self.control.write("3")
            time.sleep(0.05)
            self.control.write(direction + "," + step)
            while True:
                msg = self.control.read()
                stdscr.emit(int(msg))
                if msg == "10" or msg == "11":
                    break
            if direction == "1":
                return (stepDiff + int(step))
            else:
                return (stepDiff - int(step))
        def process(percentVal):
            if percentVal == 0:
                self.statusButton.setChecked(False)
                self.statusBar().showMessage("end press!")
            elif percentVal == 10:
                self.IQRstatus.setStyleSheet(self.off_style)
                self.IQRstatus.setFormat("off")
            elif percentVal == 11:
                self.IQRstatus.setStyleSheet(self.on_style)
                self.IQRstatus.setFormat("on")
            else:
                pass
        def ready():
            self.statusButton.setEnabled(True)
            self.QLineEdit_StopStyle(self.stepInput)
            self.statusBar().showMessage("operation ends")
            if self.hide:
                if self.invisiablePanel.isVisible():
                    self.invisiablePanel.setVisible(False)
                    self.modeLongButton.setEnabled(True)
                    self.modeShortButton.setEnabled(True)
                    self.modeLongButton.setStyleSheet(self.able_style)
                    self.modeShortButton.setStyleSheet(self.able_style)
                    self.statusBar().showMessage("hide the free mode")
            else:
                if not self.invisiablePanel.isVisible():
                    self.invisiablePanel.setVisible(True)
                    self.modeLongButton.setEnabled(False)
                    self.modeShortButton.setEnabled(False)
                    self.modeLongButton.setStyleSheet(self.inable_style)
                    self.modeShortButton.setStyleSheet(self.inable_style)
                    self.statusBar().showMessage("show the free mode")
            if self.exit:
                self.statusBar().showMessage("exit the controller")
                self.control.disconnect()
                sys.exit()
        def result(stepDiff):
            self.stepDiff = stepDiff
            if self.stepDiff <= 0:
                self.stepChange.setText(str(self.stepDiff))
            else:
                self.stepChange.setText("+" + str(self.stepDiff))

        # intial the client
        def client_init(stdscr):
            self.control = ControlClient("10.10.91.96", 5052)
            self.control.write("init")
            msg = self.control.read()
            stdscr.emit(int(msg))
        client_worker = Worker(client_init)
        client_worker.signals.progress.connect(process)
        client_worker.signals.finished.connect(ready)
        self.statusBar().showMessage("waiting for connecting...")
        self.threadPool.start(client_worker)

    def keyPressEvent(self, event):
        if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_H:
            if self.statusButton.isEnabled():
                if self.invisiablePanel.isVisible():
                    self.hide = True
                    self.invisiablePanel.setVisible(False)
                    self.modeLongButton.setEnabled(True)
                    self.modeShortButton.setEnabled(True)
                    self.modeLongButton.setStyleSheet(self.able_style)
                    self.modeShortButton.setStyleSheet(self.able_style)
                    self.statusBar().showMessage("hide the free mode")
                else:
                    self.hide = False
                    self.invisiablePanel.setVisible(True)
                    self.modeLongButton.setEnabled(False)
                    self.modeShortButton.setEnabled(False)
                    self.modeLongButton.setStyleSheet(self.inable_style)
                    self.modeShortButton.setStyleSheet(self.inable_style)
                    self.statusBar().showMessage("show the free mode")
            else:
                if self.invisiablePanel.isVisible():
                    self.hide = True
                    self.statusBar().showMessage("hide the free mode after finished!")
                else:
                    self.hide = False
                    self.statusBar().showMessage("show the free mode after finished!")
        elif event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_W:
            reply = QMessageBox.question(self, "Message", "Are you sure to quit?")
            if reply == QMessageBox.Yes:
                if self.statusButton.isEnabled():
                    self.statusBar().showMessage("exit the controller")
                    self.control.disconnect()
                    sys.exit()
                else:
                    self.exit = True
                    self.statusBar().showMessage("exit after finished!")
            else:
                return
        elif event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_X and self.statusButton.isEnabled():
            reply = QMessageBox.question(self, "Message", "Are you sure to quit both controller and raspberry slave?")
            if reply == QMessageBox.Yes:
                self.statusBar().showMessage("exit the controller")
                self.control.write("kill")
                self.control.disconnect()
                sys.exit()
            else:
                return
        else:
            pass

    def closeEvent(self, event):
        reply = QMessageBox.question(self, "Message", "Are you sure to force quit?")
        if reply == QMessageBox.Yes:
            self.statusBar().showMessage("exit the controller")
            self.control.disconnect()
            sys.exit()
        else:
            event.ignore()

if __name__=='__main__':
    app = QApplication(sys.argv)
    controller = MainWindow()
    controller.show()
    sys.exit(app.exec())
