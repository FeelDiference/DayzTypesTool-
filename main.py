import sys
from PyQt5.QtWidgets import QApplication
from ui import XMLViewer

if __name__ == '__main__':
    app = QApplication(sys.argv)
    viewer = XMLViewer()
    viewer.show()
    sys.exit(app.exec_())
