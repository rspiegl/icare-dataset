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
IMAGE_CSV_PATH = BASE_PATH + 'images.csv'

SCORE_CSV_COLUMNS = ['number', 'score', 'rule', 'solved', 'hard', 'p', 'n', 'tp', 'fn', 'fp', 'tn', 'precision',
                     'recall',
                     'tnr', 'fnr', 'accuracy', 'f1',
                     'total_duration', 'images_mean', 'images_variance', 'images_duration', 'images_duration_min',
                     'images_duration_max',
                     'pause_mean', 'pause_variance', 'pause_duration', 'pause_duration_min', 'pause_duration_max']
SCORE_CSV_DROP = ['p', 'n', 'tp', 'fn', 'fp', 'tn', 'images_mean', 'images_variance', 'images_duration_min',
                  'images_duration_max',
                  'pause_mean', 'pause_variance', 'pause_duration_min', 'pause_duration_max']
SCORE_CSV_INDEX = ['participant', 'dataset']
IMAGE_CSV_COLUMNS = ['trial', 'true_value', 'pred_value', 'duration', 'break',
                     'switches_fixations', 'fixations', 'p_nan', 'len', 'switches',
                     'line_start_x', 'line_start_y', 'line_end_x', 'line_end_y']
IMAGE_CSV_DROP = ['line_start_x', 'line_start_y', 'line_end_x', 'line_end_y']
IMAGE_CSV_INDEX = ['participant', 'dataset', 'image']


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
    image_dics = []

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
                image_break = 0
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
                                      'duration': image_duration, 'break': image_break, 'line_start_x': None,
                                      'line_start_y': None, 'line_end_x': None, 'line_end_y': None, 'switches': None}
                image_dics.append(image_duration_dic)

    if scores:
        part_score_df = pd.DataFrame(score_dics, index=SCORE_CSV_INDEX)
        save_dataframes(SCORE_CSV_PATH, SCORE_CSV_COLUMNS, part_score_df)
    if images:
        image_duration_df = pd.DataFrame(image_dics, index=IMAGE_CSV_INDEX)
        save_dataframes(IMAGE_CSV_PATH, IMAGE_CSV_COLUMNS, image_duration_df)


def save_dataframes(path, df):
    if os.path.exists(path):
        temp_df = pd.read_csv(path)
        temp_df = temp_df.append(df, sort=False)
    else:
        temp_df = df

    temp_df.to_csv(path)


def load_scores_dataframe():
    return pd.read_csv(SCORE_CSV_PATH, index_col=SCORE_CSV_INDEX)


def load_images_dataframe():
    return pd.read_csv(IMAGE_CSV_PATH, index_col=IMAGE_CSV_INDEX)


def transform_camerarot_fixedposition():
    replace = ('camerarot', 'fixed_pos')
    replace2 = ('rot_images', 'camera_rotation')
    replace3 = ('random_board_images_big', 'random_board')
    ending = ('.txt', '.json')
    path_replace = ('processing', 'json')
    base_path = 'processing/{}/*.txt'
    import json

    for i in range(3, 15):
        dict_files = Utilities.list_files(base_path.format(i))
        for dict_file in dict_files:
            save_path = dict_file.replace(ending[0], ending[1]).replace(path_replace[0], path_replace[1])
            dic = Utilities.read_dic(dict_file)
            if replace[0] in dict_file:
                for image in dic['eyetracking']:
                    image[0][0] = image[0][0].replace(replace[0], replace[1])
                save_path = save_path.replace(replace[0], replace[1])
            elif replace2[0] in dict_file:
                for image in dic['eyetracking']:
                    image[0][0] = image[0][0].replace(replace2[0], replace2[1])
                save_path = save_path.replace(replace2[0], replace2[1])
            elif replace3[0] in dict_file:
                for image in dic['eyetracking']:
                    image[0][0] = image[0][0].replace(replace3[0], replace3[1])
                save_path = save_path.replace(replace3[0], replace3[1])

            new_dic = convert_to_upload(dic)

            if not os.path.exists('json/{}/'.format(i)):
                os.makedirs('json/{}/'.format(i))
            with open(save_path, 'w') as file:
                json.dump(new_dic, file)


def copy_pic_toJson():
    path_pre = 'json/'
    base_path = 'processing/{}/*.txt'
    from shutil import copyfile

    for i in range(3, 15):
        dict_files = Utilities.list_files(base_path.format(i))
        for dict_file in dict_files:
            dic = Utilities.read_dic(dict_file)
            for image in dic['eyetracking']:
                picture = image[0][0]
                dir_name = path_pre + os.path.dirname(picture)
                if not os.path.exists(dir_name):
                    os.makedirs(dir_name)
                copyfile(picture, path_pre + picture)


def convert_to_upload(dic):
    geometry_keys = ['x', 'y', 'width', 'height']
    screen_resolution = {'width': 1920, 'height': 1200}
    geometry = {k: v for (k, v) in zip(geometry_keys, dic['geometry'])}
    trials = []
    for trial in dic['eyetracking']:
        trial_dic = {'image_path': trial[0][0], 'true_value': trial[0][1], 'pred_value': trial[1],
                     'duration_ms': round(trial[2] / 1000), 'trial_capture': trial[3]}
        trials.append(trial_dic)

    return {'geometry': geometry, 'screen_resolution': screen_resolution, 'trials': trials}
