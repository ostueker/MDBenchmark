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
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import click

from .cli import cli
from .utils import calc_slope_intercept, lin_func, generate_output_name
from . import console

def plot_line(df, label, ax=None):
    if ax is None:
        ax = plt.gca()

    p = ax.plot('nodes', 'ns/day', '.-', data=df, ms='10', label=label)
    color = p[0].get_color()
    slope, intercept = calc_slope_intercept(
        (df['nodes'].iloc[0], df['ns/day'].iloc[0]), (df['nodes'].iloc[1],
                                                      df['ns/day'].iloc[1]))
    # avoid a label and use values instead of pd.Series
    ax.plot(
        df['nodes'],
        lin_func(df['nodes'].values, slope, intercept),
        ls='--',
        color=color,
        alpha=.5)
    return ax


def plot_over_group(df, ax=None):
    # plot all lines
    gb = df.groupby(['gpu','module','host'])
    groupby = ['gpu','module','host']
    for key, df in gb:
        label = ' '.join(['{}={}'.format(n, v) for n, v in zip(groupby, key)])
        plot_line(ax=ax, df=df, label=label)

    # style axes
    ax.set_xlabel('Number of nodes')
    ax.set_ylabel('Performance [ns/day]')
    ax.legend()

    #ax2 = ax.twiny()
    #ax1_xticks = ax.get_xticks()
    #ax2.set_xticks(ax1_xticks)
    #ax2.set_xbound(ax.get_xbound())
    #ax2.set_xticklabels(gb.get_group(list(gb.groups.keys())[0])['ncores'])
    #ax2.set_xlabel('{}'.format('{}\n\nCores'.format(df['host'][0])))

    return ax


@cli.command()
@click.option(
    '--csv',
    help='name of csv file',
    multiple=True,
    show_default=True)
@click.option(
    '--output-name',
    '-o',
    default=None,
    help="name of output files",
    show_default=True)
@click.option(
    '--output-type',
    '-t',
    help="file extension for plot outputs",
    #type=click.Choice(['png', 'pdf', 'svg', 'jpeg']),
    show_default=True,
    default='png')
@click.option(
    '--host-name',
    '-h',
    default=None,
    multiple=True,
    help="hostname",
    show_default=True)
@click.option(
    '--module-name',
    '-h',
    default=None,
    multiple=True,
    help="module name or engine name",
    show_default=True)
@click.option(
    '--host-name',
    '-h',
    default=None,
    multiple=True,
    help="hostname",
    show_default=True)
@click.option(
    '--gpu/--no-gpu',
    help="plot data for GPU runs",
    show_default=True,
    default=False)
@click.option(
    '--cpu/--no-cpu',
    help="plot data for GPU runs",
    show_default=True,
    default=True)
def plot(csv, output_name, output_type, host_name, module_name, gpu, cpu):
    """Plot nice things"""
    df_list = []
    for c in csv:
        tmp_df = pd.read_csv(c, index_col=0)
        # append df_list
        df_list.append(tmp_df)

    df = pd.concat(df_list)
    # Remove NaN values. These are missing ncores/performance data.
    df = df.dropna()

    # preprocess the commandline entries
    print(gpu)
    print(cpu)
    print(host_name)
    print(module_name)
    gpu_list = []
    if gpu is True:
        gpu_list.append(True)
    if cpu is True:
        gpu_list.append(False)
    print(gpu_list)
    # here I split all data frames into the posible smallest segments
    # this is necessary so we can plot all individually
    split_df = df.groupby(['gpu', 'module', 'host'])

    print(split_df)
    # here I initialize the list which will be plotted
    df_list = []
    for key, df in split_df:
        if any(gpu in key for gpu in gpu_list) and len(host_name) == 0 and len(module_name) == 0:
            df_list.append(df)
        elif any(gpu in key for gpu in gpu_list) and any(host in key for host in host_name) and len(module_name) == 0:
            df_list.append(df)
        elif any(gpu in key for gpu in gpu_list) and len(host_name) == 0 and any(module in key for module in module_name):
            df_list.append(df)
        elif any(gpu in key for gpu in gpu_list) and any(host in key for host in host_name) and any(module in key for module in module_name):
            df_list.append(df)
    if len(df_list) == 0:
        console.error(
            'Your selections contained no Benchmarking Information'
            'Are you sure all your selections are correct?')

    df = pd.concat(df_list)
    fig = Figure()
    FigureCanvas(fig)
    ax = fig.add_subplot(111)
    plot_over_group(df, ax=ax)

    if output_name is None:
        output_name = generate_output_name("output_type")
    if output_type not in output_name:
        output_name = '{}.{}'.format(output_name, output_type)
    fig.savefig(output_name)
