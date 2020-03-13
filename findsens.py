import os
import pandas as pd
import numpy as np

cwd = os.getcwd()


def import_sensitivities(ratio, file_location=False, thermo=False):
    """
    Ratio is the C/O starting gas ratio
    file_location is the LSR C and O binding energy, fasle to load the base case
    thermo is either False to load reaction sensitivities or True to load thermo sensitivities
    """
    try:
        # load in the sensitivity csv files
        if file_location is False:
            pd.read_csv('./base/sensitivities/' + str(ratio) + 'RxnSensitivity.csv')
        else:
            pd.read_csv('./' + str(file_location) + '/sensitivities/' + str(ratio) + 'RxnSensitivity.csv')
    except:
        print('Cannot find ' + str(ratio) + 'RxnSensitivity.csv for:    ' + file_location)


array = os.listdir('./small-grid/')
array = sorted(array)

ratios = [0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.6, 1.8, 2.0, 2.2, 2.4, 2.6]

for f in array:
    rxndata = []
    thermodata = []
    f = 'small-grid/' + f
    for ratio in ratios:
        import_sensitivities(ratio, file_location=f)

array = os.listdir('./large-grid/')
array = sorted(array)

for f in array:
    rxndata = []
    thermodata = []
    f = 'large-grid/' + f
    for ratio in ratios:
        import_sensitivities(ratio, file_location=f)
