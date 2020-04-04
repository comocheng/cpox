"""
This script runs 15 simulations (each corresponding to a different starting
ratio) in Cantera.

Reactor conditions are replicated from: "Methane catalytic partial oxidation on
autothermal Rh and Pt foam catalysts: Oxidation and reforming zones, transport
effects,and approach to thermodynamic equilibrium"
Horn 2007, doi:10.1016/j.jcat.2007.05.011

Ref 17: "Syngas by catalytic partial oxidation of methane on rhodium:
Mechanistic conclusions from spatially resolved measurements and numerical
simulations"
Horn 2006, doi:10.1016/j.jcat.2006.05.008

Ref 18: "Spatial and temporal profiles in millisecond partial oxidation
processes"
Horn 2006, doi:10.1007/s10562-006-0117-8
"""
import cantera as ct
import numpy as np
import scipy
import pylab
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.pyplot import cm
from matplotlib.ticker import NullFormatter, MaxNLocator, LogLocator
plt.switch_backend('agg')  # needed for saving figures
import csv
import os
import rmgpy
import rmg
import re
import operator
import pandas as pd
import pylab
from cycler import cycler
import seaborn as sns
import os
import multiprocessing

# this chemkin file is from the cti generated by rmg
gas = ct.Solution('./cantera/chem_annotated.cti', 'gas')
surf = ct.Interface('./cantera/chem_annotated.cti', 'surface1', [gas])

print("This mechanism contains {} gas reactions and {} surface reactions".format(gas.n_reactions, surf.n_reactions))

i_ar = gas.species_index('Ar')

# unit conversion factors to SI
mm = 0.001
cm = 0.01
ms = mm
minute = 60.0

#######################################################################
# Input Parameters
#######################################################################
t_in = 700  # K - in the paper, it was ~698.15K at the start of the cat surface and ~373.15 for the gas inlet temp
t_cat = t_in
length = 70 * mm  # Reactor length - m
diam = 16.5 * mm  # Reactor diameter - in m, from Ref 17 & Ref 18
area = (diam/2.0)**2*np.pi  # Reactor cross section area (area of tube) in m^2
porosity = 0.81  # Monolith channel porosity, from Ref 17, sec 2.2.2
cat_area_per_vol = 1.6e4  # m2/m3, which is 160 cm2/cm3, as used in Horn 2006
flow_rate = 4.7  # slpm, as seen in as seen in Horn 2007
tot_flow = 0.208  # constant inlet flow rate in mol/min, equivalent to 4.7 slpm
flow_rate = flow_rate * .001 / 60  # m^3/s, as seen in as seen in Horn 2007
velocity = flow_rate / area  # m/s

# The PFR will be simulated by a chain of 'N_reactors' stirred reactors.
N_reactors = 7001

on_catalyst = 1000  # catalyst length 10mm, from Ref 17
off_catalyst = 2000
dt = 1.0

# new sensitivities
# length = 110 * mm  # Reactor length - m
# N_reactors = 11001
# on_catalyst = 1000
# off_catalyst = 11000

reactor_len = length/(N_reactors-1)
rvol = area * reactor_len * porosity

# catalyst area in one reactor
cat_area = cat_area_per_vol * rvol



def plot_gas(data, x_lim=None):
    """
    Plots gas-phase species profiles through the PFR.

    xlim is either None or a tuple (x_min, x_max)
    """
    gas_out, surf_out, gas_names, surf_names, dist_array, T_array = data

    # Plot in mol/min
    fig, axs = plt.subplots()

    axs.set_prop_cycle(cycler('color', ['m', 'g', 'b', 'y', 'c', 'k', 'g']))

    for i in range(len(gas_out[0, :])):
        if i != i_ar:
            if gas_out[:, i].max() > 5.e-3:
                axs.plot(dist_array, gas_out[:, i], label=gas_names[i])
                species_name = gas_names[i]
                if species_name.endswith(')'):
                    if species_name[-3] == '(':
                        species_name = species_name[0:-3]
                    else:
                        species_name = species_name[0:-4]
                if species_name == "O2":
                    axs.annotate("O$_2$", fontsize=12, color='y',
                                    xy=(dist_array[900], gas_out[:, i][900] + gas_out[:, i][900] / 100.0),
                                    va='bottom', ha='center')
                elif species_name == "CO2":
                    axs.annotate("CO$_2$", fontsize=12, color='c',
                                    xy=(dist_array[2300], gas_out[:, i][2300] + gas_out[:, i][2300] / 10.0), va='bottom',
                                    ha='center')
                elif species_name == "CO":
                    axs.annotate("CO", fontsize=12, color='m',
                                    xy=(dist_array[1500], gas_out[:, i][1500] + 0.001),
                                    va='top', ha='center')
                elif species_name == "H2":
                    axs.annotate("H$_2$", fontsize=12, color='g',
                                    xy=(dist_array[2200], gas_out[:, i][2200] - 0.001),
                                    va='top', ha='center')
                elif species_name == "CH4":
                    axs.annotate("CH$_4$", fontsize=12, color='b',
                                    xy=(dist_array[900], gas_out[:, i][900] + gas_out[:, i][900] / 100.0),
                                    va='bottom', ha='center')
                elif species_name == "H2O":
                    axs.annotate("H$_2$O", fontsize=12, color='k',
                                    xy=(dist_array[1800], gas_out[:, i][1800] + gas_out[:, i][1800] / 40.0 + 0.001), va='bottom',
                                    ha='center')
                else:
                    axs.annotate(species_name, fontsize=12,
                                    xy=(dist_array[-1], gas_out[:, i][-1] + gas_out[:, i][-1] / 10.0), va='top',
                                    ha='center')
            else:
                axs.plot(0, 0)

    axs.set_prop_cycle(cycler('color', ['m', 'g', 'b', 'y', 'c', 'r', 'k', 'g']))

    ax2 = axs.twinx()
    ax2.plot(dist_array, T_array, label='temperature', color='r')

    axs.plot([dist_array[on_catalyst], dist_array[on_catalyst]], [0, 0.15], linestyle='--', color='xkcd:grey')
    axs.plot([dist_array[off_catalyst], dist_array[off_catalyst]], [0, 0.15], linestyle='--', color='xkcd:grey')
    axs.annotate("catalyst", fontsize=13, xy=(dist_array[1500], 0.14), va='center', ha='center')

    for item in (
            axs.get_xticklabels() + axs.get_yticklabels() + ax2.get_xticklabels() + ax2.get_yticklabels()):
        item.set_fontsize(13)

    axs.legend(loc='upper center', bbox_to_anchor=(0.5, -0.2), fancybox=False, shadow=False, ncol=4)

    if x_lim is not None:
        x_min, x_max = x_lim
        axs.set_xlim(float(x_min), float(x_max))
        ax2.set_xlim(float(x_min), float(x_max))
    else:
        axs.set_xlim(0.0, length / mm)
        ax2.set_xlim(0.0, length / mm)
    axs.set_ylim(0., 0.15)
    ax2.set_ylim(600, 2400)
    axs.set_xlabel('Position (mm)', fontsize=16)
    axs.set_ylabel('Flow (mol/min)', fontsize=16)
    ax2.set_ylabel('Temperature (K)', fontsize=16)

    for n in range(len(gas_names)):
        if gas_names[n] == 'CH4(2)':
            c_in = gas_out[0][n]
        if gas_names[n] == 'O2(3)':
            o_in = gas_out[0][n]
    ratio = round(c_in / (o_in * 2), 1)

    out_dir = 'figures'
    os.path.exists(out_dir) or os.makedirs(out_dir)

    if x_lim is not None:
        fig.savefig(out_dir + '/' + str(ratio) + 'ratioZoom.pdf', bbox_inches='tight',)
    else:
        fig.savefig(out_dir + '/' + str(ratio) + 'ratioFull.pdf', bbox_inches='tight',)


def plot_surf(data):
    """Plots surface site fractions through the PFR."""
    gas_out, surf_out, gas_names, surf_names, dist_array, T_array = data

    fig, axs = plt.subplots()
    axs.set_prop_cycle(cycler('color', ['m', 'g', 'b', 'y', 'c', 'r', 'k', 'g']))

    # Plot two temperatures (of gas-phase and surface vs only surface.)
    for i in range(len(surf_out[0, :])):
        if surf_out[:, i].max() > 5.e-3:
            axs.plot(dist_array, surf_out[:, i], label=surf_names[i])
    axs.plot([dist_array[on_catalyst], dist_array[on_catalyst]], [0, 1.2], linestyle='--', color='xkcd:grey')
    axs.plot([dist_array[off_catalyst], dist_array[off_catalyst]], [0, 1.2], linestyle='--', color='xkcd:grey')
    axs.annotate("catalyst", fontsize=13, xy=(dist_array[1500], 1.1), va='center', ha='center')

    for item in (
            axs.get_xticklabels() + axs.get_yticklabels()):
        item.set_fontsize(13)

    axs.legend(loc='upper center', bbox_to_anchor=(0.5, -0.2), fancybox=False, shadow=False, ncol=4)
    axs.set_ylim(0, 1.2)
    axs.set_xlim(8, 22)
    axs.set_xlabel('Position (mm)', fontsize=16)
    axs.set_ylabel('Site fraction', fontsize=16)

    #     temperature = np.round(T_array[0],0)
    for n in range(len(gas_names)):
        if gas_names[n] == 'CH4(2)':
            c_in = gas_out[0][n]
        if gas_names[n] == 'O2(3)':
            o_in = gas_out[0][n]
    ratio = c_in / (o_in * 2)
    ratio = round(ratio, 1)

    out_dir = 'figures'
    os.path.exists(out_dir) or os.makedirs(out_dir)
    fig.savefig(out_dir + '/' + str(ratio) + 'surf.pdf', bbox_inches='tight')


def monolith_simulation(gas, surf, temp, mol_in, verbose=False, sens=False):
    """
    Set up and solve the monolith reactor simulation.

    Verbose prints out values as you go along
    Sens is for sensitivity, in the form [perturbation, reaction #]

    Args:
        gas (ct.Solution): The cantera Solution object of the gas
        surf (ct.Interface): The cantera Interface object of the surface
        temp (float): The temperature in Kelvin
        mol_in (3-tuple or iterable): the inlet molar ratios of (CH4, O2, Ar)
        verbose (Boolean): whether to print intermediate results
        sens (False or 2-tuple/list): if not False, then should be a 2-tuple or list [dk, rxn]
                in which dk = relative change (eg. 0.01) and rxn = the index of the surface reaction rate to change

    Returns:
        gas_out, # gas molar flow rate in moles/minute
        surf_out, # surface mole fractions
        gas_names, # gas species names
        surf_names, # surface species names
        dist_array, # distances (in mm)
        T_array # temperatures (in K)
    """
    ch4, o2, ar = mol_in
    ratio = ch4 / (2 * o2)

    X = f"CH4(2):{ch4}, O2(3):{o2}, Ar:{ar}"
    gas.TPX = 273.15, ct.one_atm, X  # need to initialize mass flow rate at STP
    # mass_flow_rate = velocity * gas.density_mass * area  # kg/s
    mass_flow_rate = flow_rate * gas.density_mass
    gas.TPX = temp, ct.one_atm, X
    temp_cat = temp
    surf.TP = temp_cat, ct.one_atm
    surf.coverages = 'X(1):1.0'
    gas.set_multiplier(1.0)

    TDY = gas.TDY
    cov = surf.coverages

    if verbose is True:
        print('  distance(mm)   X_CH4        X_O2        X_H2       X_CO       X_H2O       X_CO2')

    # create a new reactor
    gas.TDY = TDY
    r = ct.IdealGasReactor(gas)
    r.volume = rvol

    # create a reservoir to represent the reactor immediately upstream. Note
    # that the gas object is set already to the state of the upstream reactor
    upstream = ct.Reservoir(gas, name='upstream')

    # create a reservoir for the reactor to exhaust into. The composition of
    # this reservoir is irrelevant.
    downstream = ct.Reservoir(gas, name='downstream')

    # Add the reacting surface to the reactor. The area is set to the desired
    # catalyst area in the reactor.
    rsurf = ct.ReactorSurface(surf, r, A=cat_area)

    # The mass flow rate into the reactor will be fixed by using a
    # MassFlowController object.
    # mass_flow_rate = velocity * gas.density_mass * area  # kg/s
    # mass_flow_rate = flow_rate * gas.density_mass
    m = ct.MassFlowController(upstream, r, mdot=mass_flow_rate)

    # We need an outlet to the downstream reservoir. This will determine the
    # pressure in the reactor. The value of K will only affect the transient
    # pressure difference.
    v = ct.PressureController(r, downstream, master=m, K=1e-5)

    sim = ct.ReactorNet([r])
    sim.max_err_test_fails = 12

    # set relative and absolute tolerances on the simulation
    sim.rtol = 1.0e-10
    sim.atol = 1.0e-20

    gas_names = gas.species_names
    surf_names = surf.species_names
    gas_out = []
    surf_out = []
    dist_array = []
    T_array = []

    surf.set_multiplier(0.0)  # no surface reactions until the gauze
    for n in range(N_reactors):
        # Set the state of the reservoir to match that of the previous reactor
        gas.TDY = r.thermo.TDY
        upstream.syncState()
        if n == on_catalyst:
            surf.set_multiplier(1.0)
            if sens is not False:
                surf.set_multiplier(1.0 + sens[0], sens[1])
        if n == off_catalyst:
            surf.set_multiplier(0.0)
        sim.reinitialize()
        sim.advance_to_steady_state()
        dist = n * reactor_len * 1.0e3  # distance in mm
        dist_array.append(dist)
        T_array.append(surf.T)
        kmole_flow_rate = mass_flow_rate / gas.mean_molecular_weight  # kmol/s
        gas_out.append(1000 * 60 * kmole_flow_rate * gas.X.copy())  # molar flow rate in moles/minute
        surf_out.append(surf.X.copy())

        # make reaction diagrams
        # out_dir = 'rxnpath'
        # os.path.exists(out_dir) or os.makedirs(out_dir)
        # elements = ['H', 'O']
        # locations_of_interest = [1000, 1200, 1400, 1600, 1800, 1999]
        # if sens is False:
        #     if n in locations_of_interest:
        #             location = str(int(n / 100))
        #             diagram = ct.ReactionPathDiagram(surf, 'X')
        #             diagram.title = 'rxn path'
        #             diagram.label_threshold = 1e-9
        #             dot_file = f"{out_dir}/rxnpath-{ratio:.1f}-x-{location}mm.dot"
        #             img_file = f"{out_dir}/rxnpath-{ratio:.1f}-x-{location}mm.pdf"
        #             diagram.write_dot(dot_file)
        #             os.system('dot {0} -Tpng -o{1} -Gdpi=200'.format(dot_file, img_file))
        #
        #             for element in elements:
        #                 diagram = ct.ReactionPathDiagram(surf, element)
        #                 diagram.title = element + 'rxn path'
        #                 diagram.label_threshold = 1e-9
        #                 dot_file = f"{out_dir}/rxnpath-{ratio:.1f}-x-{location}mm-{element}.dot"
        #                 img_file = f"{out_dir}/rxnpath-{ratio:.1f}-x-{location}mm-{element}.pdf"
        #                 diagram.write_dot(dot_file)
        #                 os.system('dot {0} -Tpng -o{1} -Gdpi=200'.format(dot_file, img_file))
        # else:
        #     pass

        if verbose is True:
            if not n % 100:
                print('  {0:10f}  {1:10f}  {2:10f}  {3:10f} {4:10f} {5:10f} {6:10f}'.format(dist, *gas[
                    'CH4(2)', 'O2(3)', 'H2(6)', 'CO(7)', 'H2O(5)', 'CO2(4)'].X * 1000 * 60 * kmole_flow_rate))

    gas_out = np.array(gas_out)
    surf_out = np.array(surf_out)
    gas_names = np.array(gas_names)
    surf_names = np.array(surf_names)
    data_out = gas_out, surf_out, gas_names, surf_names, dist_array, T_array
    return data_out

def run_one_simulation(ratio):
    """
    Start all of the simulations all at once using multiprocessing
    """
    fo2 = 1 / (2. * ratio + 1 + 79. / 21.)
    fch4 = 2 * fo2 * ratio
    far = 79 * fo2 / 21
    ratio_in = [fch4, fo2, far]  # mol fractions

    a = monolith_simulation(gas, surf, t_in, ratio_in)
    print("Finished simulation at a C/O ratio of {:.1f}".format(ratio))
    gas_out, surf_out, gas_names, surf_names, dist_array, T_array = a
    plot_gas(a)
    plot_gas(a, x_lim=(8,25))
    plot_surf(a)
    return [ratio, [gas_out, gas_names, dist_array, T_array]]


def deriv(gas_out):
    deriv = []
    for x in range(len(gas_out) - 1):
        deriv.append((gas_out[x+1] - gas_out[x])/.01)
    deriv.append(0.)
    return deriv


def calculate(data, type='sens'):
    """
    Calculate properties of interest from the raw data

    :param data: the data
    :param type: 'sens' for sensitivity analyses
                 'output' for saving the output csv
                 'ratio' for plotting
    :return:
    """
    gas_out_data, gas_names_data, dist_array_data, T_array_data = data

    reference = []
    for a in range(len(gas_names_data)):
        reference.append([gas_names_data[a], [gas_out_data[:, a]]])

    for x in reference:
        if x[0] == 'CH4(2)':
            ch4_in = x[1][0][0]
            ch4_out = x[1][0][-1]
            if ch4_out < 0:
                ch4_out = 0.
            ch4_depletion = ch4_in - ch4_out
            reference_ch4_conv = ch4_depletion / ch4_in  # Sensitivity definition 7: CH4 conversion

            d_ch4 = deriv(x[1][0])
            reference_max_ch4_conv = min(d_ch4)  # Sensitivity definition 15: maximum rate of CH4 conversion

            for y in range(len(x[1][0])):
                if (ch4_in - x[1][0][y]) / ch4_in >= 0.95:
                    reference_dist_to_95_ch4_conv = dist_array_data[y]  # Sensitivity definition 14: distance to 95% CH4 conversion
                else:
                    # never reached 95% conversion
                    reference_dist_to_95_ch4_conv = dist_array_data[-1]
        if x[0] == 'Ar':
            ar = x[1][0][-1]
        if x[0] == 'O2(3)':
            o2_in = x[1][0][0]
            o2_out = x[1][0][-1]
            if o2_out < 0:
                o2_out = 0.  # O2 can't be negative
            elif o2_out > o2_in:
                o2_out = o2_in  # O2 can't be created, to make it equal to O2 in
            o2_depletion = o2_in - o2_out
            reference_o2_conv = o2_depletion / o2_in  # Sensitivity definition 13: O2 conversion
        if x[0] == 'CO(7)':
            co_out = x[1][0][-1]
        if x[0] == 'H2(6)':
            h2_out = x[1][0][-1]
        if x[0] == 'H2O(5)':
            h2o_out = x[1][0][-1]
        if x[0] == 'CO2(4)':
            co2_out = x[1][0][-1]

    ratio = ch4_in / (2 * o2_in)

    # negative sensitivity is higher selectivity
    reference_h2_sel = h2_out / (ch4_depletion * 2)  # Sensitivity definition 5: H2 selectivity
    if reference_h2_sel <= 0:
        reference_h2_sel = 1.0e-15  # selectivity can't be 0

    reference_co_sel = co_out / ch4_depletion  # Sensitivity definition 3: CO selectivity
    if reference_co_sel <= 0:
        reference_co_sel = 1.0e-15  # selectivity can't be 0

    reference_syngas_selectivity = reference_co_sel + reference_h2_sel  # Sensitivity definition 1: SYNGAS selectivity

    reference_syngas_yield = reference_syngas_selectivity * reference_ch4_conv  # Sensitivity definition 2: SYNGAS yield
    if reference_syngas_yield <= 0:
        reference_syngas_yield = 1.0e-15  # yield can't be 0

    reference_co_yield = co_out / ch4_in  # Sensitivity definition 4: CO % yield
    # reference_co_yield = reference_co_sel * reference_ch4_conv

    reference_h2_yield = h2_out / (2 * ch4_in)  # Sensitivity definition 6: H2 % yield
    # reference_h2_yield = reference_h2_sel * reference_ch4_conv

    # Sensitivity definition 8: H2O + CO2 selectivity
    reference_h2o_sel = h2o_out / (ch4_depletion * 2)
    reference_co2_sel = co2_out / ch4_depletion
    if reference_h2o_sel <= 0:
        reference_h2o_sel = 1.0e-15  # H2O selectivity can't be 0
    if reference_co2_sel <= 0:
        reference_co2_sel = 1.0e-15  # CO2 selectivity can't be 0
    reference_full_oxidation_selectivity = reference_h2o_sel + reference_co2_sel

    # Sensitivity definition 9: H2O + CO2 yield
    reference_full_oxidation_yield = reference_full_oxidation_selectivity * reference_ch4_conv

    # Sensitivity definition 10: exit temperature
    reference_exit_temp = T_array_data[-1]

    # Sensitivity definition 11: peak temperature
    reference_peak_temp = max(T_array_data)

    # Sensitivity definition 12: distance to peak temperautre
    reference_peak_temp_dist = dist_array_data[T_array_data.index(max(T_array_data))]

    if type is 'sens':
        return reference_syngas_selectivity, reference_syngas_yield, reference_co_sel, reference_co_yield, reference_h2_sel, reference_h2_yield, reference_ch4_conv, reference_full_oxidation_selectivity, reference_full_oxidation_yield, reference_exit_temp, reference_peak_temp, reference_peak_temp_dist, reference_o2_conv, reference_max_ch4_conv, reference_dist_to_95_ch4_conv
    elif type is 'ratio':
        return reference_co_sel, reference_h2_sel, reference_ch4_conv, reference_exit_temp, reference_o2_conv, reference_co2_sel, reference_h2o_sel
    else:
        return ratio, ch4_in, ch4_out, co_out, h2_out, h2o_out, co2_out, reference_exit_temp, reference_peak_temp, reference_peak_temp_dist, reference_o2_conv, reference_max_ch4_conv, reference_dist_to_95_ch4_conv


def calc_sensitivities(reference, new, index=None):
    """Calculates sensitivities given old simulation results and perturbed simulation results"""
    reference_syngas_selectivity, reference_syngas_yield, reference_co_sel, reference_co_yield, reference_h2_sel, reference_h2_yield, reference_ch4_conv, reference_full_oxidation_selectivity, reference_full_oxidation_yield, reference_exit_temp, reference_peak_temp, reference_peak_temp_dist, reference_o2_conv = reference
    new_syngas_selectivity, new_syngas_yield, new_co_sel, new_co_yield, new_h2_sel, new_h2_yield, new_ch4_conv, new_full_oxidation_selectivity, new_full_oxidation_yield, new_exit_temp, new_peak_temp, new_peak_temp_dist, new_o2_conv = new

    Sens5 = (new_h2_sel - reference_h2_sel) / (reference_h2_sel * dk)
    Sens3 = (new_co_sel - reference_co_sel) / (reference_co_sel * dk)
    Sens1 = (new_syngas_selectivity - reference_syngas_selectivity) / (reference_syngas_selectivity * dk)
    Sens2 = (new_syngas_yield - reference_syngas_yield) / (reference_syngas_yield * dk)
    Sens4 = (new_co_yield - reference_co_yield) / (reference_co_yield * dk)
    Sens6 = (new_h2_yield - reference_h2_yield) / (reference_h2_yield * dk)
    Sens7 = (new_ch4_conv - reference_ch4_conv) / (
            reference_ch4_conv * dk)
    Sens13 = (new_o2_conv - reference_o2_conv) / (reference_o2_conv * dk)
    Sens8 = (new_full_oxidation_selectivity - reference_full_oxidation_selectivity) / (
            reference_full_oxidation_selectivity * dk)
    Sens9 = (new_full_oxidation_yield - reference_full_oxidation_yield) / (reference_full_oxidation_yield * dk)
    Sens10 = (new_exit_temp - reference_exit_temp) / (reference_exit_temp * dk)
    Sens11 = (new_peak_temp - reference_peak_temp) / (reference_peak_temp * dk)
    Sens12 = (new_peak_temp_dist - reference_peak_temp_dist) / (reference_peak_temp_dist * dk)
    Sens14 = (new_max_ch4_conv - reference_max_ch4_conv) / (reference_max_ch4_conv * dk)
    Sens15 = (new_dist_to_95_ch4_conv - reference_dist_to_95_ch4_conv) / (reference_dist_to_95_ch4_conv * dk)

    if index is not None:
        rxn = surf.reaction_equations()[index]
        return rxn, Sens1, Sens2, Sens3, Sens4, Sens5, Sens6, Sens7, Sens8, Sens9, Sens10, Sens11, Sens12, Sens13, Sens14, Sens15
    else:
        return Sens1, Sens2, Sens3, Sens4, Sens5, Sens6, Sens7, Sens8, Sens9, Sens10, Sens11, Sens12, Sens13, Sens14, Sens15


def plot_ratio_comparisions(data):
    ratios = [d[0] for d in data]
    fig, axs = plt.subplots(1, 2)

    # plot exit conversion and temp
    ch4_conv = [d[1][2] for d in data]
    axs[0].plot(ratios, ch4_conv, 'bo-', label='CH4', color='limegreen')
    o2_conv = [d[1][4] for d in data]
    axs[0].plot(ratios, o2_conv, 'bo-', label='O2', color='blue')
    ax2 = axs[0].twinx()
    temp = [d[1][3] for d in data]
    ax2.plot(ratios, temp, 'bo-', label='temp', color='orange')
    ax2.set_ylim(600.0, 2000)

    # plot exit selectivities
    co_sel = [d[1][0] for d in data]
    axs[1].plot(ratios, co_sel, 'bo-', label='CO', color='green')
    h2_sel = [d[1][1] for d in data]
    axs[1].plot(ratios, h2_sel, 'bo-', label='H2', color='purple')
    co2_sel = [d[1][5] for d in data]
    axs[1].plot(ratios, co2_sel, 'bo-', label='CO2', color='navy')
    h2o_sel = [d[1][6] for d in data]
    axs[1].plot(ratios, h2o_sel, 'bo-', label='H2O', color='dodgerblue')

    axs[0].legend()
    axs[1].legend()
    axs[0].set_ylabel('Exit conversion (%)', fontsize=13)
    ax2.set_ylabel('Exit temperature (K)', fontsize=13)
    axs[0].set_xlabel('C/O Ratio', fontsize=13)
    axs[1].set_xlabel('C/O Ratio', fontsize=13)
    axs[1].set_ylabel('Exit selectivity (%)', fontsize=13)
    plt.tight_layout()
    fig.set_figheight(6)
    fig.set_figwidth(16)
    out_dir = 'figures'
    os.path.exists(out_dir) or os.makedirs(out_dir)
    fig.savefig(out_dir + '/' + 'conversion&selectivity.pdf', bbox_inches='tight')


def sensitivity(gas, surf, old_data, temp, dk):
    """
    Rerun simulations for each perturbed surface reaction and compare to the
    original simulation (data) to get a numberical value for sensitivity.
    """
    sensitivity_results = []
    gas_out_data, gas_names_data, dist_array_data, T_array_data = old_data

    reference = []
    for a in range(len(gas_names_data)):
        reference.append([gas_names_data[a], [gas_out_data[:, a]]])

    # getting the ratio
    for x in reference:
        if x[0] == 'CH4(2)':
            ch4_in = x[1][0][0]
        if x[0] == 'O2(3)':
            o2_in = x[1][0][0]
        if x[0] == 'Ar':
            ar_in = x[1][0][0]
    ratio = ch4_in / (2 * o2_in)
    moles_in = [ch4_in, o2_in, ar_in]

    reference_data = calculate(old_data)

    # run the simulations
    for rxn in range(surf.n_reactions):
        gas_out, surf_out, gas_names, surf_names, dist_array, T_array = monolith_simulation(gas, surf, temp, moles_in, sens=[dk, rxn])
        c = [gas_out, gas_names, dist_array, T_array]
        new_data = calculate(c, type='sens')
        sensitivities = calc_sensitivities(reference_data, new_data, index=rxn)
        sensitivity_results.append(sensitivities)
    return sensitivity_results


def export(rxns_translated, ratio):
    k = (pd.DataFrame.from_dict(data=rxns_translated, orient='columns'))
    k.columns = ['Reaction', 'SYNGAS Selec', 'SYNGAS Yield', 'CO Selectivity', 'CO % Yield', 'H2 Selectivity', 'H2 % Yield',
                 'CH4 Conversion', 'H2O+CO2 Selectivity', 'H2O+CO2 yield', 'Exit Temp', 'Peak Temp',
                 'Dist to peak temp', 'O2 Conversion', 'Max CH4 Conv', 'Dist to 95 CH4 Conv']
    out_dir = 'sensitivities'
    os.path.exists(out_dir) or os.makedirs(out_dir)

    k.to_csv(out_dir + '/{:.1f}RxnSensitivity.csv'.format(ratio), header=True)


def sensitivity_worker(data):
    print('Starting sensitivity simulation for a C/O ratio of {:.1f}'.format(data[0]))
    old_data = data[1][0]
    ratio = data[0]
    try:
        sensitivities = sensitivity(gas, surf, old_data, t_in, dk)
        print('Finished sensitivity simulation for a C/O ratio of {:.1f}'.format(ratio))

        reactions = [d[0] for d in sensitivities]  # getting the reactions
        rxns_translated = []
        for x in reactions:
            for key, smile in names.items():
                x = re.sub(re.escape(key), smile, x)
            rxns_translated.append(x)
        print('Finished translating for C/O ratio of {:.1f}'.format(ratio))
        sensitivities = [list(s) for s in sensitivities]
        for x in range(len(rxns_translated)):
            sensitivities[x][0] = rxns_translated[x]
        export(sensitivities, ratio)
    except Exception as e:
        print(str(e))


if __name__ == "__main__":


    ratios = [.6, .7, .8, .9, 1., 1.1, 1.2, 1.3, 1.4, 1.6, 1.8, 2., 2.2, 2.4, 2.6]
    data = []
    num_threads = min(multiprocessing.cpu_count(), len(ratios))
    pool = multiprocessing.Pool(processes=num_threads)
    data = pool.map(run_one_simulation, ratios, 1)
    pool.close()
    pool.join()

    output = []
    for r in data:
        output.append(calculate(r[1], type='output'))
    k = (pd.DataFrame.from_dict(data=output, orient='columns'))
    k.columns = ['C/O ratio', 'CH4 in', 'CH4 out', 'CO out', 'H2 out', 'H2O out', 'CO2 out', 'Exit temp', 'Max temp', 'Dist to max temp', 'O2 conv', 'Max CH4 Conv', 'Dist to 95 CH4 Conv']
    k.to_csv('data.csv', header=True)  # raw data

    ratio_comparison = []
    for r in data:
        ratio_comparison.append([r[0], calculate(r[1], type='ratio')])

    plot_ratio_comparisions(ratio_comparison)

    species_dict = rmgpy.data.kinetics.KineticsLibrary().get_species('chemkin/species_dictionary.txt')
    keys = species_dict.keys()
    # get the first listed smiles string for each molecule
    smile = []
    for s in species_dict:
        smile.append(species_dict[s].molecule[0])
        if len(species_dict[s].molecule) is not 1:
            print('There are %d dupllicate smiles for %s:' % (len(species_dict[s].molecule), s))
            for a in range(len(species_dict[s].molecule)):
                print('%s' % (species_dict[s].molecule[a]))

    # translate the molecules from above into just smiles strings
    smiles = []
    for s in smile:
        smiles.append(s.to_smiles())
    names = dict(zip(keys, smiles))

    worker_input = []
    dk = 1.0e-2
    num_threads = min(multiprocessing.cpu_count(), len(data))
    pool = multiprocessing.Pool(processes=num_threads)
    worker_input = []
    for r in range(len(data)):
        worker_input.append([data[r][0], [data[r][1]]])
    pool.map(sensitivity_worker, worker_input, 1)
    pool.close()
    pool.join()
