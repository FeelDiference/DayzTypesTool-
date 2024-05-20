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
        """Initializes the UI components."""
        self.setWindowTitle("Mass Edit")
        self.setGeometry(100, 100, 400, 600)

        layout = QVBoxLayout()
        layout.addLayout(self.create_action_buttons())  # Переместили кнопки OK/Cancel наверх
        layout.addLayout(self.create_multiplier_buttons())
        layout.addLayout(self.create_param_inputs())
        layout.addLayout(self.create_category_selector())
        layout.addLayout(self.create_sliders())
        layout.addWidget(self.create_edit_frame("Usage"))
        layout.addWidget(self.create_edit_frame("Value"))
        layout.addWidget(self.create_edit_frame("Tag"))

        self.setLayout(layout)
        self.load_initial_values()

    def create_multiplier_buttons(self):
        """Creates and returns the layout for multiplier buttons."""
        multiplier_layout = QHBoxLayout()
        self.multiplier_buttons = {
            'x10': self.create_button("X10", "x10.png"),
            'x5': self.create_button("X5", "x5.png"),
            'x2': self.create_button("X2", "x2.png"),
            'standard': self.create_button("Standard", "standard.png"),
            'div2': self.create_button("/2", "div2.png"),
            'div5': self.create_button("/5", "div5.png"),
            'div10': self.create_button("/10", "div10.png")
        }
        for button in self.multiplier_buttons.values():
            multiplier_layout.addWidget(button)
        return multiplier_layout

    def create_button(self, text, icon):
        """Creates and returns a QPushButton with given text and icon."""
        button = QPushButton(text, self)
        button.setIcon(QIcon(os.path.join('icons', icon)))
        button.clicked.connect(self.onMultiplierClicked)
        return button

    def create_param_inputs(self):
        """Creates and returns the layout for parameter inputs."""
        param_layout = QVBoxLayout()
        self.parameters = ['nominal', 'min', 'lifetime', 'restock']
        self.checkboxes = {}
        self.input_fields = {}

        for param in self.parameters:
            layout = QHBoxLayout()
            checkbox = QCheckBox(param.capitalize(), self)
            self.checkboxes[param] = checkbox
            layout.addWidget(checkbox)

            input_field = QLineEdit(self)
            input_field.setPlaceholderText("Enter value manually")
            input_field.textChanged.connect(lambda text, p=param: self.onInputChanged(p))
            self.input_fields[param] = input_field
            layout.addWidget(input_field)

            param_layout.addLayout(layout)
        return param_layout

    def create_category_selector(self):
        """Creates and returns the layout for category selector."""
        category_layout = QHBoxLayout()
        self.category_checkbox = QCheckBox("Category", self)
        self.category_combo = QComboBox(self)
        self.category_combo.addItems(self.xml_logic.category_options)
        category_layout.addWidget(self.category_checkbox)
        category_layout.addWidget(self.category_combo)
        return category_layout

    def create_sliders(self):
        """Creates and returns the layout for sliders."""
        slider_layout = QVBoxLayout()
        slider_layout.addLayout(self.create_slider("Lifetime"))
        slider_layout.addLayout(self.create_slider("Restock"))
        return slider_layout

    def create_slider(self, param):
        """Creates and returns a slider layout for the given parameter."""
        layout = QHBoxLayout()
        label = QLabel(f"{param} (%):", self)
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

        layout.addWidget(label)
        layout.addWidget(slider)
        layout.addWidget(slider_value_label)
        layout.addWidget(avg_value_label)

        if param.lower() == "lifetime":
            self.lifetime_slider = slider
            self.lifetime_slider_label = slider_value_label
            self.lifetime_avg_label = avg_value_label
        elif param.lower() == "restock":
            self.restock_slider = slider
            self.restock_slider_label = slider_value_label
            self.restock_avg_label = avg_value_label

        return layout

    def create_edit_frame(self, param):
        """Creates and returns an edit frame for the given parameter."""
        frame = QFrame(self)
        frame.setFrameShape(QFrame.StyledPanel)
        layout = QVBoxLayout()
        frame.setLayout(layout)
        layout.addWidget(QLabel(f"{param} edit", self))

        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)

        content_widget = QWidget()
        content_layout = QVBoxLayout()
        content_widget.setLayout(content_layout)
        scroll_area.setWidget(content_widget)

        setattr(self, f"{param.lower()}_content_layout", content_layout)
        self.load_initial_elements(param, content_layout)

        add_layout = QHBoxLayout()
        add_button = QPushButton(f"Add {param}", self)
        add_combo = QComboBox(self)
        add_combo.addItems(getattr(self.xml_logic, f"{param.lower()}_options"))
        add_button.clicked.connect(lambda: self.onAddClicked(param, add_combo))
        add_layout.addWidget(add_button)
        add_layout.addWidget(add_combo)
        layout.addLayout(add_layout)
        setattr(self, f"{param.lower()}_add_combo", add_combo)

        return frame

    def create_action_buttons(self):
        """Creates and returns the layout for action buttons."""
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK", self)
        ok_button.clicked.connect(self.onOk)
        button_layout.addWidget(ok_button)

        cancel_button = QPushButton("Cancel", self)
        cancel_button.clicked.connect(self.onCancel)
        button_layout.addWidget(cancel_button)
        return button_layout

    def load_initial_elements(self, param, layout):
        """Loads initial elements for the given parameter into the layout."""
        selected_items = self.xml_logic.get_selected_items()
        all_elements = [element.get('name') for item in selected_items for element in item.findall(param.lower())]
        common_elements = set(all_elements)

        for element in common_elements:
            self.add_element_layout(param, layout, element)

    def add_element_layout(self, param, layout, element_value):
        """Adds a layout for an element with the given value."""
        element_layout = QHBoxLayout()
        combo = QComboBox(self)
        combo.addItems(getattr(self.xml_logic, f"{param.lower()}_options"))
        combo.setCurrentText(element_value)
        combo.currentTextChanged.connect(lambda value, p=param, el=element_layout: self.update_element_value(p, value, el))
        remove_button = QPushButton("Remove", self)
        remove_button.clicked.connect(lambda: self.onRemoveClicked(param, element_value, element_layout))
        element_layout.addWidget(combo)
        element_layout.addWidget(remove_button)
        layout.addLayout(element_layout)
        return element_layout

    def update_element_value(self, param, value, layout):
        """Updates the value of an element."""
        selected_items = self.xml_logic.get_selected_items()
        for item in selected_items:
            elements = item.findall(param.lower())
            for element in elements:
                if element.get('name') == value:
                    element.set('name', value)
                    print(f"Updated {param} element to value '{value}' for item '{item.get('name')}'")
                    self.xml_logic.viewer.update_item_in_list(item.get('name'))

    def onAddClicked(self, param, combo):
        """Handles the add button click for a parameter."""
        value = combo.currentText()
        selected_items = self.xml_logic.get_selected_items()
        content_layout = getattr(self, f"{param.lower()}_content_layout")
        added_elements = set()

        for item in selected_items:
            existing_elements = item.findall(param.lower())
            if not any(element.get('name') == value for element in existing_elements):
                ET.SubElement(item, param.lower(), name=value)
                added_elements.add(value)
                print(f"Added {param} element with value '{value}' to item '{item.get('name')}'")
                self.xml_logic.viewer.update_item_in_list(item.get('name'))
            else:
                print(f"{param} element with value '{value}' already exists for item '{item.get('name')}'")

        if added_elements:
            self.add_element_layout(param, content_layout, value)
            self.force_refresh_active_item()  # Принудительно обновляем активный элемент

    def onRemoveClicked(self, param, value, layout):
        """Handles the remove button click for a parameter."""
        selected_items = self.xml_logic.get_selected_items()
        for item in selected_items:
            elements = item.findall(param.lower())
            for element in elements:
                if element.get('name') == value:
                    item.remove(element)
                    print(f"Removed {param} element with value '{value}' from item '{item.get('name')}'")
                    self.xml_logic.viewer.update_item_in_list(item.get('name'))
        for i in reversed(range(layout.count())):
            widget = layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        self.force_refresh_active_item()  # Принудительно обновляем активный элемент

    def update_slider_label(self, label, value, param):
        """Updates the label for a slider."""
        label.setText(f"{value}%")
        print(f"Slider {param.capitalize()} updated to {value}%")
        self.update_avg_value_label(param, getattr(self, f"{param}_avg_label"), value)
        self.apply_slider_value(param, value)  # Применяем значение сразу

    def update_avg_value_label(self, param, label, slider_value=100):
        """Updates the average value label for a parameter."""
        original_values = self.original_values[param]
        if original_values:
            total_value = sum(original_values)
            avg_value = total_value / len(original_values)
            adjusted_avg_value = avg_value * (slider_value / 100)
            adjusted_avg_value_minutes = adjusted_avg_value / 60
            label.setText(f"Avg: {adjusted_avg_value_minutes:.2f} min")

    def onMultiplierClicked(self):
        """Handles multiplier button clicks."""
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

        for param in self.parameters:
            if self.checkboxes[param].isChecked() and not self.input_fields[param].text():
                for item in self.xml_logic.get_selected_items():
                    element = item.find(param)
                    if element is not None and element.text.isdigit():
                        current_value = int(element.text)
                        new_value = int(current_value * multiplier)
                        element.text = str(new_value)
                        print(f"Set {param} to {new_value} for item '{item.get('name')}' using multiplier {multiplier}")
                        self.xml_logic.viewer.update_item_in_list(item.get('name'))
                        self.force_refresh_active_item()  # Принудительно обновляем активный элемент

    def onInputChanged(self, param):
        """Handles input field text changes."""
        if self.input_fields[param].text():
            self.apply_input_value(param, self.input_fields[param].text())
        self.checkboxes[param].setEnabled(not self.input_fields[param].text())

    def onOk(self):
        """Handles OK button click."""
        # Сразу применяем все изменения
        self.accept()

    def onCancel(self):
        """Handles Cancel button click."""
        self.reject()

    def apply_slider_value(self, param, slider_value):
        """Applies the value from the slider to the selected items."""
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
                    print(f"Set {param} to {new_value} for item '{item.get('name')}' using slider value {slider_value}%")
                    self.xml_logic.viewer.update_item_in_list(item.get('name'))
                    self.force_refresh_active_item()  # Принудительно обновляем активный элемент
                except IndexError as e:
                    print(f"IndexError: {e}. Index: {index}, Param: {param}, Selected Items: {len(selected_items)}, Original Values: {len(self.original_values[param])}")
                    QMessageBox.critical(self, "Error", f"IndexError: {e}. Check the console for more details.")
                    return

    def apply_combo_values(self, param, selected_items):
        """Applies combo box values to the selected items."""
        combo = getattr(self, f"{param}_add_combo")
        value = combo.currentText()
        if value:
            for item in selected_items:
                existing_elements = item.findall(param.lower())
                if not any(element.get('name') == value for element in existing_elements):
                    ET.SubElement(item, param.lower(), name=value)
                    print(f"Added new {param} element with value '{value}' to item '{item.get('name')}'")
                    self.xml_logic.viewer.update_item_in_list(item.get('name'))
                    self.force_refresh_active_item()  # Принудительно обновляем активный элемент

    def apply_input_value(self, param, value):
        """Applies the input value to the selected items."""
        selected_items = self.xml_logic.get_selected_items()
        for item in selected_items:
            element = item.find(param)
            if element is not None:
                element.text = value
            else:
                element = ET.SubElement(item, param)
                element.text = value
            print(f"Set {param} to {value} for item '{item.get('name')}'")
            self.xml_logic.viewer.update_item_in_list(item.get('name'))
            self.force_refresh_active_item()  # Принудительно обновляем активный элемент

    def loadStandardValues(self):
        """Loads standard values from the configuration file."""
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
                        print(f"Set {param} to standard value {standard_value} for item '{item.get('name')}'")
                        self.xml_logic.viewer.update_item_in_list(item.get('name'))
                        self.force_refresh_active_item()  # Принудительно обновляем активный элемент

    def load_initial_values(self):
        """Loads initial values for combo boxes."""
        selected_items = self.xml_logic.get_selected_items()
        self.load_initial_combo_value('usage', selected_items)
        self.load_initial_combo_value('value', selected_items)
        self.load_initial_combo_value('tag', selected_items)

    def load_initial_combo_value(self, param, selected_items):
        """Loads initial combo box values for the given parameter."""
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

    def load_slider_values(self):
        """Loads the slider values."""
        self.lifetime_slider.setValue(self.lifetime_slider_value)
        self.lifetime_slider_label.setText(f"{self.lifetime_slider_value}%")
        self.restock_slider.setValue(self.restock_slider_value)
        self.restock_slider_label.setText(f"{self.restock_slider_value}%")
        print(f"Loading slider values: Lifetime: {self.lifetime_slider_value}%, Restock: {self.restock_slider_value}%")

    def showEvent(self, event):
        """Handles the show event."""
        super().showEvent(event)
        self.load_slider_values()

    def closeEvent(self, event):
        """Handles the close event."""
        super().closeEvent(event)
        self.lifetime_slider_value = self.lifetime_slider.value()
        self.restock_slider_value = self.restock_slider.value()
        print(f"Closing dialog. Current slider values: Lifetime: {self.lifetime_slider_value}%, Restock: {self.restock_slider_value}%")

    def get_initial_values(self, param):
        """Gets the initial values for the given parameter."""
        selected_items = self.xml_logic.get_selected_items()
        initial_values = [int(item.find(param).text) for item in selected_items if item.find(param) is not None and item.find(param).text.isdigit()]
        return initial_values

    def force_refresh_active_item(self):
        """Forces a refresh of the active item."""
        self.parent.xml_logic.saveCurrentItemDetails()
        self.parent.force_update_active_item()
