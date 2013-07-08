# some other useful imports
import html, re, sys
# add DoX core to path
sys.path.append("dox")
# main class import
from dox import *
# interface with PyQt
from PyQt4 import QtCore, QtGui

class lists(QtGui.QMainWindow):
    selectChangeOverride = False
    def __init__(self, dox, worker):
        QtGui.QMainWindow.__init__(self)
        self.dox = dox
        self.worker = worker
        self.setWindowTitle("DoX: List tasks")
        self.setWindowIcon(QtGui.QIcon("check.png"))
        self.resize(1040, 600)
        self.setGeometry(QtGui.QStyle.alignedRect(QtCore.Qt.LeftToRight, QtCore.Qt.AlignCenter, self.size(),
                                                  QtGui.QDesktopWidget().availableGeometry()))
        # main layout
        self.mainLayout = QtGui.QHBoxLayout()
        self.mainLayout.addWidget(self.buildMain())
        self.mainLayout.addWidget(self.buildSide())
        # main widget
        self.mainWidget = QtGui.QWidget()
        self.mainWidget.setLayout(self.mainLayout)
        self.setCentralWidget(self.mainWidget)
        # signal listeners
        self.connect(self.worker, QtCore.SIGNAL("refresh()"), self.refresh)
        # protocol handlers
        QtGui.QDesktopServices.setUrlHandler("dox", self.handleURL)
    def buildMain(self):
        # controls
        tables = []
        for i in range(2):
            table = QtGui.QTableWidget()
            table.setColumnCount(6)
            table.setHorizontalHeaderLabels(["#", "Task", "!", "Due", "Repeat", "Tags"])
            table.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
            table.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
            table.setShowGrid(False)
            table.verticalHeader().setVisible(False)
            tables.append(table)
        self.taskTable, self.doneTable = tables
        # tabs
        self.listTabs = QtGui.QTabWidget()
        taskTab = QtGui.QWidget()
        doneTab = QtGui.QWidget()
        self.listTabs.addTab(taskTab, "To-do")
        self.listTabs.addTab(doneTab, "Done")
        # layouts
        taskLayout = QtGui.QVBoxLayout()
        taskLayout.addWidget(self.taskTable)
        taskTab.setLayout(taskLayout)
        doneLayout = QtGui.QVBoxLayout()
        doneLayout.addWidget(self.doneTable)
        doneTab.setLayout(doneLayout)
        # shortcuts
        switchTabs1 = QtGui.QShortcut(self)
        switchTabs1.setKey("Ctrl+Tab")
        switchTabs2 = QtGui.QShortcut(self)
        switchTabs2.setKey("Ctrl+Shift+Tab")
        # connections
        self.taskTable.itemSelectionChanged.connect(self.taskSelectionChanged)
        self.doneTable.itemSelectionChanged.connect(self.doneSelectionChanged)
        self.listTabs.currentChanged.connect(self.tabSwitched)
        switchTabs1.activated.connect(self.switchTab)
        switchTabs2.activated.connect(self.switchTab)
        # return new tabs
        return self.listTabs
    def buildSide(self):
        # controls
        self.infoContent = QtGui.QLabel("Select a task on the left.")
        self.infoContent.setAlignment(QtCore.Qt.AlignCenter)
        self.infoContent.setOpenExternalLinks(True)
        self.infoContent.setWordWrap(True)
        self.infoDone = QtGui.QPushButton("Done")
        self.infoDone.setEnabled(False)
        self.infoMove = QtGui.QPushButton("Move")
        self.infoMove.setEnabled(False)
        self.infoEdit = QtGui.QPushButton("Edit")
        self.infoEdit.setEnabled(False)
        self.infoDelete = QtGui.QPushButton("Delete")
        self.infoDelete.setEnabled(False)
        self.filterPriCheck = QtGui.QCheckBox("Restrict list to tasks with minimum priority:")
        self.filterPriCombo = QtGui.QComboBox()
        self.filterPriCombo.addItems(["Medium (1)", "High (2)", "Critical (3)"])
        self.filterPriCombo.setEnabled(False)
        self.filterTagCheck = QtGui.QCheckBox("Restrict list to tasks with assigned tags:")
        self.filterTagEdit = QtGui.QLineEdit()
        self.filterTagEdit.setEnabled(False)
        # tabs
        self.controlTabs = QtGui.QTabWidget()
        infoTab = QtGui.QWidget()
        sortTab = QtGui.QWidget()
        filterTab = QtGui.QWidget()
        self.controlTabs.addTab(infoTab, "Task")
        self.controlTabs.addTab(sortTab, "Sort")
        self.controlTabs.addTab(filterTab, "Filter")
        self.controlTabs.setMaximumWidth(250)
        # layouts
        cmdLayout = QtGui.QHBoxLayout()
        cmdLayout.addWidget(self.infoDone)
        cmdLayout.addWidget(self.infoMove)
        cmdLayout.addWidget(self.infoEdit)
        cmdLayout.addWidget(self.infoDelete)
        infoLayout = QtGui.QVBoxLayout()
        infoLayout.addWidget(self.infoContent)
        infoLayout.addLayout(cmdLayout)
        infoTab.setLayout(infoLayout)
        sortLayout = QtGui.QVBoxLayout()
        sortLayout.addWidget(QtGui.QLabel("Coming soon..."))
        sortTab.setLayout(sortLayout)
        filterLayout = QtGui.QVBoxLayout()
        filterLayout.addWidget(self.filterPriCheck)
        filterLayout.addWidget(self.filterPriCombo)
        filterLayout.addWidget(self.filterTagCheck)
        filterLayout.addWidget(self.filterTagEdit)
        filterTab.setLayout(filterLayout)
        # connections
        self.filterPriCheck.toggled.connect(self.filterPriToggled)
        self.filterTagCheck.toggled.connect(self.filterTagToggled)
        # return new tabs
        return self.controlTabs
    def refresh(self):
        # flush table
        self.taskTable.setRowCount(0)
        # reallocate table
        self.taskTable.setRowCount(len(self.dox.tasks))
        # loop through tasks
        count = 0
        for taskObj in self.dox.tasks:
            # cell values
            cells = [str(taskObj.id), taskObj.title, str(taskObj.pri), prettyDue(taskObj.due) if taskObj.due else "<none>",
                     prettyRepeat(taskObj.repeat) if taskObj.repeat else "<none>", ", ".join(taskObj.tags)]
            column = 0
            for cell in cells:
                # set each cell
                self.taskTable.setItem(count, column, QtGui.QTableWidgetItem(cell))
                column += 1
            count += 1
        # resize columns
        self.taskTable.resizeColumnsToContents()
        # flush table
        self.doneTable.setRowCount(0)
        # reallocate table
        self.doneTable.setRowCount(len(self.dox.done))
        # loop through done tasks
        count = 0
        for taskObj in self.dox.done:
            # cell values
            cells = [str(taskObj.id), taskObj.title, str(taskObj.pri), prettyDue(taskObj.due) if taskObj.due else "<none>",
                     prettyRepeat(taskObj.repeat) if taskObj.repeat else "<none>", ", ".join(taskObj.tags)]
            column = 0
            for cell in cells:
                # set each cell
                self.doneTable.setItem(count, column, QtGui.QTableWidgetItem(cell))
                column += 1
            count += 1
        # resize columns
        self.doneTable.resizeColumnsToContents()
    def taskSelectionChanged(self):
        self.selectionChanged(True)
    def doneSelectionChanged(self):
        self.selectionChanged(False)
    def selectionChanged(self, isTasks):
        # if not setting selection programatically
        if not self.selectChangeOverride:
            # select from correct table
            table = self.taskTable if isTasks else self.doneTable
            # list of rows selected
            rows = []
            for i in table.selectedIndexes():
                if i.row() not in rows:
                    rows.append(i.row())
            # nothing selected
            if len(rows) == 0:
                self.infoContent.setText("Select a task on the left.")
                # disable all controls
                self.infoDone.setEnabled(False)
                self.infoMove.setEnabled(False)
                self.infoEdit.setEnabled(False)
                self.infoDelete.setEnabled(False)
            # one row selected, show details
            elif len(rows) == 1:
                id = table.item(rows[0], 0).text()
                # fetch from correct table
                if isTasks:
                    taskObj = self.dox.getTask(int(id))
                else:
                    taskObj = self.dox.getDone(int(id))
                pris = ["Low", "Medium", "High", "Critical"]
                # convert a URL into an <a> tag with correct link
                def linkify(match):
                    # group 0 is entire match
                    href = match.group(0)
                    # no protocol, default to http://
                    if not match.group(1):
                        href = "http://" + href
                    # return <a> tag
                    return "<a href=\"" + href.replace("\"", "%22") + "\">" + html.escape(match.group(0)) + "</a>"
                # linkify all URLs, including ones that look like links (e.g. "foo.com")
                descWrap = re.sub("([a-z]+://)?([a-z\-\+]+\.)+[a-z]{2,6}([/#?]\S*[^\.,\s\[\]\(\)])*", linkify, taskObj.desc, flags=re.IGNORECASE)
                # HTML new lines
                descWrap = descWrap.replace("\n", "<br/>")
                # link tags to internal protocol for tag filtering
                tagWrap = ["<a href=\"dox://tag/{0}\">{0}</a>".format(x) for x in taskObj.tags]
                # set new content
                self.infoContent.setText("<b>{}</b><br/><br/>{}Priority: {} ({}){}{}{}".format(taskObj.title,
                                                                                               descWrap + "<br/><br/>" if descWrap else "",
                                                                                               pris[taskObj.pri], taskObj.pri,
                                                                                               "<br/>Due: " + prettyDue(taskObj.due) if taskObj.due else "",
                                                                                               "<br/>Repeat: " + prettyRepeat(taskObj.repeat) if taskObj.repeat else "",
                                                                                               "<br/><br/>" + "  ".join(tagWrap) if tagWrap else ""))
                # enable all controls
                self.infoDone.setEnabled(True)
                self.infoMove.setEnabled(True)
                self.infoEdit.setEnabled(True)
                self.infoDelete.setEnabled(True)
            # multiple rows selected
            else:
                self.infoContent.setText("{} tasks selected.".format(len(rows)))
                # only enable multiple delete and competion
                self.infoDone.setEnabled(True)
                self.infoMove.setEnabled(False)
                self.infoEdit.setEnabled(False)
                self.infoDelete.setEnabled(True)
    def switchTab(self):
        # toggle tab index (1 - 1 = 0, 1 - 0 = 1)
        self.listTabs.setCurrentIndex(1 - self.listTabs.currentIndex())
    def tabSwitched(self, index):
        # clear selection on other table (i.e. not new selected one) on switch
        table = self.taskTable if index == 1 else self.doneTable
        table.clearSelection()
    def filterPriToggled(self, checked):
        self.filterPriCombo.setEnabled(checked)
    def filterTagToggled(self, checked):
        self.filterTagEdit.setEnabled(checked)
    @QtCore.pyqtSlot(QtCore.QUrl)
    def handleURL(self, url):
        # tag filter request
        if url.host() == "tag":
            tag = url.path()[1:]
            # switch to filter tab
            self.controlTabs.setCurrentIndex(2)
            # enable filtering by tag
            self.filterTagCheck.setChecked(True)
            # append tag to current list
            if self.filterTagEdit.text():
                self.filterTagEdit.setText(self.filterTagEdit.text() + " " + quote(tag))
            else:
                self.filterTagEdit.setText(quote(tag))
    def closeEvent(self, event):
        # don't actually close - window is reused
        self.hide()
        event.ignore()