import glob
import math
import os
import re
import statistics

import matplotlib
matplotlib.use('qt5agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

import seaborn as sns
from PIL import Image

import processing.Eyetracker as Eyetracker
from processing import Evaluation

W = 1920
H = 1200
RES = (W, H)

plot_width = plot_height = 512
plot_size = [plot_width, plot_height]
dpi = 100
fig_size = [plot_width/dpi, plot_height/dpi]
plot_range = [[0, plot_width], [0, plot_height]]


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


def process_picture_eyetracking_data(eyetracking_data):
    gazes = []
    for gaze_data in eyetracking_data:
        gaze = process_gaze_data(gaze_data)
        if not gaze.is_nan():
            gazes.append(gaze)

    return gazes


def process_picture(picture_data):
    data = list()
    data.append(picture_data[0])
    data.append(picture_data[1])
    data.append(round(picture_data[2] / 1000, 2))
    data.append(process_picture_eyetracking_data(picture_data[4]))

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
        buf = create_heatmap(picture[3])
        if buf:
            heatmaps.append([picture[0][0], buf])

    return heatmaps


def create_heatmap(processed_data):
    buf = [e.get() for e in processed_data]

    return list(zip(*buf))


def trim_heatmaps(heatmaps, pic_geometry):
    maps = list()
    for heatmap in heatmaps:
        xs, ys = trim_heatmap(heatmap[1], pic_geometry)

        maps.append([heatmap[0], [xs, ys]])

    return maps


def trim_heatmap(heatmap, pic_geometry):
    xpic, ypic, width, height = pic_geometry

    xs = [width if x > xpic + width else x - xpic if x > xpic else 0 for x in heatmap[0]]
    ys = [height if y > ypic + height else y - ypic if y > ypic else 0 for y in heatmap[1]]

    return xs, ys


def create_plots(heatmaps, participant_id):
    plot_path = "plots/{}/".format(participant_id)
    dataset_identifier = re.findall(r'([^\/]+\/)[^\/]+\.', heatmaps[0][0])[0]
    print("Dataset identifier: {}".format(dataset_identifier))
    if not os.path.isdir(plot_path+dataset_identifier):
        os.makedirs(plot_path+dataset_identifier)

    print("Creating {} plots".format(len(heatmaps)))

    for index, heatmap in enumerate(heatmaps):

        if len(heatmap[1][0]) < 5:
            print("Gazedata less than 5 for {}".format(heatmap[0]))
            continue

        img = Image.open(heatmap[0])
        img = img.resize(plot_size)

        figure = Figure(figsize=(8.4, 4.8), dpi=100)
        canvas = FigureCanvas(figure)

        axes = figure.subplots(ncols=3, nrows=1)
        axes[0].set_title('Original')
        axes[0].imshow(img, zorder=1)
        axes[1].set_title('KDE')
        sns.kdeplot(heatmap[1][0], heatmap[1][1], cmap='YlOrRd', alpha=0.5, zorder=2, shade=True, shade_lowest=False,
                    n_levels=7, ax=axes[1])
        axes[1].imshow(img, zorder=1)
        axes[2].set_title('2D Histogram')
        axes[2].hist2d(heatmap[1][0], heatmap[1][1], bins=40, range=plot_range, alpha=0.6, zorder=2, cmin=0.01)
        axes[2].invert_yaxis()
        axes[2].imshow(img, zorder=1)

        pic_name = re.findall(r'([^\/]+\/[^\/]+)\.', heatmap[0])[0]
        path = plot_path + pic_name + "_{}.png".format(participant_id)
        path = _duplicate_path(path)
        figure.canvas.print_png(path)
        figure.clf()


def create_histogram_temp(heatmap, img_path, name='cali'):
    figure = Figure(figsize=fig_size, dpi=dpi, frameon=False)  # frameoff for transparent background
    canvas = FigureCanvas(figure)

    img = Image.open(img_path)
    img = img.resize(plot_size)

    ax = figure.gca()
    ax.axis('off')
    ax.hist2d(heatmap[0], heatmap[1], bins=40, range=plot_range, alpha=0.6, zorder=2, cmin=0.01)
    ax.invert_yaxis()
    ax.imshow(img, zorder=1)

    path = name + '_temp.png'
    figure.canvas.print_png(path)
    figure.clf()

    return path


def main_pipeline(paths, participant_id):
    total_time = 0
    for index, path in enumerate(paths):
        print("Starting process of test {} of {} -- {}".format(index+1, len(paths), path))
        e = Evaluation.Evaluation.create_from_file(path)
        processed = process(e.picture_data)

        heatmaps = create_heatmaps(processed)
        trimmed = trim_heatmaps(heatmaps, e.pic_geometry_global)
        create_plots(trimmed, participant_id)

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


if __name__ == '__main__':
    paths = [f for f in glob.glob('*.txt')]
    main_pipeline(paths, 1)
