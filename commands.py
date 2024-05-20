from PyQt5.QtWidgets import QUndoCommand, QLineEdit, QComboBox, QTextEdit, QCheckBox

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
