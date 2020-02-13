export RMGpy=/scratch/westgroup/mazeau/Cat/RMG-Py
find . -name runsimulations.sh -execdir sh -c "sbatch runsimulations.sh" \;
