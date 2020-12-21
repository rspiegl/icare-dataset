import os
from typing import List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy.stats as stats

from processing.Evaluate import RANGE_PIC, BINS
from processing.Prepare import load_images_dataframe

PATH = 'diagrams/{}/'
FILE = '{}.png'
SWITCHES = 'switches'
REPLACE = {'sr': 'SR', 'sd': 'SD', 'svrt1': 'SVRT1', 'svrt19': 'SVRT19', 'svrt20': 'SVRT20', 'svrt21': 'SVRT21',
           'random_board_images_big_diff5': 'RBP5', 'random_board_images_big_diff1': 'RBP1',
           'fixed_pos_diff5': 'FP5', 'fixed_pos_diff1': 'FP1', 'rot_images_diff5': 'CR5',
           'rot_images_diff1': 'CR1'}
DATASETS = ['SR', 'SVRT1', 'RBP5', 'RBP1', 'SD', 'SVRT19', 'FP5', 'FP1', 'SVRT20', 'SVRT21', 'CR5', 'CR1']
DATASETS_BY_ORDER = ['SR', 'SD', 'SVRT1', 'SVRT19', 'SVRT20', 'SVRT21', 'RBP5', 'RBP1', 'FP5', 'FP1', 'CR5', 'CR1']


def switches_histogram(df=None):
    if df is None:
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
    bins = np.arange(0, data.max() + 0.5)
    data.hist(bins=bins, grid=False, rwidth=0.8, color='black')
    plt.gca().set_xlim(left=-1, right=70)
    plt.gca().set_xlabel('Number of alternations of fixations over the middle line')
    plt.gca().set_ylabel('Number of instances')
    plt.savefig(save_path)
    plt.clf()


def create_histogram_cropped(data, img, file: str) -> None:
    plt.hist2d(data['x'], data['y'], weights=data['dur'], bins=BINS,
               range=RANGE_PIC, alpha=0.8, zorder=2, cmin=0.0001)
    plt.margins(0, 0)
    plt.gca().invert_yaxis()
    plt.gca().xaxis.set_major_locator(plt.NullLocator())
    plt.gca().yaxis.set_major_locator(plt.NullLocator())
    plt.gca().set_axis_off()
    plt.imshow(img, zorder=1)
    plt.savefig(file, bbox_inches='tight', pad_inches=0)


def densityplots(df: pd.DataFrame, column: str, group_column: str = 'dataset', group_column_order: tuple = DATASETS,
                 nrows: int = 3, ncols: int = 4, figsize: tuple = (12, 9), sharey: bool = True, sharex: bool = True) \
        -> None:
    fig, axes = plt.subplots(nrows=nrows, ncols=ncols, figsize=figsize, sharey=sharey, sharex=sharex)
    gb = df.groupby(group_column)
    for (dataset, ax) in zip(group_column_order, axes.flatten()):
        data = gb.get_group(dataset)[column]
        d = np.diff(np.unique(data)).min()
        left = data.min() - float(d) / 2
        right = data.max() + float(d) / 2
        ax.hist(data, np.arange(left, right + d, d), density=True)
        ax.set_title(dataset)


def scatterplots(df: pd.DataFrame, columns: List[str], group_column: str = 'dataset',
                 group_column_order: tuple = DATASETS,
                 nrows: int = 3, ncols: int = 4, figsize: tuple = (12.5, 9), sharey: bool = True, sharex: bool = True) \
        -> None:
    fig, axes = plt.subplots(nrows=nrows, ncols=ncols, figsize=figsize, sharey=sharey, sharex=sharex)
    fig.tight_layout()
    fig.subplots_adjust(bottom=0.06)
    gb = df.groupby(group_column)
    for (dataset, ax) in zip(group_column_order, axes.flatten()):
        ax.scatter(gb.get_group(dataset)[columns[0]], gb.get_group(dataset)[columns[1]], s=50, c='black')
        ax.set_xticks(range(7))
        ax.set_yticks(range(0, 36, 5))
        ax.set_title(dataset)

    for a in axes[-1, :]:
        a.set_xlabel(columns[0])
    for a in axes[:, 0]:
        a.set_ylabel(columns[1])

    fig.savefig('scatter.png', bbox_inces='tight', pad_inches=0)


def _pop_std(x: pd.Series):
    return x.std(ddof=0)


def calculate_mean(df: pd.DataFrame, columns: List[str], group_column: str = 'dataset') -> pd.DataFrame:
    return df.groupby(group_column).agg({c: ['mean', _pop_std] for c in columns})


def calculate_correlation(df: pd.DataFrame, column_1: str = 'fixations', column_2: str = 'switches_fixations') \
        -> Tuple[float, float, int]:
    return stats.pearsonr(df[column_1], df[column_2]) + (len(df[column_1]),)
