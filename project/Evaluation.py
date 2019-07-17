import statistics
import time

CUSTOM_EVAL_NAN = {'nan': float('nan')}

class Evaluation:

    def __init__(self, tester_data, tracker_data, data=None):
        self.tester_data = tester_data
        self.tracker_data = tracker_data

        if data:
            self.data = data
        else:
            self.data = {}
            self.evaluate()

    def evaluate(self):
        self.data["screen_resolution"] = (1920, 1200)

        self.data["p"] = sum(i[0].count(1) for i in self.tester_data)
        self.data["n"] = sum(i[0].count(0) for i in self.tester_data)
        durations = list(zip(*self.tester_data))[2]
        tp, fn, fp, tn = 0, 0, 0, 0

        for case in self.tester_data:
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
        self.data["tp"] = tp
        self.data["fn"] = fn
        self.data["fp"] = fp
        self.data["tn"] = tn

        self.data["precision"] = tp / (tp + fp)
        self.data["recall"] = tp / (tp + fn)
        self.data["tnr"] = tn / (tn + fp)
        self.data["fnr"] = fn / (fn + tp)
        self.data["accuracy"] = (tp + tn) / (tp + tn + fp + fn)
        self.data["f1"] = (2 * tp) / (2 * tp + fp + fn)
        self.data["mean"] = statistics.mean(durations)
        self.data["variance"] = statistics.pvariance(durations)

        self.data["tester_data"] = self.tester_data

    def set_pic_geometry(self, geometry):
        self.data["pic_geometry"] = geometry

    def save_to_file(self):
        timestamp = time.strftime('%Y-%m-%d_%H:%M:%S', time.localtime())

        with open(timestamp + '.txt', 'w') as file:
            file.write(str(self.data))

    def save_tracker_data_to_file(self):
        timestamp = time.strftime('%Y-%m-%d_%H:%M:%S', time.localtime())

        with open(timestamp + '_eyetracking.txt', 'w') as file:
            for data in self.tracker_data:
                file.write(str(data) + '\n')

    @staticmethod
    def _load_from_file(path):
        with open(path, 'r') as file:
            data = eval(file.read(), CUSTOM_EVAL_NAN)

        return data

    @staticmethod
    def _load_tracker_data_from_file(path):
        tracker_data = []

        with open(path, 'r') as file:
            for line in [s.strip() for s in file.readlines()]:
                tracker_data.append(eval(line, CUSTOM_EVAL_NAN))

        return tracker_data

    @staticmethod
    def create_from_files(data, tracker):
        data = Evaluation._load_from_file(data)
        tracker_data = Evaluation._load_tracker_data_from_file(tracker)

        return Evaluation(data["tester_data"], tracker_data, data)
