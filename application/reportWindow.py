import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QDialog
import os
from PyQt6.QtCore import Qt

from application.classes import colors, class_names, class_names_full


class ReportWindow(QDialog):
    def __init__(self, report, parent=None):
        super().__init__(parent)
        self.report = report
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Отчёт")
        self.resize(438, 800)

        layout = QVBoxLayout()
        self.table = QTableWidget()
        layout.addWidget(self.table)
        self.setLayout(layout)

        self.populate_table()
        self.set_table_alignment()

    def populate_table(self):
        unique_files = list(self.report.keys())
        rows = sum(len(self.report[file]['bbox']) for file in unique_files)

        self.table.setRowCount(rows)
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(['Имя файла', 'Класс дефекта', 'x', 'y', 'w', 'h', ])

        row = 0
        for file_path, data in self.report.items():
            bboxes = data['bbox']
            labels = data['class']
            file_name = os.path.basename(file_path)

            for i in range(len(bboxes)):
                if i == 0:
                    self.table.setItem(row, 0, QTableWidgetItem(file_name))
                    self.table.setSpan(row, 0, len(bboxes), 1)

                bbox = bboxes[i]
                x_item = QTableWidgetItem(str(round(bbox[0])))
                y_item = QTableWidgetItem(str(round(bbox[1])))
                w_item = QTableWidgetItem(str(round(bbox[2])))
                h_item = QTableWidgetItem(str(round(bbox[3])))
                class_item = QTableWidgetItem(class_names_full[class_names[str(int(labels[i]))]])

                self.table.setItem(row, 1, class_item)
                self.table.setItem(row, 2, x_item)
                self.table.setItem(row, 3, y_item)
                self.table.setItem(row, 4, w_item)
                self.table.setItem(row, 5, h_item)

                row += 1

        self.table.resizeColumnsToContents()

    def set_table_alignment(self):
        for row in range(self.table.rowCount()):
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item:
                    item.setTextAlignment(0x0004 | 0x0080)


