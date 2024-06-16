import os
import cv2
import csv
import datetime
from tqdm import tqdm
from ultralytics import YOLO

import pandas as pd

colors = {
    '0': (0, 0, 255),
    '1': (0, 255, 0),
    '2': (255, 0, 0),
    '3': (0, 255, 255),
    '4': (255, 0, 255)
}


def make_submit(report, filename=None):
    headers = ['filename', 'class_id', 'rel_x', 'rel_y', 'width', 'height']

    submit = []
    for file_path, values in report.items():
        file_name = os.path.basename(file_path)
        for bboxn, label in zip(values['bboxn'], values['class']):
            bboxn_line = ';'.join([str(item) for item in bboxn])
            line = f'{file_name};{int(label)};{bboxn_line}'
            submit.append(line)
    if file_name:
        output_file = filename
    else:
        output_file = now.strftime("%Y%m%d_%H%M%S") + 'submit.csv'

    with open(output_file, mode='w', newline='') as file:
        writer = csv.writer(file, delimiter=';')
        writer.writerow(headers)
        for row in submit:
            writer.writerow(row.split(';'))
    print(f"Данные успешно записаны в {output_file}")


def inference_model(images, model, filename):
    outputs = {}
    for image in tqdm(images):
        output = model.inference(image)
        if output:
            outputs |= output
    
    make_submit(outputs, filename)


class StackedYOLO:
    def __init__(self, detectors, classificators=None, thresholds=None):
        self.model_detection = detectors   
        self.model_classification = classificators
        self.thresholds = thresholds if thresholds else [.5] * len(detectors)

    def inference(self, file_path: str):
        image = cv2.imread(file_path)
        image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) 
        labels, bboxes, bboxesn = [], [], []
        flags = []

        if self.model_classification:
            for idx, model in enumerate(self.model_classification):
                flag = (model.predict(image_gray, verbose = False, show=False)[0].probs.data[1].item() > self.thresholds[idx]) * 1
                flags.append(flag)
        else:
            flags = [1] * len(self.model_detection)
        
        for idx, model in enumerate(self.model_detection):
            if flags[idx]:
                output = model.predict(image, verbose = False, show=False)
    
                label = output[0].boxes.cls.cpu().numpy().tolist()
                bbox = output[0].boxes.xywh.cpu().numpy().tolist()
                bboxn = output[0].boxes.xywhn.cpu().numpy().tolist()

                if len(self.model_detection) != 1:
                    label = [idx] * len(label)
    
                labels.extend(label) 
                bboxes.extend(bbox) 
                bboxesn.extend(bboxn)

        return {file_path: {'bbox': bboxes, 'class': labels, 'bboxn': bboxesn}}

def paint(path, bbox, classes, file):
    # Загрузка изображения
    image = cv2.imread(path)

    for box, label in zip(bbox, classes):

    # Координаты и размеры bounding box (пример)

        # Распакуем значения
        x, y, h, w = list(map(int, box))

        # Вычислим нижний правый угол прямоугольника
        end_x = x + w
        end_y = y + h

        # Нарисуем прямоугольник на изображении (цвет - зелёный, толщина линии - 2)

        cv2.rectangle(image, (x, y), (end_x, end_y), colors[str(int(label))], 2)


    # Сохранить изображение с bounding box
    cv2.imwrite(file, image)



