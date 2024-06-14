import sys
import os
import json
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QSize, QRect
from PyQt6.QtGui import QIcon, QPixmap, QAction, QPainter, QPen, QColor
from PIL import Image
from PIL.ImageQt import ImageQt

import random


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.auto_detecting = False
        self.report = {}
        self.image_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.gif')

        self.setWindowTitle("Defect Detector")
        self.setGeometry(100, 100, 800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QGridLayout(central_widget)

        # --------------------------------------------------------------------------------------------------------------#
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("&Файл")
        file_menu_open_file = file_menu.addAction("Добавить файлы")
        file_menu_open_folder = file_menu.addAction("Добавить папку")
        file_menu.addSeparator()
        file_menu_clear = file_menu.addAction("Очистить список")

        file_menu_open_file.triggered.connect(self.open_file)
        file_menu_open_folder.triggered.connect(self.open_folder)
        file_menu_clear.triggered.connect(self.clear_list)

        # --------------------------------------------------------------------------------------------------------------#
        detect_menu = menu_bar.addMenu("&Детектирование")
        detect_menu_image_detect = detect_menu.addAction("Выполнить детекцию на изображении")
        detect_menu_all_image_detect = detect_menu.addAction("Выполнить детекцию на всех изображениях")
        detect_menu.addSeparator()
        detect_menu_auto_detect = detect_menu.addAction(QIcon(r'D:\Education\hackaton\application\static\icon2.png'),
                                                        "Включить автоматическое детектирование")

        detect_menu_image_detect.triggered.connect(self.inference_one)
        detect_menu_all_image_detect.triggered.connect(self.inference_all)
        detect_menu_auto_detect.triggered.connect(self.switch)

        # --------------------------------------------------------------------------------------------------------------#
        report_menu = menu_bar.addMenu("&Отчёт")
        report_menu_make_report = report_menu.addAction("Создать отчёт")
        report_menu_edit_report = report_menu.addAction("Редактировать отчёт")
        report_menu_load_report = report_menu.addAction("Загрузить отчёт")

        report_menu_make_report.triggered.connect(self.make_report)
        # report_menu_edit_report.triggered.connect(self.edit_report)
        report_menu_load_report.triggered.connect(self.load_report)

        # --------------------------------------------------------------------------------------------------------------#
        about_menu = menu_bar.addMenu("&About")

        # about_menu.triggered.connect(self.about)

        # --------------------------------------------------------------------------------------------------------------#
        self.center_label = QLabel()
        self.center_label.setStyleSheet("border: 1px solid black;")
        self.center_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.center_label.setFixedSize(600, 400)  # Fixing the size of the QLabel

        # --------------------------------------------------------------------------------------------------------------#
        self.list_widget = QListWidget()
        self.list_widget.setIconSize(QSize(146, 100))
        self.list_widget.setMinimumWidth(175)
        self.list_widget.itemClicked.connect(self.display_image)
        # self.list_widget.item.connect(self.display_image)

        # --------------------------------------------------------------------------------------------------------------#
        self.bottom_label = QLabel("")
        self.bottom_label.setStyleSheet("border: 1px solid black;")

        # --------------------------------------------------------------------------------------------------------------#
        main_layout.addWidget(self.center_label, 1, 0, 1, 1)
        main_layout.addWidget(self.list_widget, 1, 1, 2, 1)
        main_layout.addWidget(self.bottom_label, 2, 0, 1, 1)

        main_layout.setRowStretch(0, 0)
        main_layout.setRowStretch(1, 1)
        main_layout.setRowStretch(2, 0)
        main_layout.setColumnStretch(0, 3)
        main_layout.setColumnStretch(1, 1)

    # ------------------------------------------------------------------------------------------------------------------#
    def open_file(self):
        files, _ = QFileDialog.getOpenFileNames(self,
                                                "Выберите файлы", "", "(*.png *.jpg *.jpeg *.bmp *.gif)")

        if files:
            progress_dialog = create_progress(len(files), self)
            for idx, file_path in enumerate(files):
                self.add_image_to_list(file_path)
                progress_dialog.setValue(idx + 1)
                if progress_dialog.wasCanceled():
                    break

            item = self.list_widget.item(0)
            if item:
                self.display_image(item)

    def open_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Выберите папку")
        if folder_path:
            self.list_widget.clear()
            progress_dialog = create_progress(len(os.listdir(folder_path)), self)
            for idx, file_name in enumerate(os.listdir(folder_path)):
                if file_name.lower().endswith(self.image_extensions):
                    file_path = os.path.join(folder_path, file_name)
                    self.add_image_to_list(file_path)

                progress_dialog.setValue(idx + 1)
                if progress_dialog.wasCanceled():
                    break

            item = self.list_widget.item(0)
            if item:
                self.display_image(item)

    def clear_list(self):
        self.list_widget.clear()
        self.report = {}
        pixmap = QPixmap('./static/templet.jpg')
        self.center_label.setPixmap(pixmap.scaled(self.center_label.size(), Qt.AspectRatioMode.KeepAspectRatio,
                                                  Qt.TransformationMode.SmoothTransformation))

    # ------------------------------------------------------------------------------------------------------------------#
    def inference_one(self, file_path=None):
        if not file_path:
            file_path = self.list_widget.currentItem().data(Qt.ItemDataRole.UserRole)

        # output = INFERENCE FUNCTION(file_path)
        # self.report |= output

        bbox = [random.randint(0, 400) for _ in range(4)]
        self.report |= {file_path: [{'bbox': bbox, 'class': 'Defect'}]}

        item = self.list_widget.currentItem()
        if item:
            self.change_image_in_list(item)
            self.display_image(item)

    def inference_all(self):
        # Вытащить все пути до изображений из self.list_widget
        try:
            file_paths = self.list_widget.selectedItems()
            print(file_paths)

            for file_path in file_paths:
                self.inference_one(file_path)

            # INFERENCE FUNCTION(file_path)

        except AttributeError:
            print('No files found')

    def switch(self):
        self.auto_detecting = False if self.auto_detecting else True

        if self.auto_detecting:
            print("Automatic detecting is active")
            item = self.list_widget.currentItem()
            if item:
                self.display_image(item)

        else:
            print("Automatic detecting is inactive")

    # ------------------------------------------------------------------------------------------------------------------#
    def make_report(self):
        print(self.report)
        path, _ = QFileDialog.getSaveFileName(self, "Save Database", '', "Database Files (*.json);;All Files (*)")
        if path:
            with open(path, 'w') as file:
                json.dump(self.report, file)

    def edit_report(self):
        pass

    def load_report(self):
        path, _ = QFileDialog.getOpenFileName(self, "Save Database", '', "Database Files (*.json);;All Files (*)")
        if path:
            with open(path, 'r') as file:
                self.report = json.load(file)

    # ------------------------------------------------------------------------------------------------------------------#
    def add_image_to_list(self, file_path):
        pixmap = QPixmap(file_path).scaled(180, 120, Qt.AspectRatioMode.KeepAspectRatio,
                                           Qt.TransformationMode.SmoothTransformation)

        item = QListWidgetItem(QIcon(pixmap), os.path.basename(file_path))
        item.setData(Qt.ItemDataRole.UserRole, file_path)
        self.list_widget.addItem(item)

    def change_image_in_list(self, item):
        file_path = item.data(Qt.ItemDataRole.UserRole)

        pixmap = QPixmap(file_path).scaled(180, 120, Qt.AspectRatioMode.KeepAspectRatio,
                                           Qt.TransformationMode.SmoothTransformation)

        painter = QPainter(pixmap)
        pen = QPen(QColor(255, 255, 0), 5)
        painter.setPen(pen)
        painter.drawRect(QRect(0, 0, 90, 60))
        # painter.drawPoint((90, 60), 20)
        painter.end()

        item_changed = QListWidgetItem(QIcon(pixmap), os.path.basename(file_path))
        item_changed.setData(Qt.ItemDataRole.UserRole, file_path)

        print(type(self.list_widget))
        # self.list_widget.ed(item_changed)

    def display_image(self, item):
        file_path = item.data(Qt.ItemDataRole.UserRole)

        if file_path in self.report.keys():
            self.draw_bbox_on_image(file_path)
        else:
            if self.auto_detecting:
                self.inference_one()
            else:
                pixmap = QPixmap(file_path)
                self.center_label.setPixmap(pixmap.scaled(self.center_label.size(), Qt.AspectRatioMode.KeepAspectRatio,
                                                          Qt.TransformationMode.SmoothTransformation))
        print('working')
        try:
            defects = self.report[file_path]
        except KeyError:
            defects = "Дефекты не обнаружены или ещё не было запущено детектирование"
        self.bottom_label.setText(f"Имя файла: {file_path}\nОбнаруженные дефекты: {defects}")

    def draw_bbox_on_image(self, file_path):
        pixmap = QPixmap(file_path)

        painter = QPainter(pixmap)
        pen = QPen(QColor(255, 255, 0), 5)
        painter.setPen(pen)

        for obj in self.report[file_path]:
            bbox, class_name = obj['bbox'], obj['class']
            painter.drawRect(QRect(*bbox))
            # painter.drawText(bbox[0], bbox[1] - 10, class_name)  # Текст немного выше bbox
        painter.end()

        self.center_label.setPixmap(pixmap.scaled(self.center_label.size(), Qt.AspectRatioMode.KeepAspectRatio,
                                                  Qt.TransformationMode.SmoothTransformation))

    # ------------------------------------------------------------------------------------------------------------------#


def create_progress(amount, parent):
    progress_dialog = QProgressDialog("Загрузка изображений...", "Отменить", 0, amount, parent)
    progress_dialog.setWindowTitle("Загрузка")
    progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
    progress_dialog.setMinimumDuration(0)

    return progress_dialog
