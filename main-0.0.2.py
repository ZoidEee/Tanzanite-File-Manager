import os
import shutil
import sys
import time

from PyQt6.QtCore import QDir, QSize, pyqtSignal, Qt, QPoint, QModelIndex, QFileInfo, QFile, QMimeData, \
    QSortFilterProxyModel
from PyQt6.QtGui import QFileSystemModel, QIcon, QPixmap, QAction, QCursor, QClipboard, QGuiApplication
from PyQt6.QtWidgets import QMainWindow, QApplication, QListView, QHBoxLayout, QWidget, QLabel, QVBoxLayout, QFrame, \
    QToolBar, QScrollArea, QSizePolicy, QMenu, QToolButton, QLineEdit, QInputDialog, QMessageBox

style_sheet = """



QFrame#sbFrame{
    border: 1px solid #c5c4c4;}

QFrame#tbFrame{
    border: 1px solid black;
    border-radius: 2px;}    
"""


class TanzSideBarMenu(QFrame):
    clicked = pyqtSignal()

    def __init__(self, tab_text, pixmap):
        super().__init__()
        self.setFixedSize(QSize(145, 35))
        self.setStyleSheet("""
            QFrame{
                border-radius: 5px;}
            QFrame:hover{ 
                background-color: #ededed;} 
        """)

        self.pixmap = pixmap
        self.tab_text = tab_text

        self.setupLayout()

    def setupLayout(self):
        self.icon = QLabel()
        self.icon.setFixedWidth(25)
        self.icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon.setPixmap(self.pixmap.scaled(20, 20, aspectRatioMode=Qt.AspectRatioMode.KeepAspectRatioByExpanding))

        self.tab_text = QLabel(self.tab_text)
        self.tab_text.setFixedWidth(110)
        self.tab_text.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

        h_box = QHBoxLayout()
        h_box.addWidget(self.icon)
        h_box.addWidget(self.tab_text)
        # self.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.setLayout(h_box)

    def mousePressEvent(self, ev):
        self.clicked.emit()


class TanzFileManger(QMainWindow):

    def __init__(self):
        super().__init__()
        self.initUI()


    def initUI(self):
        self.setWindowTitle("Tanz")
        self.setFixedSize(800, 500)
        self.clipboard = QGuiApplication.clipboard()
        self.homePath = QDir.homePath()

        self.visited_directory_list = [QDir.homePath()]
        self.forward_directory_list = []
        self.bookmarked = []

        self.setupActions()
        self.setupMainWindow()

        self.show()

    def setupMainWindow(self):
        """ This below pertains to the Toolbar """
        self.core_toolbar = QToolBar()
        self.core_toolbar.setContextMenuPolicy(Qt.ContextMenuPolicy.PreventContextMenu)
        self.core_toolbar.setParent(self)
        self.core_toolbar.setFixedSize(800, 45)
        self.core_toolbar.setMovable(False)
        self.core_toolbar.toggleViewAction().setEnabled(False)
        self.core_toolbar.setIconSize(QSize(25, 25))
        self.core_toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)

        '''actions = [
            ("icons/back.png", "Back"), # re-add the functions back
            ("icons/forward.png", "Forward"),
            ("icons/vert-menu.png", "Menu"),
            ("icons/search.png", "Search")
        ]
        for icon_path, tooltip in actions: # add function after the "tooltip, function"
            icon = QIcon(QPixmap(icon_path))
            action = QAction(icon, tooltip, self)
            #action.triggered.connect(function)
            self.core_toolbar.addAction(action)
        '''
        toolbar_back_icon = QIcon(QPixmap("icons/back.png"))
        self.t_back_act = QAction(toolbar_back_icon, "")
        self.t_back_act.setEnabled(False)
        self.t_back_act.setToolTip("Back")
        self.t_back_act.triggered.connect(self.goBack)

        toolbar_forward_icon = QIcon(QPixmap("icons/forward.png"))
        self.t_frwd_act = QAction(toolbar_forward_icon, "")
        self.t_frwd_act.setEnabled(False)
        self.t_frwd_act.triggered.connect(self.goForward)

        toolbar_menu_icon = QIcon(QPixmap("icons/vert-menu.png"))
        self.toolbar_menu_act = QAction(toolbar_menu_icon, "")
        self.setupToolBarMenu()

        t_srch_i = QIcon(QPixmap("icons/search.png"))
        self.t_srch_act = QAction(t_srch_i, "")

        self.setupToolBarDirDisp()

        # Spacers
        spacer_1 = QWidget()
        spacer_1.setFixedWidth(5)
        spacer_2 = QWidget()
        spacer_2.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        spacer_3 = QWidget()
        spacer_3.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        spacer_4 = QWidget()
        spacer_4.setFixedWidth(5)
        spacer_4.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.core_toolbar.addWidget(spacer_1)
        self.core_toolbar.addAction(self.t_back_act)
        self.core_toolbar.addAction(self.t_frwd_act)
        self.core_toolbar.addWidget(spacer_2)
        self.core_toolbar.addWidget(self.pathOutput)
        self.core_toolbar.addWidget(spacer_3)
        self.core_toolbar.addAction(self.toolbar_menu_act)
        """ This removes a arrow from the QToolBar>QAction>QMenu """
        toolbar_menu_btn = self.core_toolbar.widgetForAction(self.toolbar_menu_act)
        toolbar_menu_btn.setPopupMode(
            QToolButton.ToolButtonPopupMode.InstantPopup)
        toolbar_menu_btn.setStyleSheet("::menu-indicator {image:none}")
        self.core_toolbar.addAction(self.t_srch_act)
        self.core_toolbar.addWidget(spacer_4)

        self.addToolBar(self.core_toolbar)
        self.addToolBarBreak(Qt.ToolBarArea.TopToolBarArea)

        """ This below pertains to the side bar """
        tLabelSize = QSize(100, 45)

        recent_tab_icon = QPixmap("icons/trash.png")
        self.tab_recent_l = TanzSideBarMenu("Recent", recent_tab_icon)

        starred_tab_icon = QPixmap("icons/trash.png")
        self.tab_starred_l = TanzSideBarMenu("Starred", starred_tab_icon)
        self.tab_starred_l.clicked.connect(self.setupBoomarkTab)

        home_tab_icon = QPixmap("icons/home.png")
        self.tab_home_l = TanzSideBarMenu("Home", home_tab_icon)
        self.tab_home_l.clicked.connect(self.loadHomeDir)

        desktop_tab_icon = QPixmap("icons/desktop.png")
        self.tab_desktop_l = TanzSideBarMenu("Desktop", desktop_tab_icon)
        self.tab_desktop_l.clicked.connect(self.loadDeskDir)

        document_tab_icon = QPixmap("icons/document.png")
        self.tab_document_l = TanzSideBarMenu("Documents", document_tab_icon)
        self.tab_document_l.clicked.connect(self.loadDocDir)

        download_tab_icon = QPixmap("icons/download.png")
        self.tab_download_l = TanzSideBarMenu("Downloads", download_tab_icon)
        self.tab_download_l.clicked.connect(self.loadDownDir)

        music_tab_icon = QPixmap("icons/music.png")
        self.tab_music_l = TanzSideBarMenu("Music", music_tab_icon)
        self.tab_music_l.clicked.connect(self.loadMusicDir)

        picture_tab_icon = QPixmap("icons/picture.png")
        self.tab_picture_l = TanzSideBarMenu("Pictures", picture_tab_icon)
        self.tab_picture_l.clicked.connect(self.loadPictDir)

        video_tab_icon = QPixmap("icons/video.png")
        self.tab_video_l = TanzSideBarMenu("Videos", video_tab_icon)
        self.tab_video_l.clicked.connect(self.loadVideoDir)

        trash_tab_icon = QPixmap("icons/trash.png")
        self.tab_trash_l = TanzSideBarMenu("Trash", trash_tab_icon)
        self.tab_trash_l.clicked.connect(self.loadTrashDir)

        self.core_list_view = QListView()
        self.core_sys_model = QFileSystemModel()
        self.core_sys_model.setFilter(QDir.Filter.NoDotAndDotDot | QDir.Filter.AllEntries | QDir.Filter.Hidden)
        self.core_sys_model.sort(0,Qt.SortOrder.AscendingOrder)
        self.core_sys_model.setRootPath(self.homePath)




        self.core_list_view.setModel(self.core_sys_model)
        self.core_list_view.setRootIndex(self.core_sys_model.index(self.homePath))
        self.core_list_view.clearSelection()
        self.core_list_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.core_list_view.customContextMenuRequested.connect(self.setupDirContMenu)

        self.core_list_view.setViewMode(QListView.ViewMode.IconMode)
        self.core_list_view.setIconSize(QSize(60, 60))
        self.core_list_view.setSpacing(5)
        self.core_list_view.setWordWrap(True)
        self.core_list_view.setSelectionRectVisible(True)
        self.core_list_view.setFrameStyle(QListView.Shape.NoFrame)
        self.core_list_view.setSelectionMode(QListView.SelectionMode.SingleSelection)
        self.core_list_view.setLayoutMode(QListView.LayoutMode.SinglePass)
        self.core_list_view.setResizeMode(QListView.ResizeMode.Adjust)
        self.core_list_view.setMovement(QListView.Movement.Snap)
        self.core_list_view.setGridSize(QSize(100, 100))  # Size of the box for each item
        self.core_list_view.doubleClicked.connect(self.loadDirec)

        ''' Setup the Layout  '''

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

        main_h_box = QHBoxLayout()
        main_h_box.setContentsMargins(0, 0, 0, 0)
        main_h_box.addWidget(sideBar_frame)
        main_h_box.addWidget(self.core_list_view)

        main_layout_wid = QWidget()
        main_layout_wid.setLayout(main_h_box)

        self.setCentralWidget(main_layout_wid)

    def setupActions(self):
        self.new_dir_act = QAction("New Folder")
        self.new_dir_act.triggered.connect(self.createDir)

        self.bookmark_dir_act = QAction("Bookmark")
        self.bookmark_dir_act.triggered.connect(self.addBookMData)

        self.paste_dir_act = QAction("Paste")
        self.paste_dir_act.setEnabled(False)
        self.paste_dir_act.triggered.connect(self.pasteDir)

        self.sel_all_dir_act = QAction("Select All")
        self.prop_dir_act = QAction("Properties")

        self.back_btn_act = QAction("Back")
        self.forward_btn_act = QAction("Forward")
        self.srch_btn_act = QAction("Search")

        self.copy_dir_act = QAction("Copy")
        self.copy_dir_act.triggered.connect(self.copyDir)

        self.cut_dir_act = QAction("Cut")
        self.move_dir_act = QAction("Move to...")
        self.copyT_dir_act = QAction("Copy to...")
        self.move_trash_act = QAction("Move to Trash")
        self.move_trash_act.triggered.connect(self.trashItem)
        self.rename_dir_act = QAction("Rename...")
        self.compress_dir_act = QAction("Compress")
        # Open default and open custom selection

    def setupToolBarMenu(self):
        self.toolbar_menu = QMenu()
        self.toolbar_menu.setStyleSheet("""
                                QMenu {
                                text-align: center;
                                }""")
        self.toolbar_menu.addAction(self.new_dir_act)
        self.toolbar_menu.addAction(self.bookmark_dir_act)
        self.toolbar_menu.addSeparator()
        self.toolbar_menu.addAction(self.paste_dir_act)
        self.toolbar_menu.addAction(self.sel_all_dir_act)
        self.toolbar_menu.addSeparator()
        # can add open in terminal
        self.toolbar_menu.addAction(self.prop_dir_act)

        self.toolbar_menu_act.setMenu(self.toolbar_menu)

    def setupToolBarDirDisp(self):
        self.dirPath_h_box = QHBoxLayout()
        self.dirPath_h_box.setContentsMargins(10, 0, 10, 0)
        self.dirPath_h_box.setSpacing(0)

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

    def setupDirContMenu(self, pos):
        index = self.core_list_view.indexAt(pos)

        if index.isValid():
            menu = QMenu()

            menu.addAction(self.cut_dir_act)
            menu.addAction(self.copy_dir_act)
            menu.addSeparator()
            menu.addAction(self.copyT_dir_act)
            menu.addAction(self.move_dir_act)
            menu.addSeparator()
            menu.addAction(self.move_trash_act)
            menu.addSeparator()
            menu.addAction(self.rename_dir_act)
            menu.addSeparator()
            menu.addAction(self.compress_dir_act)
            menu.addSeparator()
            menu.addAction(self.bookmark_dir_act)
            menu.addSeparator()
            menu.addAction(self.prop_dir_act)
            menu.exec(QCursor.pos())


        else:
            menu = QMenu()

            menu.addAction(self.new_dir_act)
            menu.addAction(self.bookmark_dir_act)
            menu.addSeparator()
            menu.addAction(self.paste_dir_act)
            menu.addAction(self.sel_all_dir_act)
            menu.addSeparator()
            menu.addAction(self.prop_dir_act)
            menu.exec(QCursor.pos())

    def displayDirPath(self, path):
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
            # sect_l.mousePressEvent = lambda event, sect=sect: self.loadDirectory("/".join(path.split("/")[:path.split("/").index(sect) + 1]))
            self.dirPath_h_box.addWidget(sect_l)

            if sect == path.split("/")[1:][-1]:
                pass
            else:
                idk = QLabel("/")
                self.dirPath_h_box.addWidget(idk)

    def goBack(self):
        if len(self.visited_directory_list) == 1:
            print(self.visited_directory_list[-1])
            self.t_back_act.setEnabled(False)
        else:
            print(self.visited_directory_list[-2])
            self.core_list_view.setRootIndex(self.core_sys_model.index(self.visited_directory_list[-2]))
            self.displayDirPath(self.visited_directory_list[-2])
            self.forward_directory_list.append(self.visited_directory_list.pop())
            self.t_frwd_act.setEnabled(True)

    def goForward(self):
        if len(self.forward_directory_list) == 0:
            self.t_frwd_act.setEnabled(False)
        else:
            print(self.forward_directory_list[-1])
            self.core_list_view.setRootIndex(self.core_sys_model.index(self.forward_directory_list[-1]))
            self.displayDirPath(self.forward_directory_list[-1])
            self.visited_directory_list.append(self.forward_directory_list.pop())
            self.t_back_act.setEnabled(True)

    def loadDirec(self):
        self.t_back_act.setEnabled(True)
        data = self.core_sys_model.filePath(self.core_list_view.currentIndex())
        if os.path.isdir(data):
            self.core_list_view.setRootIndex(self.core_sys_model.index(data))
            self.core_sys_model.setRootPath(data)
            self.visited_directory_list.append(data)
            self.displayDirPath(data)
        elif os.path.isfile(data):
            # self.openFile(data)
            self.visited_directory_list.append(data)

        time.sleep(0.2)

    def loadHomeDir(self):
        direc = QDir.homePath()
        self.core_list_view.setRootIndex(self.core_sys_model.index(direc))
        self.visited_directory_list.append(direc)
        self.displayDirPath(direc)

    def loadDeskDir(self):
        direc = QDir.homePath() + "/Desktop"
        self.core_list_view.setRootIndex(self.core_sys_model.index(direc))
        self.visited_directory_list.append(direc)
        self.displayDirPath(direc)

    def loadDocDir(self):
        direc = QDir.homePath() + "/Documents"
        self.core_list_view.setRootIndex(self.core_sys_model.index(direc))
        self.visited_directory_list.append(direc)
        self.displayDirPath(direc)

    def loadDownDir(self):
        direc = QDir.homePath() + "/Downloads"
        self.core_list_view.setRootIndex(self.core_sys_model.index(direc))
        self.visited_directory_list.append(direc)
        self.displayDirPath(direc)

    def loadMusicDir(self):
        direc = QDir.homePath() + "/Music"
        self.core_list_view.setRootIndex(self.core_sys_model.index(direc))
        self.visited_directory_list.append(direc)
        self.displayDirPath(direc)

    def loadPictDir(self):
        direc = QDir.homePath() + "/Pictures"
        self.core_list_view.setRootIndex(self.core_sys_model.index(direc))
        self.visited_directory_list.append(direc)
        self.displayDirPath(direc)

    def loadVideoDir(self):
        direc = QDir.homePath() + "/Videos"
        self.core_list_view.setRootIndex(self.core_sys_model.index(direc))
        self.visited_directory_list.append(direc)
        self.displayDirPath(direc)

    def loadTrashDir(self):
        direc = QDir.homePath() + "/.local/share/Trash/files"
        index = self.core_sys_model.index(direc)
        self.core_list_view.setRootIndex(index)
        self.visited_directory_list.append(direc)
        self.displayDirPath(direc)








    def copyDir(self):
        copy_direc_path = self.core_sys_model.filePath(self.core_list_view.currentIndex())
        data = QMimeData()
        data.setText(copy_direc_path)
        self.clipboard.setMimeData(data)
        self.paste_dir_act.setEnabled(True)

    def pasteDir(self):
        clip = self.clipboard
        rDir = self.core_sys_model.filePath(self.core_list_view.rootIndex())
        direcView = self.core_sys_model.filePath(self.core_list_view.rootIndex())

        print(f"Directory in view: {rDir}")

        if clip.mimeData().hasText():
            clip_data = clip.mimeData().text()
            dir_name = clip_data.split("/")[-1]
            print(f"Copied directory : {clip.mimeData().text()}")
            if QDir(clip_data).exists():
                print("Path is a Directory")
                dir_exists = True
                for entry in QDir(direcView).entryList(QDir.Filter.NoDotAndDotDot | QDir.Filter.AllEntries):
                    print(f"Directory contains: {entry}")
                    if QDir(rDir + f"/{entry}").exists():
                        print("Path is a Directory")
                        if dir_name == entry:
                            print(f"Located directory: {entry}")
                            print("Directory needs renaming")
                            self.copyWarning(dir_name)
                            break
                        else:
                            print(f"Could not locate directory: {entry}")
                            print("Okay to copy to this location")
                            # Copy to this location
                            dir_exists = False
                    elif QFile(rDir + f"/{entry}").exists():
                        print("Path is a File")
                        print(f"Did not locate: {dir_name}")
                        dir_exists = False
                if not dir_exists:
                    shutil.copytree(clip_data,rDir+f"/{dir_name}")



            if QFile(clip_data).exists():
                print("Path is a File")
                for ent in QDir(rDir).entryList(QDir.Filter.NoDotAndDotDot | QDir.Filter.Files):
                    if ent == dir_name:
                        print(f"Located file with mathing name: {ent}")
                        self.copyWarning(dir_name)

    def currentDir(self):
        return self.core_sys_model.filePath(self.core_list_view.rootIndex())

    def copyWarning(self, dir):
        message_box = QMessageBox()
        message_box.setWindowTitle("Warning")
        message_box.setText(f"Directory '{dir}' already exists in this location")
        # message_box.addButton("Overwrite", QMessageBox.ButtonRole.ActionRole)
        message_box.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
        message_box.addButton("Change name", QMessageBox.ButtonRole.AcceptRole)

        message_box.setDefaultButton(QMessageBox.StandardButton.Cancel)
        message_box.buttonClicked.connect(self.copyDirOptions)

        self.input_d = QInputDialog()
        self.input_d.setWindowTitle("Change Name")
        self.input_d.setLabelText("Enter a new Directory name:")
        self.input_d.setTextValue(dir.split("/")[-1])
        self.input_d.accepted.connect(self.updateDirectoryName)

        message_box.exec()

    def copyDirOptions(self, button):
        print(button.text())
        if button.text() == "Change name":
            self.input_d.exec()

    def updateDirectoryName(self):
        direc_name = self.input_d.textValue()
        comp = self.clipboard.text().split(os.path.sep)
        comp[-1] = direc_name
        new_path = os.path.sep.join(comp)

        if QDir(self.clipboard.text()).exists():
            print("Directory")
            shutil.copytree(self.clipboard.text(), new_path)

        elif QFile(self.clipboard.text()).exists():
            print("File")

            shutil.copy2(self.clipboard.text(), new_path)

    ''' 
        Can this be done in using QDir or any other modules
        '''

    def createDir(self):
        while True:
            dir_name, ok = QInputDialog.getText(self, "New Folder", "Name: ")
            if not ok:
                break
            dir_path = os.path.join(self.core_sys_model.rootPath(), dir_name)
            if os.path.exists(dir_path):
                QMessageBox.warning(self, "Warning",
                                    f"Directory '{dir_name}' already exists. Please enter a different name.")
            else:
                new_direc = QDir(dir_path)
                new_direc.mkdir(dir_path)
                # print(f"Directory '{dir_name}' created at '{path}'")
                break



    def addBookMData(self):
        dir_path = os.path.join(self.core_sys_model.rootPath(), self.core_list_view.currentIndex().data())
        self.bookmarked.append(dir_path)

    def removeBookMData(self):
        """ Need to figure out still """
        pass

    def setupBoomarkTab(self):
        """ Need to figure out still """
        pass

    def trashItem(self):
        curr = self.core_sys_model.filePath(self.core_list_view.currentIndex())
        print(curr)
        if QDir(curr).exists():
            print("Directory")
            QFile.moveToTrash(curr)
        elif QFile(curr).exists():
            print("File")
            QFile.moveToTrash(curr)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet(style_sheet)
    window = TanzFileManger()

    sys.exit(app.exec())
