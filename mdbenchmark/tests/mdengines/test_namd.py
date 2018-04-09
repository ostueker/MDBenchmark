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
from six.moves import StringIO

import pytest
from mdbenchmark.ext.click_test import cli_runner
from mdbenchmark.mdengines import namd


@pytest.fixture
def log():
    return StringIO("""
    Info: Benchmark time: 1 CPUs 1.13195 s/step 13.1013 days/ns 2727.91 MB memory
    """)


@pytest.fixture
def empty_log():
    return StringIO("""
    not the log you are looking for
    """)


def test_parse_ns_day(log):
    assert namd.parse_ns_day(log) == 1 / 13.1013


def test_parse_ncores(log):
    assert namd.parse_ncores(log) == 1


@pytest.mark.parametrize('parse', (namd.parse_ncores, namd.parse_ns_day))
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


@pytest.mark.parametrize('input_file', ('md', 'md.namd'))
def test_check_file_extension(capsys, input_file, tmpdir):
    """Test that we check for all files needed to run NAMD benchmarks."""

    output = 'ERROR File md.namd does not exist, but is needed for NAMD benchmarks.\n'
    with pytest.raises(SystemExit) as e:
        namd.check_input_file_exists(input_file)
        out, err = capsys.readouterr()
        assert e.type == SystemExit
        assert e.code == 1
        assert out == output

    NEEDED_FILES = ['md.namd', 'md.psf', 'md.pdb']
    with tmpdir.as_cwd():
        # Create files first
        for fn in NEEDED_FILES:
            with open(fn, 'w') as fh:
                fh.write('dummy file')

        assert namd.check_input_file_exists(input_file)


@pytest.mark.parametrize(
    'file_content, output, exit_exception, exit_code',
    [('dummy file', '', False, 0),
     ('parameters ./relative/path/',
      'ERROR No absolute path detected in NAMD file!\n', SystemExit, 1),
     ('parameters abc', 'ERROR No absolute path detected in NAMD file!\n',
      SystemExit, 1),
     ('coordinates ../another/relative/path',
      'ERROR Relative file paths are not allowed in NAMD files!\n', SystemExit,
      1), ('structure $',
           'ERROR Variable Substitutions are not allowed in NAMD files!\n',
           SystemExit, 1)])
def test_analyze_namd_file(capsys, tmpdir, file_content, output,
                           exit_exception, exit_code):
    """Test that we check the `.namd` file as expected."""

    with tmpdir.as_cwd():
        # Make sure that we do not throw any error when everything is fine!
        with open('md.namd', 'w') as fh:
            fh.write(file_content)

        with open('md.namd', 'r') as fh:
            if exit_exception:
                with pytest.raises(exit_exception) as e:
                    namd.analyze_namd_file(fh)
                    out, err = capsys.readouterr()
                    assert out.type == exit_exception
                    assert out.code == exit_code
                    assert out == output
            else:
                namd.analyze_namd_file(fh)
                out, err = capsys.readouterr()
                assert out == output


def test_cleanup_before_restart(tmpdir):
    """Test that the cleanup of each directory works as intended for NAMD."""
    FILES_TO_DELETE = [
        'job_thing.err.123job', 'job_thing.out.123job', 'job.po12345',
        'job.o12345', 'benchmark.out'
    ]
    FILES_TO_KEEP = ['md.namd', 'md.pdb', 'md.psf', 'bench.job']

    # Create temporary directory
    tmp = tmpdir.mkdir("mdbenchmark")

    # Create empty files
    for f in FILES_TO_DELETE + FILES_TO_KEEP:
        open('{}/{}'.format(tmp, f), 'a').close()

    # Run the cleanup script
    namd.cleanup_before_restart(dtr.Tree(tmp.strpath))

    # Look for files that were left
    files_found = []
    for f in FILES_TO_KEEP:
        files_found.extend(glob(os.path.join(tmp.strpath, f)))

    # Get rid of the `tmp` path and only compare the actual filenames
    assert FILES_TO_KEEP == [x[len(str(tmp)) + 1:] for x in files_found]
