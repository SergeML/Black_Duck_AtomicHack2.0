import os
import csv
import cv2
import json

import pyodbc

from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QSize, QRect
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QPen, QColor, QFont, QBrush
from ultralytics import YOLO

from model import DetectModel
from reportWindow import ReportWindow
from settingsDB import connection_parameters as config

from classes import colors, class_names, class_names_full


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Initialization
        weights_path = os.path.join('./weights', 'stupidYOLO.pt')

        self.auto_detecting = False
        self.image_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.gif')
        self.report = {}
        self.connection = None

        self.model = DetectModel(YOLO(weights_path))
        self.model.load(weights_path)

        self.setup_ui()

    def setup_ui(self):
        # Main window setup

        self.setWindowTitle("Defect Detector")
        self.resize(1200, 800)

        screen = self.screen().availableGeometry()
        size = self.geometry()
        x = (screen.width() - size.width()) // 2
        y = (screen.height() - size.height()) // 2
        self.move(x, y)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QGridLayout(central_widget)

        # Menus setup
        self.setup_menus()

        # Widgets setup
        self.center_label = QLabel()
        self.center_label.setStyleSheet("border: 1px solid black;")
        self.center_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.center_label.setMinimumSize(1024, 576)

        self.list_widget = QListWidget()
        self.list_widget.setIconSize(QSize(146, 100))
        self.list_widget.setMinimumWidth(230)
        self.list_widget.itemClicked.connect(self.display_image)

        self.bottom_label = QLabel("")
        self.bottom_label.setStyleSheet("border: 1px solid black;")

        # Layout setup
        main_layout.addWidget(self.center_label, 1, 0, 1, 1)
        main_layout.addWidget(self.list_widget, 1, 1, 2, 1)
        main_layout.addWidget(self.bottom_label, 2, 0, 1, 1)

        main_layout.setRowStretch(1, 1)
        main_layout.setColumnStretch(0, 3)
        main_layout.setColumnStretch(1, 1)

    def setup_menus(self):
        menu_bar = self.menuBar()

        # File menu
        file_menu = menu_bar.addMenu("&Файл")
        file_menu_open_file = file_menu.addAction("Добавить файлы")
        file_menu_open_folder = file_menu.addAction("Добавить папку")
        file_menu.addSeparator()
        file_menu_clear = file_menu.addAction("Очистить список")

        file_menu_open_file.triggered.connect(self.open_files)
        file_menu_open_folder.triggered.connect(self.open_folder)
        file_menu_clear.triggered.connect(self.clear_list)

        # Detection menu
        detect_menu = menu_bar.addMenu("&Детектирование")
        detect_menu_image_detect = detect_menu.addAction("Выполнить детекцию на изображении")
        detect_menu_all_image_detect = detect_menu.addAction("Выполнить детекцию на всех изображениях")
        detect_menu.addSeparator()
        self.detect_menu_auto_detect = detect_menu.addAction("Aвтоматическое детектирование")
        self.detect_menu_auto_detect.setCheckable(True)

        detect_menu_image_detect.triggered.connect(self.inference_one)
        detect_menu_all_image_detect.triggered.connect(self.inference_all)
        self.detect_menu_auto_detect.triggered.connect(self.switch_auto_detect)

        # Report menu
        report_menu = menu_bar.addMenu("&Отчёт")
        report_menu_make_report = report_menu.addAction("Создать отчёт")
        report_menu_open_report = report_menu.addAction("Посмотреть отчёт")
        report_menu_load_report = report_menu.addAction("Загрузить отчёт")
        # report_menu.addSeparator()
        # report_menu_submit = report_menu.addAction("Создать submission")

        report_menu_make_report.triggered.connect(self.make_report)
        report_menu_open_report.triggered.connect(self.open_report)
        report_menu_load_report.triggered.connect(self.load_report)
        # report_menu_submit.triggered.connect(self.make_submit)

        # About menu
        database_menu = menu_bar.addMenu("&База данных")
        database_menu_connect_to_database = database_menu.addAction("Подключиться к БД")
        database_menu_send_to_database = database_menu.addAction("Отправить отчёт")

        database_menu_connect_to_database.triggered.connect(self.connect_to_database)
        database_menu_send_to_database.triggered.connect(self.send_to_database)

    def open_files(self):
        extension_image = 'Изображения (*.png *.jpg *.jpeg *.bmp *.gif)'
        extension_video = 'Видео (*.avi *.mp4)'

        dialog = QFileDialog()
        options = dialog.options()
        files, extension = dialog.getOpenFileNames(self, "Выберите файлы", "",
                                                   f"{extension_image};;{extension_video}",
                                                   options=options)

        if files:
            if extension == extension_image:
                self.process_images(files)
            elif extension == extension_video:
                self.process_videos(files)

    def process_images(self, files):
        progress_dialog = create_progress(len(files), self)
        for idx, file_path in enumerate(files):
            self.add_image_to_list(file_path)
            progress_dialog.setValue(idx + 1)
            if progress_dialog.wasCanceled():
                break

        item = self.list_widget.item(0)
        if item:
            self.display_image(item)

    def process_videos(self, files):
        for count, file in enumerate(files):
            filename = os.path.basename(file).split('.')[0]
            cap = cv2.VideoCapture(file)
            fps = cap.get(cv2.CAP_PROP_FPS)
            interval = 0.5
            interval_frames = int(interval * fps)

            frame_indices = [i * interval_frames for i in
                             range(int(cap.get(cv2.CAP_PROP_FRAME_COUNT) // interval_frames))]

            progress_dialog = create_progress(len(frame_indices), self)
            progress_dialog.setLabelText(f"Обработка {count + 1}-го видео")

            for idx, frame_index in enumerate(frame_indices):
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
                ret, frame = cap.read()

                if not ret:
                    break

                filename_ = f'{filename}_({frame_index}).jpg'
                file_path = './images/' + filename_
                cv2.imwrite(file_path, frame)

                progress_dialog.setValue(idx + 1)
                if progress_dialog.wasCanceled():
                    break

                self.add_image_to_list(file_path)

            cap.release()

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

        self.bottom_label.setText("")

    # ------------------------------------------------------------------------------------------------------------------#
    def inference_one(self, file_path=None):
        try:
            if not file_path:
                file_path = self.list_widget.currentItem().data(Qt.ItemDataRole.UserRole)

                output = self.model.inference(file_path)
                self.report |= output

                item = self.list_widget.currentItem()
                if item:
                    self.change_image_in_list(item)
                    self.display_image(item)
        except AttributeError:
            QMessageBox.critical(self, 'Warning', "Нет доступных для детектирования изображений.")

    def inference_all(self):
        paths = self.get_all_paths()

        if paths:
            progress_dialog = create_progress(len(paths), self)
            progress_dialog.setLabelText('Обнаружение дефектов...')

            for idx, file_path in enumerate(paths):
                if file_path not in self.report.keys():
                    output = self.model.inference(file_path)
                    self.report |= output

                    item = self.list_widget.item(idx)
                    self.change_image_in_list(item)

                progress_dialog.setValue(idx + 1)
                if progress_dialog.wasCanceled():
                    break

            item = self.list_widget.currentItem()
            self.display_image(item)

        else:
            QMessageBox.critical(self, 'Warning', "Нет доступных для детектирования изображений.")

    def switch_auto_detect(self):
        self.auto_detecting = False if self.auto_detecting else True

        if self.auto_detecting:
            self.detect_menu_auto_detect.setIcon(QIcon.fromTheme('dialog-ok'))
            item = self.list_widget.currentItem()
            if item:
                self.display_image(item)

        else:
            self.detect_menu_auto_detect.setIcon(QIcon())

    # ------------------------------------------------------------------------------------------------------------------#
    def make_report(self):
        print(self.report)
        path, _ = QFileDialog.getSaveFileName(self, "Save Database", '', "Database Files (*.json);;All Files (*)")
        if path:
            with open(path, 'w') as file:
                json.dump(self.report, file)

    def open_report(self):
        table_window = ReportWindow(self.report, self)
        table_window.show()

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
        brush = QBrush(QColor(255, 255, 0))
        painter.setBrush(brush)

        diameter = 20
        x = pixmap.width() - diameter - 5
        y = pixmap.height() - diameter - 5
        painter.drawEllipse(x, y, diameter, diameter)
        painter.end()

        item.setIcon(QIcon(pixmap))

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

        if file_path in self.report.keys():
            description = self.format_report(file_path)
        else:
            description = (f"Имя файла: {file_path}\n\nОбработка изображения еще не выполнена. \nПожалуйста, загрузите "
                           f"изображение и запустите процесс детекции для получения подробной информации о дефектах.")

        self.bottom_label.setText(description)
        self.bottom_label.setAlignment(Qt.AlignmentFlag.AlignTop)

    def draw_bbox_on_image(self, file_path):
        pixmap = QPixmap(file_path)
        painter = QPainter(pixmap)

        for bbox, class_name in zip(self.report[file_path]['bbox'], self.report[file_path]['class']):
            color = colors[str(int(class_name))]
            label = class_names[str(int(class_name))]
            bbox = [int(i) for i in bbox]

            pen = QPen(QColor(*color), 10)
            painter.setPen(pen)
            painter.drawRect(QRect(*bbox))

            text_rect = QRect(bbox[0] - 5, bbox[1] - 70, 150, 70)
            painter.fillRect(text_rect, QColor(*color))

            painter.setPen(QColor(0, 0, 0))
            painter.setFont(QFont('Arial', 60))
            painter.drawText(bbox[0], bbox[1] - 10, label)

        painter.end()

        self.center_label.setPixmap(pixmap.scaled(self.center_label.size(), Qt.AspectRatioMode.KeepAspectRatio,
                                                  Qt.TransformationMode.SmoothTransformation))

    def get_all_paths(self):
        paths = []
        for index in range(self.list_widget.count()):
            item = self.list_widget.item(index)
            path = item.data(Qt.ItemDataRole.UserRole)
            paths.append(path)
        return paths

    def make_submit(self):
        headers = ['filename', 'class_id', 'rel_x', 'rel_y', 'width', 'height']

        submit = []
        for file_path, values in self.report.items():
            file_name = os.path.basename(file_path)
            for bboxn, label in zip(values['bboxn'], values['class']):
                bboxn_line = ';'.join([str(item) for item in bboxn])
                line = f'{file_name};{int(label)};{bboxn_line}'
                submit.append(line)

        output_file = 'submit.csv'

        with open(output_file, mode='w', newline='') as file:
            writer = csv.writer(file, delimiter=';')
            writer.writerow(headers)
            for row in submit:
                writer.writerow(row.split(';'))
        print(f"Данные успешно записаны в {output_file}")

    def format_report(self, filename):
        report = self.report[filename]
        bboxes = report['bbox']
        classes = report['class']

        defect_count = {name: 0 for name in class_names.values()}

        description = f"Имя файла: {filename}\n\nНайденные дефекты:\n"

        for i, bbox in enumerate(bboxes):
            defect_class = class_names[str(int(classes[i]))]
            defect_count[defect_class] += 1

            description += (f"{i + 1}. Дефект \"{defect_class}\" "
                            f"({class_names_full[defect_class]}) "
                            f"в координатах (x: {bbox[0]:.2f}, y: {bbox[1]:.2f}, "
                            f"ширина: {bbox[2]:.2f}, высота: {bbox[3]:.2f})\n")

        if len(bboxes) == 0:
            description += "Дефектов не обнаружено\n"
        else:
            description += "\nОбщее количество дефектов:\n"
            for defect_class, count in defect_count.items():
                description += f"- {class_names_full[defect_class]} ({defect_class}): {count}\n"

        return description

    def connect_to_database(self):
        try:
            self.connection = pyodbc.connect(
            f"DSN={config['DSN']};UID={config['UID']};PWD={config['PWD']}"
        )
        except pyodbc.InterfaceError:
            QMessageBox.critical(self, 'Warning', "Не могу подключиться к БД. Проверьте параметры подключения.")

    def send_to_database(self):
        if self.connection:
            INSERT = ("INSERT INTO TABLE (filename, class_id, rel_x, rel_y, width, height) VALUES ('%s', '%s', '%s', "
                      "'%s','%s');")

            cursor = self.connection.cursor()

            for file_path, values in self.report.items():
                file_name = os.path.basename(file_path)
                for bboxn, label in zip(values['bboxn'], values['class']):
                    bboxn_ = [str(item) for item in bboxn]
                    label_ = str(int(label))

                    data = [file_name] + bboxn_ + [label_]

                    QUERY = INSERT % data
                    cursor.execute(QUERY)
                    data = cursor.fetchall()

            self.connection.close()

    # ------------------------------------------------------------------------------------------------------------------#


def create_progress(amount, parent):
    progress_dialog = QProgressDialog("Загрузка изображений...", "Остановить", 0, amount, parent)
    progress_dialog.setWindowTitle("Загрузка")
    progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
    progress_dialog.setMinimumDuration(0)

    return progress_dialog
