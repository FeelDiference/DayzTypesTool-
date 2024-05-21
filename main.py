import sys
from PyQt5.QtWidgets import QApplication
from ui import XMLViewer
from qt_material import apply_stylesheet
import qtawesome as qta  # Импортируем библиотеку QtAwesome
from PyQt5.QtGui import QFont

if __name__ == '__main__':
    app = QApplication(sys.argv)
    viewer = XMLViewer()
    apply_stylesheet(app, theme='light_amber.xml')
    font = QFont("Source Sans Pro", 8)  # Уменьшаем размер шрифта
    app.setFont(font)
    viewer.show()
    sys.exit(app.exec_())
