#!/bin/sh
#SBATCH --job-name=d3-processor
#SBATCH -N 1
#SBATCH --cpus-per-task 16
#SBATCH --mem-per-cpu=32G
#SBATCH --time=3-00:00:00

source ~/.bashrc
conda activate nlp

poetry install
poetry run cli main --s2_use_papers --s2_use_abstracts --s2_use_authors --s2_filter_dblp