import os
import shutil
import sys
import time

from PyQt6.QtCore import QDir, QSize, pyqtSignal, Qt, QFileInfo, QFile, QMimeData, \
    QItemSelectionModel, QPoint, QUrl, QStorageInfo
from PyQt6.QtGui import QFileSystemModel, QIcon, QPixmap, QAction, QCursor, QGuiApplication, QFontDatabase, \
    QFont, QFontMetrics, QDesktopServices, QStandardItemModel, QStandardItem
from PyQt6.QtWidgets import QMainWindow, QApplication, QListView, QHBoxLayout, QWidget, QLabel, QVBoxLayout, QFrame, \
    QToolBar, QScrollArea, QSizePolicy, QMenu, QLineEdit, QInputDialog, QMessageBox, QPushButton, QDialog, \
    QAbstractItemView, QDialogButtonBox, QGridLayout

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


class AddressBarLabel(QLabel):
    clicked = pyqtSignal(str)

    def __init__(self, txt, font):
        super().__init__(txt)
        self.fontMetrics = QFontMetrics(font)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFont(font)
        self.setStyleSheet("""
            QLabel{ border-radius: 5px; }
            QLabel:hover{ background-color: #ededed; }
        """)
        self.setFixedWidth(self.fontMetrics.horizontalAdvance(txt) + 15)
        self.setFixedHeight(25)

    def mousePressEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.text())


class PropertiesWindow(QDialog):
    def __init__(self, path):
        super().__init__()
        self.path = path
        self.labels = [
            "Name",
            "Type",
            "Contents",
            "Parent folder",
            "Modified",
            "Created On",
            "Free Space",
        ]
        self.initializeUI()

    def initializeUI(self):
        self.setWindowTitle("Properties")
        self.setFixedSize(400, 450)
        self.setupPropertiesWindow()

    def setupPropertiesWindow(self):
        # Toolbar
        # Tabs
        # Layout
        self.prop_layout_core = QVBoxLayout()
        self.prop_upper_layout = QHBoxLayout()
        self.prop_upper_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.prop_bottom_layout = QGridLayout()
        self.prop_bottom_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.prop_icon_btn = QPushButton()
        self.itemCheck()
        self.prop_icon_btn.setFixedSize(85, 85)
        self.prop_upper_layout.addWidget(self.prop_icon_btn)

        for i, label in enumerate(self.labels):
            prop_label = QLabel(label)
            prop_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            prop_label.setFrameShape(QFrame.Shape.Box)
            prop_label.setStyleSheet("padding: 0,0,10px,0;")
            prop_label.setFixedSize(125, 35)
            self.prop_bottom_layout.addWidget(prop_label, i, 0)

        self.prop_name_le = QLineEdit()
        self.prop_name_le.setFixedSize(250, 25)
        file_info = QFileInfo(self.path)

        if QDir(self.path).exists():
            file_type = "Folder"
        elif QFile(self.path).exists():
            file_ext = file_info.suffix()
            file_type_map = {
                "pdf": "PDF document",
                "txt": "Text document",
                "docx": "Microsoft Word document",
            }
            file_type = file_type_map.get(file_ext, "Unknown file type")
        self.prop_type_data = QLabel(file_type)

        self.prop_type_data.setFixedSize(250, 35)
        self.prop_type_data.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.prop_contents_data = QLabel()
        self.direcContents()
        self.prop_contents_data.setText(f"{self.num_files} items, totalling {self.total_size_str}")
        self.prop_contents_data.setFixedSize(250, 35)
        self.prop_contents_data.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.prop_parent_data = QLabel(file_info.dir().path())
        self.prop_parent_data.setFixedSize(250, 35)
        self.prop_parent_data.setAlignment(Qt.AlignmentFlag.AlignCenter)

        modified_on = file_info.lastModified().toString("yyyy-MM-dd HH:mm:ss")
        self.prop_modified_data = QLabel(modified_on)
        self.prop_modified_data.setFixedSize(250, 35)
        self.prop_modified_data.setAlignment(Qt.AlignmentFlag.AlignCenter)

        created_on = file_info.birthTime().toString("yyyy-MM-dd HH:mm:ss")
        self.prop_created_data = QLabel(created_on)
        self.prop_created_data.setFixedSize(250, 35)
        self.prop_created_data.setAlignment(Qt.AlignmentFlag.AlignCenter)

        storage = QStorageInfo.root()
        data = storage.bytesAvailable() / (1000 * 1000 * 1000)
        free_space = "{:.5f}".format(data)
        self.prop_free_data = QLabel(free_space[:5] + " GB")
        self.prop_free_data.setFixedSize(250, 35)
        self.prop_free_data.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.prop_bottom_layout.addWidget(self.prop_name_le, 0, 1)
        self.prop_bottom_layout.addWidget(self.prop_type_data, 1, 1)
        self.prop_bottom_layout.addWidget(self.prop_contents_data, 2, 1)
        self.prop_bottom_layout.addWidget(self.prop_parent_data, 3, 1)
        self.prop_bottom_layout.addWidget(self.prop_modified_data, 4, 1)
        self.prop_bottom_layout.addWidget(self.prop_created_data, 5, 1)
        self.prop_bottom_layout.addWidget(self.prop_free_data, 6, 1)

        self.prop_layout_core.addLayout(self.prop_upper_layout)
        self.prop_layout_core.addLayout(self.prop_bottom_layout)
        self.setLayout(self.prop_layout_core)
        self.prop_name_le.setText(file_info.fileName())

    def itemCheck(self):
        if QDir(self.path).exists():
            pixmap = QPixmap("icons/folder.png")
            prop_icon = QIcon(pixmap)
            self.prop_icon_btn.setIconSize(QSize(75, 75))
            self.prop_icon_btn.setIcon(prop_icon)
        elif QFile(self.path).exists():
            pixmap = QPixmap("icons/file.png")
            prop_icon = QIcon(pixmap)
            self.prop_icon_btn.setIconSize(QSize(75, 75))
            self.prop_icon_btn.setIcon(prop_icon)

    def direcContents(self):
        # Create a QDir object for the directory
        direc = QDir(self.path)

        # Get the list of items in the directory
        items = direc.entryInfoList()

        # Initialize counters for the number of files and the total size
        self.num_files = 0
        total_size = 0

        # Loop over the items in the directory
        for item in items:
            # Check if the item is a file
            if item.isFile():
                # Increment the file counter
                self.num_files += 1
                # Add the size of the file to the total size
                total_size += item.size()

        # Convert the total size to MB, KB, or GB
        if total_size >= 1024 * 1024 * 1024:
            self.total_size_str = "{:.2f} GB".format(total_size / (1024 * 1024 * 1024))
        elif total_size >= 1024 * 1024:
            self.total_size_str = "{:.2f} MB".format(total_size / (1024 * 1024))
        elif total_size >= 1024:
            self.total_size_str = "{:.2f} KB".format(total_size / 1024)
        else:
            self.total_size_str = "{} bytes".format(total_size)

    def closeEvent(self, event):
        new_name = self.prop_name_le.text()
        if new_name != QFileInfo(self.path).fileName():
            new_path = QFileInfo(self.path).dir().filePath(new_name)
            if QFile(self.path).exists():
                QFile(self.path).rename(new_path)
            elif QDir(self.path).exists():
                QDir(self.path).rename(self.path, new_path)
        event.accept()


class SearchWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Search")
        self.resize(600, 400)

        # Create widgets
        self.search_edit = QLineEdit()
        self.search_button = QPushButton("Search")
        self.search_results_view = QListView()
        self.search_results_model = QStandardItemModel()
        self.search_results_view.setModel(self.search_results_model)
        self.search_results_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.search_results_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.search_results_view.setViewMode(QListView.ViewMode.IconMode)
        self.search_results_view.setIconSize(QSize(60, 60))
        self.search_results_view.setSpacing(5)
        self.search_results_view.setWordWrap(True)
        self.search_results_view.setSelectionRectVisible(True)
        self.search_results_view.setFrameStyle(QListView.Shape.Box)
        self.search_results_view.setSelectionMode(QListView.SelectionMode.SingleSelection)
        self.search_results_view.setLayoutMode(QListView.LayoutMode.SinglePass)
        self.search_results_view.setResizeMode(QListView.ResizeMode.Adjust)
        self.search_results_view.setMovement(QListView.Movement.Snap)
        self.search_results_view.setGridSize(QSize(100, 100))
        self.search_results_view.doubleClicked.connect(self.openSelectedFile)

        self.cancel_button = QPushButton("Cancel")
        self.open_button = QPushButton("Open")
        self.button_box = QDialogButtonBox(Qt.Orientation.Horizontal)
        self.button_box.addButton(self.cancel_button, QDialogButtonBox.ButtonRole.RejectRole)
        self.button_box.addButton(self.open_button, QDialogButtonBox.ButtonRole.AcceptRole)

        # Create layout
        layout = QVBoxLayout()
        layout.addWidget(self.search_edit)
        layout.addWidget(self.search_button)
        layout.addWidget(self.search_results_view)
        layout.addWidget(self.button_box)
        self.setLayout(layout)

        # Connect signals and slots
        self.search_button.clicked.connect(self.searchFileSystem)
        self.cancel_button.clicked.connect(self.reject)
        self.open_button.clicked.connect(self.openSelectedFile)

    def searchFileSystem(self):
        query = self.search_edit.text()
        if query:
            self.search_results_model.clear()
            for root, dirs, files in os.walk("/"):
                for name in dirs + files:
                    if query.lower() in name.lower():
                        item = QStandardItem(name)
                        path = os.path.join(root, name)
                        if os.path.isdir(path):
                            item.setIcon(QIcon("icons/folder.png"))
                        else:
                            item.setIcon(QIcon("icons/file.png"))
                        item.setData(path, Qt.ItemDataRole.UserRole)
                        self.search_results_model.appendRow(item)
            if self.search_results_model.rowCount() == 0:
                item = QStandardItem("No results found.")
                self.search_results_model.appendRow(item)

    def openSelectedFile(self):
        index = self.search_results_view.currentIndex()
        if index.isValid():
            path = index.data(Qt.ItemDataRole.UserRole)
            if os.path.isfile(path):
                QDesktopServices.openUrl(QUrl.fromLocalFile(path))
            elif os.path.isdir(path):
                self.parent().loadDirectory(path)
            self.accept()


class AddressBar(QFrame):
    directoryClicked = pyqtSignal(str)  # New signal

    def __init__(self, menu, menu_btn):
        super().__init__()
        self.actions()
        self.menu_btn = menu_btn

        # Set the font for the address bar
        font_family = QFontDatabase.systemFont(QFontDatabase.SystemFont.GeneralFont).family()
        self.font = QFont(font_family, 11)

        self.fontMetrics = QFontMetrics(self.font)

        # Set the size and margins for the address bar
        self.setFixedSize(QSize(600, 35))
        self.setContentsMargins(0, 0, 0, 0)
        self.setObjectName("main_frame")
        self.setStyleSheet("""
            QFrame#main_frame { border: 1px solid black;
                                border-radius: 2px;}
        """)

        # Create the layout and subframe for the address bar
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.sub_frame = QFrame()

        # Create the sub-layout for the address bar
        self.sub_layout = QHBoxLayout()
        self.sub_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.sub_layout.setContentsMargins(0, 0, 0, 0)

        # Set the sub-layout for the subframe
        self.sub_frame.setLayout(self.sub_layout)
        self.layout.addWidget(self.sub_frame)
        self.setLayout(self.layout)

        # Store the menu object as an instance variable
        self.menu = menu

    def stripAddressBar(self):
        # Remove all widgets and spacer items from the sub-layout
        for i in reversed(range(self.sub_layout.count())):
            item = self.sub_layout.itemAt(i)
            if item.widget():
                self.sub_layout.removeWidget(item.widget())
            else:
                pass

    def updateAddressBar(self, path):
        # Remove any existing content from the address bar
        self.stripAddressBar()

        if path.startswith("/"):
            path = path[1:]
        # Split the path into subdirectories
        self.sub_path = path.split("/")

        total_width = 0
        self.sub_dirs = []

        # Add a QLabel widget for each subdirectory and a separator after each one
        for i1, sub_dir in enumerate(self.sub_path):
            sub_dir_l = AddressBarLabel(sub_dir, self.font)
            sub_dir_width = self.fontMetrics.horizontalAdvance(sub_dir) + 15
            total_width += sub_dir_width + 8  # Eight compensates for the /

            if total_width > 600:
                # Remove the first subdirectory and separator until the total width is less than or equal to 600
                while total_width > 600 and self.sub_layout.count() > 1:
                    item = self.sub_layout.takeAt(0)
                    widget = item.widget()
                    if widget is not None:
                        widget.deleteLater()
                    else:
                        spacer = item.spacerItem()
                        if spacer is not None:
                            spacer.deleteLater()
                    self.sub_layout.takeAt(
                        0).widget().deleteLater()  # This deletes the "/" form the beginning of the path
                    total_width -= sub_dir_width + 10

            self.sub_dirs.append(sub_dir_l)
            sub_dir_l.clicked.connect(self.onSubDirectoryClicked)  # Connect the label's clicked signal
            self.sub_layout.addWidget(sub_dir_l)

            if i1 < len(self.sub_path) - 1:
                sep = QLabel("/")
                sep.setFixedWidth(self.fontMetrics.horizontalAdvance("/"))
                # self.sub_dirs.append(sep)
                self.sub_layout.addWidget(sep)

            # Enable context menus for each QLabel that is not a separator
            sub_dir_l.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            sub_dir_l.customContextMenuRequested.connect(lambda pos, i=i1: self.showContextMenu(pos, i))

        # Set the font weight of the last subdirectory to bold and adjust its width to fit the text
        self.sub_dirs[-1].setStyleSheet("font-weight: bold")
        w = self.fontMetrics.horizontalAdvance(
            self.sub_dirs[-1].text()) + 10  # +10 adds 10 pixels to the bolded directory
        self.sub_dirs[-1].setFixedWidth(w)

        # Set the spacing and width for the sub-layout and subframe
        self.sub_layout.setSpacing(0)
        self.sub_frame.setFixedWidth(total_width)

    def onSubDirectoryClicked(self, index):
        # Emit the directoryClicked signal with the directory name and path at the clicked index
        clicked_directory_path = None
        for i, directory in enumerate(self.sub_path):
            if directory.endswith(index):
                clicked_directory_path = '/'.join(self.sub_path[:i + 1])
                break
        if clicked_directory_path is not None:
            self.directoryClicked.emit("/" + clicked_directory_path)

    def showContextMenu(self, pos, index):
        menu = self.menu
        menu.addAction(self.new_folder_act)
        menu.addAction(self.open_new_tab_act)
        menu.addAction(self.properties_act)
        if index == len(self.sub_dirs) - 1:
            # If the last directory in the path --> display on QPushButton
            # Calculate the position of the context menu based on the position of the QPushButton
            btn_pos = self.menu_btn.mapToGlobal(QPoint(0, 0))
            btn_width = self.menu_btn.width()
            btn_height = self.menu_btn.height()
            menu_width = menu.sizeHint().width()
            menu_height = menu.sizeHint().height()
            x = int(btn_pos.x() + (btn_width / 2) - (menu_width / 2))
            y = int(btn_pos.y() + btn_height)
            action = menu.exec(QPoint(x, y))
        else:
            # else display on the QLabel
            # Calculates the position of the context menu based on the position of the QLabel
            label_pos = self.sub_dirs[index].mapToGlobal(QPoint(0, 0))
            label_width = self.sub_dirs[index].width()
            label_height = self.sub_dirs[index].height()
            menu_width = menu.sizeHint().width()
            menu_height = menu.sizeHint().height()
            x = int(label_pos.x() + (label_width / 2) - (menu_width / 2))
            y = int(label_pos.y() + label_height)
            action = menu.exec(QPoint(x, y))
        # Handle the selected action (currently, just print)
        if action == self.new_folder_act:
            print("New Folder selected")
        elif action == self.open_new_tab_act:
            print("Open in New Tab selected")
        elif action == self.properties_act:
            print("Properties selected")

    def actions(self):
        # Create Actions
        self.new_folder_act = QAction("New Folder")
        self.open_new_tab_act = QAction("Open in New Tab")
        self.properties_act = QAction("Properties")


class TanzFileManger(QMainWindow):
    def __init__(self):
        super().__init__()
        self.cut_path = None

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

        self.adr_bar.directoryClicked.connect(self.updateFileView)

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
        self.toolbar_back_btn = QPushButton(toolbar_back_icon, "")
        self.toolbar_back_btn.setIconSize(QSize(25, 25))
        self.toolbar_back_btn.setFixedSize(30, 30)
        self.toolbar_back_btn.setStyleSheet("QPushButton {text-align:center;}")
        self.toolbar_back_btn.setEnabled(False)
        self.toolbar_back_btn.clicked.connect(self.goBack)

        toolbar_forward_icon = QIcon(QPixmap("icons/forward.png"))
        self.toolbar_forward_btn = QPushButton(toolbar_forward_icon, "")
        self.toolbar_forward_btn.setIconSize(QSize(25, 25))
        self.toolbar_forward_btn.setFixedSize(30, 30)
        self.toolbar_forward_btn.setStyleSheet("QPushButton {text-align:center;}")
        self.toolbar_forward_btn.setEnabled(False)
        self.toolbar_forward_btn.clicked.connect(self.goForward)

        toolbar_menu_icon = QIcon(QPixmap("icons/vert-menu.png"))
        self.toolbar_menu_btn = QPushButton(toolbar_menu_icon, "")
        self.toolbar_menu_btn.setIconSize(QSize(25, 25))
        self.toolbar_menu_btn.setFixedSize(30, 30)
        self.toolbar_menu_btn.setStyleSheet("""
                QPushButton {text-align:center;}
                QPushButton::menu-indicator {image:none}
        """)

        search_icon = QIcon(QPixmap("icons/search.png"))
        self.toolbar_search_btn = QPushButton(search_icon, "")
        self.toolbar_search_btn.setIconSize(QSize(25, 25))
        self.toolbar_search_btn.setFixedSize(30, 30)
        self.toolbar_search_btn.setStyleSheet("QPushButton {text-align:center;}")
        self.toolbar_search_btn.clicked.connect(self.showSearchWindow)

        # Create a QMenu object for the address bar context menu
        address_bar_menu = QMenu()

        # Pass the menu object to the AddressBar constructor
        self.adr_bar = AddressBar(address_bar_menu, self.toolbar_menu_btn)
        # self.core_toolbar.addWidget(self.adr_bar)

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
        self.core_toolbar.addWidget(self.toolbar_back_btn)
        self.core_toolbar.addWidget(self.toolbar_forward_btn)
        self.core_toolbar.addWidget(spacer_2)
        self.core_toolbar.addWidget(self.adr_bar)
        self.core_toolbar.addWidget(spacer_3)
        self.core_toolbar.addWidget(self.toolbar_menu_btn)
        self.core_toolbar.addWidget(self.toolbar_search_btn)
        self.core_toolbar.addWidget(spacer_4)

        self.addToolBar(self.core_toolbar)
        self.addToolBarBreak(Qt.ToolBarArea.TopToolBarArea)
        self.setupToolBarMenu()  # set up the menu associated with the toolbar

        """ This below pertains to the side bar """
        recent_tab_icon = QPixmap("icons/recent.png")
        self.tab_recent_l = TanzSideBarMenu("Recent", recent_tab_icon)

        starred_tab_icon = QPixmap("icons/bookmark.png")
        self.tab_starred_l = TanzSideBarMenu("Starred", starred_tab_icon)

        home_tab_icon = QPixmap("icons/home.png")
        self.tab_home_l = TanzSideBarMenu("Home", home_tab_icon)
        self.tab_home_l.clicked.connect(self.loadHomeDir)

        desktop_tab_icon = QPixmap("icons/desktop.png")
        self.tab_desktop_l = TanzSideBarMenu("Desktop", desktop_tab_icon)
        self.tab_desktop_l.clicked.connect(self.loadDeskDir)

        document_tab_icon = QPixmap("icons/documents.png")
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

        self.bookmark_dir_act = QAction("Bookmark")  # No work done

        self.paste_dir_act = QAction("Paste")
        self.paste_dir_act.setEnabled(False)
        self.paste_dir_act.triggered.connect(self.paste)

        self.sel_all_dir_act = QAction("Select All")
        self.sel_all_dir_act.triggered.connect(self.selectAllData)

        self.prop_dir_act = QAction("Properties")  # No work done
        self.prop_dir_act.triggered.connect(self.showProperties)

        self.copy_dir_act = QAction("Copy")
        self.copy_dir_act.triggered.connect(self.copy)

        self.cut_dir_act = QAction("Cut")
        self.cut_dir_act.triggered.connect(self.cut)

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

        self.toolbar_menu_btn.setMenu(self.toolbar_menu)

    def setupDirContMenu(self, pos):
        index = self.core_list_view.indexAt(pos)

        if index.isValid():
            menu = QMenu()

            menu.addAction(self.cut_dir_act)
            menu.addAction(self.copy_dir_act)
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

    def setupToolBarDirDisp(self):
        self.scroll_addr_bar = QScrollArea()
        self.addrBar_h_box = QHBoxLayout()
        self.addrBar_h_box.setContentsMargins(0, 0, 0, 0)
        self.scroll_addr_bar.setFixedSize(600, 30)

        self.scroll_addr_bar.setLayout(self.addrBar_h_box)

    def displayDirPath(self):
        curr_path = self.core_sys_model.filePath(self.core_list_view.rootIndex())
        spl_curr_path = curr_path.split("/")[1:]
        for i in reversed(range(self.addrBar_h_box.count())):
            item = self.addrBar_h_box.itemAt(i)
            if item.widget():
                self.addrBar_h_box.removeWidget(item.widget())
                # item.widget().deleteLater()
            elif item.spacerItem():
                self.addrBar_h_box.removeItem(item.spacerItem())
            else:
                pass

        for sub_dir in spl_curr_path:
            sub_dir_l = QLabel(sub_dir)
            self.addrBar_h_box.addWidget(sub_dir_l)

            if sub_dir == spl_curr_path[-1]:
                pass
            else:
                sep = QLabel("/")
                self.addrBar_h_box.addWidget(sep)

    def loadDirectory(self):

        curr_index = self.core_list_view.currentIndex()
        curr_direc = self.core_sys_model.filePath(curr_index)

        if QDir(curr_direc).exists():
            self.core_list_view.setRootIndex(self.core_sys_model.index(curr_direc))
            self.core_sys_model.setRootPath(curr_direc)
            self.visited_directory_list.append(curr_direc)
            self.adr_bar.updateAddressBar(curr_direc)
        elif QFile(curr_direc).exists():
            # self.openFile(data)
            self.visited_directory_list.append(curr_direc)
        self.toolbar_back_btn.setEnabled(True)
        time.sleep(0.2)

    def goBack(self):
        if len(self.visited_directory_list) == 1:
            self.toolbar_back_btn.setEnabled(False)
        else:
            prev_directory = self.visited_directory_list.pop()
            self.forward_directory_list.append(prev_directory)
            self.core_list_view.setRootIndex(self.core_sys_model.index(self.visited_directory_list[-1]))
            self.core_sys_model.setRootPath(self.visited_directory_list[-1])
            self.adr_bar.updateAddressBar(self.visited_directory_list[-1])
            self.toolbar_forward_btn.setEnabled(True)
            self.toolbar_back_btn.setEnabled(len(self.visited_directory_list) > 1)

    def goForward(self):
        if len(self.forward_directory_list) == 0:
            self.toolbar_forward_btn.setEnabled(False)
        else:
            next_directory = self.forward_directory_list.pop()
            self.visited_directory_list.append(next_directory)
            self.core_list_view.setRootIndex(self.core_sys_model.index(next_directory))
            self.core_sys_model.setRootPath(next_directory)
            self.adr_bar.updateAddressBar(next_directory)
            self.toolbar_back_btn.setEnabled(True)
            self.toolbar_forward_btn.setEnabled(len(self.forward_directory_list) > 0)

    def loadHomeDir(self):
        try:
            directory = QDir.homePath()
            self.core_list_view.setRootIndex(self.core_sys_model.index(directory))
            self.visited_directory_list.append(directory)
            self.adr_bar.updateAddressBar(directory)
            self.toolbar_back_btn.setEnabled(True)
        except Exception as e:
            QMessageBox.critical(None, "Error", f"Failed to load home directory: {e}")

    def loadDeskDir(self):
        try:
            directory = QDir.homePath() + "/Desktop"
            self.core_list_view.setRootIndex(self.core_sys_model.index(directory))
            self.visited_directory_list.append(directory)
            self.adr_bar.updateAddressBar(directory)
            self.toolbar_back_btn.setEnabled(True)
        except Exception as e:
            QMessageBox.critical(None, "Error", f"Failed to load home directory: {e}")

    def loadDocDir(self):
        try:
            directory = QDir.homePath() + "/Documents"
            self.core_list_view.setRootIndex(self.core_sys_model.index(directory))
            self.visited_directory_list.append(directory)
            self.adr_bar.updateAddressBar(directory)
            self.toolbar_back_btn.setEnabled(True)
        except Exception as e:
            QMessageBox.critical(None, "Error", f"Failed to load home directory: {e}")

    def loadDownDir(self):
        try:
            directory = QDir.homePath() + "/Downloads"
            self.core_list_view.setRootIndex(self.core_sys_model.index(directory))
            self.visited_directory_list.append(directory)
            self.adr_bar.updateAddressBar(directory)
            self.toolbar_back_btn.setEnabled(True)
        except Exception as e:
            QMessageBox.critical(None, "Error", f"Failed to load home directory: {e}")

    def loadMusicDir(self):
        try:
            directory = QDir.homePath() + "/Music"
            self.core_list_view.setRootIndex(self.core_sys_model.index(directory))
            self.visited_directory_list.append(directory)
            self.adr_bar.updateAddressBar(directory)
            self.toolbar_back_btn.setEnabled(True)
        except Exception as e:
            QMessageBox.critical(None, "Error", f"Failed to load home directory: {e}")

    def loadPictDir(self):
        try:
            directory = QDir.homePath() + "/Pictures"
            self.core_list_view.setRootIndex(self.core_sys_model.index(directory))
            self.visited_directory_list.append(directory)
            self.adr_bar.updateAddressBar(directory)
            self.toolbar_back_btn.setEnabled(True)
        except Exception as e:
            QMessageBox.critical(None, "Error", f"Failed to load home directory: {e}")

    def loadVideoDir(self):
        try:
            directory = QDir.homePath() + "/Videos"
            self.core_list_view.setRootIndex(self.core_sys_model.index(directory))
            self.visited_directory_list.append(directory)
            self.adr_bar.updateAddressBar(directory)
            self.toolbar_back_btn.setEnabled(True)
        except Exception as e:
            QMessageBox.critical(None, "Error", f"Failed to load home directory: {e}")

    def loadTrashDir(self):
        try:
            directory = QDir.homePath() + "/.local/share/Trash/files"
            index = self.core_sys_model.index(directory)
            self.core_list_view.setRootIndex(index)
            self.visited_directory_list.append(directory)
            self.adr_bar.updateAddressBar(directory)
            self.toolbar_back_btn.setEnabled(True)
        except Exception as e:
            QMessageBox.critical(None, "Error", f"Failed to load home directory: {e}")

    def updateFileView(self, directory_path):
        index = self.core_sys_model.index(directory_path)
        self.adr_bar.updateAddressBar(directory_path)
        self.core_list_view.setRootIndex(index)
        self.core_sys_model.setRootPath(directory_path)
        self.visited_directory_list.append(directory_path)

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
            # self.copyDirs(clip_data, data_path)
            self.copyFileDir(data_path)
        else:
            # self.copyFiles(clip_data, data_path)
            self.copyFileDir(data_path)

    def moveFile(self, src, dst_dir, dst_name):
        dst_path = os.path.join(dst_dir, dst_name)
        if os.path.exists(dst_path):
            dst_name = self.renameFile(dst_dir, dst_name)
            dst_path = os.path.join(dst_dir, dst_name)
        try:
            shutil.move(src, dst_path)
        except Exception as e:
            QMessageBox.critical(None, "Error", f"Failed to move file: {e}")

    def copyFileDir(self, dst_dir):
        for path in self.file_paths:
            if QDir(path).exists():
                dst_name = self.cpRenameDir(dst_dir, os.path.basename(path))
                dst_path = os.path.join(dst_dir, dst_name)
                try:
                    shutil.copytree(path, dst_path)
                except FileExistsError:
                    self.pasteDir(path, dst_dir, os.path.basename(path))
                except Exception as e:
                    QMessageBox.critical(None, "Error", f"Failed to copy directory: {e}")

            elif QFile(path).exists():
                dst_name = self.renameFile(dst_dir, os.path.basename(path))
                dst_path = os.path.join(dst_dir, dst_name)
                try:
                    shutil.copy2(path, dst_path)
                except Exception as e:
                    QMessageBox.critical(None, "Error", f"Failed to copy file: {e}")

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

    def showSearchWindow(self):
        search_window = SearchWindow(self)
        search_window.exec()

    def selectAllData(self):
        curr = self.core_sys_model.filePath(self.core_list_view.rootIndex())
        direc = QDir(curr)
        direc.setFilter(QDir.Filter.NoDotAndDotDot | QDir.Filter.Hidden | QDir.Filter.AllEntries)
        self.file_paths = []  # create an empty list to store file paths
        for i in range(direc.count()):
            i_name = direc[i]
            i_path = os.path.join(curr, i_name)
            # i_info = QFileInfo(i_path)
            item = self.core_list_view.model().index(i_path)
            self.core_list_view.selectionModel().select(item, QItemSelectionModel.SelectionFlag.Select)
            self.file_paths.append(i_path)  # append a file path to list
        QApplication.clipboard().setText('\n'.join(self.file_paths))  # copy file paths to clipboard
        self.paste_dir_act.setEnabled(True)  # enable paste action

        # print(f"[LOG]: selectAllData\n    -{i_name}\n    -{i_path}\n    -{i_info}\n")

    def showProperties(self):
        index = self.core_list_view.currentIndex()
        if index.isValid():
            path = self.core_sys_model.filePath(index)
            properties_window = PropertiesWindow(path)
            properties_window.setModal(True)
            properties_window.exec()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet(style_sheet)
    window = TanzFileManger()
    sys.exit(app.exec())
