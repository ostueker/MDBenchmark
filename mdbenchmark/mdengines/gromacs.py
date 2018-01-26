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
import os
from glob import glob
from six import string_types
import warnings
import click
import datreant.core as dtr
import mdsynthesis as mds
from jinja2.exceptions import TemplateNotFound
from shutil import copyfile


def parse_ns_day(fh):
    """parse nanoseconds per day from a GROMACS log file

    Parameters
    ----------
    fh : str / filehandle
        filename or string of log file to read

    Returns
    -------
    float
        nanoseconds per day
    """
    if isinstance(fh, string_types):
        with open(fh) as f:
            lines = f.readlines()
    else:
        lines = fh.readlines()
        fh.seek(0)

    for line in lines:
        if 'Performance' in line:
            return float(line.split()[1])
    warnings.warn(UserWarning, "No Performance data found.")
    return 0


def parse_ncores(fh):
    """parse number of cores from a GROMACS log file

    Parameters
    ----------
    fh : str / filehandle
        filename or string of log file to read

    Returns
    -------
    float
        number of cores job was run on
    """
    if isinstance(fh, string_types):
        with open(fh) as f:
            lines = f.readlines()
    else:
        lines = fh.readlines()
        fh.seek(0)

    for line in lines:
        if 'Running on' in line:
            return int(line.split()[6])

    warnings.warn(UserWarning, "No CPU data found.")
    return 0


def analyze_run(sim):
    """
    Analyze Performance data of a GROMACS simulation
    """
    ns_day = 0

    # search all output files and ignore GROMACS backup files
    output_files = glob(os.path.join(sim.relpath, '[!#]*log*'))
    if output_files:
        with open(output_files[0]) as fh:
            ns_day = parse_ns_day(fh)
            ncores = parse_ncores(fh)

    # Backward compatibility to previously created mdbenchmark systems
    if 'time' not in sim.categories:
        sim.categories['time'] = 0

    # backward compatibility
    if 'module' in sim.categories:
        module = sim.categories['module']
    else:
        module = sim.categories['version']

    return (module, sim.categories['nodes'], ns_day, sim.categories['time'],
            sim.categories['gpu'], sim.categories['host'], ncores)


def write_bench(top, tmpl, nodes, gpu, module, name, host, time):
    sim = mds.Sim(
        top['{}/'.format(nodes)],
        categories={
            'module': module,
            'gpu': gpu,
            'nodes': nodes,
            'host': host,
            'time': time,
            'name': name,
            'started': False
        })

    # copy input files
    tpr = '{}.tpr'.format(name)

    if not os.path.exists(tpr):
        raise click.FileError(
            tpr, hint='File does not exist or is not readable.')

    copyfile(tpr, sim[tpr].relpath)
    # Add some time buffer to the requested time. Otherwise the queuing system
    # kills the jobs before GROMACS can finish
    formatted_time = '{:02d}:{:02d}:00'.format(*divmod(time + 5, 60))
    formatted_module = "gromacs"
    script = tmpl.render(
        name=name,
        gpu=gpu,
        module=module,
        formatted_module=formatted_module,
        n_nodes=nodes,
        time=time,
        formatted_time=formatted_time)

    with open(sim['bench.job'].relpath, 'w') as fh:
        fh.write(script)

def formatted_md_engine_name(modulename):
    if 'gromacs' in modulename:
        return "gromacs"
    elif 'namd' in modulename:
        return "namd"
    else:
        raise RuntimeError("No Module Detected! did you specify the module?")
