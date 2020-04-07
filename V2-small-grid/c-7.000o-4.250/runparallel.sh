#!/bin/bash
#SBATCH --job-name=sensitivity
#SBATCH --error=error.log
#SBATCH --output=output.log
#SBATCH -n 1
#SBATCH -N 1
#SBATCH --partition=west,short,large
#SBATCH --exclude=c5003
#SBATCH -c 15
#SBATCH --mem-per-cpu=1Gb
#SBATCH --time=24:00:00

source activate rmg_env
python copyme-parallel.py
#python copymetest.py
