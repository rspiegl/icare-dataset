import glob
import os.path
import re

import numpy as np
import pandas as pd
from PIL import Image
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from processing import Prepare, InteractiveSelectors
from processing.pygazeanalyser import detectors, gazeplotter

DATASETS = ['sr', 'svrt1', 'random_board_images_big_diff5',
            'random_board_images_big_diff1', 'sd', 'svrt19', 'camerarot_diff5',
            'camerarot_diff1', 'svrt20', 'svrt21', 'rot_images_diff5',
            'rot_images_diff1']
IDS = [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
GEOMETRY = (703, 54, 512, 512)
PATH = "processing/prepared/{}/{}/"
IMAGE_NAME_REGEX = r'[^\/]+\/\d+_([^\/]+)\.'

RANGE_GUI = [[0, 1920], [0, 1160]]
RANGE_PIC = [[0, 512], [0, 512]]
PLOT_SIZE = [512, 512]
DPI = 100
FIG_SIZE = [51.2, 51.2]
MAX_VEL = 120
DEFAULT_CALIBRATION = (6.4, 32.0)


def range_from_geo(g):
    return [[g[0], g[0] + g[2]], [g[1], g[1] + g[3]]]


def get_file_paths(path):
    f = glob.glob(path + '*.pkl')
    f.sort(key=os.path.getmtime)
    images = [i for i in f if 'calibration' not in i]
    files = []
    for image in images:
        cali, im_path = None, None
        if os.path.exists(image[:-4] + '_calibration.pkl'):
            cali = image[:-4] + '_calibration.pkl'
        if os.path.exists(image[:-4] + '.jpg'):
            im_path = image[:-4] + '.jpg'
        elif os.path.exists(image[:-4] + '.png'):
            im_path = image[:-4] + '.png'

        files.append([image, cali, im_path])
    return files


def get_cali(calis, im):
    for c in calis:
        if im[:-4] in c:
            return c
    return None


def trim_image(listxy):
    xpic, ypic, width, height = GEOMETRY

    coords = [[x - xpic, y - ypic] for x, y in listxy if
              xpic <= x <= xpic + width and ypic <= y <= ypic + height]
    if not coords:
        return None

    c = np.asarray(coords, dtype=np.int)
    return np.asarray([c[:, 0], c[:, 1]])


def trim_fixations(fix: dict):
    tx, ty, tdur = [], [], []
    xpic, ypic, width, height = GEOMETRY

    for x, y, dur in zip(fix['x'], fix['y'], fix['dur']):
        if xpic <= x <= xpic + width and ypic <= y <= ypic + height:
            tx.append(x - xpic)
            ty.append(y - ypic)
            tdur.append(dur)
    return {'x': np.asarray(tx), 'y': np.asarray(ty), 'dur': np.asarray(tdur)}


def trim_saccades(sac: list):
    n = []
    xpic, ypic, width, height = GEOMETRY
    for st, et, dur, sx, sy, ex, ey in sac:
        if (xpic <= sx <= xpic + width and ypic <= sy <= ypic + height
                and xpic <= ex <= xpic + width and ypic <= ey <= ypic + height):
            n.append([st, et, dur, sx - xpic, sy - ypic, ex - xpic, ey - ypic])

    return n


def offset_calibration(image_df: pd.DataFrame, calibration_df: pd.DataFrame):
    xy = image_df.drop('times', axis=1).values
    xy_cali = calibration_df.values

    xybins = 40
    bin_middle = GEOMETRY[2] / xybins / 2
    H, xedges, yedges = np.histogram2d(xy_cali[:, 0], xy_cali[:, 1], bins=xybins, range=RANGE_PIC)
    x_cent, y_cent = np.unravel_index(H.argmax(), H.shape)
    x_offset = xedges[x_cent] + bin_middle - (RANGE_PIC[0][1] // 2)
    y_offset = yedges[y_cent] + bin_middle - (RANGE_PIC[1][1] // 2)

    new = [[x - x_offset, y - y_offset] for x, y in xy]
    return np.asarray(new, dtype=np.int)


def offset_calibration_default(image_df: pd.DataFrame):
    xy = image_df.drop('times', axis=1).values
    new = [[x - DEFAULT_CALIBRATION[0], y - DEFAULT_CALIBRATION[1]] for x, y in xy]
    return np.asarray(new, dtype=np.int)


def draw_plots(trim: np.ndarray, cali_trim: np.ndarray, image_path: str, save_path: str, trim_fix: dict,
               trim_sac: list, good_path: str = None):
    img = Image.open(image_path)
    img = img.resize(PLOT_SIZE)
    figure = Figure(figsize=(18, 11.5), dpi=DPI)
    canvas = FigureCanvas(figure)
    axes = figure.subplots(ncols=3, nrows=2)
    axes[0][0].set_title('Original')
    axes[0][0].imshow(img, zorder=1)
    if trim is not None:
        axes[0][1].set_title('Uncalibrated')
        axes[0][1].hist2d(trim[0], trim[1], bins=40, range=RANGE_PIC, alpha=0.6, zorder=2, cmin=0.01)
        axes[0][1].invert_yaxis()
        axes[0][1].imshow(img, zorder=1)
    else:
        axes[0][1].axis('off')
    if cali_trim is not None:
        axes[0][2].set_title('Calibrated')
        axes[0][2].hist2d(cali_trim[0], cali_trim[1], bins=40, range=RANGE_PIC, alpha=0.6, zorder=2, cmin=0.01)
        axes[0][2].invert_yaxis()
        axes[0][2].imshow(img, zorder=1)
    else:
        axes[0][2].axis('off')
    if trim_fix:
        siz = 3 * (trim_fix['dur'] / 30)
        axes[1][0].set_title('Fixations')
        axes[1][0].imshow(img, zorder=1)
        axes[1][0].scatter(trim_fix['x'], trim_fix['y'], s=siz, marker='o', color='g', alpha=0.7, zorder=2)

        axes[1][1].set_title('Scanpath')
        axes[1][1].imshow(img, zorder=1)
        for i in range(len(trim_fix['x'])):
            axes[1][1].annotate(str(i), (trim_fix['x'][i], trim_fix['y'][i]), zorder=4, alpha=1,
                                horizontalalignment='center', verticalalignment='center',
                                multialignment='center', color='g')

        if trim_sac:
            axes[1][2].set_title('Scanpath zoomed with saccades')
            axes[1][2].scatter(trim_fix['x'], trim_fix['y'], s=siz, marker='o', color='g', alpha=0.2, zorder=2)
            for i in range(len(trim_fix['x'])):
                axes[1][2].annotate(str(i), (trim_fix['x'][i], trim_fix['y'][i]), zorder=4, alpha=1,
                                    horizontalalignment='center', verticalalignment='center',
                                    multialignment='center')
            for st, et, dur, sx, sy, ex, ey in trim_sac:
                axes[1][2].arrow(sx, sy, ex - sx, ey - sy, alpha=0.7, zorder=3, fill=True, shape='full', width=10,
                                 head_width=20, head_starts_at_zero=False, overhang=0)
            axes[1][2].invert_yaxis()
        else:
            axes[1][2].axis('off')
    else:
        axes[1][0].axis('off')
        axes[1][1].axis('off')

    figure.canvas.print_png(save_path)
    if good_path and len(trim_fix['x']) > 4:
        figure.canvas.print_png(good_path)
    figure.clf()


def create_plots(ids=(3, 14), dats=DATASETS, good_pic=True):
    for i in range(ids[0], ids[1]):
        for d in dats:
            print('id: {}, dat: {}'.format(i, d))
            ici = get_file_paths(PATH.format(i, d))
            for im, cali, im_path in ici:
                impk = pd.read_pickle(im)
                im_cali = None
                if cali:
                    im_cali = offset_calibration(impk.dropna(), pd.read_pickle(cali))
                else:
                    im_cali = offset_calibration_default(impk.dropna())
                cali_trim = trim_image(im_cali)

                trim = trim_image(impk.dropna().drop('times', axis=1).values)
                _, fixations = detectors.fixation_detection(impk['x'].values, impk['y'].values, impk['times'].values,
                                                            maxdist=42, mindur=100)
                _, saccades = detectors.saccade_detection(impk['x'].values, impk['y'].values, impk['times'].values,
                                                          minlen=20, maxvel=MAX_VEL)
                trim_fix = trim_fixations(gazeplotter.parse_fixations(fixations))
                trim_sac = trim_saccades(saccades)

                path = 'plots/{}/{}/'.format(i, d)
                if not os.path.exists(path):
                    os.makedirs(path)
                good_path = 'plots/{}/'.format(d)
                if not os.path.exists(good_path):
                    os.makedirs(good_path)
                save_path = path + im.rpartition('/')[-1][:-4] + '.png'
                good_path += str(i) + '_' + im.rpartition('/')[-1][:-4] + '.png'
                draw_plots(trim, cali_trim, im_path, save_path, trim_fix, trim_sac, good_path if good_pic else None)


def find_middle_lines(ids=(3, 14), dats=DATASETS):
    image_df = Prepare.load_images_dataframe().set_index(Prepare.IMAGE_DURATION_CSV_COLUMNS[:3])
    cont = "c"
    for i in range(ids[0], ids[1]):
        for d in dats:
            print('id: {}, dat: {}'.format(i, d))
            ici = get_file_paths(PATH.format(i, d))
            for im, cali, im_path in ici:
                image_name = re.findall(IMAGE_NAME_REGEX, im_path)[0]
                impk = pd.read_pickle(im)

                trim = trim_image(impk.dropna().drop('times', axis=1).values)
                if trim:
                    x, y, = trim
                    line_start, line_end = InteractiveSelectors.get_line_coords(x, y, im_path)
                    image_df.at[(i, d, image_name), 'line_start_x'] = line_start[0]
                    image_df.at[(i, d, image_name), 'line_start_y'] = line_start[1]
                    image_df.at[(i, d, image_name), 'line_end_x'] = line_end[0]
                    image_df.at[(i, d, image_name), 'line_end_y'] = line_end[1]
            cont = input(d + " done, e for exit")
            if cont == "e":
                print("stopped after {} {}".format(i, d))
                break
        if cont != "e":
            cont = input("ID " + str(i) + " done, e for exit")
        if cont == "e":
            print("stopped at {}".format(i))
            break

    image_df.to_csv(Prepare.IMAGE_DURATION_CSV_PATH, columns=Prepare.IMAGE_DURATION_CSV_COLUMNS[3:])


if __name__ == '__main__':
    pass
