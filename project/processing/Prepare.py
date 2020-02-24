import os
import re
import shutil

import numpy as np
import pandas as pd

import Utilities
import processing.TestProcessor as tp
from Utilities import RawDataVersion
from processing.TestEvaluation import TestEvaluation

BASE_PATH = 'processing/prepared/'
PATH = BASE_PATH + '{}/'

SCORE_CSV_PATH = BASE_PATH + 'scores.csv'
IMAGE_DURATION_CSV_PATH = BASE_PATH + 'images.csv'

SCORE_CSV_COLUMNS = ['participant', 'dataset', 'number', 'p', 'n', 'tp', 'fn', 'fp', 'tn', 'precision', 'recall',
                     'tnr', 'fnr', 'accuracy', 'f1',
                     'total_duration', 'images_mean', 'images_variance', 'images_duration', 'images_duration_min',
                     'images_duration_max',
                     'pause_mean', 'pause_variance', 'pause_duration', 'pause_duration_min', 'pause_duration_max']
SCORE_CSV_INDEX = SCORE_CSV_COLUMNS[:2]
IMAGE_DURATION_CSV_COLUMNS = ['participant', 'dataset', 'image', 'true_value', 'pred_value', 'duration', 'break']
IMAGE_DURATION_CSV_INDEX = IMAGE_DURATION_CSV_COLUMNS[:3]

def determine_version(dic):
    if 'calibration' in dic:
        version = RawDataVersion.TESTCALIBRATION
    else:
        version = RawDataVersion.TRIALCALIBRATION
    return version


def clean_timestamps_from_raws(directory):
    files = Utilities.list_files(directory + '*.txt')
    for file in files:
        new_file = file[:-16] + file[-4:]
        os.rename(file, new_file)


def prepare_dataframes(directory, pid, scores=True, images=True, image_generation=True):
    files = Utilities.list_files(directory + '*.txt')
    path = PATH.format(pid)
    if not os.path.isdir(path):
        os.makedirs(path)

    score_dics = []
    image_duration_dics = []

    for file in files:
        dic = Utilities.read_dic(file)
        dataset = re.findall(tp.identifier_regex, file)[0]
        dataset_path = path + dataset + '/'
        version = determine_version(dic)
        geometry = dic['geometry']
        # score evaluation
        e = TestEvaluation()
        e.evaluate(dic['eyetracking'])
        evals = {'participant': pid, 'dataset': dataset}
        evals.update(e.__dict__)
        score_dics.append(evals)

        if not images and not image_generation:
            continue

        if not os.path.isdir(dataset_path):
            os.makedirs(dataset_path)
        prev = 0
        # image evaluation
        for index, trial in enumerate(dic['eyetracking']):
            image_name = re.findall(tp.identifier_regex, trial[0][0])[0]
            image_path = dataset_path + str(index) + '_' + image_name

            # copy file
            if os.path.exists(trial[0][0]):
                shutil.copyfile(trial[0][0], image_path + trial[0][0][-4:])

            processed = tp.process_picture(trial)
            if processed[3] and not os.path.exists(image_path + '.pkl') and image_generation:
                timestamps = tp.get_timestamps(processed[3])
                coords = tp.get_coords_for_heatmaps([processed])[0]

                image_df = pd.DataFrame({'x': coords[1][0], 'y': coords[1][1], 'times': timestamps})
                if not (np.isnan(image_df['x'].values)).all():
                    image_df.to_pickle(image_path + '.pkl')

                if version == RawDataVersion.TRIALCALIBRATION and len(coords) == 3 and coords[2]:
                    xs, ys = tp.trim_heatmap(coords[2], geometry)
                    if xs and ys:
                        image_df = pd.DataFrame({'x': list(xs), 'y': list(ys)})
                        image_df.to_pickle(image_path + '_calibration.pkl')

            if images:
                image_duration = round(processed[2] / 1000, 3)
                # break calculation
                image_break = None
                if index == 0:
                    if len(trial) > 5:
                        prev = trial[5][1]
                    elif trial[3]:
                        prev = trial[3][-1]['system_time_stamp']
                    elif not trial[3]:
                        prev = (image_duration + 0.5) * 1000 * 1000
                else:
                    if len(trial) > 5:
                        image_break = round((trial[5][0] - prev) / 1000 / 1000, 3)
                        prev = trial[5][-1]
                    elif trial[3]:
                        image_break = round((trial[3][0]['system_time_stamp'] - prev) / 1000 / 1000, 3)
                        prev = trial[3][-1]['system_time_stamp']
                    elif not trial[3]:
                        prev += (image_duration + 0.5) * 1000 * 1000
                image_duration_dic = {'participant': pid, 'dataset': dataset, 'image': image_name,
                                      'true_value': processed[0][1], 'pred_value': processed[1],
                                      'duration': image_duration, 'break': image_break}
                image_duration_dics.append(image_duration_dic)

    if scores:
        part_score_df = pd.DataFrame(score_dics)
        save_dataframes(SCORE_CSV_PATH, SCORE_CSV_COLUMNS, part_score_df)
    if images:
        image_duration_df = pd.DataFrame(image_duration_dics)
        save_dataframes(IMAGE_DURATION_CSV_PATH, IMAGE_DURATION_CSV_COLUMNS, image_duration_df)


def save_dataframes(path, columns, df):
    if os.path.exists(path):
        temp_df = pd.read_csv(path)
        temp_df = temp_df.append(df, sort=False)
    else:
        temp_df = df

    temp_df.to_csv(path, columns=columns, index=False)


def load_scores_dataframe():
    return pd.read_csv(SCORE_CSV_PATH)
