from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QCheckBox, QSlider, QComboBox, QScrollArea, QFrame, QMessageBox, QWidget, QProgressBar
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
import os
import xml.etree.ElementTree as ET

class LoadDataThread(QThread):
    data_loaded = pyqtSignal(dict)
    progress = pyqtSignal(int)  # Add a signal for progress

    def __init__(self, xml_logic, parameters):
        super().__init__()
        self.xml_logic = xml_logic
        self.parameters = parameters

    def run(self):
        initial_values = {}
        total_items = len(self.xml_logic.get_selected_items())
        processed_items = 0

        for param in self.parameters:
            initial_values[param] = self._get_initial_values(param)
            processed_items += 1
            progress = int((processed_items / total_items) * 100)
            self.progress.emit(progress)  # Emit progress

        self.data_loaded.emit(initial_values)

    def _get_initial_values(self, param):
        selected_items = self.xml_logic.get_selected_items()
        initial_values = [int(item.find(param).text) for item in selected_items if item.find(param) is not None and item.find(param).text.isdigit()]
        return initial_values

class MassEditDialog(QDialog):
    def __init__(self, xml_logic, parent=None):
        super().__init__(parent)
        self.xml_logic = xml_logic
        self.parent = parent
        self.initial_values = {}
        self.parameters = ['nominal', 'min', 'lifetime', 'restock']
        self.lifetime_slider_value = parent.lifetime_slider_value
        self.restock_slider_value = parent.restock_slider_value

        self.initUI()
        self.load_initial_values()

    def initUI(self):
        self.setWindowTitle("Mass Edit")
        self.setGeometry(100, 100, 400, 600)

        layout = QVBoxLayout()
        layout.addLayout(self.create_action_buttons())
        layout.addLayout(self.create_multiplier_buttons())
        layout.addLayout(self.create_param_inputs())
        layout.addLayout(self.create_category_selector())
        layout.addLayout(self.create_sliders())
        layout.addWidget(self.create_edit_frame("Usage"))
        layout.addWidget(self.create_edit_frame("Value"))
        layout.addWidget(self.create_edit_frame("Tag"))

        # Add progress bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        self.setLayout(layout)

    def load_initial_values(self):
        self.thread = LoadDataThread(self.xml_logic, self.parameters)
        self.thread.data_loaded.connect(self.on_data_loaded)
        self.thread.progress.connect(self.update_progress_bar)  # Connect the progress signal
        self.thread.start()

    def update_progress_bar(self, progress):
        self.progress_bar.setValue(progress)

    def on_data_loaded(self, initial_values):
        self.initial_values = initial_values
        self.load_slider_values()

    def load_slider_values(self):
        self.lifetime_slider.setValue(self.lifetime_slider_value)
        self.lifetime_slider_label.setText(f"{self.lifetime_slider_value}%")
        self.restock_slider.setValue(self.restock_slider_value)
        self.restock_slider_label.setText(f"{self.restock_slider_value}%")
        print(f"Loading slider values: Lifetime: {self.lifetime_slider_value}%, Restock: {self.restock_slider_value}%")

    def create_multiplier_buttons(self):
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
        button = QPushButton(text, self)
        button.setIcon(QIcon(os.path.join('icons', icon)))
        button.clicked.connect(self.onMultiplierClicked)
        return button

    def create_param_inputs(self):
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
        category_layout = QHBoxLayout()
        self.category_checkbox = QCheckBox("Category", self)
        self.category_combo = QComboBox(self)
        self.category_combo.addItems(self.xml_logic.category_options)
        category_layout.addWidget(self.category_checkbox)
        category_layout.addWidget(self.category_combo)
        return category_layout

    def create_sliders(self):
        slider_layout = QVBoxLayout()
        slider_layout.addLayout(self.create_slider("Lifetime"))
        slider_layout.addLayout(self.create_slider("Restock"))
        return slider_layout

    def create_slider(self, param):
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
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK", self)
        ok_button.clicked.connect(self.onOk)
        button_layout.addWidget(ok_button)

        cancel_button = QPushButton("Cancel", self)
        cancel_button.clicked.connect(self.onCancel)
        button_layout.addWidget(cancel_button)
        return button_layout

    def load_initial_elements(self, param, layout):
        selected_items = self.xml_logic.get_selected_items()
        all_elements = [element.get('name') for item in selected_items for element in item.findall(param.lower())]
        common_elements = set(all_elements)

        for element in common_elements:
            self.add_element_layout(param, layout, element)

    def add_element_layout(self, param, layout, element_value):
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
        selected_items = self.xml_logic.get_selected_items()
        for item in selected_items:
            elements = item.findall(param.lower())
            for element in elements:
                if element.get('name') == value:
                    element.set('name', value)
                    print(f"Updated {param} element to value '{value}' for item '{item.get('name')}'")
                    self.xml_logic.viewer.update_item_in_list(item.get('name'))

    def onAddClicked(self, param, combo):
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
        label.setText(f"{value}%")
        print(f"Slider {param.capitalize()} updated to {value}%")
        self.update_avg_value_label(param, getattr(self, f"{param}_avg_label"), value)
        self.apply_slider_value(param, value)  # Применяем значение сразу

    def update_avg_value_label(self, param, label, slider_value=100):
        initial_values = self.initial_values.get(param, [])
        if initial_values:
            total_value = sum(initial_values)
            avg_value = total_value / len(initial_values)
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
        if self.input_fields[param].text():
            self.apply_input_value(param, self.input_fields[param].text())
        self.checkboxes[param].setEnabled(not self.input_fields[param].text())

    def onOk(self):
        self.accept()

    def onCancel(self):
        self.reject()

    def apply_slider_value(self, param, slider_value):
        selected_items = self.xml_logic.get_selected_items()
        if len(self.initial_values[param]) != len(selected_items):
            QMessageBox.critical(self, "Error", "The number of original values does not match the number of selected items.")
            return
        for index, item in enumerate(selected_items):
            element = item.find(param)
            if element is not None and element.text.isdigit():
                try:
                    original_value = self.initial_values[param][index]
                    new_value = int(original_value * (slider_value / 100))
                    element.text = str(new_value)
                    print(f"Set {param} to {new_value} for item '{item.get('name')}' using slider value {slider_value}%")
                    self.xml_logic.viewer.update_item_in_list(item.get('name'))
                    self.force_refresh_active_item()  # Принудительно обновляем активный элемент
                except IndexError as e:
                    print(f"IndexError: {e}. Index: {index}, Param: {param}, Selected Items: {len(selected_items)}, Initial Values: {len(self.initial_values[param])}")
                    QMessageBox.critical(self, "Error", f"IndexError: {e}. Check the console for more details.")
                    return

    def apply_combo_values(self, param, selected_items):
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
        for param in self.parameters:
            if self.checkboxes[param].isChecked():
                selected_items = self.xml_logic.get_selected_items()
                for item in selected_items:
                    item_name = item.get('name')
                    original_value = self.xml_logic.initial_values.get(item_name, {}).get(param, '')
                    element = item.find(param)
                    if element is not None:
                        element.text = original_value
                    else:
                        element = ET.SubElement(item, param)
                        element.text = original_value
                    print(f"Restored {param} to {original_value} for item '{item.get('name')}'")
                self.force_refresh_active_item()  # Принудительно обновляем активный элемент

    def force_refresh_active_item(self):
        self.parent.xml_logic.saveCurrentItemDetails()
        self.parent.force_update_active_item()
