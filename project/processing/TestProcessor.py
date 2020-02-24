import glob
import math
import os
import re
import statistics

import matplotlib
import numpy as np

matplotlib.use('qt5agg')
import seaborn as sns
from PIL import Image
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

import Utilities
import processing.Eyetracker as Eyetracker

W = 1920
H = 1200
RES = (W, H)

plot_width = plot_height = 512
plot_size = [plot_width, plot_height]
dpi = 100
fig_size = [plot_width / dpi, plot_height / dpi]
plot_range = [[0, plot_width], [0, plot_height]]

identifier_regex = r'[^\/]+\/([^\/]+)\.'


def process_gaze_data(gaze_data):
    left = gaze_data['left_gaze_point_on_display_area']
    right = gaze_data['right_gaze_point_on_display_area']

    left = tuple(l * res for l, res in zip(left, RES))
    right = tuple(r * res for r, res in zip(right, RES))

    if not math.isnan(left[0]):
        left = tuple(round(l) for l in left)

    if not math.isnan(right[0]):
        right = tuple(round(r) for r in right)

    t = round(gaze_data['system_time_stamp'] / 1000, 1)  # convert to ms

    return Eyetracker.GazePoint(left, right, timestamp=t)


def process_picture_eyetracking_data(eyetracking_data):
    gazes = []
    for gaze_data in eyetracking_data:
        gaze = process_gaze_data(gaze_data)
        gazes.append(gaze)

    return gazes


def process_picture(picture_data):
    data = list()
    data.append(picture_data[0])
    data.append(picture_data[1])
    data.append(round(picture_data[2] / 1000, 3))
    data.append(process_picture_eyetracking_data(picture_data[3]))

    if len(picture_data) > 4:
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
        percent = round(counter / max * 100, 2)
        if percent >= 75.0:
            high_percent += 1
        print("{}%: {} from {}".format(percent, counter, max))
        percents.append(percent)

    print("Mean of all pictures: {}%".format(statistics.mean(percents)))
    print("Pictures with over 75% nan: {}".format(high_percent))


def get_coords_for_heatmaps(processed_data):
    heatmaps = list()
    for picture in processed_data:
        tmp = list()
        tmp.append(picture[0][0])
        tmp.append(get_coords_for_heatmap(picture[3]))
        if len(picture) > 4:
            tmp.append(get_coords_for_heatmap(picture[4]))
        heatmaps.append(tmp)

    return heatmaps


def get_coords_for_heatmap(processed_data):
    buf = [e.get() for e in processed_data]

    return list(zip(*buf))


def get_timestamps(processed_data):
    times = [e.timestamp for e in processed_data]
    times = [round(x - times[0], 1) for x in times]
    return times


def offset_calibrations(heatmaps, geometry):
    calibrated = list()
    for heatmap in heatmaps:
        if not heatmap[1]:
            print('no eyetracking data for ' + heatmap[0])
            continue
        calibrated.append(offset_calibration(heatmap, geometry))

    return calibrated


def offset_calibration(heatmap, geometry):
    """
    :param heatmap: 3 tuple of path, eyetracking, calibration
    :param geometry: picture geometry
    :return: 2 tuple of path, calibrated eyetracking
    """
    calibrated = list()
    calibrated.append(heatmap[0])

    if len(heatmap) < 3 or not heatmap[2]:
        calibrated.append(heatmap[1])
        return calibrated

    xybins = 40
    bin_middle = geometry[2] / xybins / 2
    rang = [[geometry[0], geometry[0] + geometry[2]], [geometry[1], geometry[1] + geometry[3]]]
    H, xedges, yedges = np.histogram2d(heatmap[2][0], heatmap[2][1], bins=xybins, range=rang)
    x_cent, y_cent = np.unravel_index(H.argmax(), H.shape)
    x_offset = xedges[x_cent] + bin_middle - (geometry[0] + geometry[2] // 2)
    y_offset = yedges[y_cent] + bin_middle - (geometry[1] + geometry[3] // 2)

    calibrated.append([[x - x_offset for x in heatmap[1][0]], [y - y_offset for y in heatmap[1][1]]])
    calibrated.append(heatmap[2])
    return calibrated


def trim_heatmaps(heatmaps, pic_geometry):
    maps = list()
    for heatmap in heatmaps:
        buf = list()
        buf.append(heatmap[0])

        xs, ys = trim_heatmap(heatmap[1], pic_geometry)
        buf.append([list(xs), list(ys)])

        if len(heatmap) > 2:
            xs, ys = trim_heatmap(heatmap[2], pic_geometry)
            buf.append([list(xs), list(ys)])

        maps.append(buf)

    return maps


def trim_heatmap(heatmap, pic_geometry):
    xpic, ypic, width, height = pic_geometry

    coords = [[x - xpic, y - ypic] for x, y in zip(*heatmap) if
              xpic <= x <= xpic + width and ypic <= y <= ypic + height]
    if coords:
        return list(zip(*coords))
    else:
        return [[], []]


def trim_heatmap_timestamps(heatmap, timestamps, pic_geometry):
    xpic, ypic, width, height = pic_geometry

    coords = [[[c[0] - xpic, c[1] - ypic], times] for c, times in zip(zip(*heatmap), timestamps) if
              xpic <= c[0] <= xpic + width and ypic <= c[1] <= ypic + height]
    if coords:
        coord, times = list(zip(*coords))
        return list(zip(*coord)), times
    else:
        return [[], []], []


def create_plots(heatmaps, participant_id, dataset_name, calibration=None):
    plot_path = "plots/{}/{}/".format(participant_id, dataset_name)
    print("Dataset identifier: {}".format(dataset_name))
    if not os.path.isdir(plot_path):
        os.makedirs(plot_path)

    if calibration:
        create_calibration_histogram(calibration, plot_path + '0calibration')

    print("Creating {} plots".format(len(heatmaps)))

    for index, heatmap in enumerate(heatmaps):

        if len(heatmap[1][0]) < 5:
            print("Gazedata less than 5 for {}".format(heatmap[0]))
            continue

        pic_name = "_" + re.findall(identifier_regex, heatmap[0])[0] + ".png"

        if len(heatmap) >= 3 and heatmap[2]:
            create_quadruple_plot(heatmap, participant_id, plot_path + str(index + 1) + pic_name)
        else:
            create_triple_plot(heatmap, participant_id, plot_path + str(index + 1) + pic_name)


def create_triple_plot(heatmap, participant_id, full_path):
    img = Image.open(heatmap[0])
    img = img.resize(plot_size)
    figure = Figure(figsize=(8.4, 4.8), dpi=dpi)
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
    figure.canvas.print_png(full_path)
    figure.clf()


def create_quadruple_plot(heatmap, participant_id, full_path):
    img = Image.open(heatmap[0])
    img = img.resize(plot_size)

    figure = Figure(figsize=(8.4, 8.4), dpi=dpi)
    canvas = FigureCanvas(figure)
    axes = figure.subplots(ncols=2, nrows=2)

    axes[0][0].set_title('Original')
    axes[0][0].imshow(img, zorder=1)

    axes[0][1].set_title('KDE')
    sns.kdeplot(heatmap[1][0], heatmap[1][1], cmap='YlOrRd', alpha=0.5, zorder=2, shade=True, shade_lowest=False,
                n_levels=7, ax=axes[0][1])
    axes[0][1].imshow(img, zorder=1)

    axes[1][0].set_title('2D Histogram')
    axes[1][0].hist2d(heatmap[1][0], heatmap[1][1], bins=40, range=plot_range, alpha=0.6, zorder=2, cmin=0.01)
    axes[1][0].invert_yaxis()
    axes[1][0].imshow(img, zorder=1)

    img = Image.open(Utilities.DatasetLoader.CALIBRATE_PICTURE)
    img = img.resize(plot_size)

    axes[1][1].set_title('Calibration')
    axes[1][1].hist2d(heatmap[2][0], heatmap[2][1], bins=40, range=plot_range, alpha=0.6, zorder=2, cmin=0.01)
    axes[1][1].invert_yaxis()
    axes[1][1].imshow(img, zorder=1)

    figure.canvas.print_png(full_path)
    figure.clf()


def create_calibration_histogram(heatmap, full_path='cali'):
    figure = Figure(figsize=fig_size, dpi=dpi, frameon=False)  # frameoff for transparent background
    canvas = FigureCanvas(figure)

    img = Image.open(Utilities.DatasetLoader.CALIBRATE_PICTURE)
    img = img.resize(plot_size)

    ax = figure.gca()
    ax.axis('off')
    ax.hist2d(heatmap[0], heatmap[1], bins=40, range=plot_range, alpha=0.6, zorder=2, cmin=0.01)
    ax.invert_yaxis()
    ax.imshow(img, zorder=1)

    path = full_path + '.png'
    figure.canvas.print_png(path)
    figure.clf()

    return path


def plots_from_raws(paths, participant_id):
    total_time = 0
    for index, path in enumerate(paths):
        print("Starting process of test {} of {} -- {}".format(index + 1, len(paths), path))
        dic = Utilities.read_dic(path)
        dataset_name = re.findall(r'([^\/]+)\.', path)[0]
        # use plot generation for trial-wide calibration
        if 'calibration' in dic:
            total_time += test_calibration(dic, participant_id, dataset_name)
        else:
            total_time += trial_calibration(dic, participant_id, dataset_name)

    print("Total time of this session and participant: {0:.3f} sec or {1} min and {2:.3f} sec".format(
        total_time, (total_time // 60), (total_time % 60)))


def trial_calibration(dic, participant_id, dataset_name):
    processed = process(dic['eyetracking'])
    heatmaps = get_coords_for_heatmaps(processed)
    offset = offset_calibrations(heatmaps, dic['geometry'])
    trimmed = trim_heatmaps(offset, dic['geometry'])
    create_plots(trimmed, participant_id, dataset_name)

    return calculate_stats(processed)


def test_calibration(dic, participant_id, dataset_name):
    processed = process(dic['eyetracking'])
    heatmaps = get_coords_for_heatmaps(processed)
    trimmed = trim_heatmaps(heatmaps, dic['geometry'])

    processed_cali = process_picture_eyetracking_data(dic['calibration'])
    cali_heat = get_coords_for_heatmap(processed_cali)
    cali_trim = trim_heatmap(cali_heat, dic['geometry'])

    create_plots(trimmed, participant_id, dataset_name, calibration=cali_trim)
    return calculate_stats(processed)


def calculate_stats(processed):
    # add iti
    sum = 50
    for picture in processed:
        sum += picture[2] / 1000

    print("Time for this dataset: {0:.3f} sec or {1} min and {2:.3f} sec".format(sum, (sum // 60), (sum % 60)))
    return sum


def _duplicate_path(path, counter=1):
    if os.path.isfile(path):
        return _copy_path(path[:-4] + '_' + str(counter) + path[-4:], counter + 1)
    else:
        return path


def _copy_path(path, counter):
    if os.path.isfile(path):
        return _copy_path(path[:-5] + str(counter) + path[-4:], counter + 1)
    else:
        return path


if __name__ == '__main__':
    paths = [f for f in glob.glob('*.txt')]
    plots_from_raws(paths, 1)
