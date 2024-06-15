import cv2


class DetectModel:
    def __init__(self, model):
        self.model = model

    def load(self, weights):
        self.model.load(weights)

    def inference(self, file_path: str):
        image = cv2.imread(file_path)
        result = self.model.predict(image)

        labels = result[0].boxes.cls.cpu().numpy()
        bboxes = result[0].boxes.xywh.cpu().numpy()
        bboxesn = result[0].boxes.xywhn.cpu().numpy()

        return {file_path: {'bbox': bboxes, 'class': labels, 'bboxn': bboxesn}}








