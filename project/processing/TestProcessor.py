import math
import os
import re
import statistics

import matplotlib.pyplot as plt
import seaborn as sns
from PIL import Image

import processing.Eyetracker as Eyetracker
from processing import Evaluation

W = 1920
H = 1200
RES = (W, H)


def process_gaze_data(gaze_data):
    left = gaze_data['left_gaze_point_on_display_area']
    right = gaze_data['right_gaze_point_on_display_area']

    left = tuple(l*res for l, res in zip(left, RES))
    right = tuple(r*res for r, res in zip(right, RES))

    if not math.isnan(left[0]):
        left = tuple(round(l) for l in left)

    if not math.isnan(right[0]):
        right = tuple(round(r) for r in right)

    return Eyetracker.GazePoint(left, right)


def process_picture(picture_data):
    data = list()
    data.append(picture_data[0])
    data.append(picture_data[1])
    data.append(round(picture_data[2] / 1000, 2))
    gazes = []
    for gaze_data in picture_data[4]:
        gaze = process_gaze_data(gaze_data)
        if not gaze.is_nan():
            gazes.append(gaze)

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
            if gazepoint.is_nan():
                counter += 1

        max = len(picture[3]) if picture[3] else 1
        percent = round(counter/max*100, 2)
        if percent >= 75.0:
            high_percent += 1
        print("{}%: {} from {}".format(percent, counter, max))
        percents.append(percent)

    print("Mean of all pictures: {}%".format(statistics.mean(percents)))
    print("Pictures with over 75% nan: {}".format(high_percent))


def create_heatmaps(processed_data):
    heatmaps = list()
    for picture in processed_data:
        buf = [e.get() for e in picture[3]]
        if buf:
            heatmaps.append([picture[0][0], list(zip(*buf))])

    return heatmaps


def trim_heatmaps(heatmaps, pic_geometry):
    maps = list()
    xpic, ypic, width, height = pic_geometry
    for heatmap in heatmaps:
        xs = [width if x > xpic+width else x-xpic if x > xpic else 0 for x in heatmap[1][0]]
        ys = [height if y > ypic+height else y-ypic if y > ypic else 0 for y in heatmap[1][1]]

        maps.append([heatmap[0], [xs, ys]])

    return maps


def create_plot(heatmaps, plot_path):
    dataset_description = re.findall(r'([^\/]+\/)[^\/]+\.', heatmaps[0][0])[0]
    if not os.path.isdir(plot_path+dataset_description):
        os.makedirs(plot_path+dataset_description)

    print("Creating {} plots".format(len(heatmaps)))

    for index, heatmap in enumerate(heatmaps):

        if len(heatmap[1][0]) < 5:
            print("Gazedata less than 5 for {}".format(heatmap[0]))
            continue

        img = Image.open(heatmap[0])
        img = img.resize((350, 350))

        fig, axes = plt.subplots(ncols=3, nrows=1, figsize=(8.4, 4.8))
        axes[0].set_title('Original')
        axes[0].imshow(img, zorder=1)
        axes[1].set_title('KDE')
        sns.kdeplot(heatmap[1][0], heatmap[1][1], cmap='YlOrRd', alpha=0.5, zorder=2, shade=True, shade_lowest=False,
                    n_levels=7, ax=axes[1])
        axes[1].imshow(img, zorder=1)
        axes[2].set_title('2D Histogram')
        axes[2].hist2d(heatmap[1][0], heatmap[1][1], bins=40, range=[[0, 350], [0, 350]], alpha=0.6, zorder=2, cmin=0.01)
        axes[2].invert_yaxis()
        axes[2].imshow(img, zorder=1)

        pic_name = re.findall(r'([^\/]+\/[^\/]+\.)', heatmap[0])[0]
        path = plot_path + pic_name + "png"
        path = _duplicate_path(path)
        fig.savefig(path)
        plt.close(fig)


def main_pipeline(paths, participant_id):
    total_time = 0
    for index, path in enumerate(paths):
        print("Starting process of test {} of {} -- {}".format(index+1, len(paths), path))
        e = Evaluation.Evaluation.create_from_file(path)
        processed = process(e.picture_data)

        heatmaps = create_heatmaps(processed)
        trimmed = trim_heatmaps(heatmaps, e.pic_geometry_global)
        create_plot(trimmed, 'plots/{}/'.format(participant_id))

        total_time += calculate_stats(processed)

    print("Total time of this session and participant: {0:.3f} sec or {1} min and {2:.3f} sec".format(
        total_time, (total_time//60), (total_time % 60)))


def calculate_stats(processed):
    # add iti
    sum = 50
    for picture in processed:
        sum += picture[2] / 1000

    print("Time for this dataset: {0:.3f} sec or {1} min and {2:.3f} sec".format(sum, (sum//60), (sum % 60)))
    return sum


def _duplicate_path(path, counter=1):
    if os.path.isfile(path):
        return _copy_path(path[:-4] + '_' + str(counter) + path[-4:], counter+1)
    else:
        return path


def _copy_path(path, counter):
    if os.path.isfile(path):
        return _copy_path(path[:-5]+str(counter)+path[-4:], counter+1)
    else:
        return path
