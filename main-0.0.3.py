import os
import shutil
import sys
import time

import send2trash
from PyQt6.QtCore import QDir, QSize, pyqtSignal, Qt, QModelIndex, QFileInfo, QFile, QMimeData, \
    QSortFilterProxyModel, QItemSelectionModel
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
            QFrame{ border-radius: 5px;}
            QFrame:hover{ background-color: #ededed;}
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
        self.setLayout(h_box)

    def mousePressEvent(self, ev):
        self.clicked.emit()


class TanzFileManger(QMainWindow):
    def __init__(self):
        super().__init__()

        self.clipboard = QGuiApplication.clipboard()
        self.homePath = QDir.homePath()
        self.visited_directory_list = [self.homePath]
        self.forward_directory_list = []

        self.initUI()

    def initUI(self):
        self.setWindowTitle("Tanz")
        self.setFixedSize(800, 500)

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

        toolbar_back_icon = QIcon(QPixmap("icons/back.png"))
        self.t_back_act = QAction(toolbar_back_icon, "")
        self.t_back_act.setEnabled(False)
        self.t_back_act.setToolTip("Back")
        self.t_back_act.triggered.connect(self.goBack)

        toolbar_forward_icon = QIcon(QPixmap("icons/forward.png"))
        self.t_forward_act = QAction(toolbar_forward_icon, "")
        self.t_forward_act.setEnabled(False)
        self.t_forward_act.triggered.connect(self.goForward)

        toolbar_menu_icon = QIcon(QPixmap("icons/vert-menu.png"))
        self.toolbar_menu_act = QAction(toolbar_menu_icon, "")
        self.setupToolBarMenu()

        search_icon = QIcon(QPixmap("icons/search.png"))
        self.search_action = QAction(search_icon, "")
        self.setupToolBarDirDisp()

        # Spacers
        SPACER_WIDTH = 5
        spacer_1 = QWidget()
        spacer_1.setFixedWidth(SPACER_WIDTH)
        spacer_2 = QWidget()
        spacer_2.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        spacer_3 = QWidget()
        spacer_3.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        spacer_4 = QWidget()
        spacer_4.setFixedWidth(SPACER_WIDTH)
        spacer_4.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.core_toolbar.addWidget(spacer_1)
        self.core_toolbar.addAction(self.t_back_act)
        self.core_toolbar.addAction(self.t_forward_act)
        self.core_toolbar.addWidget(spacer_2)
        self.core_toolbar.addWidget(self.pathOutput)
        self.core_toolbar.addWidget(spacer_3)
        self.core_toolbar.addAction(self.toolbar_menu_act)

        toolbar_menu_btn = self.core_toolbar.widgetForAction(self.toolbar_menu_act)
        toolbar_menu_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        toolbar_menu_btn.setStyleSheet("::menu-indicator {image:none}")

        self.core_toolbar.addAction(self.search_action)
        self.core_toolbar.addWidget(spacer_4)

        self.addToolBar(self.core_toolbar)
        self.addToolBarBreak(Qt.ToolBarArea.TopToolBarArea)

        """ This below pertains to the side bar """
        recent_tab_icon = QPixmap("icons/trash.png")
        self.tab_recent_l = TanzSideBarMenu("Recent", recent_tab_icon)

        starred_tab_icon = QPixmap("icons/trash.png")
        self.tab_starred_l = TanzSideBarMenu("Starred", starred_tab_icon)
        # self.tab_starred_l.clicked.connect(self.setupBoomarkTab)

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
        self.core_sys_model.sort(0, Qt.SortOrder.AscendingOrder)
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
        self.core_list_view.doubleClicked.connect(self.loadDirectory)

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
        self.new_dir_act.triggered.connect(self.createNewDirectory)

        self.bookmark_dir_act = QAction("Bookmark") # No work done

        self.paste_dir_act = QAction("Paste")
        self.paste_dir_act.setEnabled(False)
        self.paste_dir_act.triggered.connect(self.paste)

        self.sel_all_dir_act = QAction("Select All")
        self.sel_all_dir_act.triggered.connect(self.selectAllData)

        self.prop_dir_act = QAction("Properties") # No work done

        self.back_btn_act = QAction("Back")
        self.back_btn_act.triggered.connect(self.goBack)

        self.forward_btn_act = QAction("Forward")
        self.forward_btn_act.triggered.connect(self.goForward)

        self.search_btn_act = QAction("Search") # No work done

        self.copy_dir_act = QAction("Copy")
        self.copy_dir_act.triggered.connect(self.copy)

        self.cut_dir_act = QAction("Cut")
        self.cut_dir_act.triggered.connect(self.cut)

        self.move_dir_act = QAction("Move to...") # No work done
        self.copyT_dir_act = QAction("Copy to...") # No work done

        self.move_trash_act = QAction("Move to Trash")
        self.move_trash_act.triggered.connect(self.trashItem)

        self.rename_dir_act = QAction("Rename...")
        self.rename_dir_act.triggered.connect(self.renameDir)

        self.compress_dir_act = QAction("Compress")
        self.compress_dir_act.triggered.connect(self.compressDir)

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

    def loadDirectory(self):
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

    def goBack(self):
        if len(self.visited_directory_list) == 1:
            print(self.visited_directory_list[-1])
            self.t_back_act.setEnabled(False)
        else:
            print(self.visited_directory_list[-2])
            self.core_list_view.setRootIndex(self.core_sys_model.index(self.visited_directory_list[-2]))
            self.displayDirPath(self.visited_directory_list[-2])
            self.forward_directory_list.append(self.visited_directory_list.pop())
            self.t_forward_act.setEnabled(True)

    def goForward(self):
        if len(self.forward_directory_list) == 0:
            self.t_forward_act.setEnabled(False)
        else:
            print(self.forward_directory_list[-1])
            self.core_list_view.setRootIndex(self.core_sys_model.index(self.forward_directory_list[-1]))
            self.displayDirPath(self.forward_directory_list[-1])
            self.visited_directory_list.append(self.forward_directory_list.pop())
            self.t_back_act.setEnabled(True)

    def loadHomeDir(self):
        directory = QDir.homePath()
        self.core_list_view.setRootIndex(self.core_sys_model.index(directory))
        self.visited_directory_list.append(directory)
        self.displayDirPath(directory)

    def loadDeskDir(self):
        directory = QDir.homePath() + "/Desktop"
        self.core_list_view.setRootIndex(self.core_sys_model.index(directory))
        self.visited_directory_list.append(directory)
        self.displayDirPath(directory)

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

    def trashItem(self):
        curr_item = self.core_sys_model.filePath(self.core_list_view.currentIndex())
        if QDir(curr_item).exists():
            QFile.moveToTrash(curr_item)
        elif QFile(curr_item).exists():
            QFile.moveToTrash(curr_item)

    def createNewDirectory(self):
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
                break

    def cut(self):
        path = self.core_sys_model.filePath(self.core_list_view.currentIndex())

        self.clipboard.clear()
        data = QMimeData()
        data.setText(path)
        self.clipboard.setText(path)

        self.paste_dir_act.setEnabled(True)
        self.cut_path = path

    def copy(self):
        path = self.core_sys_model.filePath(self.core_list_view.currentIndex())

        self.clipboard.clear()
        data = QMimeData()
        data.setText(path)
        self.clipboard.setText(path)

        self.paste_dir_act.setEnabled(True)

    def paste(self):
        data_path = self.core_sys_model.filePath(self.core_list_view.rootIndex())

        clip_data = self.clipboard.mimeData().text()
        data_name = os.path.basename(clip_data)

        if self.cut_path:
            self.moveFile(self.cut_path, data_path, data_name)
            self.cut_path = None
        elif os.path.isdir(clip_data):
            self.copyDir(clip_data, data_path, data_name)
        else:
            self.copyFile(clip_data, data_path, data_name)

    def copyFile(self, src, dst_dir, dst_name):
        dst_path = os.path.join(dst_dir, dst_name)
        if os.path.exists(dst_path):
            dst_name = self.renameFile(dst_dir, dst_name)
            dst_path = os.path.join(dst_dir, dst_name)
        try:
            shutil.copy2(src, dst_path)
        except Exception as e:
            QMessageBox.critical(None, "Error", f"Failed to copy file: {e}")

    def copyDir(self, src, dst_dir, dst_name):
        dst_path = os.path.join(dst_dir, dst_name)
        if os.path.exists(dst_path):
            dst_name = self.cpRenameDir(dst_dir, dst_name)
            dst_path = os.path.join(dst_dir, dst_name)
        try:
            shutil.copytree(src, dst_path)
        except Exception as e:
            QMessageBox.critical(None, "Error", f"Failed to copy directory: {e}")

    def moveFile(self, src, dst_dir, dst_name):
        dst_path = os.path.join(dst_dir, dst_name)
        if os.path.exists(dst_path):
            dst_name = self.renameFile(dst_dir, dst_name)
            dst_path = os.path.join(dst_dir, dst_name)
        try:
            shutil.move(src, dst_path)
        except Exception as e:
            QMessageBox.critical(None, "Error", f"Failed to move file: {e}")
    def renameFile(self, dst_dir, dst_name):
        name, ext = os.path.splitext(dst_name)
        i = 1
        while True:
            new_name = f"{name} (copy {i}){ext}"
            new_path = os.path.join(dst_dir, new_name)
            if not os.path.exists(new_path):
                return new_name
            i += 1

    def cpRenameDir(self, dst_dir, dst_name):
        name = dst_name
        i = 1
        while True:
            new_name = f"{name} (copy {i})"
            new_path = os.path.join(dst_dir, new_name)
            if not os.path.exists(new_path):
                return new_name
            i += 1


    def pasteDir(self, src, dst_dir, dst_name):
        dst_path = os.path.join(dst_dir, dst_name)
        if os.path.exists(dst_path):
            dst_name = self.cpRenameDir(dst_dir, dst_name)
            dst_path = os.path.join(dst_dir, dst_name)
        try:
            shutil.copytree(src, dst_path)
        except FileExistsError:
            self.pasteDir(src, dst_dir, dst_name)
        except Exception as e:
            QMessageBox.critical(None, "Error", f"Failed to paste directory: {e}")

    def pasteFile(self, src, dst_dir, dst_name):
        dst_path = os.path.join(dst_dir, dst_name)
        if os.path.exists(dst_path):
            dst_name = self.renameFile(dst_dir, dst_name)
            dst_path = os.path.join(dst_dir, dst_name)
        try:
            shutil.copy2(src, dst_path)
        except FileExistsError:
            self.pasteFile(src, dst_dir, dst_name)
        except Exception as e:
            QMessageBox.critical(None, "Error", f"Failed to paste file: {e}")


    def copyToDir(self):
        pass

    def moveToDir(self):
        pass

    def renameDir(self):
        # Get the path of the directory to rename
        index = self.core_list_view.currentIndex()
        dir_path = self.core_sys_model.filePath(index)

        # Get the new name for the directory
        new_name, ok = QInputDialog.getText(self, "Rename Directory", "Enter a new name:",
                                            text=self.core_sys_model.fileName(index))
        if ok:
            # Rename the directory
            new_path = os.path.join(os.path.dirname(dir_path), new_name)
            os.rename(dir_path, new_path)

            # Update the view to show the renamed directory
            self.core_list_view.setRootIndex(self.core_sys_model.index(dir_path).parent())
        elif not ok:
            pass

    def compressDir(self):
        # Get the path of the directory to compress
        dir_path = self.core_sys_model.filePath(self.core_list_view.currentIndex())

        # Compress the directory
        shutil.make_archive(dir_path, 'zip', dir_path)

        # Update the view to show the compressed file
        self.core_list_view.setRootIndex(self.core_sys_model.index(dir_path).parent())

    def bookmarkDir(self):
        pass

    def selectAllData(self):
        curr = self.core_sys_model.filePath(self.core_list_view.rootIndex())
        direc = QDir(curr)

        for i in range(direc.count()):
            i_name = direc[i]
            i_path = os.path.join(curr,i_name)
            i_info = QFileInfo(i_path)
            item = self.core_list_view.model().index(i_path)
            self.core_list_view.selectionModel().select(item, QItemSelectionModel.SelectionFlag.Select)


    def showProperties(self):
        pass


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet(style_sheet)
    window = TanzFileManger()
    sys.exit(app.exec())
