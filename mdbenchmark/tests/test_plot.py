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
import numpy as np
import pytest
import os
from numpy.testing import assert_equal
from pandas.testing import assert_frame_equal

from mdbenchmark import utils
from mdbenchmark.ext.click_test import cli_runner


@pytest.mark.parametrize('module_selection', 'host', [
    ('gromacs/2018', 'draco'),
    ('namd/2.12', 'draco'),
    ('gromacs/2016.3', 'hydra')
])
def test_plot_filtering_success(cli_runner, tmpdir, data module_selection, expected_df, host):
    """Test whether we can plot over different groups.
    """
    with tmpdir.as_cwd():

        output = 'The following modules will be plotted {{'{}'}}.\n'.format{module_selection} \
                 'Your file was saved as testpng.png in the working directory.''

        result = cli_runner.invoke(cli.cli, [
            'plot',
            '--csv=test.csv', '--module-name={}'.format(module_selection),
            '--host-name={}'.format(host), '--output-name=testpng'
        ])
        assert result.exit_code == 0
        assert result.output == output
        assert os .path.exists("testpng.png")


def test_plot_filtering_fail(cli_runner, tmpdir):
    """Test unsuccessful filtering and error message.
    """
    with tmpdir.as_cwd():

        output = ''

        result = cli_runner.invoke(cli.cli, [
            'plot',
            '--csv=test.csv', '--module-name={}'.format(module_selection),
            '--host-name={}'.format(host), '--output-name=testpng'
        ])


def test_plot_gpu(cli_runner, tmpdir):
    """Test gpu flage without any host or module.
    """
    with tmpdir.as_cwd():

        output = ''

        result = cli_runner.invoke(cli.cli, [
            'plot',
            '--csv=test.csv', '--module-name={}'.format(module_selection),
            '--host-name={}'.format(host), '--output-name=testpng'
        ])


@pytest.mark.parametrize('host', ('draco', 'hydra'))
def test_plot_host_only(cli_runner, tmpdir):
    """Test only giving a host.
    """
    with tmpdir.as_cwd():

        output = ''

        result = cli_runner.invoke(cli.cli, [
            'plot',
            '--csv=test.csv', '--module-name={}'.format(module_selection),
            '--host-name={}'.format(host), '--output-name=testpng'
        ])


@pytest.mark.parametrize('module', ('gromacs', 'namd', 'namd/2.12', 'gromacs/2018'))
def test_plot_module_only(cli_runner, tmpdir, module):
    """Test only giving a module.
    """
    with tmpdir.as_cwd():

        output = ''

        result = cli_runner.invoke(cli.cli, [
            'plot',
            '--csv=test.csv', '--module-name={}'.format(module_selection),
            '--host-name={}'.format(host), '--output-name=testpng'
        ])


@pytest.mark.parametrize('output_type', ('png', 'pdf'))
def test_plot_output_type(cli_runner, tmpdir, output_type):
    """check whether output types are constructed correctly
    """
    with tmpdir.as_cwd():

        result = cli_runner.invoke(cli.cli, [
            'plot',
            '--csv=test.csv'.format(data['analyze-files-gromacs']),
        ])
        assert result.exit_code == 0
        assert os.path.exists("testfile.{}".format(output_type))
