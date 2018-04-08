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

import click
import datreant.core as dtr
import numpy as np
import pytest
from mdbenchmark.ext.click_test import cli_runner
from mdbenchmark.mdengines import gromacs
from six.moves import StringIO


@pytest.fixture
def log():
    return StringIO("""
    Performance:           123.45           0.123
    Running on 1 node with total 32 cores, 64 logical cores, 0 compatible GPUs
    """)


@pytest.fixture
def empty_log():
    return StringIO("""
    not the log you are looking for
    """)


def test_parse_ns_day(log):
    assert gromacs.parse_ns_day(log) == 123.45


def test_parse_ncores(log):
    assert gromacs.parse_ncores(log) == 32


@pytest.mark.parametrize('parse', (gromacs.parse_ncores, gromacs.parse_ns_day))
def test_parse_empty_log(empty_log, parse):
    assert np.isnan(parse(empty_log))


@pytest.fixture
def sim(tmpdir_factory):
    folder = tmpdir_factory.mktemp('simulation')
    return dtr.Treant(
        str(folder),
        categories={
            'nodes': 42,
            'host': 'foo',
            'gpu': False,
            'version': 'bar'
        })


def test_analyze_run_backward_compatibility(sim):
    res = gromacs.analyze_run(sim)
    assert res[0] == 'bar'
    assert res[1] == 42
    assert np.isnan(res[2])
    assert res[3] == 0
    assert not res[4]
    assert res[5] == 'foo'
    assert np.isnan(res[6])


def test_cleanup_before_restart(tmpdir):
    """Test that the cleanup of each directory works as intended."""
    FILES_TO_DELETE = [
        'job_thing.err.123job', 'job_thing.out.123job', 'md.log', 'md.xtc',
        'md.cpt', 'md.edr', 'job.po12345', 'job.o12345', 'md.out'
    ]
    FILES_TO_KEEP = ['md.mdp', 'md.tpr', 'bench.job']

    # Create temporary directory
    tmp = tmpdir.mkdir("mdbenchmark")

    # Create empty files
    for f in FILES_TO_DELETE + FILES_TO_KEEP:
        open('{}/{}'.format(tmp, f), 'a').close()

    # Run the cleanup script
    gromacs.cleanup_before_restart(dtr.Tree(tmp.strpath))

    # Look for files that were left
    files_found = []
    for f in FILES_TO_KEEP:
        files_found.extend(glob(os.path.join(str(tmp), f)))

    # Get rid of the `tmp` path and only compare the actual filenames
    assert FILES_TO_KEEP == [x[len(str(tmp)) + 1:] for x in files_found]


def test_check_file_extension(capsys, tmpdir):
    """Test that we check for all files needed to run GROMACS benchmarks."""
    output = 'ERROR File md.tpr does not exist, but is needed for GROMACS benchmarks.\n'
    with pytest.raises(SystemExit) as e:
        gromacs.check_input_file_exists('md')
        out, err = capsys.readouterr()
        assert e.type == SystemExit
        assert e.code == 1
        assert out == output

    with tmpdir.as_cwd():
        # Create files first
        with open('md.tpr', 'w') as fh:
            fh.write('dummy file')

        assert gromacs.check_input_file_exists('md')
