import glob
import os.path

import numpy as np
import pandas as pd
from PIL import Image
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

DATASETS = ['sr', 'svrt1', 'random_board_images_big_diff5',
            'random_board_images_big_diff1', 'sd', 'svrt19', 'camerarot_diff5',
            'camerarot_diff1', 'svrt20', 'svrt21', 'rot_images_diff5',
            'rot_images_diff1']

GEOMETRY = (703, 54, 512, 512)
PATH = "processing/prepared/{}/{}/"

RANGE_GUI = [[0, 1920], [0, 1160]]
RANGE_PIC = [[0, 512], [0, 512]]
PLOT_SIZE = [512, 512]
DPI = 100
FIG_SIZE = [51.2, 51.2]


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


def draw_plots(trim: np.ndarray, cali_trim: np.ndarray, image_path: str, save_path: str):
    img = Image.open(image_path)
    img = img.resize(PLOT_SIZE)
    figure = Figure(figsize=(8.4, 4.8), dpi=DPI)
    canvas = FigureCanvas(figure)
    axes = figure.subplots(ncols=3, nrows=1)
    axes[0].set_title('Original')
    axes[0].imshow(img, zorder=1)
    if trim is not None:
        axes[1].set_title('Uncalibrated')
        axes[1].hist2d(trim[0], trim[1], bins=40, range=RANGE_PIC, alpha=0.6, zorder=2, cmin=0.01)
        axes[1].invert_yaxis()
        axes[1].imshow(img, zorder=1)
    else:
        axes[1].axis('off')
    if cali_trim is not None:
        axes[2].set_title('Calibrated')
        axes[2].hist2d(cali_trim[0], cali_trim[1], bins=40, range=RANGE_PIC, alpha=0.6, zorder=2, cmin=0.01)
        axes[2].invert_yaxis()
        axes[2].imshow(img, zorder=1)
    else:
        axes[2].axis('off')

    figure.canvas.print_png(save_path)
    figure.clf()


def create_plots(ids=(3, 14)):
    for i in range(ids[0], ids[1]):
        for d in DATASETS:
            print('id: {}, dat: {}'.format(i, d))
            ici = get_file_paths(PATH.format(i, d))
            for im, cali, im_path in ici:
                impk = pd.read_pickle(im)
                cali_trim = None
                if cali:
                    im_cali = offset_calibration(impk.dropna(), pd.read_pickle(cali))
                    cali_trim = trim_image(im_cali)

                trim = trim_image(impk.dropna().drop('times', axis=1).values)

                path = 'plots/{}/{}/'.format(i, d)
                if not os.path.exists(path):
                    os.makedirs(path)
                save_path = path + im.rpartition('/')[-1][:-4] + '.png'
                draw_plots(trim, cali_trim, im_path, save_path)


if __name__ == '__main__':
    pass
