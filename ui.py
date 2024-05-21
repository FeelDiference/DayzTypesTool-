from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget,
    QLabel, QCheckBox, QLineEdit, QScrollArea, QShortcut,
    QComboBox, QListWidgetItem, QToolBar, QAction, QToolButton, QMenu, QFrame, QSpacerItem, QSizePolicy
)
from PyQt5.QtGui import QFont, QKeySequence, QIcon
from PyQt5.QtCore import Qt, QPropertyAnimation, QSize
import qtawesome as qta
from xml_logic import XMLLogic
from mass_edit import MassEditDialog

class XMLViewer(QWidget):
    def __init__(self):
        super().__init__()

        self.xml_logic = XMLLogic(self)
        self.selected_items = set()
        self.lifetime_slider_value = 100
        self.restock_slider_value = 100
        self.selected_categories = set(self.xml_logic.category_options)
        self.category_checkboxes = {}
        self.initUI()

    def initUI(self):
        self.setWindowTitle('DayZ StandAlone XML Viewer')
        self.setGeometry(100, 100, 1200, 600)

        layout = QVBoxLayout()

        # Create the toolbar
        self.toolbar = QToolBar()
        self.addToolBarActions()
        layout.addWidget(self.toolbar)

        # Create the horizontal layout for main content
        main_layout = QHBoxLayout()

        # Create the vertical layout for the left column (buttons)
        self.left_column = QFrame(self)
        self.left_column.setFrameShape(QFrame.NoFrame)
        self.left_column.setFixedWidth(40)
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)
        left_layout.setAlignment(Qt.AlignTop)
        self.left_column.setLayout(left_layout)

        # Create the hamburger button
        self.hamburger_button = QPushButton(self)
        self.hamburger_button.setIcon(qta.icon('fa.bars'))
        self.hamburger_button.setFixedSize(30, 30)
        self.hamburger_button.clicked.connect(self.toggle_filter_panel)
        left_layout.addWidget(self.hamburger_button)

        # Add left column to main layout
        main_layout.addWidget(self.left_column)

        # Create the filter panel
        self.filter_panel = QFrame(self)
        self.filter_panel.setFrameShape(QFrame.NoFrame)
        self.filter_panel.setFixedWidth(0)  # Initially hidden
        filter_layout = QVBoxLayout()
        filter_layout.setContentsMargins(0, 0, 0, 0)
        filter_layout.setSpacing(10)
        filter_layout.setAlignment(Qt.AlignTop)
        self.filter_panel.setLayout(filter_layout)

        # Add collapsible functionality to the category header
        self.category_toggle_button = self.create_toggle_button("Category Filter", self.toggle_category_section)
        filter_layout.addWidget(self.category_toggle_button)

        # Add category filter checkboxes directly to the filter panel
        self.category_container = self.create_filter_container()
        filter_layout.addWidget(self.category_container)

        self.category_all_checkbox = QCheckBox("All (0)", self)
        self.category_all_checkbox.setChecked(True)
        self.category_all_checkbox.stateChanged.connect(self.toggle_all_categories)
        self.category_container.layout().addWidget(self.category_all_checkbox)

        for category in self.xml_logic.category_options:
            checkbox = QCheckBox(category, self)
            checkbox.setChecked(True)
            checkbox.stateChanged.connect(self.toggle_category_selection)
            self.category_checkboxes[category] = checkbox
            self.category_container.layout().addWidget(checkbox)

        # Add collapsible functionality to the usage filter
        self.usage_toggle_button = self.create_toggle_button("Usage Filter", self.toggle_usage_section)
        filter_layout.addWidget(self.usage_toggle_button)

        # Add usage filter container
        self.usage_container = self.create_filter_container()
        filter_layout.addWidget(self.usage_container)

        # Add collapsible functionality to the nominal filter
        self.nominal_toggle_button = self.create_toggle_button("Nominal Filter", self.toggle_nominal_section)
        filter_layout.addWidget(self.nominal_toggle_button)

        # Add nominal filter container
        self.nominal_container = self.create_filter_container()
        filter_layout.addWidget(self.nominal_container)

        # Add collapsible functionality to the min filter
        self.min_toggle_button = self.create_toggle_button("Min Filter", self.toggle_min_section)
        filter_layout.addWidget(self.min_toggle_button)

        # Add min filter container
        self.min_container = self.create_filter_container()
        filter_layout.addWidget(self.min_container)

        filter_layout.addStretch(1)

        main_layout.addWidget(self.filter_panel)

        # Create the vertical layout for the middle column (list and selection)
        middle_column = QFrame(self)
        middle_column.setFrameShape(QFrame.NoFrame)
        middle_layout = QVBoxLayout()
        middle_layout.setContentsMargins(0, 0, 0, 0)
        middle_layout.setSpacing(0)
        middle_column.setLayout(middle_layout)

        # Create the horizontal layout for the list widget header
        list_header_layout = QHBoxLayout()
        list_header_layout.setContentsMargins(5, 0, 5, 0)
        list_header_layout.setSpacing(0)

        self.select_visible_checkbox = QCheckBox(self)
        self.select_visible_checkbox.setFixedSize(20, 20)
        self.select_visible_checkbox.stateChanged.connect(self.select_visible_items)
        list_header_layout.addWidget(self.select_visible_checkbox)

        list_header_label = QLabel("Objects Name", self)
        list_header_label.setAlignment(Qt.AlignCenter)
        list_header_layout.addWidget(list_header_label)

        # Create a container for the header to fix its position
        list_header_container = QFrame(self)
        list_header_container.setLayout(list_header_layout)
        list_header_container.setFixedHeight(40)
        middle_layout.addWidget(list_header_container)

        # Create the list widget
        self.list_widget = QListWidget(self)
        self.list_widget.itemClicked.connect(self.displayItemDetails)
        middle_layout.addWidget(self.list_widget)

        main_layout.addWidget(middle_column)

        # Create the details area with scroll
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)

        self.details_widget = QWidget()
        self.details_layout = QVBoxLayout()
        self.details_widget.setLayout(self.details_layout)
        self.scroll_area.setWidget(self.details_widget)

        main_layout.addWidget(self.scroll_area)

        layout.addLayout(main_layout)
        self.setLayout(layout)

        # Apply custom CSS for checkboxes
        self.setStyleSheet("""
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border: 1px solid black;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                background-color: #00FF00;
                border: 1px solid black;
            }
            QCheckBox::indicator:unchecked {
                background-color: #FFFFFF;
                border: 1px solid black;
            }
        """)

        # Create shortcuts for undo and redo
        undo_shortcut = QShortcut(QKeySequence('Ctrl+Z'), self)
        undo_shortcut.activated.connect(self.undo)

        redo_shortcut = QShortcut(QKeySequence('Ctrl+Shift+Z'), self)
        redo_shortcut.activated.connect(self.redo)

    def addToolBarActions(self):
        open_action = QAction(qta.icon('fa.folder-open'), 'Open XML', self)
        open_action.triggered.connect(self.openFile)
        self.toolbar.addAction(open_action)

        save_action = QAction(qta.icon('fa.save'), 'Save XML', self)
        save_action.triggered.connect(self.saveFile)
        self.toolbar.addAction(save_action)

        save_as_action = QAction(qta.icon('fa.save'), 'Save As', self)
        save_as_action.triggered.connect(self.saveFileAs)
        self.toolbar.addAction(save_as_action)

        # Add MassEdit button to the toolbar
        mass_edit_action = QAction(qta.icon('fa.edit'), 'Mass Edit', self)
        mass_edit_action.triggered.connect(self.openMassEditDialog)
        self.toolbar.addAction(mass_edit_action)

    def create_toggle_button(self, text, slot):
        button = QToolButton(self)
        button.setText(text)
        button.setCheckable(True)
        button.setChecked(True)
        button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        button.setArrowType(Qt.DownArrow)
        button.clicked.connect(slot)
        return button

    def create_filter_container(self):
        container = QFrame(self)
        container.setFrameShape(QFrame.NoFrame)
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 0, 10, 0)  # Reduce margins for compactness
        layout.setSpacing(20)  # Set spacing between checkboxes to 20 pixels
        container.setLayout(layout)
        return container

    def toggle_category_section(self):
        self.toggle_section(self.category_toggle_button, self.category_container)

    def toggle_usage_section(self):
        self.toggle_section(self.usage_toggle_button, self.usage_container)

    def toggle_nominal_section(self):
        self.toggle_section(self.nominal_toggle_button, self.nominal_container)

    def toggle_min_section(self):
        self.toggle_section(self.min_toggle_button, self.min_container)

    def toggle_section(self, button, container):
        if button.isChecked():
            button.setArrowType(Qt.DownArrow)
            container.show()
        else:
            button.setArrowType(Qt.RightArrow)
            container.hide()

    def update_category_filter_text(self):
        for category, checkbox in self.category_checkboxes.items():
            count = len(self.xml_logic.get_filtered_items([category]))
            checkbox.setText(f"{category} ({count})")

    def toggle_all_categories(self, state):
        checked = state == Qt.Checked
        for checkbox in self.category_checkboxes.values():
            checkbox.setChecked(checked)
        self.selected_categories = set(self.xml_logic.category_options) if checked else set()
        self.update_category_filter_text()
        self.loadXMLItems()

    def toggle_category_selection(self, state):
        checkbox = self.sender()
        category = checkbox.text().split(' ')[0]
        if state == Qt.Checked:
            self.selected_categories.add(category)
        else:
            self.selected_categories.discard(category)

        all_checked = all(checkbox.isChecked() for checkbox in self.category_checkboxes.values())
        self.category_all_checkbox.setChecked(all_checked)
        self.update_category_filter_text()
        self.loadXMLItems()

    def toggle_filter_panel(self):
        current_width = self.filter_panel.width()
        new_width = 200 if current_width == 0 else 0

        self.animation = QPropertyAnimation(self.filter_panel, b"maximumWidth")
        self.animation.setDuration(500)
        self.animation.setStartValue(current_width)
        self.animation.setEndValue(new_width)
        self.animation.start()

    def select_visible_items(self, state):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            item.setCheckState(state)

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

        self.update_category_filter_text()

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
            self.loadXMLItems()

    def saveFile(self):
        self.xml_logic.saveFile()

    def saveFileAs(self):
        self.xml_logic.saveFileAs()

    def displayItemDetails(self, item):
        self.xml_logic.displayItemDetails(item)
        self.list_widget.clearSelection()  # Убираем выделение с объекта

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
        self.xml_logic.saveCurrentItemDetails()  # Сохранить текущий объект перед массовыми изменениями
        self.mass_edit_dialog = MassEditDialog(self.xml_logic, self)
        self.mass_edit_dialog.setModal(False)  # Allow interaction with the main window
        self.mass_edit_dialog.lifetime_slider_value = self.lifetime_slider_value
        self.mass_edit_dialog.restock_slider_value = self.restock_slider_value
        self.mass_edit_dialog.load_slider_values()  # Load current slider values
        self.mass_edit_dialog.finished.connect(self.onMassEditDialogClosed)  # Connect the finished signal to update the active item
        self.mass_edit_dialog.show()

    def force_update_active_item(self):
        self.xml_logic.saveCurrentItemDetails()
        self.clear_details_layout()  # Очищаем текущие детали

    def update_item_in_list(self, item_name):
        """Обновляет элемент в списке на основе имени элемента."""
        for i in range(self.list_widget.count()):
            list_item = self.list_widget.item(i)
            if list_item.text() == item_name:
                print(f"Updating item in list: {item_name}")  # Debug info
                self.displayItemDetails(list_item)
                break
            
    def onMassEditDialogClosed(self):
        print("Mass Edit dialog closed")  # Debug info
        self.loadXMLItems()  # Перезагрузить элементы XML
        self.force_update_active_item()

    def get_selected_list_items(self):
        selected_items = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == Qt.Checked:
                selected_items.append(item)
        return selected_items

    def refresh_active_item(self):
        selected_items = self.get_selected_list_items()
        if selected_items:
            last_item_name = selected_items[-1].text()
            for index in range(self.list_widget.count()):
                list_item = self.list_widget.item(index)
                if list_item.text() == last_item_name:
                    self.list_widget.setCurrentItem(list_item)
                    self.displayItemDetails(list_item)
                    break
