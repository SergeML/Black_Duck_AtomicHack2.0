import sys
from PyQt6.QtWidgets import QApplication

from mainWindow import MainWindow


if __name__ == '__main__':
    app = QApplication(sys.argv)

    main_window = MainWindow()
    main_window.show()

    result = app.exec()
    sys.exit(result)
