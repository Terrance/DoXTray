# some other useful imports
import os, sys, webbrowser
# add DoX core to path
sys.path.append("dox")
# main class import
from dox import *
# window class imports
from add import *
from lists import *
# interface with PyQt
from PyQt4 import QtCore, QtGui

class fileMonitor(QtCore.QThread):
    def __init__(self, dox):
        QtCore.QThread.__init__(self)
        # connect to API
        self.dox = dox
        # load tasks
        self.dox.loadTasks()
        # set last read time to now
        self.fileLastMod = datetime.datetime.now()
        # trigger refresh for list window
        self.emit(QtCore.SIGNAL("refresh()"))
    def run(self):
        while True:
            # tasks list has been modified since last check
            if self.dox.tasksFileLastMod() > self.fileLastMod:
                # reload tasks from file
                self.dox.loadTasks()
                # update last mod. time
                self.fileLastMod = self.dox.tasksFileLastMod()
                # trigger refresh for list window
                self.emit(QtCore.SIGNAL("refresh()"))
            # sleep for a bit
            time.sleep(5)
    def listsSaved(self):
        # update last mod. time now without triggering refresh
        self.fileLastMod = self.dox.tasksFileLastMod()

class dueMonitor(QtCore.QThread):
    def __init__(self, dox):
        QtCore.QThread.__init__(self)
        # connect to API
        self.dox = dox
        # empty list of past notifications
        self.notified = []
    def run(self):
        while True:
            now = datetime.datetime.now()
            today = datetime.datetime.combine(now.date(), datetime.time())
            noTasks = True
            # remove tasks from notified that don't exist
            self.notified = [x for x in self.notified if x[0] in self.dox.tasks]
            # loop all tasks
            for taskObj in self.dox.tasks:
                # if task is due now
                if taskObj.due and ((taskObj.due[1] and taskObj.due[0] < now) or (not taskObj.due[1] and taskObj.due[0] <= today)):
                    # check it hasn't been notified recently
                    ok = True
                    for notify in self.notified:
                        # compare to see if notified about before
                        if notify[0] == taskObj:
                            # if notified about in the last hour
                            if notify[1] + datetime.timedelta(hours=1) > now:
                                ok = False
                            else:
                                # remove previous record as new one will be added
                                self.notified.remove(notify)
                            break
                    if ok:
                        noTasks = False
                        # popup alert
                        self.emit(QtCore.SIGNAL("warning(QString, QString)"), taskObj.title, (taskObj.desc if taskObj.desc else "Due now!"))
                        # add to known notified list
                        self.notified.append((taskObj, now))
                        # only do one for now
                        break
            # if nothing to notify about, sleep for a while
            time.sleep(60 if noTasks else 10)

class tray(QtGui.QSystemTrayIcon):
    def __init__(self, dox):
        QtGui.QSystemTrayIcon.__init__(self)
        # components
        self.setIcon(QtGui.QIcon("check.png"))
        self.setToolTip("DoX")
        # construct other features
        self.dox = dox
        self.fileMonitor = fileMonitor(dox)
        self.dueMonitor = dueMonitor(dox)
        self.addWindow = add(dox)
        self.listsWindow = lists(dox, self.fileMonitor)
        # connections
        self.activated.connect(self.activate)
        # signal listeners
        self.connect(self.fileMonitor, QtCore.SIGNAL("refresh()"), self.listsWindow.refresh)
        self.connect(self.fileMonitor, QtCore.SIGNAL("refresh()"), self.makeMenu)
        self.connect(self.dueMonitor, QtCore.SIGNAL("warning(QString, QString)"), self.warning)
        self.connect(self.addWindow, QtCore.SIGNAL("info(QString, QString)"), self.info)
        self.connect(self, QtCore.SIGNAL("refresh()"), self.listsWindow.refresh)
        self.connect(self.addWindow, QtCore.SIGNAL("refresh()"), self.listsWindow.refresh)
        self.connect(self.listsWindow, QtCore.SIGNAL("listsSaved()"), self.makeMenu)
        self.connect(self.listsWindow, QtCore.SIGNAL("listsSaved()"), self.fileMonitor.listsSaved)
        # start polling
        self.fileMonitor.start()
        self.dueMonitor.start()
        # create context menu
        self.makeMenu()
        # show tray icon
        self.show()
    def makeMenu(self):
        self.mainMenu = QtGui.QMenu()
        listsAction = self.mainMenu.addAction("&List tasks")
        listsAction.triggered.connect(self.listTasks)
        addAction = self.mainMenu.addAction("&Add task...")
        addAction.triggered.connect(self.addTask)
        self.mainMenu.addSeparator()
        # submenu to quickly complete a task
        if self.dox.getCount():
            self.markDoneMenu = self.mainMenu.addMenu("Mark &done")
            tasks = self.dox.getAllTasks()
            for taskObj in tasks:
                pos = self.dox.idToPos(taskObj.id)
                markAction = self.markDoneMenu.addAction("{}{}. {}".format("&" if pos <= 9 else "", pos, taskObj.title.replace("&", "&&")))
                markAction.setData(pos)
                markAction.triggered.connect(self.markDone)
        # submenu to quickly undo a task
        if self.dox.getCount(False):
            self.markUndoMenu = self.mainMenu.addMenu("&Undo task")
            tasks = self.dox.getAllTasks(False)
            for taskObj in tasks:
                pos = self.dox.idToPos(taskObj.id, False)
                markAction = self.markUndoMenu.addAction("{}{}. {}".format("&" if pos <= 9 else "", pos, taskObj.title.replace("&", "&&")))
                markAction.setData(pos)
                markAction.triggered.connect(self.markUndo)
        self.mainMenu.addSeparator()
        tasksAction = self.mainMenu.addAction("&Edit tasks.txt")
        tasksAction.triggered.connect(self.editTasks)
        doneAction = self.mainMenu.addAction("Edi&t done.txt")
        doneAction.triggered.connect(self.editDone)
        self.mainMenu.addSeparator()
        exitAction = self.mainMenu.addAction("E&xit DoX")
        exitAction.triggered.connect(QtGui.QApplication.quit)
        # default to listing tasks
        self.mainMenu.setDefaultAction(listsAction)
        # assign the menu
        self.setContextMenu(self.mainMenu)
    def addTask(self):
        # bring window to front, focus on text field
        self.addWindow.show()
        self.addWindow.raise_()
        self.addWindow.stringEdit.setFocus()
    def listTasks(self):
        # bring window to front
        self.listsWindow.show()
        self.listsWindow.raise_()
        # set initial split position
        if not self.listsWindow.splitMoved:
            self.listsWindow.splitWidget.moveSplitter(760, 1)
            self.listsWindow.splitMoved = True
        self.listsWindow.refresh()
    def markDone(self):
        # fetch task associated with action
        pos = self.sender().data()
        # mark as done
        self.dox.doneNthTask(pos)
        # resave and refresh
        self.saveAndRefresh()
    def markUndo(self):
        # fetch task associated with action
        pos = self.sender().data()
        # mark as done
        self.dox.undoNthTask(pos)
        # resave and refresh
        self.saveAndRefresh()
    def saveAndRefresh(self):
        # save tasks
        self.dox.saveTasks()
        # update lists window if open
        self.emit(QtCore.SIGNAL("refresh()"))
        # update context menu
        self.makeMenu()
    def editTasks(self):
        # open a text editor with tasks.txt
        webbrowser.open(os.path.join(os.path.expanduser("~"), "DoX", "tasks.txt"))
    def editDone(self):
        # open a text editor with tasks.txt
        webbrowser.open(os.path.join(os.path.expanduser("~"), "DoX", "done.txt"))
    def info(self, title, desc):
        # information popup
        self.showMessage("DoX: " + title, desc)
    def warning(self, title, desc):
        # alert popup
        self.showMessage("DoX: " + title, desc, QtGui.QSystemTrayIcon.Warning)
    def activate(self, reason):
        # double-clicked
        if reason == 2:
            self.listTasks()
        # middle-clicked
        elif reason == 4:
            self.addTask()

if __name__ == "__main__":
    # make Qt application
    app = QtGui.QApplication(sys.argv)
    # start tray icon
    foreground = tray(dox())
    # execute
    app.exec_()
