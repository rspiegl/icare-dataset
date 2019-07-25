import statistics

import processing.Eyetracker as Eyetracker


def process_gaze_data(gaze_data):
    left = gaze_data['left_gaze_point_on_display_area']
    right = gaze_data['right_gaze_point_on_display_area']

    return Eyetracker.GazePoint(left, right)


def process_picture(picture_data):
    data = list()
    data.append(picture_data[0])
    data.append(picture_data[1])
    data.append(round(picture_data[2] / 1000, 2))
    gazes = []
    for gaze_data in picture_data[4]:
        gazes.append(process_gaze_data(gaze_data))

    data.append(gazes)

    return data


def process(tester_data):
    data = []
    for picture in tester_data:
        data.append(process_picture(picture))

    return data


def check_nan_counter(processed_data):
    percents = list()
    high_percent = 0
    for picture in processed_data:
        counter = 0
        for gazepoint in picture[3]:
            if gazepoint.has_nan():
                counter += 1

        max = len(picture[3]) if picture[3] else 1
        percent = round(counter/max*100, 2)
        if percent >= 75.0:
            high_percent += 1
        print("{}%: {} from {}".format(percent, counter, max))
        percents.append(percent)

    print("Mean of all pictures: {}%".format(statistics.mean(percents)))
    print("Pictures with over 75% nan: {}".format(high_percent))
