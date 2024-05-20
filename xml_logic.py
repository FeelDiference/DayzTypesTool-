import os
import xml.etree.ElementTree as ET
from PyQt5.QtWidgets import (
    QUndoStack, QUndoCommand, QLineEdit, QComboBox, QTextEdit, QCheckBox,
    QLabel, QPushButton, QHBoxLayout, QFileDialog
)
from PyQt5.QtCore import Qt
from xml.dom import minidom

class EditCommand(QUndoCommand):
    def __init__(self, widget, new_value, description, parent=None):
        super().__init__(description, parent)
        self.widget = widget
        self.new_value = new_value
        self.old_value = self.get_current_value()

    def get_current_value(self):
        if isinstance(self.widget, QLineEdit):
            return self.widget.text()
        elif isinstance(self.widget, QComboBox):
            return self.widget.currentText()
        elif isinstance(self.widget, QTextEdit):
            return self.widget.toPlainText()
        elif isinstance(self.widget, QCheckBox):
            return self.widget.isChecked()
        return None

    def undo(self):
        self.set_value(self.old_value)

    def redo(self):
        self.set_value(self.new_value)

    def set_value(self, value):
        self.widget.blockSignals(True)
        if isinstance(self.widget, QLineEdit):
            self.widget.setText(value)
        elif isinstance(self.widget, QComboBox):
            self.widget.setCurrentText(value)
        elif isinstance(self.widget, QTextEdit):
            self.widget.setPlainText(value)
        elif isinstance(self.widget, QCheckBox):
            self.widget.setChecked(value)
        self.widget.blockSignals(False)

class XMLLogic:
    def __init__(self, viewer):
        self.viewer = viewer
        self.xml_root = None
        self.current_item = None
        self.details_widgets = {}  # Инициализация атрибута
        self.undo_stacks = {}  # Добавление для управления undo/redo командами
        self.current_undo_stack = None

        # Define category, usage, value, and tag options
        self.category_options = [
            "clothes", "containers", "explosives", "food", "weapons", "vehiclesparts"
        ]
        self.usage_options = [
            "Coast", "Farm", "Firefighter", "Hunting", "Industrial", "Medic",
            "Military", "Office", "Police", "Prison", "School", "Town", "Village"
        ]
        self.value_options = ["Tier1", "Tier2", "Tier3", "Tier4"]
        self.tag_options = ["shelves", "floor"]

    def openFile(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self.viewer, "Open XML File", "", "XML Files (*.xml);;All Files (*)", options=options)
        if file_name:
            self.loadXML(file_name)
        return file_name

    def loadXML(self, file_name):
        self.xml_tree = ET.parse(file_name)
        self.xml_root = self.xml_tree.getroot()
        self.viewer.loadXMLItems()

    def saveFile(self):
        if self.xml_tree is not None:
            file_name = self.xml_tree.getroot().attrib.get('file', 'output.xml')
            self.prettify_and_write_xml(file_name)

    def saveFileAs(self):
        if self.xml_tree is not None:
            options = QFileDialog.Options()
            file_name, _ = QFileDialog.getSaveFileName(self.viewer, "Save XML File", "", "XML Files (*.xml);;All Files (*)", options=options)
            if file_name:
                self.prettify_and_write_xml(file_name)

    def prettify_and_write_xml(self, file_name):
        rough_string = ET.tostring(self.xml_root, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        with open(file_name, 'w', encoding='utf-8') as f:
            f.write(reparsed.toprettyxml(indent="  "))

    def get_filtered_items(self, selected_categories):
        if selected_categories is None or not selected_categories:
            return self.xml_root.findall('type')
        filtered_items = []
        for item in self.xml_root.findall('type'):
            category = item.find('category')
            if category is not None and category.attrib.get('name') in selected_categories:
                filtered_items.append(item)
        return filtered_items

    def get_selected_items(self):
        selected_list_items = self.viewer.get_selected_list_items()
        selected_items = []
        for list_item in selected_list_items:
            item = next((x for x in self.xml_root.findall('type') if x.get('name') == list_item.text()), None)
            if item is not None:
                selected_items.append(item)
        return selected_items

    def saveCurrentItemDetails(self):
        if self.current_item is not None:
            print(f"Saving current item details for: {self.current_item.get('name')}")  # Debug info
            if 'name' in self.details_widgets:  # Проверка на наличие ключа 'name'
                self.current_item.set('name', self.details_widgets['name'].text())

            # Handle all child elements that are in self.details_widgets
            for tag in self.details_widgets:
                if tag in ['flags', 'category', 'usage', 'value', 'tag']:
                    # Remove existing elements with the same tag
                    for elem in self.current_item.findall(tag):
                        self.current_item.remove(elem)
                    # Add updated elements
                    widgets = self.details_widgets[tag]
                    if tag in ['usage', 'value']:
                        for widget, layout in widgets:
                            if isinstance(widget, QLineEdit):
                                ET.SubElement(self.current_item, tag, name=widget.text())
                            elif isinstance(widget, QComboBox):
                                ET.SubElement(self.current_item, tag, name=widget.currentText())
                    else:
                        if not isinstance(widgets, list):
                            widgets = [widgets]
                        for widget in widgets:
                            if isinstance(widget, QLineEdit):
                                ET.SubElement(self.current_item, tag, name=widget.text())
                            elif isinstance(widget, QComboBox):
                                ET.SubElement(self.current_item, tag, name=widget.currentText())
                else:
                    child = self.current_item.find(tag)
                    if child is not None:
                        child.text = self.details_widgets[tag].text()

    def displayItemDetails(self, item):
        # Save changes of the current item before switching
        if self.current_item is not None:
            self.saveCurrentItemDetails()

        self.current_item = next((x for x in self.xml_root.findall('type') if x.get('name') == item.text()), None)

        if self.current_item is not None:
            print(f"Displaying details for: {self.current_item.get('name')}")  # Debug info

            self.viewer.clear_details_layout()

            self.details_widgets.clear()

            # Create or get the undo stack for the current item
            if self.current_item.get('name') not in self.undo_stacks:
                self.undo_stacks[self.current_item.get('name')] = QUndoStack(self.viewer)
            self.current_undo_stack = self.undo_stacks[self.current_item.get('name')]

            name_label = QLabel('Name:', self.viewer)
            name_edit = QLineEdit(self.current_item.get('name'), self.viewer)
            name_edit.setFixedHeight(30)
            name_edit.textChanged.connect(lambda text, widget=name_edit: self.add_undo_command(widget, text))
            self.viewer.details_layout.addWidget(name_label)
            self.viewer.details_layout.addWidget(name_edit)
            self.details_widgets['name'] = name_edit  # Добавляем виджет имени в details_widgets

            for child in self.current_item:
                if child.tag == 'flags':
                    flags_label = QLabel('Flags:', self.viewer)
                    self.viewer.details_layout.addWidget(flags_label)

                    for flag in child.attrib:
                        flag_checkbox = QCheckBox(flag, self.viewer)
                        flag_checkbox.setChecked(child.attrib[flag] == '1')
                        flag_checkbox.stateChanged.connect(lambda state, widget=flag_checkbox: self.add_undo_command(widget, state == Qt.Checked))
                        self.viewer.details_layout.addWidget(flag_checkbox)
                        self.details_widgets[flag] = flag_checkbox
                elif child.tag == 'category':
                    detail_label = QLabel(f"{child.tag.capitalize()}:", self.viewer)
                    detail_combo = QComboBox(self.viewer)
                    detail_combo.addItems(self.category_options)
                    detail_combo.setCurrentText(child.attrib['name'])
                    detail_combo.setFixedHeight(30)
                    detail_combo.currentTextChanged.connect(lambda text, widget=detail_combo: self.add_undo_command(widget, text))
                    self.viewer.details_layout.addWidget(detail_label)
                    self.viewer.details_layout.addWidget(detail_combo)
                    self.details_widgets['category'] = detail_combo
                elif child.tag == 'tag':
                    self.add_tag_field(child.attrib.get('name', ''))
                elif child.tag == 'usage':
                    self.add_usage_field(child.attrib['name'])
                elif child.tag == 'value':
                    self.add_value_field(child.attrib['name'])
                else:
                    detail_label = QLabel(f"{child.tag.capitalize()}:", self.viewer)
                    detail_edit = QLineEdit(child.text, self.viewer)
                    detail_edit.setFixedHeight(30)
                    detail_edit.textChanged.connect(lambda text, widget=detail_edit: self.add_undo_command(widget, text))
                    self.viewer.details_layout.addWidget(detail_label)
                    self.viewer.details_layout.addWidget(detail_edit)
                    self.details_widgets[child.tag] = detail_edit

            # Add buttons to add new Usage and Value fields
            add_usage_button = QPushButton('Add Usage', self.viewer)
            add_usage_button.clicked.connect(lambda: self.add_usage_field())
            self.viewer.details_layout.addWidget(add_usage_button)

            add_value_button = QPushButton('Add Value', self.viewer)
            add_value_button.clicked.connect(lambda: self.add_value_field())
            self.viewer.details_layout.addWidget(add_value_button)

            # Add button to add tag field
            add_tag_button = QPushButton('Add Tag', self.viewer)
            add_tag_button.clicked.connect(self.add_tag_field)
            self.viewer.details_layout.addWidget(add_tag_button)

    def add_usage_field(self, usage_name=''):
        print(f"Adding usage field: {usage_name}")  # Debug info

        usage_layout = QHBoxLayout()
        detail_label = QLabel("Usage:", self.viewer)
        detail_combo = QComboBox(self.viewer)
        detail_combo.addItems(self.usage_options)
        detail_combo.setCurrentText(usage_name)
        detail_combo.setFixedHeight(30)
        detail_combo.currentTextChanged.connect(lambda text, widget=detail_combo: self.add_undo_command(widget, text))
        usage_layout.addWidget(detail_label)
        usage_layout.addWidget(detail_combo)

        remove_usage_button = QPushButton('Remove', self.viewer)
        remove_usage_button.setFixedHeight(30)
        remove_usage_button.clicked.connect(lambda: self.remove_field(usage_layout, 'usage', detail_combo))
        usage_layout.addWidget(remove_usage_button)

        insert_position = self.find_insert_position('usage')
        self.viewer.details_layout.insertLayout(insert_position, usage_layout)

        if 'usage' not in self.details_widgets:
            self.details_widgets['usage'] = []
        self.details_widgets['usage'].append((detail_combo, usage_layout))

    def add_value_field(self, value_name=''):
        print(f"Adding value field: {value_name}")  # Debug info

        value_layout = QHBoxLayout()
        detail_label = QLabel("Value:", self.viewer)
        detail_combo = QComboBox(self.viewer)
        detail_combo.addItems(self.value_options)
        detail_combo.setCurrentText(value_name)
        detail_combo.setFixedHeight(30)
        detail_combo.currentTextChanged.connect(lambda text, widget=detail_combo: self.add_undo_command(widget, text))
        value_layout.addWidget(detail_label)
        value_layout.addWidget(detail_combo)

        remove_value_button = QPushButton('Remove', self.viewer)
        remove_value_button.setFixedHeight(30)
        remove_value_button.clicked.connect(lambda: self.remove_field(value_layout, 'value', detail_combo))
        value_layout.addWidget(remove_value_button)

        insert_position = self.find_insert_position('value')
        self.viewer.details_layout.insertLayout(insert_position, value_layout)

        if 'value' not in self.details_widgets:
            self.details_widgets['value'] = []
        self.details_widgets['value'].append((detail_combo, value_layout))

    def find_insert_position(self, field_type):
        last_category_pos = None
        last_usage_pos = None

        for i in range(self.viewer.details_layout.count()):
            item = self.viewer.details_layout.itemAt(i)
            if item is not None:
                widget = item.widget()
                if widget is not None:
                    if widget == self.details_widgets.get('category'):
                        last_category_pos = i
                    elif any(widget == w[0] for w in self.details_widgets.get('usage', [])):
                        last_usage_pos = i

        if field_type == 'usage':
            if last_category_pos is not None:
                return last_category_pos + 1
            return 2  # Если нет category, вернем позицию после имени

        if field_type == 'value':
            if last_usage_pos is not None:
                return last_usage_pos + 1
            if last_category_pos is not None:
                return last_category_pos + 1
            return 2  # Если нет category и usage, вернем позицию после имени

        return self.viewer.details_layout.count() - 3  # Перед добавлением кнопок

    def add_tag_field(self, tag_name=''):
        print(f"Adding tag field: {tag_name}")  # Debug info

        tag_layout = QHBoxLayout()
        detail_label = QLabel("Tag:", self.viewer)
        detail_combo = QComboBox(self.viewer)
        detail_combo.addItems(self.tag_options)
        detail_combo.setCurrentText(tag_name)
        detail_combo.setFixedHeight(30)
        detail_combo.currentTextChanged.connect(lambda text, widget=detail_combo: self.add_undo_command(widget, text))
        tag_layout.addWidget(detail_label)
        tag_layout.addWidget(detail_combo)

        remove_tag_button = QPushButton('Remove', self.viewer)
        remove_tag_button.setFixedHeight(30)
        remove_tag_button.clicked.connect(lambda: self.remove_field(tag_layout, 'tag', detail_combo))
        tag_layout.addWidget(remove_tag_button)

        insert_position = self.find_insert_position('tag')
        self.viewer.details_layout.insertLayout(insert_position, tag_layout)

        if 'tag' not in self.details_widgets:
            self.details_widgets['tag'] = []
        self.details_widgets['tag'].append((detail_combo, tag_layout))

    def remove_field(self, layout, field_type, widget):
        print(f"Removing field: {field_type}, widget: {widget}")  # Debug info

        if field_type in self.details_widgets and widget in [w[0] for w in self.details_widgets[field_type]]:
            self.details_widgets[field_type] = [(w, l) for w, l in self.details_widgets[field_type] if w != widget]
            if layout is not None:
                for i in reversed(range(layout.count())):
                    item = layout.itemAt(i).widget()
                    if item is not None:
                        layout.removeWidget(item)
                        item.deleteLater()

    def add_undo_command(self, widget, new_value):
        if isinstance(widget, QLineEdit) and widget.text() == new_value:
            return
        elif isinstance(widget, QComboBox) and widget.currentText() == new_value:
            return
        elif isinstance(widget, QTextEdit) and widget.toPlainText() == new_value:
            return
        elif isinstance(widget, QCheckBox) and widget.isChecked() == new_value:
            return

        command = EditCommand(widget, new_value, "Edit Value")
        self.current_undo_stack.push(command)

    def undo(self):
        if self.current_undo_stack and not self.current_undo_stack.isClean():
            self.current_undo_stack.undo()

    def redo(self):
        if self.current_undo_stack and not self.current_undo_stack.isClean():
            self.current_undo_stack.redo()

    def _remove_layout_with_widgets(self, layout):
        for i in reversed(range(layout.count())):
            item = layout.itemAt(i)
            if item is not None:
                widget_to_remove = item.widget()
                if widget_to_remove is not None:
                    layout.removeWidget(widget_to_remove)
                    widget_to_remove.deleteLater()
        self.viewer.details_layout.removeItem(layout)
