import os.path
import platform
import subprocess
import sys
import time

from PyQt6.QtWidgets import QApplication, QTreeView, QAbstractItemDelegate, QWidget, QVBoxLayout, QMainWindow, \
    QListWidgetItem, QListWidget, QLabel, QHBoxLayout, QFrame, QToolBar, QPushButton, QListView, QGridLayout, QStyle, \
    QSizePolicy, QSpacerItem, QScrollArea, QAbstractScrollArea, QMenu, QToolButton
from PyQt6.QtCore import QDir, Qt, QAbstractItemModel, QModelIndex, QSize, QRect, pyqtSignal, QEvent
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QFileSystemModel, QAction, QFont

style_sheet = """


QLabel#tabLabel{
    border-radius: 5px;}

QLabel#tabLabel:hover{ 
    background-color: #ededed;} 

QFrame#sbFrame{
    border: 2px solid grey;}
    
QFrame#tbFrame{
    border: 1px solid black;
    border-radius: 2px;}    
"""


class ClickableLabel(QLabel):
    clicked = pyqtSignal()

    def mousePressEvent(self, ev):
        self.clicked.emit()


class MyListView(QListView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.createActions()
        self.setupListView()
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.createMenu)

    def setupListView(self):
        self.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.setViewMode(QListWidget.ViewMode.IconMode)
        self.setLayoutMode(QListWidget.LayoutMode.SinglePass)
        self.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.setMovement(QListWidget.Movement.Snap)

        self.setIconSize(QSize(60, 60))  # size of icons for each item
        self.setSpacing(20)  # spacing between each item
        self.setGridSize(QSize(100, 100))  # Size of the box for each item
        self.setWordWrap(True)
        self.setSelectionRectVisible(True)  # doesn't apply with .setSelectionMode --> SingleSelection
        self.setFrameStyle(QListWidget.Shape.NoFrame)

    def createMenu(self, pos):
        menu = QMenu(self)
        index = self.indexAt(pos)

        if index.isValid():  # user clicked dir/file
            menu.addAction(self.open_directory_act)
            menu.addAction(self.cut_directory_act)
            menu.addSeparator()
            menu.addAction(self.copy_directory_act)
            menu.addAction(self.paste_directory_act)
            menu.addSeparator()
            menu.addAction(self.copyTo_directory_act)
            menu.addAction(self.move_directory_act)
            menu.addSeparator()
            menu.addAction(self.rename_directory_act)
            menu.addAction(self.delete_directory_act)
            menu.addSeparator()
            menu.addAction(self.properties_directory_act)

            menu.exec(self.mapToGlobal(pos))

        else:  # user clicked blank space
            menu.addAction(self.new_directory_act)
            menu.addAction(self.properties_directory_act)

            menu.exec(self.mapToGlobal(pos))

    def createActions(self):
        self.open_directory_act = QAction("Open")
        self.copy_directory_act = QAction("Copy")
        self.paste_directory_act = QAction("Paste")
        self.copyTo_directory_act = QAction("Copy to...")
        self.move_directory_act = QAction("Move to...")
        self.cut_directory_act = QAction("Cut")
        self.delete_directory_act = QAction("Delete")
        self.properties_directory_act = QAction("Properties")
        self.new_directory_act = QAction("New Folder")
        self.selectAll_directory_act = QAction("Select All")
        self.rename_directory_act = QAction("Rename")

    def copy(self, model):
        index = self.currentIndex()
        if index.isValid():
            self.copiedIndex = index
            self.copiedPath

class MyToolBar(QToolBar):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        if isinstance(parent, QMainWindow):
            self.setParent(parent)
            parent.addToolBar(Qt.ToolBarArea.TopToolBarArea, self)
        self.setup()

    def setup(self):
        self.setFixedHeight(45)
        self.setMovable(False)
        self.toggleViewAction().setEnabled(False)
        self.setIconSize(QSize(25, 25))
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)

    def event(self, event):
        if event.type() == QEvent.Type.ContextMenu:
            return True
        return super().event(event)


class Tanz(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initializeUI()

    def initializeUI(self):
        # Set window properties
        self.setWindowTitle("Tanzanite File Manager")
        # self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setMinimumSize(800, 500)

        self.visited_directory_list = [QDir.homePath()]
        self.forward_directory_list = []

        self.setUpActions()
        self.setUpToolBarMenu()
        self.setUpMainWindow()

        self.show()

    def setUpMainWindow(self):
        self.main_toolbar = MyToolBar()
        self.setUpToolBar()

        self.addToolBar(self.main_toolbar)
        self.addToolBarBreak()

        # Create Side Bar QLabel(s) and ClickableLabel(s)
        tLabelSize = QSize(175, 45)

        self.tab_recent_l = QLabel("Recent")
        self.tab_recent_l.setObjectName("tabLabel")
        self.tab_recent_l.setFixedSize(tLabelSize)
        self.tab_recent_l.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

        self.tab_starred_l = QLabel("Starred")
        self.tab_starred_l.setObjectName("tabLabel")
        self.tab_starred_l.setFixedSize(tLabelSize)
        self.tab_starred_l.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

        self.tab_home_l = ClickableLabel("Home")
        self.tab_home_l.setObjectName("tabLabel")
        self.tab_home_l.setFixedSize(tLabelSize)
        self.tab_home_l.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        self.tab_home_l.clicked.connect(self.loadHomeDir)

        self.tab_desktop_l = ClickableLabel("Desktop")
        self.tab_desktop_l.setObjectName("tabLabel")
        self.tab_desktop_l.setFixedSize(tLabelSize)
        self.tab_desktop_l.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        self.tab_desktop_l.clicked.connect(self.loadDeskDir)

        self.tab_document_l = ClickableLabel("Documents")
        self.tab_document_l.setObjectName("tabLabel")
        self.tab_document_l.setFixedSize(tLabelSize)
        self.tab_document_l.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        self.tab_document_l.clicked.connect(self.loadDocDir)

        self.tab_download_l = ClickableLabel("Downloads")
        self.tab_download_l.setObjectName("tabLabel")
        self.tab_download_l.setFixedSize(tLabelSize)
        self.tab_download_l.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        self.tab_download_l.clicked.connect(self.loadDownDir)

        self.tab_music_l = ClickableLabel("Music")
        self.tab_music_l.setObjectName("tabLabel")
        self.tab_music_l.setFixedSize(tLabelSize)
        self.tab_music_l.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        self.tab_music_l.clicked.connect(self.loadMusicDir)

        self.tab_picture_l = ClickableLabel("Pictures")
        self.tab_picture_l.setObjectName("tabLabel")
        self.tab_picture_l.setFixedSize(tLabelSize)
        self.tab_picture_l.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        self.tab_picture_l.clicked.connect(self.loadPictDir)

        self.tab_video_l = ClickableLabel("Videos")
        self.tab_video_l.setObjectName("tabLabel")
        self.tab_video_l.setFixedSize(tLabelSize)
        self.tab_video_l.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        self.tab_video_l.clicked.connect(self.loadVideoDir)

        self.tab_trash_l = ClickableLabel("Trash")
        self.tab_trash_l.setObjectName("tabLabel")
        self.tab_trash_l.setFixedSize(tLabelSize)
        self.tab_trash_l.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        self.tab_trash_l.clicked.connect(self.loadTrashDir)

        self.list_widget = MyListView()  # Create QListWidget
        self.model = QFileSystemModel()
        self.model.setRootPath(QDir.homePath())
        self.list_widget.setModel(self.model)
        self.list_widget.setRootIndex(self.model.index(QDir.homePath()))

        """ Adjust QListWidget properties """

        self.list_widget.doubleClicked.connect(self.directory_load)
        # Create Layouts
        core_v_box = QVBoxLayout()
        core_v_box.addWidget(self.list_widget)

        sideBar_v_box = QVBoxLayout()  # Create sideBar container as QVBoxLayout
        sideBar_v_box.setSpacing(0)
        sideBar_v_box.setContentsMargins(0, 0, 0, 0)
        sideBar_v_box.setAlignment(Qt.AlignmentFlag.AlignTop)

        sideBar_v_box.addWidget(self.tab_recent_l)
        sideBar_v_box.addWidget(self.tab_starred_l)
        sideBar_v_box.addWidget(self.tab_home_l)
        sideBar_v_box.addWidget(self.tab_desktop_l)
        sideBar_v_box.addWidget(self.tab_document_l)
        sideBar_v_box.addWidget(self.tab_music_l)
        sideBar_v_box.addWidget(self.tab_picture_l)
        sideBar_v_box.addWidget(self.tab_video_l)
        sideBar_v_box.addWidget(self.tab_trash_l)

        sideBar_frame = QFrame()
        sideBar_frame.setObjectName("sbFrame")
        sideBar_frame.setFrameStyle(QFrame.Shape.Box)
        # sideBar_frame.setLineWidth(2) # now in style_sheet variable
        sideBar_frame.setLayout(sideBar_v_box)

        core_h_box = QHBoxLayout()
        core_h_box.setContentsMargins(0, 0, 0, 0)
        core_h_box.addWidget(sideBar_frame)
        core_h_box.addLayout(core_v_box)

        core_wid = QWidget()
        core_wid.setLayout(core_h_box)

        self.setCentralWidget(core_wid)

    def setUpToolBar(self):

        t_back_i = QIcon(QPixmap("icons/back.png"))
        self.t_back_act = QAction(t_back_i, "")
        self.t_back_act.setToolTip("Back")
        self.t_back_act.triggered.connect(self.directory_back_process)

        t_fwrd_i = QIcon(QPixmap("icons/forward.png"))
        self.t_frwd_act = QAction(t_fwrd_i, "")
        self.t_frwd_act.setEnabled(False)
        self.t_frwd_act.triggered.connect(self.directory_forward_process)

        toolbar_menu_icon = QIcon(QPixmap("icons/vert-menu.png"))
        self.toolbar_menu_act = QAction(toolbar_menu_icon, "")
        self.toolbar_menu_act.setMenu(self.toolbar_menu)

        t_srch_i = QIcon(QPixmap("icons/search.png"))
        self.t_srch_act = QAction(t_srch_i, "")

        self.dirPath_h_box = QHBoxLayout()
        self.dirPath_h_box.setContentsMargins(10, 0, 10, 0)
        self.dirPath_h_box.setSpacing(5)
        self.dirPath_h_box.setAlignment(Qt.AlignmentFlag.AlignLeft)

        pathOutput_widget = QWidget()
        pathOutput_widget.setLayout(self.dirPath_h_box)
        self.pathOutput = QScrollArea()
        self.pathOutput.setFixedSize(575, 30)
        self.pathOutput.setObjectName("tbFrame")

        self.pathOutput.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.pathOutput.horizontalScrollBar().setStyleSheet("QScrollBar {height:0px}")
        self.pathOutput.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.pathOutput.setWidgetResizable(True)
        self.pathOutput.setWidget(pathOutput_widget)

        spacer_1 = QWidget()
        spacer_1.setFixedWidth(5)
        spacer_2 = QWidget()
        spacer_2.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        spacer_3 = QWidget()
        spacer_3.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        spacer_4 = QWidget()
        spacer_4.setFixedWidth(5)
        spacer_4.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.main_toolbar.addWidget(spacer_1)
        self.main_toolbar.addAction(self.t_back_act)
        self.main_toolbar.addAction(self.t_frwd_act)
        self.main_toolbar.addWidget(spacer_2)
        self.main_toolbar.addWidget(self.pathOutput)
        self.main_toolbar.addWidget(spacer_3)

        self.main_toolbar.addAction(self.toolbar_menu_act)
        toolbar_menu_btn = self.main_toolbar.widgetForAction(self.toolbar_menu_act)
        toolbar_menu_btn.setPopupMode(
            QToolButton.ToolButtonPopupMode.InstantPopup)
        toolbar_menu_btn.setStyleSheet('::menu-indicator {image: none}')

        self.main_toolbar.addAction(self.t_srch_act)
        self.main_toolbar.addWidget(spacer_4)

        self.display_directory_path(QDir.homePath())

    def setUpToolBarMenu(self):
        self.toolbar_menu = QMenu()
        self.toolbar_menu.setStyleSheet("""
                QMenu {
                text-align: center;
                }""")
        self.toolbar_menu.addAction(self.new_directory_act)
        self.toolbar_menu.addAction(self.bookmark_act)
        self.toolbar_menu.addSeparator()
        self.toolbar_menu.addAction(self.paste_directory_act)
        self.toolbar_menu.addAction(self.select_all_act)
        self.toolbar_menu.addSeparator()
        # can add open in terminal
        self.toolbar_menu.addAction(self.properties_act)

    def setUpActions(self):

        self.copy_dir_init_act = MyListView().copyTo_directory_act
        self.copy_dir_init_act.triggered.connect(self.copy_directory)


        ''' self.copy_directory_act = QAction("Copy")
        self.copy_directory_act.triggered.connect(self.copy_directory)
        '''


        self.paste_directory_act = QAction("Paste")
        # self.paste_directory_act.triggered.connect(self.paste_directory)

        self.new_directory_act = QAction("New Folder")
        self.new_directory_act.triggered.connect(self.new_directory)

        self.delete_directory_act = QAction("Delete")
        self.delete_directory_act.triggered.connect(self.delete_directory)

        self.cut_directory_act = QAction("Cut")

        self.move_directory_act = QAction("Move to...")

        self.move_to_trash_act = QAction("Move to Trash")

        self.rename_act = QAction("Rename")

        self.select_all_act = QAction("Select All")
        # self.select_all_act.triggered.connect(self.select_all)

        self.bookmark_act = QAction("Add to Bookmarks")

        self.properties_act = QAction("Properties")

    def directory_load(self):
        data = self.model.filePath(self.list_widget.currentIndex())
        if os.path.isdir(data):
            self.list_widget.setRootIndex(self.model.index(data))
            self.visited_directory_list.append(data)
            self.display_directory_path(data)
        elif os.path.isfile(data):
            self.openFile(data)
            self.visited_directory_list.append(data)

        time.sleep(0.2)

    def directory_back_process(self):
        self.t_frwd_act.setEnabled(True)
        if len(self.visited_directory_list) == 1:
            print(self.visited_directory_list[-1])
            self.list_widget.setRootIndex(self.model.index(self.visited_directory_list[-1]))
        else:
            print(self.visited_directory_list[-2])
            self.list_widget.setRootIndex(self.model.index(self.visited_directory_list[-2]))
            self.display_directory_path(self.visited_directory_list[-2])
            self.forward_directory_list.append(self.visited_directory_list.pop())

    def directory_forward_process(self):
        if len(self.forward_directory_list) == 0:
            self.t_back_act.setEnabled(False)
        else:
            print(self.forward_directory_list[-1])
            self.list_widget.setRootIndex(self.model.index(self.forward_directory_list[-1]))
            self.display_directory_path(self.forward_directory_list[-1])
            self.visited_directory_list.append(self.forward_directory_list.pop())

    def copy_directory(self):
        print(self.list_widget.currentIndex())
        pass

    def delete_directory(self):
        pass

    def new_directory(self):
        pass

    def openFile(self, data):
        if platform.system() == "Darwin":  # macOS
            subprocess.call(("open", data))
        elif platform.system() == "Windows":  # Windows
            os.startfile(data)
        else:  # linux variants
            subprocess.call(("xdg-open", data))

    def display_directory_path(self, path):
        for i in reversed(range(self.dirPath_h_box.count())):
            item = self.dirPath_h_box.itemAt(i)
            if item.widget():
                self.dirPath_h_box.removeWidget(item.widget())
                # item.widget().deleteLater()
            elif item.spacerItem():
                self.dirPath_h_box.removeItem(item.spacerItem())
            else:
                pass

        for sect in path.split("/")[1:]:
            sect_l = QLabel(sect)
            sect_l.setStyleSheet("""
                QLabel{
                    max-height: 25px;
                    font-size: 15px;
                    border-radius: 5px;
                    padding-left: 5px;
                    padding-right: 5px;
                    text-align:center;
                    }
                QLabel:hover{
                    background-color: #ededed;
                    }
            """)
            self.dirPath_h_box.addWidget(sect_l)
            if sect == path.split("/")[1:][-1]:
                pass
            else:
                idk = QLabel("/")
                self.dirPath_h_box.addWidget(idk)

        # spacer = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding)
        # self.dirPath_h_box.addItem(spacer)

    def loadHomeDir(self):
        direc = QDir.homePath()
        self.list_widget.setRootIndex(self.model.index(direc))
        self.visited_directory_list.append(direc)
        self.display_directory_path(direc)

    def loadDeskDir(self):
        direc = QDir.homePath() + "/Desktop"
        self.list_widget.setRootIndex(self.model.index(direc))
        self.visited_directory_list.append(direc)
        self.display_directory_path(direc)

    def loadDocDir(self):
        direc = QDir.homePath() + "/Documents"
        self.list_widget.setRootIndex(self.model.index(direc))
        self.visited_directory_list.append(direc)
        self.display_directory_path(direc)

    def loadDownDir(self):
        direc = QDir.homePath() + "/Downloads"
        self.list_widget.setRootIndex(self.model.index(direc))
        self.visited_directory_list.append(direc)
        self.display_directory_path(direc)

    def loadMusicDir(self):
        direc = QDir.homePath() + "/Music"
        self.list_widget.setRootIndex(self.model.index(direc))
        self.visited_directory_list.append(direc)
        self.display_directory_path(direc)

    def loadPictDir(self):
        direc = QDir.homePath() + "/Pictures"
        self.list_widget.setRootIndex(self.model.index(direc))
        self.visited_directory_list.append(direc)
        self.display_directory_path(direc)

    def loadVideoDir(self):
        direc = QDir.homePath() + "/Videos"
        self.list_widget.setRootIndex(self.model.index(direc))
        self.visited_directory_list.append(direc)
        self.display_directory_path(direc)

    def loadTrashDir(self):
        direc = QDir.homePath() + "~/.local/share/Trash/files"
        self.list_widget.setRootIndex(self.model.index(direc))
        self.visited_directory_list.append(direc)
        self.display_directory_path(direc)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet(style_sheet)
    window = Tanz()
    sys.exit(app.exec())
