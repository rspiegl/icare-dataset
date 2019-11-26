import statistics


class TestEvaluation:

    def __init__(self):
        self.p, self.n, self.tp, self.fn, self.fp, self.tn = (0,) * 6
        self.precision, self.recall, self.tnr, self.fnr, self.accuracy = (0,) * 5
        self.f1, self.mean, self.variance, self.duration, self.number = (0,) * 5

    def evaluate(self, picture_data, number=35):
        self.number = number
        if self.number >= len(picture_data):
            calculation_data = picture_data
            self.number = len(picture_data)
        elif self.number > 0:
            calculation_data = picture_data[:self.number]
        elif self.number < 0:
            calculation_data = picture_data[self.number:]
        else:
            raise Exception("Can't calculate score when number of picture data is {}".format(self.number))

        self.p = sum(i[0].count(1) for i in calculation_data)
        self.n = sum(i[0].count(0) for i in calculation_data)
        durations = [round(x / 1000 / 1000, 3) for x in list(zip(*calculation_data))[2]]
        tp, fn, fp, tn = 0, 0, 0, 0

        for case in calculation_data:
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

        self.precision = round(0 if tp + fp == 0 else tp / (tp + fp), 4)
        self.recall = round(tp / (tp + fn), 4)
        self.tnr = round(tn / (tn + fp), 4)
        self.fnr = round(fn / (fn + tp), 4)
        self.accuracy = round((tp + tn) / (tp + tn + fp + fn), 4)
        self.f1 = round((2 * tp) / (2 * tp + fp + fn), 4)
        self.mean = round(statistics.mean(durations), 3)
        self.variance = round(statistics.pvariance(durations), 3)
        self.duration = round(sum(durations), 3)

    def as_dict(self):
        return self.__dict__

    def from_dict(self, dictionary):
        for item in dictionary.items():
            self.__setattr__(item[0], item[1])

        return self

    @classmethod
    def create_from_file(cls, dic):
        return cls().from_dict(dic)
