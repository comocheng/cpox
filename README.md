# Catalytic Partial OXidation of methane
Reproducable scripts that go with my CPOX paper:
Automated Mechanism Generation Using Linear Scaling Relationships and
Sensitivity Analyses applied to Catalytic Partial Oxidation of Methane

Emily J. Mazeau, Priyanka Satpute, Katrin Blondal, C. Franklin Goldsmith, Richard H. West

The rh folder corresponds to simulations on Rh(111), the paper's "base" case

All RMG input files are up to date with the 3.0 release of RMG-Py and RMG-database, found at https://github.com/ReactionMechanismGenerator
* `input.py` is the RMG input file
* `simulations.py` runs the Cantera simulations and sensitivity analyses
* `plot-<size>-grid` makes volcano plots


`large-grid` and `small-grid` contain the individual RMG and Cantera simulations for every metal

`base-large-grid` and `base-small-grid` contain volcano plots for the non-perturbed results of interest

`sensitivities-large-grid` and `sensitivities-small-grid` contain volcano plots for each individual reaction

`other-figures` contains other figures from the paper
