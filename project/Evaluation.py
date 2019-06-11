import ast
import statistics
import time


class Evaluation:

    def __init__(self, dataset, tester_data):
        self.dataset = dataset
        self.tester_data = tester_data
        self.data = {}

        self.evaluate()

    def evaluate(self):
        self.data["p"] = sum(i.count(1) for i in self.dataset.data)
        self.data["n"] = sum(i.count(0) for i in self.dataset.data)
        real_dict = dict(self.dataset.data)
        durations = list(zip(*self.tester_data))[2]
        tp, fn, fp, tn = 0, 0, 0, 0

        for case in self.tester_data:
            true_condition = real_dict[case[0]]
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

        self.data["true_data"] = self.dataset.data
        self.data["tester_data"] = self.tester_data

    def save_to_file(self):
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())

        with open(timestamp + '.txt', 'w') as file:
            file.write(str(self.data))

    def load_from_file(self, path):
        with open(path, 'r') as file:
            self.data = ast.literal_eval(file.read())