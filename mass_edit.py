import os
import xml.etree.ElementTree as ET
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QCheckBox, QSlider, QComboBox, QScrollArea, QFrame, QMessageBox, QWidget
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

class MassEditDialog(QDialog):
    def __init__(self, xml_logic, parent=None):
        super().__init__(parent)
        self.xml_logic = xml_logic
        self.parent = parent

        # Initialize slider values
        self.lifetime_slider_value = parent.lifetime_slider_value
        self.restock_slider_value = parent.restock_slider_value

        # Initialize original values
        self.original_values = {
            'lifetime': self.get_initial_values('lifetime'),
            'restock': self.get_initial_values('restock')
        }

        self.initUI()

    def initUI(self):
        self.setWindowTitle("Mass Edit")
        self.setGeometry(100, 100, 400, 600)

        layout = QVBoxLayout()

        # Create multiplier buttons
        multiplier_layout = QHBoxLayout()
        self.multiplier_buttons = {
            'x10': QPushButton("X10", self),
            'x5': QPushButton("X5", self),
            'x2': QPushButton("X2", self),
            'standard': QPushButton("Standard", self),
            'div2': QPushButton("/2", self),
            'div5': QPushButton("/5", self),
            'div10': QPushButton("/10", self)
        }
        for key, button in self.multiplier_buttons.items():
            button.setIcon(QIcon(os.path.join('icons', f'{key}.png')))
            button.clicked.connect(self.onMultiplierClicked)
            multiplier_layout.addWidget(button)
        layout.addLayout(multiplier_layout)

        # Create checkboxes and input fields
        self.parameters = ['nominal', 'min', 'lifetime', 'restock']
        self.checkboxes = {}
        self.input_fields = {}
        for param in self.parameters:
            param_layout = QHBoxLayout()
            checkbox = QCheckBox(param.capitalize(), self)
            self.checkboxes[param] = checkbox
            param_layout.addWidget(checkbox)

            input_field = QLineEdit(self)
            input_field.setPlaceholderText("Enter value manually")
            input_field.textChanged.connect(lambda text, param=param: self.onInputChanged(param))
            self.input_fields[param] = input_field
            param_layout.addWidget(input_field)

            layout.addLayout(param_layout)

        # Create category dropdown
        category_layout = QHBoxLayout()
        category_label = QLabel("Category:", self)
        self.category_combo = QComboBox(self)
        self.category_combo.addItems(self.xml_logic.category_options)
        category_layout.addWidget(category_label)
        category_layout.addWidget(self.category_combo)
        layout.addLayout(category_layout)

        # Create sliders for lifetime and restock
        self.create_slider(layout, "Lifetime")
        self.create_slider(layout, "Restock")

        # Create frames for Usage, Value, and Tag
        self.usage_frame = self.create_edit_frame("Usage")
        layout.addWidget(self.usage_frame)

        self.value_frame = self.create_edit_frame("Value")
        layout.addWidget(self.value_frame)

        self.tag_frame = self.create_edit_frame("Tag")
        layout.addWidget(self.tag_frame)

        # Create OK and Cancel buttons
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK", self)
        ok_button.clicked.connect(self.onOk)
        button_layout.addWidget(ok_button)

        cancel_button = QPushButton("Cancel", self)
        cancel_button.clicked.connect(self.onCancel)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

        self.load_initial_values()

    def create_slider(self, layout, param):
        slider_layout = QHBoxLayout()
        slider_label = QLabel(f"{param} (%):", self)
        slider = QSlider(Qt.Horizontal, self)
        slider.setMinimum(10)
        slider.setMaximum(200)
        slider.setTickInterval(10)
        slider.setTickPosition(QSlider.TicksBelow)
        slider_value_label = QLabel(f"{getattr(self, f'{param.lower()}_slider_value')}%", self)
        slider.setValue(getattr(self, f'{param.lower()}_slider_value'))
        slider.valueChanged.connect(lambda value: self.update_slider_label(slider_value_label, value, param.lower()))

        avg_value_label = QLabel(self)
        self.update_avg_value_label(param.lower(), avg_value_label)

        slider_layout.addWidget(slider_label)
        slider_layout.addWidget(slider)
        slider_layout.addWidget(slider_value_label)
        slider_layout.addWidget(avg_value_label)

        if param.lower() == "lifetime":
            self.lifetime_slider = slider
            self.lifetime_slider_label = slider_value_label
            self.lifetime_avg_label = avg_value_label
        elif param.lower() == "restock":
            self.restock_slider = slider
            self.restock_slider_label = slider_value_label
            self.restock_avg_label = avg_value_label

        layout.addLayout(slider_layout)

    def create_edit_frame(self, param):
        frame = QFrame(self)
        frame.setFrameShape(QFrame.StyledPanel)
        frame.setLayout(QVBoxLayout())
        frame.layout().addWidget(QLabel(f"{param} edit", self))

        # Add existing elements
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        frame.layout().addWidget(scroll_area)

        content_widget = QWidget()
        content_layout = QVBoxLayout()
        content_widget.setLayout(content_layout)
        scroll_area.setWidget(content_widget)

        setattr(self, f"{param.lower()}_content_layout", content_layout)
        self.load_initial_elements(param, content_layout)

        # Add button and combo to add new elements
        add_layout = QHBoxLayout()
        add_button = QPushButton(f"Add {param}", self)
        add_combo = QComboBox(self)
        add_combo.addItems(getattr(self.xml_logic, f"{param.lower()}_options"))
        add_button.clicked.connect(lambda: self.onAddClicked(param, add_combo))
        add_layout.addWidget(add_button)
        add_layout.addWidget(add_combo)
        frame.layout().addLayout(add_layout)
        setattr(self, f"{param.lower()}_add_combo", add_combo)

        return frame

    def load_initial_elements(self, param, layout):
        selected_items = self.xml_logic.get_selected_items()
        all_elements = []
        for item in selected_items:
            elements = item.findall(param.lower())
            for element in elements:
                all_elements.append(element.get('name'))

        common_elements = set(all_elements)
        for element in all_elements:
            common_elements &= {element}

        for element in common_elements:
            self.add_element_layout(param, layout, element)

    def add_element_layout(self, param, layout, element_value):
        element_layout = QHBoxLayout()
        combo = QComboBox(self)
        combo.addItems(getattr(self.xml_logic, f"{param.lower()}_options"))
        combo.setCurrentText(element_value)
        combo.currentTextChanged.connect(lambda value, param=param, element_layout=element_layout: self.update_element_value(param, value, element_layout))
        remove_button = QPushButton("Remove", self)
        remove_button.clicked.connect(lambda: self.onRemoveClicked(param, element_value, element_layout))
        element_layout.addWidget(combo)
        element_layout.addWidget(remove_button)
        layout.addLayout(element_layout)
        return element_layout

    def update_element_value(self, param, value, layout):
        selected_items = self.xml_logic.get_selected_items()
        for item in selected_items:
            elements = item.findall(param.lower())
            for element in elements:
                if element.get('name') == value:
                    element.set('name', value)
                    print(f"Updated {param} element to value '{value}' for item '{item.get('name')}'")
                    self.xml_logic.viewer.update_item_in_list(item)

    def onAddClicked(self, param, combo):
        value = combo.currentText()
        selected_items = self.xml_logic.get_selected_items()
        content_layout = getattr(self, f"{param.lower()}_content_layout")
        added_elements = set()
        print(f"Trying to add {param} element with value '{value}' to selected items.")  # Debug info

        for item in selected_items:
            existing_elements = item.findall(param.lower())
            if not any(element.get('name') == value for element in existing_elements):
                ET.SubElement(item, param.lower(), name=value)
                added_elements.add(value)
                print(f"Added {param} element with value '{value}' to item '{item.get('name')}'")
                self.xml_logic.viewer.update_item_in_list(item)
            else:
                print(f"{param} element with value '{value}' already exists for item '{item.get('name')}'")

        if added_elements:
            self.add_element_layout(param, content_layout, value)

    def onRemoveClicked(self, param, value, layout):
        selected_items = self.xml_logic.get_selected_items()
        for item in selected_items:
            print(f"Processing item: {item.get('name')}")  # Debug info
            elements = item.findall(param.lower())
            for element in elements:
                if element.get('name') == value:
                    item.remove(element)
                    print(f"Removed {param} element with value '{value}' from item '{item.get('name')}'")
                    self.xml_logic.viewer.update_item_in_list(item)
        for i in reversed(range(layout.count())):
            widget = layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

    def update_slider_label(self, label, value, param):
        label.setText(f"{value}%")
        print(f"Slider {param.capitalize()} updated to {value}%")
        self.update_avg_value_label(param, getattr(self, f"{param}_avg_label"), value)

    def update_avg_value_label(self, param, label, slider_value=100):
        original_values = self.original_values[param]
        if original_values:
            total_value = sum(original_values)
            avg_value = total_value / len(original_values)
            adjusted_avg_value = avg_value * (slider_value / 100)
            adjusted_avg_value_minutes = adjusted_avg_value / 60
            label.setText(f"Avg: {adjusted_avg_value_minutes:.2f} min")

    def onMultiplierClicked(self):
        sender = self.sender()
        multiplier = 1
        if sender == self.multiplier_buttons['x10']:
            multiplier = 10
        elif sender == self.multiplier_buttons['x5']:
            multiplier = 5
        elif sender == self.multiplier_buttons['x2']:
            multiplier = 2
        elif sender == self.multiplier_buttons['div2']:
            multiplier = 0.5
        elif sender == self.multiplier_buttons['div5']:
            multiplier = 0.2
        elif sender == self.multiplier_buttons['div10']:
            multiplier = 0.1
        elif sender == self.multiplier_buttons['standard']:
            self.loadStandardValues()
            return

        self.xml_logic.saveCurrentItemDetails()  # Сохранить текущий объект перед массовыми изменениями

        for param in self.parameters:
            if self.checkboxes[param].isChecked() and not self.input_fields[param].text():
                for item in self.xml_logic.get_selected_items():
                    element = item.find(param)
                    if element is not None and element.text.isdigit():
                        current_value = int(element.text)
                        new_value = int(current_value * multiplier)
                        element.text = str(new_value)
                        self.xml_logic.viewer.update_item_in_list(item)

    def onInputChanged(self, param):
        self.checkboxes[param].setEnabled(not self.input_fields[param].text())

    def onOk(self):
        self.xml_logic.saveCurrentItemDetails()  # Сохранить текущий объект перед массовыми изменениями

        selected_items = self.xml_logic.get_selected_items()
        print(f"Selected items: {[item.get('name') for item in selected_items]}")  # Debug info

        for param in self.parameters:
            if self.input_fields[param].text():
                new_value = self.input_fields[param].text()
                for item in selected_items:
                    element = item.find(param)
                    if element is not None:
                        element.text = new_value
                    else:
                        element = ET.SubElement(item, param)
                        element.text = new_value
                    print(f"Set {param} to {new_value} for item '{item.get('name')}'")  # Debug info
                    self.xml_logic.viewer.update_item_in_list(item)

        # Apply category
        new_category = self.category_combo.currentText()
        for item in selected_items:
            category_element = item.find('category')
            if category_element is not None:
                category_element.set('name', new_category)
            else:
                ET.SubElement(item, 'category', name=new_category)
            print(f"Set category to {new_category} for item '{item.get('name')}'")  # Debug info
            self.xml_logic.viewer.update_item_in_list(item)

        # Apply Usage, Value, Tag
        self.apply_combo_values('usage', selected_items)
        self.apply_combo_values('value', selected_items)
        self.apply_combo_values('tag', selected_items)

        # Apply slider values
        self.apply_slider_value('lifetime', self.lifetime_slider.value())
        self.apply_slider_value('restock', self.restock_slider.value())

        # Save slider values
        self.lifetime_slider_value = self.lifetime_slider.value()
        self.restock_slider_value = self.restock_slider.value()
        print(f"Saving slider values: Lifetime: {self.lifetime_slider_value}%, Restock: {self.restock_slider_value}%")

        self.parent.lifetime_slider_value = self.lifetime_slider_value
        self.parent.restock_slider_value = self.restock_slider_value

        self.accept()
        self.xml_logic.viewer.loadXMLItems()  # Перезагрузить элементы XML

        # Восстановить последний активный элемент
        if selected_items:
            last_item_name = selected_items[-1].get('name')
            for index in range(self.xml_logic.viewer.list_widget.count()):
                list_item = self.xml_logic.viewer.list_widget.item(index)
                if list_item.text() == last_item_name:
                    self.xml_logic.viewer.list_widget.setCurrentItem(list_item)
                    self.xml_logic.viewer.displayItemDetails(list_item)
                    break

    def apply_combo_values(self, param, selected_items):
        combo = getattr(self, f"{param}_add_combo")
        value = combo.currentText()
        print(f"Applying {param} with value '{value}' to selected items.")  # Debug info
        if value:
            for item in selected_items:
                print(f"Processing item: {item.get('name')}")  # Debug info
                existing_elements = item.findall(param.lower())
                if not any(element.get('name') == value for element in existing_elements):
                    ET.SubElement(item, param.lower(), name=value)
                    print(f"Added new {param} element with value '{value}' to item '{item.get('name')}'")
                    self.xml_logic.viewer.update_item_in_list(item)
                else:
                    print(f"{param} element with value '{value}' already exists for item '{item.get('name')}'")

    def onCancel(self):
        self.reject()

    def apply_slider_value(self, param, slider_value):
        selected_items = self.xml_logic.get_selected_items()
        if len(self.original_values[param]) != len(selected_items):
            QMessageBox.critical(self, "Error", "The number of original values does not match the number of selected items.")
            return
        for index, item in enumerate(selected_items):
            element = item.find(param)
            if element is not None and element.text.isdigit():
                try:
                    original_value = self.original_values[param][index]
                    new_value = int(original_value * (slider_value / 100))
                    element.text = str(new_value)
                    self.xml_logic.viewer.update_item_in_list(item)
                except IndexError as e:
                    print(f"IndexError: {e}. Index: {index}, Param: {param}, Selected Items: {len(selected_items)}, Original Values: {len(self.original_values[param])}")
                    QMessageBox.critical(self, "Error", f"IndexError: {e}. Check the console for more details.")
                    return

    def loadStandardValues(self):
        config_file = os.path.join('Config', 'default_config.xml')
        if os.path.exists(config_file):
            tree = ET.parse(config_file)
            root = tree.getroot()
            for param in self.parameters:
                standard_value = root.find(param).text
                for item in self.xml_logic.get_selected_items():
                    element = item.find(param)
                    if element is not None:
                        element.text = standard_value
                        self.xml_logic.viewer.update_item_in_list(item)

    def load_slider_values(self):
        self.lifetime_slider.setValue(self.lifetime_slider_value)
        self.lifetime_slider_label.setText(f"{self.lifetime_slider_value}%")
        self.restock_slider.setValue(self.restock_slider_value)
        self.restock_slider_label.setText(f"{self.restock_slider_value}%")
        print(f"Loading slider values: Lifetime: {self.lifetime_slider_value}%, Restock: {self.restock_slider_value}%")

    def showEvent(self, event):
        super().showEvent(event)
        self.load_slider_values()

    def closeEvent(self, event):
        super().closeEvent(event)
        self.lifetime_slider_value = self.lifetime_slider.value()
        self.restock_slider_value = self.restock_slider.value()
        print(f"Closing dialog. Current slider values: Lifetime: {self.lifetime_slider_value}%, Restock: {self.restock_slider_value}%")

    def get_initial_values(self, param):
        selected_items = self.xml_logic.get_selected_items()
        initial_values = []
        for item in selected_items:
            element = item.find(param)
            if element is not None and element.text.isdigit():
                initial_values.append(int(element.text))
        return initial_values

    def load_initial_values(self):
        selected_items = self.xml_logic.get_selected_items()
        self.load_initial_combo_value('usage', selected_items)
        self.load_initial_combo_value('value', selected_items)
        self.load_initial_combo_value('tag', selected_items)

    def load_initial_combo_value(self, param, selected_items):
        values = set()
        for item in selected_items:
            elements = item.findall(param.lower())
            for element in elements:
                values.add(element.get('name'))

        combo = getattr(self, f"{param.lower()}_add_combo")
        if len(values) == 1:
            combo.setCurrentText(next(iter(values)))
        else:
            combo.setCurrentIndex(-1)  # No selection
