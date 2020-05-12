import os

import numpy as np
import matplotlib.pyplot as plt

from processing.Evaluate import DATASETS, RANGE_PIC, BINS
from processing.Prepare import load_images_dataframe

PATH = 'diagrams/{}/'
FILE = '{}.png'
SWITCHES = 'switches'


def switches_histogram():
    df = load_images_dataframe()
    gb = df.groupby('dataset')
    for d in DATASETS:
        group = gb.get_group(d)
        create_histogram(group['switches_fixations'], SWITCHES, d)
    create_histogram(df['switches_fixations'], SWITCHES, 'all')


def create_histogram(data, directory: str, file: str):
    save_path = PATH.format(directory)
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    save_path += FILE.format(file)
    bins = np.arange(0, data.max() + 1.5) - 0.5
    data.hist(bins=bins, grid=False)
    plt.gca().set_xlabel('Number of alternations of fixations over the middle line')
    plt.gca().set_ylabel('Bin counts')
    plt.savefig(save_path)
    plt.clf()

def create_histogram_cropped(data, img, file: str):
    plt.hist2d(data['x'], data['y'], weights=data['dur'], bins=BINS,
               range=RANGE_PIC, alpha=0.8, zorder=2, cmin=0.0001)
    plt.margins(0, 0)
    plt.gca().invert_yaxis()
    plt.gca().xaxis.set_major_locator(plt.NullLocator())
    plt.gca().yaxis.set_major_locator(plt.NullLocator())
    plt.gca().set_axis_off()
    plt.imshow(img, zorder=1)
    plt.savefig(file, bbox_inches='tight', pad_inches=0)