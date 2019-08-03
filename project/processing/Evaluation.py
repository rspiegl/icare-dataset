import re
import statistics
import time

CUSTOM_EVAL_NAN = {'nan': float('nan')}


class Evaluation:

    def __init__(self):
        self.screen_resolution = (1920, 1200)
        self.p, self.n, self.tp, self.fn, self.fp, self.tn = (0,) * 6
        self.precision, self.recall, self.tnr, self.fnr, self.accuracy = (0,) * 5
        self.f1, self.mean, self.variance = (0,) * 3
        self.pic_geometry_global, self.central_widget_geometry_global = None, None
        self.picture_data = None

    def evaluate(self, picture_data):
        self.picture_data = picture_data

        self.p = sum(i[0].count(1) for i in self.picture_data)
        self.n = sum(i[0].count(0) for i in self.picture_data)
        durations = list(zip(*self.picture_data))[2]
        tp, fn, fp, tn = 0, 0, 0, 0

        for case in self.picture_data:
            true_condition = case[0][1]
            pred_condition = case[1]
            if true_condition:
                if pred_condition:
                    tp = tp + 1
                else:
                    fn = fn + 1
            else:
                if pred_condition:
                    fp = fp + 1
                else:
                    tn = tn + 1

        self.tp = tp
        self.fn = fn
        self.fp = fp
        self.tn = tn

        self.precision = 0 if tp+fp == 0 else tp / (tp + fp)
        self.recall = tp / (tp + fn)
        self.tnr = tn / (tn + fp)
        self.fnr = fn / (fn + tp)
        self.accuracy = (tp + tn) / (tp + tn + fp + fn)
        self.f1 = (2 * tp) / (2 * tp + fp + fn)
        self.mean = statistics.mean(durations)
        self.variance = statistics.pvariance(durations)

    def set_pic_geometry(self, geometry):
        self.pic_geometry_global = geometry

    def set_central_widget_geometry(self, geometry):
        self.central_widget_geometry_global = geometry

    def as_dict(self):
        return self.__dict__

    def save_to_file(self):
        dataset_identifier = re.findall(r'([^\/]+)\/[^\/]+\.', self.picture_data[0][0][0])[0]
        timestamp = time.strftime('%m-%d_%H-%M', time.localtime())
        dir_path = 'processing/'

        with open(dir_path + dataset_identifier + '_' + timestamp + '.txt', 'w') as file:
            file.write(str(self.as_dict()))

    def from_dict(self, dictionary):
        for item in dictionary.items():
            self.__setattr__(item[0], item[1])

        return self

    @classmethod
    def create_from_file(cls, path):
        dictionary = Evaluation._load_from_file(path)
        return cls().from_dict(dictionary)

    @staticmethod
    def _load_from_file(path):
        with open(path, 'r') as file:
            dictionary = eval(file.read(), CUSTOM_EVAL_NAN)

        return dictionary
