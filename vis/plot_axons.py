"""
Plot the diffusion grid per saved timestep. Plot the axon paths at those 
timesteps overlaid on the grid.

Should be run from root directory of project.

INPUT:  
    - DIFFUSION_DIR: directory containing diffusion_<timestep>.csv grid files
    - AXON_DIR: directory containing axon_<axon_id>_<axon_type>.csv path files
    - OUTPUT_DIR: where to put the output file
OUTPUT:
    - plot of diffusion grid and axon paths in OUTPUT_DIR/axon_graphs.png
"""

import glob
import os
import csv
import numpy as np
import math
import sys
from matplotlib import pyplot as plt
import matplotlib.patheffects as PathEffects

# number of timesteps to plot 
PLOT_EVERY_TIMESTEP = 50

# get test dir from command line input
if len(sys.argv) != 2:
    print('Usage: plot_axons.py <TEST_NAME>')
    sys.exit(1)

TEST_NAME = sys.argv[1]

# get filenames of all diffusion timesteps that were saved
DIFFUSION_DIR = os.path.join('data', TEST_NAME, 'raw')
diffusion_filenames = [filename for i, filename in 
    enumerate(glob.glob(os.path.join(DIFFUSION_DIR, 'diff_*.tsv'))) 
    if i % PLOT_EVERY_TIMESTEP == 0]
NUM_PLOTS = len(diffusion_filenames)

print(f'{NUM_PLOTS} timesteps found')

AXON_DIR = os.path.join('data', TEST_NAME, 'processed')
axon_filenames = glob.glob(os.path.join(AXON_DIR, 'axon*'))

OUTPUT_DIR = os.path.join('data', TEST_NAME, 'vis')
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'axon_graph.png')

# create output directory if it doesn't already exist
if not os.path.isdir(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# we want to find a pair of integers that multiply to the nearest square of
# NUM_PLOTS, which are found by floor(root) and ceil(root). Use the larger one
# as the width to make the plot look nicer
root = math.sqrt(NUM_PLOTS)
rows = min(math.floor(root), math.ceil(root))
cols = max(math.floor(root), math.ceil(root))

# Initialize axes and subplots
print(f'Dimension of plot: ({rows}, {cols})')
fig,ax = plt.subplots(rows, cols, figsize=(cols*5 + 1, rows*5 + 1))
pos = 0

# specify which color to plot each axon type in
COLORS = {-1: 'k', 0: 'w', 1: '#ffff14', 2: 'm'}

# go through each timestep we have for the diffusion data and plot the 
# diffusion heatmap and the axons on top
for pos in range(rows * cols):
    # determine x, y subplot
    xpos = pos % cols
    ypos = math.floor(pos / cols)

    # run out of timesteps
    if pos >= len(diffusion_filenames):
        # turn off extra plots
        print(f'Hiding subplot ({ypos}, {xpos})')
        ax[ypos, xpos].set_visible(False)
        continue

    # PLOT STUFF
    print(f'Creating subplot {pos} from {diffusion_filenames[pos]} at ({ypos}, {xpos})')

    diffusion_file = diffusion_filenames[pos]
    # extract timestep from the filename
    timestep = int(diffusion_file[diffusion_file.find('_')+1:diffusion_file.find('.tsv')])

    # get indices of where each axon info begins
    with open(diffusion_file) as diff_file:
        lines = diff_file.readlines()
        split_indices = [i for i, line in enumerate(lines) if line[0] == '=']

    # split the file and separate all the grids
    split_indices.append(-1)
    grid_list = [lines[split_indices[i]+2:split_indices[i+1]-1] for i in range(len(split_indices) - 1)]

    # TODO: adapt this to plot all grids
    grid = []
    for line in grid_list[0]:
        line = line.strip().split('\t')
        new_line = []
        for val in line:
            try:
                val = float(val)
            except:
                val = 0.0
            new_line.append(val)
        grid.append(new_line)

    # load csv as numpy array. trailing comma prevents use of loadtxt or
    # csv.reader, so we use genfromtxt to fill the 'missing' column with 0s
    #diffusion_arr = np.genfromtxt(diffusion_file, delimiter='\t', filling_values=0.0)
    diffusion_arr = np.array(grid)

    im = ax[ypos, xpos].imshow(diffusion_arr)
    ax[ypos, xpos].set_title(f'Step={timestep}', fontsize=15)

    # plot axons on top of heatmap
    for ax_filename in axon_filenames:
        # load axon files from position csv
        # we can use loadtxt here because there is no trailing comma
        axon_arr = np.loadtxt(open(ax_filename), delimiter=',')

        # extract axon id and type from name
        ax_info = ax_filename.replace('.', '_').split('_')
        try:
            axon_id = ax_info[1]
            axon_type = int(ax_info[2])
        except IndexError:
            # if the filename is not properly formatted, use default values
            axon_id = -1
            axon_type = -1
    
        try:
            # get data up to current timestep
            x_arr = axon_arr[0][0:timestep]
            y_arr = axon_arr[1][0:timestep]
        except IndexError:
            # if there's an issue plotting just up to timestep, just plot the whole thing
            x_arr = axon_arr[0]
            y_arr = axon_arr[1]

        # plot data        
        ax[ypos, xpos].plot(x_arr, y_arr, color=COLORS[axon_type])
        # label with axon id
        if x_arr.size and y_arr.size:
            ax[ypos, xpos].add_artist(plt.Circle((x_arr[0], y_arr[0]), radius=2, color=COLORS[axon_type]))
            txt = ax[ypos, xpos].text(x_arr[0], y_arr[0], axon_id, color='k')
            txt.set_path_effects([PathEffects.withStroke(linewidth=2, foreground='w')])

# save figure
print(f'Saving {OUTPUT_FILE}')
plt.savefig(OUTPUT_FILE)
