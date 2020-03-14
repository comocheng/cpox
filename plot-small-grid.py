#!/usr/bin/env python
# coding: utf-8

from matplotlib import pyplot as plt
import matplotlib
import seaborn as sns
sns.set_style("ticks")
sns.set_context("paper", font_scale=1.5, rc={"lines.linewidth": 2.0})

import os
import re
import pandas as pd
import numpy as np
import shutil
import subprocess
import multiprocessing
import re
import cantera as ct
from matplotlib import animation
import sys
import statistics
import itertools

max_cpus = multiprocessing.cpu_count()

# set up the LSR grid, for the smaller, more interesting one
carbon_range = (-7.5, -5.5)
oxygen_range = (-5.25, -3.25)
grid_size = 9
mesh  = np.mgrid[carbon_range[0]:carbon_range[1]:grid_size*1j,
                 oxygen_range[0]:oxygen_range[1]:grid_size*1j]

with sns.axes_style("whitegrid"):
    plt.axis('square')
    plt.xlim(carbon_range)
    plt.ylim(oxygen_range)
    plt.yticks(np.arange(-5.25,-3,0.5))
plt.show()

# just to double-check
experiments = mesh.reshape((2,-1)).T

with sns.axes_style("whitegrid"):
    plt.axis('square')
    plt.xlim(carbon_range)
    plt.ylim(oxygen_range)
    plt.yticks(np.arange(-5.25,-3,0.5))
    plt.plot(*experiments.T, marker='o', linestyle='none')
plt.clf()
extent = carbon_range + oxygen_range

# Because the center of a corner pixel is in fact the corner of the grid
# Becaus we want to stretch the image a little
c_step = mesh[0,1,0]-mesh[0,0,0]
o_step = mesh[1,0,1]-mesh[1,0,0]
carbon_range2 = (carbon_range[0]-c_step/2, carbon_range[1]+c_step/2)
oxygen_range2 = (oxygen_range[0]-c_step/2, oxygen_range[1]+c_step/2)
extent2 = carbon_range2 + oxygen_range2


def calculate(data):
    ratio = data[1]
    ch4_in = data[2]
    ch4_out = data[3]
    co_out = data[4]
    h2_out = data[5]
    h2o_out = data[6]
    co2_out = data[7]
    exit_T = data[8]
    max_T = data[9]
    dist_Tmax = data[10]
    o2_conv = data[11]

    ch4_depletion = ch4_in - ch4_out
    ch4_conv = ch4_depletion / ch4_in
    h2_sel = h2_out / (ch4_depletion * 2)
    h2_yield = h2_out / ( ch4_in * 2)
    co_sel = co_out / ch4_depletion
    co_yield = co_out / ch4_in
    syngas_sel = co_sel + h2_sel
    syngas_yield = syngas_sel * ch4_conv
    co2_sel = co2_out / ch4_depletion
    h2o_sel = h2o_out / (2 * ch4_depletion)
    fullox_sel = h2o_sel + co2_sel
    fullox_yield = fullox_sel * ch4_conv

    return syngas_sel, syngas_yield, co_sel, co_yield, h2_sel, h2_yield, ch4_conv, fullox_sel, fullox_yield, exit_T, max_T, dist_Tmax, o2_conv


def import_data(ratio, file_location=False):
    """
    This imports dict_conversions_celectivities from the original simulation
    """
    if file_location is False:
        data = pd.read_csv('./data.csv')
    else:
        data = pd.read_csv('./small-grid/' + file_location + '/data.csv')

    data = data.get_values()
    for x in range(len(data)):
        r = round(data[x][1],1)
        if r == ratio:
            return calculate(data[x])


# For close packed surfaces from
# Abild-Pedersen, F.; Greeley, J.; Studt, F.; Rossmeisl, J.; Munter, T. R.;
# Moses, P. G.; Skúlason, E.; Bligaard, T.; Norskov, J. K.
# Scaling Properties of Adsorption Energies for Hydrogen-Containing Molecules on
# Transition-Metal Surfaces. Phys. Rev. Lett. 2007, 99 (1), 016105
# DOI: 10.1103/PhysRevLett.99.016105.
abildpedersen_energies = { # Carbon, then Oxygen
'Ru': ( -6.397727272727272, -5.104763568600047),
'Rh': ( -6.5681818181818175, -4.609771721406942),
'Ni': ( -6.045454545454545, -4.711681807593758),
'Pd': ( -6, -3.517877940833916),
'Pt': ( -6.363636363636363, -3.481481481481482),
}


def lavaPlot(overall_rate, title, axis=False, folder=False, interpolation=True):
    """
    Overall data to plot in a 9x9 LSR grid

    Title is a string for what definition is used
    Axis is a list of a min and max value or False.  This is to normalize colors across many plots
    Folder is a string that specifies where to save the images
    Interpolation is False to just plot boxes
    """
    overall_rate = np.array(overall_rate)
    rates = overall_rate

    rates_grid = np.reshape(rates, (grid_size,grid_size))
    for i in range(0,8):
        for j in range(0, 8 - i):
            rates_grid[i][j], rates_grid[8 - j][8 - i] = rates_grid[8 - j][8 - i], rates_grid[i][j]
    if axis is False:  # no normalizing
        if interpolation is True:
            plt.imshow(rates_grid, origin='lower',
                       interpolation='spline16',
                       extent=extent2, aspect='equal', cmap="Spectral_r",)
        else:
            plt.imshow(rates_grid, origin='lower',
                       extent=extent2, aspect='equal', cmap="Spectral_r",)
    else:
        if interpolation is True:
            plt.imshow(rates_grid, origin='lower',
                       interpolation='spline16',
                       extent=extent2, aspect='equal', cmap="Spectral_r",
                       vmin=axis[0], vmax=axis[1],)
        else:
            plt.imshow(rates_grid, origin='lower',
                       extent=extent2, aspect='equal', cmap="Spectral_r",
                       vmin=axis[0], vmax=axis[1],)

    for metal, coords in abildpedersen_energies.items():
        color = {'Ag':'k','Au':'k','Cu':'k'}.get(metal,'k')
        plt.plot(coords[0], coords[1], 'o'+color)
        plt.text(coords[0], coords[1]-0.1, metal, color=color, fontsize=16)
    plt.xlim(carbon_range)
    plt.ylim(oxygen_range)
    plt.yticks(np.arange(-5.25,-3.,0.5))
    plt.xlabel('$\Delta E^C$ (eV)', fontsize=22)
    plt.ylabel('$\Delta E^O$ (eV)', fontsize=22)
    plt.xticks(fontsize=18)
    plt.yticks(fontsize=18)
    plt.colorbar().ax.tick_params(labelsize=18)
    out_dir = 'lsr'
    os.path.exists(out_dir) or os.makedirs(out_dir)
    if folder is False:
        plt.savefig(out_dir + '/' + str(title) +'.pdf', bbox_inches='tight')
    else:
        plt.savefig(out_dir + '/' + str(folder) + '/' + str(title) +'.pdf', bbox_inches='tight')
    plt.show()
    plt.clf()


def lavaPlotAnimate(overall_rate, title, axis=False, folder=False, interpolation=True):
    """
    Overall data to plot in a 9x9 LSR grid

    Title is a string for what definition is used
    Axis is a list of a min and max value or False.  This is to normalize colors across many plots
    Folder is a string that specifies where to save the images
    Interpolation is False to just plot boxes
    """
    fig = plt.figure()
    ims = []

    for ratio in range(len(overall_rate)):
        rates = np.array(overall_rate[ratio])

        rates_grid = np.reshape(rates, (grid_size,grid_size))
        for i in range(0,8):
            for j in range(0, 8 - i):
                rates_grid[i][j], rates_grid[8 - j][8 - i] = rates_grid[8 - j][8 - i], rates_grid[i][j]
        if axis is False:  # no normalizing
            if interpolation is True:
                im = plt.imshow(rates_grid, origin='lower',
                           interpolation='spline16',
                           extent=extent2, aspect='equal', cmap="Spectral_r",
                           animated=True)
            else:
                im = plt.imshow(rates_grid, origin='lower',
                           extent=extent2, aspect='equal', cmap="Spectral_r",
                           animated=True)
        else:
            if interpolation is True:
                im = plt.imshow(rates_grid, origin='lower',
                           interpolation='spline16',
                           extent=extent2, aspect='equal', cmap="Spectral_r",
                           vmin=axis[0], vmax=axis[1], animated=True)
            else:
                im = plt.imshow(rates_grid, origin='lower',
                           extent=extent2, aspect='equal', cmap="Spectral_r",
                           vmin=axis[0], vmax=axis[1], animated=True)
        ims.append([im])
    for metal, coords in abildpedersen_energies.items():
        color = {'Ag':'k','Au':'k','Cu':'k'}.get(metal,'k')
        plt.plot(coords[0], coords[1], 'o'+color)
        plt.text(coords[0], coords[1]-0.1, metal, color=color, fontsize=16)
    plt.xlim(carbon_range)
    plt.ylim(oxygen_range)
    plt.yticks(np.arange(-5.25,-3.,0.5))
    plt.xlabel('$\Delta E^C$ (eV)', fontsize=22)
    plt.ylabel('$\Delta E^O$ (eV)', fontsize=22)
    plt.xticks(fontsize=18)
    plt.yticks(fontsize=18)
    plt.colorbar().ax.tick_params(labelsize=18)
    plt.tight_layout()
    ani = animation.ArtistAnimation(fig, ims, interval=100, repeat_delay=300, blit=True)
    out_dir = 'lsr'
    os.path.exists(out_dir) or os.makedirs(out_dir)
    if folder is False:
        ani.save(out_dir + '/' + str(title) + '.gif', writer='pillow', fps=5)
    else:
        os.path.exists(out_dir + '/' + str(folder)) or os.makedirs(out_dir + '/' + str(folder))
        ani.save(out_dir + '/' + str(folder) + '/' + str(title) + '.gif', writer='pillow', fps=5)
        # ani.save(out_dir + '/' + str(folder) + '/' + str(title) + '.mpg', writer='ffmpeg', fps=5)


array = os.listdir('./small-grid/')
array = sorted(array)

# for plotting
c_s = []
o_s = []
for x in array:
    _, c, o = x.split("-")
    c = c[:-1]
    c = -1 *float(c)
    o = -1* float(o)
    c_s.append(c)
    o_s.append(o)

ratios = [0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.6, 1.8, 2.0, 2.2, 2.4, 2.6]
ratios_title = ['06', '07', '08', '09', '10', '11', '12', '13', '14', '16', '18', '20', '22', '24', '26']
sens_types = ['SynGasSelec', 'SynGasYield', 'COSelec', 'COYield', 'H2Selec',
              'H2Yield', 'CH4Conv', 'FullOxSelec', 'FullOxYield', 'ExitT',
              'MaxT', 'DistToMaxT', 'O2Conv']


def loadWorker(ratio):
    ans = []
    for f in array:
        ans.append(import_data(ratio, file_location=f))
    return ans


num_threads = len(ratios)
pool = multiprocessing.Pool(processes=num_threads)
all_data = pool.map(loadWorker, ratios, 1)
pool.close()
pool.join()


def spansWorker(sens):
    all_sens_data = []
    for x in range(len(all_data)):  # for each ratio
        for y in range(len(all_data[0])):
            # x has len 15 and is each of the ratios
            # y has len 81 and is each of the lsr binding energies
            # the last number is the type of sensitivity definition and is 0-12
            all_sens_data.append(all_data[x][y][sens])
    vmax = max(all_sens_data)
    vmin = min(all_sens_data)
    return [vmin, vmax]


def basePlotWorker(ratio):
    # plots without interpolation
    for s in range(len(all_data[ratio][0])):
        data_to_plot = []
        for x in range(len(all_data[ratio])):
            data_to_plot.append(all_data[ratio][x][s])
        title = sens_types[s] + str(ratios_title[ratio])
        lavaPlot(data_to_plot, title, axis=spans[s], folder='base', interpolation=False)


def baseAnimateWorker(sens):
    # make gifs
    data_to_plot = []
    for ratio in range(len(all_data)):
        tmp = []
        for metal in range(len(all_data[0])):
            tmp.append(all_data[ratio][metal][sens])
        data_to_plot.append(tmp)
    title = sens_types[sens]
    lavaPlotAnimate(data_to_plot, title, spans[sens], folder='base-animate', interpolation=False)


sens_index = list(range(len(sens_types)))
pool = multiprocessing.Pool(processes=13)
spans = pool.map(spansWorker, sens_index, 1)
pool.close()
pool.join()

ratios_index = list(range(len(ratios)))
if max_cpus >= 28:
    num_threads = 28
    lump = 1
else:
    num_threads = max_cpus
    lump = int(28./max_cpus)
pool = multiprocessing.Pool(processes=num_threads)
pool.map_async(basePlotWorker, ratios_index, lump)
pool.map_async(baseAnimateWorker, sens_index, lump)
pool.close()
pool.join()


def import_sensitivities(ratio, file_location=False, thermo=False):
    """
    Ratio is the C/O starting gas ratio
    file_location is the LSR C and O binding energy, fasle to load the base case
    thermo is either False to load reaction sensitivities or True to load thermo sensitivities
    """
    if file_location is False:
        if thermo is False:
            data = pd.read_csv('./sensitivities/' + str(ratio) + 'RxnSensitivity.csv')
        else:
            data = pd.read_csv('./sensitivities/' + str(ratio) + 'ThermoSensitivity.csv')
    else:
        if thermo is False:
            data = pd.read_csv('./small-grid/' + file_location + '/sensitivities/' + str(ratio) + 'RxnSensitivity.csv')
        else:
            data = pd.read_csv('./small-grid/' + file_location + '/sensitivities/' + str(ratio) + 'ThermoSensitivity.csv')
    data = data.values
    data = data.tolist()
    return data


def loadSensDataWorker(array):
    rxndata = []
    for ratio in ratios:
        rxndata.append(import_sensitivities(ratio, file_location=array))
        # thermodata.append(import_sensitivities(ratio, file_location=f, thermo=True))
    return rxndata


num_threads = max_cpus
lump = 1
pool = multiprocessing.Pool(processes=num_threads)
allrxndata = pool.map(loadSensDataWorker, array, lump)
pool.close()
pool.join()

reactions = set()  # create list of unique reactions
for f in range(len(allrxndata)):  # for each lsr binding energy
    for r in range(len(allrxndata[f][0])):  # for each reaction
        reactions.add(allrxndata[f][0][r][1])  # append the reaction itself
reactions = list(reactions)


def sensPlot(overall_rate, title, axis=False, folder=False):
    """
    overall sensitivity data to plot
    title is a string for what definition is used
    to normalize colors across many plots, False doesn't normalize axes
    folder specifies where to save the images
    """
    cmap = plt.get_cmap("Spectral_r")
    # cmap.set_bad(color='k', alpha=None)
    cmaplist = list(map(cmap,range(256)))
    cmaplist[0]=(0,0,0,0.3)
    newcmap = cmap.from_list('newcmap',cmaplist, N=256)
    cmap = newcmap

    overall_rate = np.array(overall_rate)
    rates = overall_rate

    rates_grid = np.reshape(rates, (grid_size,grid_size))
    for i in range(0,8):
        for j in range(0, 8 - i):
            rates_grid[i][j], rates_grid[8 - j][8 - i] = rates_grid[8 - j][8 - i], rates_grid[i][j]
    if axis is False:  # no normalizing
        plt.imshow(rates_grid, origin='lower',
                   extent=extent2, aspect='equal', cmap="Spectral_r",)
    else:
        plt.imshow(rates_grid, origin='lower',
               extent=extent2, aspect='equal', cmap="Spectral_r",
               vmin=axis[0], vmax=axis[1],)

    for metal, coords in abildpedersen_energies.items():
        color = {'Ag':'k','Au':'k','Cu':'k'}.get(metal,'k')
        plt.plot(coords[0], coords[1], 'o'+color)
        plt.text(coords[0], coords[1]-0.1, metal, color=color, fontsize=16)
    plt.xlim(carbon_range)
    plt.ylim(oxygen_range)
    plt.yticks(np.arange(-5.25,-3.,0.5))
    plt.xlabel('$\Delta E^C$ (eV)', fontsize=22)
    plt.ylabel('$\Delta E^O$ (eV)', fontsize=22)
    plt.xticks(fontsize=18)
    plt.yticks(fontsize=18)
    plt.colorbar().ax.tick_params(labelsize=18)
    out_dir = 'lsr'
    os.path.exists(out_dir) or os.makedirs(out_dir)
    if folder is False:
        plt.savefig(out_dir + '/' + str(title) +'.pdf', bbox_inches='tight')
    else:
        os.path.exists(out_dir + '/' + str(folder)) or os.makedirs(out_dir + '/' + str(folder))
        plt.savefig(out_dir + '/' + str(folder) + '/' + str(title) +'.pdf', bbox_inches='tight')
    plt.show()
    plt.clf()


def sensPlotWorker(input):
    rxn, s = input
    tot_sens = 0.

    for r in range(len(allrxndata[0])):  # for a single ratio
        sensitivities = []
        for f in range(len(array)):  # for lsr binding energies
            got_value = False
            for p in range(len(allrxndata[f][r])):  # matching the reaction
                if allrxndata[f][r][p][1] == np.str(rxn):
                    sensitivities.append(allrxndata[f][r][p][s+2])
                    got_value = True
            if got_value is False:
                # this reaction didn't show up on this metal, so it isn't
                # sensitive, so put a placeholder in
                sensitivities.append(0.)

        tot_sens += sum(abs(np.array(sensitivities)))
        STDEV = statistics.stdev(sensitivities)
        MAX = max(abs(np.array(sensitivities)))

        title = rxn + ' '+ sens_types[s-2] + ' ' + str(ratios[r])
        sensPlot(sensitivities, title, folder='rxnsensitivities', axis=[-1*MAX, MAX])
        sensPlot(sensitivities, title, folder='rxnsensitivities-stdev', axis=[-1*STDEV*2, STDEV*2])

    return [rxn, tot_sens, sens_types[s]]


def sensPlotAnimate(overall_rate, title, axis=False, folder=False):
    """
    overall sensitivity data to plot
    title is a string for what definition is used
    to normalize colors across many plots, False doesn't normalize axes
    folder specifies where to save the images
    """
    fig = plt.figure()
    ims = []

    cmap = plt.get_cmap("Spectral_r")
    # cmap.set_bad(color='k', alpha=None)
    cmaplist = list(map(cmap,range(256)))
    cmaplist[0]=(0,0,0,0.3)
    newcmap = cmap.from_list('newcmap',cmaplist, N=256)
    cmap = newcmap

    for ratio in range(len(overall_rate)):
        rates = np.array(overall_rate[ratio])

        rates_grid = np.reshape(rates, (grid_size,grid_size))
        for i in range(0,8):
            for j in range(0, 8 - i):
                rates_grid[i][j], rates_grid[8 - j][8 - i] = rates_grid[8 - j][8 - i], rates_grid[i][j]
        if axis is False:  # no normalizing
            im = plt.imshow(rates_grid, origin='lower',
                       extent=extent2, aspect='equal', cmap="Spectral_r",)
        else:
            im = plt.imshow(rates_grid, origin='lower',
                   extent=extent2, aspect='equal', cmap="Spectral_r",
                   vmin=axis[0], vmax=axis[1],)
        ims.append([im])

    for metal, coords in abildpedersen_energies.items():
        color = {'Ag':'k','Au':'k','Cu':'k'}.get(metal,'k')
        plt.plot(coords[0], coords[1], 'o'+color)
        plt.text(coords[0], coords[1]-0.1, metal, color=color, fontsize=16)
    plt.xlim(carbon_range)
    plt.ylim(oxygen_range)
    plt.yticks(np.arange(-5.25,-3,0.5))
    plt.xlabel('$\Delta E^C$ (eV)', fontsize=22)
    plt.ylabel('$\Delta E^O$ (eV)', fontsize=22)
    plt.xticks(fontsize=18)
    plt.yticks(fontsize=18)
    plt.colorbar().ax.tick_params(labelsize=18)
    plt.tight_layout()
    ani = animation.ArtistAnimation(fig, ims, interval=100, repeat_delay=300, blit=True)
    out_dir = 'lsr'
    os.path.exists(out_dir) or os.makedirs(out_dir)
    if folder is False:
        ani.save(out_dir + '/' + str(title) + '.gif', writer='animation.PillowWriter', fps=5)
    else:
        os.path.exists(out_dir + '/' + str(folder)) or os.makedirs(out_dir + '/' + str(folder))
        ani.save(out_dir + '/' + str(folder) + '/' + str(title) + '.gif', writer='pillow', fps=5)
        # ani.save(out_dir + '/' + str(folder) + '/' + str(title) + '.mpg', writer='ffmpeg', fps=5)
    plt.clf()


def sensPlotAnimateWorker(input):
    rxn, s = input

    sensitivities = []
    for r in range(len(allrxndata[0])):  # for a single ratio
        tmp_sens = []
        for f in range(len(array)):  # for lsr binding energies
            got_value = False
            for p in range(len(allrxndata[f][r])):  # matching the reaction
                if allrxndata[f][r][p][1] == np.str(rxn):
                    tmp_sens.append(allrxndata[f][r][p][s+2])
                    got_value = True
            if got_value is False:
                # this reaction didn't show up on this metal, so it isn't
                # sensitive, so put a placeholder in
                tmp_sens.append(0.)
        sensitivities.append(tmp_sens)
    # standardizing the colors across all ratios
    flat = [item for sublist in sensitivities for item in sublist]
    MAX = max(abs(np.array(flat)))
    STDEV = statistics.stdev(flat)
    title = str(rxn) + str(sens_types[s])
    sensPlotAnimate(sensitivities, title, axis=[-1*MAX,MAX], folder='rxnsensitivities-animate')
    sensPlotAnimate(sensitivities, title, axis=[-1*STDEV*2,STDEV*2], folder='rxnsensitivities-animate-stdev')

    return [rxn, sens_types[s-2], MAX]


num_threads = max_cpus
lump = int(len(reactions)*15/max_cpus)+1
input = list(itertools.product(reactions, sens_index))
pool = multiprocessing.Pool(processes=num_threads)
sum_sens = pool.map(sensPlotWorker, input, lump)
pool.close()
pool.join()

pool = multiprocessing.Pool(processes=num_threads)
max_sens = pool.map(sensPlotAnimateWorker, input, lump)
pool.close()
pool.join()

sorted_max_sens = sorted(max_sens, key=lambda l:l[2], reverse=True)
for x in sorted_max_sens:
    print('{}\t{}\t{}'.format(x[0], x[1], x[2]))
k = pd.DataFrame.from_records(sorted_max_sens, columns=['Reaction', 'Sens Type', 'Maximum'])
k.to_csv('maxsens.csv', header=True)

for x in sum_sens:
    print('{}\t{}\t{}'.format(x[0], x[1], x[2]))
k = pd.DataFrame.from_records(sum_sens, columns=['Reaction', 'Total Sens', 'Sens Type'])
k.to_csv('sumsens.csv', header=True)
