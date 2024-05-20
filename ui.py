from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget,
    QLabel, QCheckBox, QLineEdit, QScrollArea, QShortcut,
    QComboBox, QListWidgetItem, QToolBar, QAction, QToolButton, QMenu
)
from PyQt5.QtGui import QFont, QKeySequence, QIcon
from PyQt5.QtCore import Qt
from xml_logic import XMLLogic
from mass_edit import MassEditDialog
import os

class XMLViewer(QWidget):
    def __init__(self):
        super().__init__()

        self.xml_logic = XMLLogic(self)
        self.selected_items = set()
        self.lifetime_slider_value = 100
        self.restock_slider_value = 100
        self.initUI()

    def initUI(self):
        self.setWindowTitle('DayZ StandAlone XML Viewer')
        self.setGeometry(100, 100, 800, 600)

        layout = QVBoxLayout()

        # Create the toolbar
        self.toolbar = QToolBar()
        self.addToolBarActions()
        layout.addWidget(self.toolbar)

        # Get category options from xml_logic
        self.category_options = ['All'] + self.xml_logic.category_options
        self.selected_categories = set(self.xml_logic.category_options)

        # Create the category filter menu
        self.category_filter_menu = QMenu(self)
        self.category_filter_combo = QToolButton(self)
        self.category_filter_combo.setText("Category Filter")
        self.category_filter_combo.setPopupMode(QToolButton.InstantPopup)
        self.category_filter_combo.setMenu(self.category_filter_menu)
        self.category_filter_combo.setFixedWidth(150)  # Установить фиксированную ширину

        all_action = QAction('All', self.category_filter_menu)
        all_action.setCheckable(True)
        all_action.setChecked(True)
        all_action.triggered.connect(self.toggle_all_categories)
        self.category_filter_menu.addAction(all_action)

        self.category_actions = []
        for category in self.xml_logic.category_options:
            action = QAction(category, self.category_filter_menu)
            action.setCheckable(True)
            action.setChecked(True)
            action.triggered.connect(self.toggle_category_selection)
            self.category_filter_menu.addAction(action)
            self.category_actions.append(action)

        self.category_filter_combo.setEnabled(False)
        self.toolbar.addWidget(self.category_filter_combo)

        # Add MassEdit button to the toolbar
        mass_edit_action = QAction(QIcon(os.path.join('icons', 'mass_edit.png')), 'MassEdit', self)
        mass_edit_action.triggered.connect(self.openMassEditDialog)
        self.toolbar.addAction(mass_edit_action)

        # Create the select/deselect all buttons
        select_buttons_layout = QHBoxLayout()
        self.select_all_button = QPushButton('Select All', self)
        self.select_all_button.clicked.connect(self.select_all_items)
        select_buttons_layout.addWidget(self.select_all_button)

        self.deselect_all_button = QPushButton('Deselect All', self)
        self.deselect_all_button.clicked.connect(self.deselect_all_items)
        select_buttons_layout.addWidget(self.deselect_all_button)

        layout.addLayout(select_buttons_layout)

        # Create the horizontal layout for list and details
        h_layout = QHBoxLayout()

        # Create the list widget
        self.list_widget = QListWidget(self)
        self.list_widget.itemClicked.connect(self.displayItemDetails)
        h_layout.addWidget(self.list_widget)

        # Create the details area with scroll
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)

        self.details_widget = QWidget()
        self.details_layout = QVBoxLayout()
        self.details_widget.setLayout(self.details_layout)
        self.scroll_area.setWidget(self.details_widget)

        h_layout.addWidget(self.scroll_area)

        layout.addLayout(h_layout)
        self.setLayout(layout)

        # Create shortcuts for undo and redo
        undo_shortcut = QShortcut(QKeySequence('Ctrl+Z'), self)
        undo_shortcut.activated.connect(self.undo)

        redo_shortcut = QShortcut(QKeySequence('Ctrl+Shift+Z'), self)
        redo_shortcut.activated.connect(self.redo)

    def addToolBarActions(self):
        open_action = QAction(QIcon(os.path.join('icons', 'open.png')), 'Open XML', self)
        open_action.triggered.connect(self.openFile)
        self.toolbar.addAction(open_action)

        save_action = QAction(QIcon(os.path.join('icons', 'save.png')), 'Save XML', self)
        save_action.triggered.connect(self.saveFile)
        self.toolbar.addAction(save_action)

        save_as_action = QAction(QIcon(os.path.join('icons', 'save_as.png')), 'Save As', self)
        save_as_action.triggered.connect(self.saveFileAs)
        self.toolbar.addAction(save_as_action)

    def update_category_filter_text(self):
        if len(self.selected_categories) == len(self.xml_logic.category_options):
            self.category_filter_combo.setText("All Categories")
        elif len(self.selected_categories) > 1:
            self.category_filter_combo.setText(f"{len(self.selected_categories)} Categories Selected")
        elif len(self.selected_categories) == 1:
            self.category_filter_combo.setText(next(iter(self.selected_categories)))
        else:
            self.category_filter_combo.setText("No Categories Selected")

    def toggle_all_categories(self, checked):
        for action in self.category_actions:
            action.setChecked(checked)
        self.selected_categories = set(self.xml_logic.category_options) if checked else set()
        self.update_category_filter_text()
        self.loadXMLItems()

    def toggle_category_selection(self, checked):
        action = self.sender()
        category = action.text()
        if checked:
            self.selected_categories.add(category)
        else:
            self.selected_categories.discard(category)

        all_checked = all(action.isChecked() for action in self.category_actions)
        self.category_filter_menu.actions()[0].setChecked(all_checked)
        self.update_category_filter_text()
        self.loadXMLItems()

    def loadXMLItems(self):
        if self.xml_logic.xml_root is None:
            return

        current_selected_items = {self.list_widget.item(i).text() for i in range(self.list_widget.count()) if self.list_widget.item(i).checkState() == Qt.Checked}
        self.selected_items.update(current_selected_items)

        self.list_widget.clear()
        for item in self.xml_logic.get_filtered_items(self.selected_categories):
            list_item = QListWidgetItem(item.get('name'))
            list_item.setFlags(list_item.flags() | Qt.ItemIsUserCheckable)
            if item.get('name') in self.selected_items:
                list_item.setCheckState(Qt.Checked)
            else:
                list_item.setCheckState(Qt.Unchecked)
            self.list_widget.addItem(list_item)

    def select_all_items(self):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            item.setCheckState(Qt.Checked)
            self.selected_items.add(item.text())

    def deselect_all_items(self):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            item.setCheckState(Qt.Unchecked)
            self.selected_items.discard(item.text())

    def openFile(self):
        file_name = self.xml_logic.openFile()
        if file_name:
            self.category_filter_combo.setEnabled(True)
            self.loadXMLItems()

    def saveFile(self):
        self.xml_logic.saveFile()

    def saveFileAs(self):
        self.xml_logic.saveFileAs()

    def displayItemDetails(self, item):
        if hasattr(self, 'mass_edit_dialog') and self.mass_edit_dialog.isVisible():
            return  # Do not update details if mass edit dialog is open
        self.xml_logic.displayItemDetails(item)

    def clear_details_layout(self):
        for i in reversed(range(self.details_layout.count())):
            item = self.details_layout.itemAt(i)
            if item is not None:
                widget_to_remove = item.widget()
                if widget_to_remove is not None:
                    self.details_layout.removeWidget(widget_to_remove)
                    widget_to_remove.deleteLater()

        if 'usage' in self.xml_logic.details_widgets:
            for widget, layout in self.xml_logic.details_widgets['usage']:
                self.xml_logic._remove_layout_with_widgets(layout)
            del self.xml_logic.details_widgets['usage']

        if 'value' in self.xml_logic.details_widgets:
            for widget, layout in self.xml_logic.details_widgets['value']:
                self.xml_logic._remove_layout_with_widgets(layout)
            del self.xml_logic.details_widgets['value']

        if 'tag' in self.xml_logic.details_widgets:
            for widget, layout in self.xml_logic.details_widgets['tag']:
                self.xml_logic._remove_layout_with_widgets(layout)
            del self.xml_logic.details_widgets['tag']

        self.xml_logic.details_widgets.clear()

    def undo(self):
        self.xml_logic.undo()

    def redo(self):
        self.xml_logic.redo()

    def openMassEditDialog(self):
        self.mass_edit_dialog = MassEditDialog(self.xml_logic, self)
        self.mass_edit_dialog.setModal(False)  # Allow interaction with the main window
        self.mass_edit_dialog.lifetime_slider_value = self.lifetime_slider_value
        self.mass_edit_dialog.restock_slider_value = self.restock_slider_value
        self.mass_edit_dialog.load_slider_values()  # Load current slider values
        self.mass_edit_dialog.show()

    def update_item_in_list(self, item):
        for i in range(self.list_widget.count()):
            list_item = self.list_widget.item(i)
            if list_item.text() == item.get('name'):
                self.displayItemDetails(list_item)
                print(f"Updated item in list: {item.get('name')}")  # Debug info
                break

    def get_selected_list_items(self):
        selected_items = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == Qt.Checked:
                selected_items.append(item)
        return selected_items
