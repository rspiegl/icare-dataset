import scipy


class TestEvaluation:

    def __init__(self):
        self.p, self.n, self.tp, self.fn, self.fp, self.tn = (0,) * 6
        self.precision, self.recall, self.tnr, self.fnr, self.accuracy = (0,) * 5
        self.f1, self.images_mean, self.images_variance, self.images_duration, self.number = (0,) * 5
        self.total_duration, self.images_duration_min, self.images_duration_max, = (0,) * 3
        self.pause_mean, self.pause_variance, self.pause_duration, self.pause_duration_min, self.pause_duration_max = (
                                                                                                                      None,) * 5

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
        breaks = []
        prev = 0
        for i, case in enumerate(calculation_data):
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
            # break calculation
            if len(case) > 5 and case[5]:
                if i is 0:
                    prev = case[5][1]
                    continue
                breaks.append(round((case[5][0] - prev) / 1000 / 1000, 3))
                prev = case[5][1]
            elif case[3]:
                if i is 0:
                    prev = case[3][-1]['system_time_stamp']
                    continue
                breaks.append(round((case[3][0]['system_time_stamp'] - prev) / 1000 / 1000, 3))
                prev = case[3][-1]['system_time_stamp']
            elif not case[3]:
                # if data is missing for one case add duration of that image to previous timestamp
                prev += (durations[i] + 0.5) * 1000 * 1000

        self.tp = tp
        self.fn = fn
        self.fp = fp
        self.tn = tn

        self.precision = round(0 if tp + fp == 0 else tp / (tp + fp), 4)
        self.recall = round(0 if tp + fn == 0 else tp / (tp + fn), 4)
        self.tnr = round(0 if tn + fp == 0 else tn / (tn + fp), 4)
        self.fnr = round(0 if fn + tp == 0 else fn / (fn + tp), 4)
        self.accuracy = round((tp + tn) / (tp + tn + fp + fn), 4)
        self.f1 = round(0 if tp + fp + fn == 0 else (2 * tp) / (2 * tp + fp + fn), 4)
        describe = scipy.stats.describe(durations)
        self.images_mean = round(describe.mean, 3)
        self.images_variance = round(describe.variance, 3)
        self.images_duration = round(sum(durations), 3)
        self.images_duration_min = describe.minmax[0]
        self.images_duration_max = describe.minmax[1]
        if breaks:
            describe = scipy.stats.describe(breaks)
            self.pause_mean = round(describe.mean, 3)
            self.pause_variance = round(describe.variance, 3)
            self.pause_duration = round(sum(breaks), 3)
            self.pause_duration_min = describe.minmax[0]
            self.pause_duration_max = describe.minmax[1]
        self.total_duration = self.images_duration + float(self.pause_duration or 0)

    def as_dict(self):
        return self.__dict__

    def from_dict(self, dictionary):
        for item in dictionary.items():
            self.__setattr__(item[0], item[1])

        return self

    @classmethod
    def create_from_file(cls, dic):
        return cls().from_dict(dic)
