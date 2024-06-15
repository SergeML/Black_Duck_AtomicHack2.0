import cv2


class DetectModel:
    def __init__(self, detector, validator=None):
        self.model_detection = detector
        self.model_classification = validator

    def load(self, weights_detector, weights_validator=None):
        self.model_detection.load(weights_detector)

    def inference(self, file_path: str):
        image = cv2.imread(file_path)
        result = self.model_detection.predict(image, verbose=False)

        labels = result[0].boxes.cls.cpu().numpy().tolist()
        bboxes = result[0].boxes.xywh.cpu().numpy().tolist()
        bboxesn = result[0].boxes.xywhn.cpu().numpy().tolist()

        return {file_path: {'bbox': bboxes, 'class': labels, 'bboxn': bboxesn}}