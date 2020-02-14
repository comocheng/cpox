# Catalytic Partial OXidation of methane
Reproducable scripts that go with my CPOX paper

The rh folder corresponds to silumations on Rh(111), the paper's "base" case

All RMG input files are up to date with the 3.0 release of RMG-Py and RMG-database, found at https://github.com/ReactionMechanismGenerator
* `input.py` is the RMG input file 
* `simulations.py` run the Cantera simulations and sensitivity analyses

`large-grid` and `small-grid` contain the individual RMG and Cantera simulations for every metal

`base-large-grid` and `base-small-grid` contain volcano plots for the non-perturbed results of interest

`sensitivities-large-grid` and `sensitivities-small-grid` contain volcano plots for each individual reaction
