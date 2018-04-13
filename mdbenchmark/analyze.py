# -*- Mode: python; tab-width: 4; indent-tabs-mode:nil; coding:utf-8 -*-
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 fileencoding=utf-8
#
# MDBenchmark
# Copyright (c) 2017 Max Linke & Michael Gecht and contributors
# (see the file AUTHORS for the full list of names)
#
# MDBenchmark is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# MDBenchmark is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with MDBenchmark.  If not, see <http://www.gnu.org/licenses/>.
import click
import mdsynthesis as mds
import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure

from . import console
from .mdengines import detect_md_engine
from .utils import generate_output_name, calc_slope_intercept, lin_func

from .cli import cli
from .mdengines.gromacs import analyze_run
from .plot import plot_line


@cli.command()
@click.option(
    '-d',
    '--directory',
    help='Path in which to look for benchmarks.',
    default='.',
    show_default=True)
@click.option(
    '-p',
    '--plot',
    is_flag=True,
    help='Generate a plot of finished benchmarks.')
@click.option(
    '--ncores',
    type=int,
    default=None,
    help='Number of cores per node. If not given it will be parsed from the '
    'benchmarks log file.',
    show_default=True)
@click.option(
    '-o', '--output-name', default=None, help="Name of the output .csv file.", type=str)
def analyze(directory, plot, ncores, output_name):
    """Analyze finished benchmarks."""
    bundle = mds.discover(directory)

    df = pd.DataFrame(columns=[
        'module', 'nodes', 'ns/day', 'run time [min]', 'gpu', 'host', 'ncores'
    ])

    for i, sim in enumerate(bundle):
        # older versions wrote a version category. This ensures backwards compatibility
        if 'module' in sim.categories:
            module = sim.categories['module']
        else:
            module = sim.categories['version']
        # call the engine specific analysis functions
        df.loc[i] = detect_md_engine(module).analyze_run(sim)

    if df.empty:
        console.error('There is no data for the given path.')

    if df.isnull().values.any():
        console.warn(
            'We were not able to gather informations for all systems. '
            'Systems marked with question marks have either crashed or '
            'were not started yet.')

    # Sort values by `nodes`
    df = df.sort_values(['host', 'module', 'run time [min]', 'gpu',
                         'nodes']).reset_index(drop=True)

    # Reformat NaN values nicely into question marks.
    df_to_print = df.replace(np.nan, '?')
    print(df_to_print)

    # here we determine which output name to use.
    if output_name is None:
        output_name = generate_output_name("csv")
    if '.csv' not in output_name:
        output_name = '{}.csv'.format(output_name)
    df.to_csv(output_name)

    if plot:
        console.warn(
            'This feature is now outdatedself.'
            'Please use mdbenchmark plot to access all plotting features')

        fig = Figure()
        FigureCanvas(fig)
        ax = fig.add_subplot(111)

        df = pd.read_csv(output_name)

        df_sel = 'nodes'
        gb = df.groupby(['gpu', 'module', 'host'])
        groupby = ['gpu', 'module', 'host']
        for key, df in gb:
            label = ' '.join(['{}={}'.format(n, v) for n, v in zip(groupby, key)])
            plot_line(df=df, df_sel=df_sel, ax=ax, label=label)

        ax.set_xlabel('Number of Nodes')
        ax.set_ylabel('Performance [ns/day]')
        ax.legend()

        fig.tight_layout()
        fig.savefig('runtimes.pdf', format='pdf')
