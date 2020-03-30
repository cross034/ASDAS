import pickle
import os
import time

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.spatial.distance import euclidean
from fastdtw import fastdtw

from data_preprocessing import main
from data_preprocessing import combiner


def get_average_curve(input_csv: pd.DataFrame):
    r"""
    Find the generalized curve to represent the class

    :param input_csv: raw class data
    :return: data points for generalized curve

    """

    general_copy = input_csv.copy()
    min_copy = input_csv.copy()
    max_copy = input_csv.copy()

    average_series = general_copy.mean()
    min_series = min_copy.min()
    max_series = max_copy.max()

    generalised = pd.DataFrame(average_series).transpose()
    minimised = pd.DataFrame(min_series).transpose()
    maximised = pd.DataFrame(max_series).transpose()

    labels = ['05 Jan', '04 Feb', '01 Mar', '05 Apr', '05 May', '04 Jun', '04 Jul', '03 Aug', '02 Sep',
              '02 Oct',
              '01 Nov', '01 Dec']
    indexes = [0, 6, 11, 18, 24, 30, 36, 42, 48, 54, 60, 66]

    plt.plot(generalised.values.tolist()[0][2:], '-g', label='general', alpha=1)
    plt.plot(minimised.values.tolist()[0][2:], '-r', label=f'min', alpha=0.5)
    plt.plot(maximised.values.tolist()[0][2:], '-b', label=f'max', alpha=0.5)

    plt.xlabel('2019')
    plt.ylabel(f'Band Values ')
    plt.title(f"DTW Curve Comparison")

    plt.xticks(indexes, labels, rotation=20)
    plt.grid(color='grey', linestyle='-', linewidth=0.25, alpha=0.5)
    plt.legend()

    plt.show()

    return generalised, minimised, maximised


# _____________________________________


def apply_dtw(template: pd.DataFrame, test: pd.DataFrame, display: False, single_pixel=False, pixel_index: int = 0):
    r"""
    Perform FastDTW algorithm on template graph and test graph.

    :param template: DataFrame with ONLY one curve to be used as reference
    :param test: DataFrame with all testing curve data
    :param display: Render graph
    :param single_pixel: To perform and display DTW on single pixel. Else perform on entire test DataFrame
    :param pixel_index: which data point (pixel) to select : 0-722
    :return: Plot, Distance and optimal Path for single pixel | List with distances between reference curve and all test
             curves.
    """
    template = template.values.tolist()[0][2:]

    if single_pixel:
        test = test.values.tolist()[pixel_index][2:]
        distance, path = fastdtw(np.asarray(template), np.asarray(test), dist=euclidean)

        if display:
            labels = ['05 Jan', '04 Feb', '01 Mar', '05 Apr', '05 May', '04 Jun', '04 Jul', '03 Aug', '02 Sep',
                      '02 Oct',
                      '01 Nov', '01 Dec']
            indexes = [0, 6, 11, 18, 24, 30, 36, 42, 48, 54, 60, 66]

            plt.plot(template, '-g', label='Template', alpha=1)
            plt.plot(test, '-r', label=f'Test : Pixel {pixel_index}', alpha=0.5)

            for entry in path:
                y_value = []
                x_value = []
                y_value.append(template[entry[0]])
                y_value.append(test[entry[1]])
                x_value.append(entry[0])
                x_value.append(entry[1])
                plt.plot(x_value, y_value, '--bo', alpha=0.3)

            plt.xlabel('2019')
            plt.ylabel(f'Band Values ')
            plt.title(f"DTW Curve Comparison")

            plt.xticks(indexes, labels, rotation=20)
            plt.grid(color='grey', linestyle='-', linewidth=0.25, alpha=0.5)
            plt.legend()

            plt.show()
        return distance, path

    else:
        distance_list = []
        for row in test.iterrows():
            test = row[1][2:]
            distance, path = fastdtw(np.asarray(template), np.asarray(test), dist=euclidean)
            distance_list.append(distance)
            print(f"Done for Data point : {row[0]}")

        if display:
            plt.bar(np.arange(len(distance_list)), distance_list)
            plt.xlabel('Pixels')
            plt.ylabel('Distance')
            plt.title('DTW Distances comparison')
            plt.axhline(y=2.00)
            plt.show()

        return distance_list


# _____________________________________


def calculate_threshold(distance_list: list, test_distance: float):
    r"""
    Calculate the threshold of the data list based on the percentile given.

    :param distance_list: Input data list
    :param test_distance: Distance of testing curve
    :return: Value of the percentile of input data
    """
    temp_data_list = distance_list.copy()
    temp_data_list.sort()

    rank = sum(i < test_distance for i in temp_data_list)
    percentile = (rank * 100) / len(distance_list)
    print(
        f"Distance = {test_distance}. "
        f"\t|\tPERCENTILE : {percentile}")

    return percentile


# _____________________________________


def pickler(generalized_curve: pd.DataFrame, distances_list: list, name_of_class: str, name_of_band: str):
    r"""
    Creates a pickle file to store Generalized curve and distances_list for that class.

    :param generalized_curve: DataFrame with ONLY one curve (Template curve)
    :param distances_list: List  of DTW distances
    :param name_of_class: Class label
    :param name_of_band: Blue | Green | Red | NIR | SWIR | NDVI / NDWI / NDBI
    :return: None
    """
    dtw_data = {'general curve': generalized_curve, 'distances list': distances_list}
    filename = os.path.abspath(__file__ + "/../../") + f"/data_2019/Pickles/{name_of_band}/DTW_{name_of_class}.dat"
    outfile = open(filename, 'wb')
    pickle.dump(dtw_data, outfile)
    outfile.close()


# _____________________________________


def unpickler(name_of_class: str, name_of_band: str):
    r"""
    Function to read DTW data from pickled file.

    :param name_of_class: Class label of requested data
    :param name_of_band: Blue | Green | Red | NIR | SWIR | NDVI / NDWI / NDBI
    :return: Dictionary with generalized curve and distances list of training samples
    """
    file_name = os.path.abspath(__file__ + "/../../") + f"/data_2019/Pickles/{name_of_band}/DTW_{name_of_class}.dat"

    infile = open(file_name, 'rb')
    new_dict = pickle.load(infile)
    infile.close()

    return new_dict


# _____________________________________


def trainer(input_data: pd.DataFrame, name_of_class: str, name_of_band: str):
    r"""
    Use training data to create a GENERALIZED curve and compute DTW-distances of every curve from it.


    :param input_data: raw input data
    :param name_of_class: Class label of requested data
    :param name_of_band: Blue | Green | Red | NIR | SWIR | NDVI / NDWI / NDBI
    :return: None
    """
    print(f"Training on : {name_of_class} - {name_of_band}")
    generalized_curve, minimised, maximised = get_average_curve(input_data)
    distances = apply_dtw(template=generalized_curve, test=input_data, single_pixel=False,
                          display=False)
    pickler(generalized_curve=generalized_curve, distances_list=distances, name_of_class=name_of_class,
            name_of_band=name_of_band)
    print(f"Pickled ! ")


# _____________________________________


def tester(test: pd.DataFrame, training_data_label: str = None):
    r"""
    Check the percentile of testing curve with generalised curve for every index and every class.

    :param test: Test DataFrame with curve data for testing (ONLY ONE in case of new, else whole training DataFrame)
    :param training_data_label: Class label of data, in case testing is done on training data with known labels.
    :return: DataFrame with distances from all class based generalized curves.
    """
    bands = ['NDVI', 'NDWI', 'NDBI']
    classes = ['Forests', 'Water', 'Agriculture', 'BarrenLand', 'Infrastructure']

    if training_data_label:
        data_frame = combiner.create_new_csv(name_of_class=training_data_label, get_geo_df=True)
        for index, rows in test.iterrows():
            for band in bands:
                for label in classes:
                    pickled_dict = unpickler(name_of_class=label, name_of_band=band)
                    test_distance, test_path = apply_dtw(template=pickled_dict['general curve'], test=rows[2:],
                                                         display=False)
                    percentile = calculate_threshold(pickled_dict['distances list'], test_distance=test_distance)

                    if f"{band}_{label}" in data_frame.columns:
                        data_frame.loc[index, f"{band}_{label}"] = percentile

                    else:
                        data_frame[f"{band}_{label}"] = ""
                        data_frame.loc[index, f"{band}_{label}"] = percentile

            if "label" in data_frame.columns:
                data_frame.loc[index, "label"] = training_data_label

            else:
                data_frame["label"] = ""
                data_frame.loc[index, "label"] = training_data_label

    else:
        data_frame = test.filter(['Lat', 'Long'], axis=1)

        for band in bands:
            for label in classes:
                print(f"For {label} and {band} :")

                pickled_dict = unpickler(name_of_class=label, name_of_band=band)
                test_distance, test_path = apply_dtw(template=pickled_dict['general curve'], test=test,
                                                     single_pixel=True, display=False)
                percentile = calculate_threshold(pickled_dict['distances list'], test_distance=test_distance)

                data_frame[f"{band}_{label}"] = ""
                data_frame.loc[0, f"{band}_{label}"] = percentile

    return data_frame


# _____________________________________


# Play:

class_name, index_of_pixel, band_name, csv_data = main.preprocess()


# pickled_dictionary = unpickler(name_of_class="Forests", name_of_band="NDWI")
# general_curve, minimised, maximised = get_average_curve(csv_data['preprocessed'])

#
# testing_distance, testing_path = apply_dtw(general_curve, test=csv_data['preprocessed'],
#                                           display=True, single_pixel=True)

# print(testing_distance)
# percentile_value = calculate_threshold(pickled_dictionary['distances list'], test_distance=testing_distance)
#
#  TRAINING THE DTW
# trainer(input_data['preprocessed'], class_name, band_name)

tested_csv = tester(csv_data['preprocessed'].iloc[[0]], training_data_label=None)
print(tested_csv)

'''
TRAINING ENTIRE DATASET FOR 2019

bands = ['NDVI', 'NDWI', 'NDBI']
classes = ['Forests', 'Water', 'Agriculture', 'BarrenLand', 'Infrastructure']

for band in bands:
    for label in classes:
        input_csv = pd.read_csv(
            os.path.abspath(__file__ + "/../../") + f"/data_2019/csv/{label}/preprocessed_{band}.csv")

        trainer(input_data=input_csv, name_of_class=label, name_of_band=band)
'''