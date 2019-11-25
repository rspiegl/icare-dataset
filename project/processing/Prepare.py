import os
import re

import pandas as pd

import Utilities
import processing.TestProcessor as tp
from processing.Evaluation import Evaluation

BASE_PATH = 'processing/prepared/'
PATH = BASE_PATH + '{}/'

SCORE_CSV_PATH = BASE_PATH + 'scores.csv'
IMAGE_DURATION_CSV_PATH = BASE_PATH + 'images.csv'

SCORE_CSV_COLUMNS = ['participant', 'dataset', 'p', 'n', 'tp', 'fn', 'fp', 'tn', 'precision', 'recall', 'tnr',
                     'fnr', 'accuracy', 'f1', 'mean', 'variance', 'duration', 'number']
SCORE_CSV_INDEX = SCORE_CSV_COLUMNS[:2]
IMAGE_DURATION_CSV_COLUMNS = ['participant', 'dataset', 'image', 'true_value', 'pred_value', 'duration']
IMAGE_DURATION_CSV_INDEX = IMAGE_DURATION_CSV_COLUMNS[:3]


def determine_version(dic):
    version = None
    if 'calibration' in dic:
        version = Utilities.RawDataVersion.TESTCALIBRATION
    else:
        version = Utilities.RawDataVersion.TRIALCALIBRATION
    return version


def clean_timestamps_from_raws(directory):
    files = Utilities.list_files(directory + '*.txt')
    for file in files:
        new_file = file[:-16] + file[-4:]
        os.rename(file, new_file)


def prepare_dataframes(directory, pid):
    files = Utilities.list_files(directory + '*.txt')
    path = PATH.format(pid)
    if not os.path.isdir(path):
        os.makedirs(path)

    score_dics = []
    image_duration_dics = []

    for file in files:
        dic = Utilities.read_dic(file)
        dataset = re.findall(tp.identifier_regex, file)[0]
        version = determine_version(dic)
        e = Evaluation()
        e.evaluate(dic['eyetracking'])
        evals = {'participant': pid, 'dataset': dataset}
        evals.update(e.__dict__)
        score_dics.append(evals)

        for trial in dic['eyetracking']:
            # recalibrate eyetracking data if available
            if version == Utilities.RawDataVersion.TRIALCALIBRATION:
                processed_calibration = tp.process_picture_eyetracking_data(trial[4])

            image_name = re.findall(tp.identifier_regex, trial[0][0])[0]
            image_duration = round(trial[2] / 1000 / 1000, 3)
            image_duration_dic = {'participant': pid, 'dataset': dataset, 'image': image_name,
                                  'true_value': trial[0][1], 'pred_value': trial[1], 'duration': image_duration}
            image_duration_dics.append(image_duration_dic)

    part_score_df = pd.DataFrame(score_dics)
    image_duration_df = pd.DataFrame(image_duration_dics)

    save_dataframes(image_duration_df, part_score_df)


def save_dataframes(image_duration_df, part_score_df):
    if os.path.exists(SCORE_CSV_PATH):
        score_csv_df = pd.read_csv(SCORE_CSV_PATH)
        score_csv_df.append(part_score_df)
    else:
        score_csv_df = part_score_df
    if os.path.exists(IMAGE_DURATION_CSV_PATH):
        image_csv_df = pd.read_csv(IMAGE_DURATION_CSV_PATH)
        image_csv_df.append(image_duration_df)
    else:
        image_csv_df = image_duration_df

    score_csv_df.to_csv(SCORE_CSV_PATH)
    image_csv_df.to_csv(IMAGE_DURATION_CSV_PATH)
