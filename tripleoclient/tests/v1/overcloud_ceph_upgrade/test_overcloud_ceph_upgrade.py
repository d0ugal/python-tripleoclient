#   Copyright 2018 Red Hat, Inc.
#
#   Licensed under the Apache License, Version 2.0 (the "License"); you may
#   not use this file except in compliance with the License. You may obtain
#   a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#   License for the specific language governing permissions and limitations
#   under the License.
#

import mock

from osc_lib.tests.utils import ParserException
from tripleoclient import constants
from tripleoclient import exceptions
from tripleoclient.tests.v1.overcloud_ceph_upgrade import fakes
from tripleoclient.v1 import overcloud_ceph_upgrade


class TestCephUpgrade(fakes.TestCephUpgrade):

    def setUp(self):
        super(TestCephUpgrade, self).setUp()

        # Get the command object to test
        app_args = mock.Mock()
        app_args.verbose_level = 1
        self.cmd = overcloud_ceph_upgrade.CephUpgrade(self.app, app_args)
        uuid4_patcher = mock.patch('uuid.uuid4', return_value="UUID4")
        self.mock_uuid4 = uuid4_patcher.start()
        self.addCleanup(self.mock_uuid4.stop)

    @mock.patch('tripleoclient.workflows.package_update.ffwd_converge_nodes',
                autospec=True)
    @mock.patch('tripleoclient.utils.prepend_environment', autospec=True)
    @mock.patch('tripleoclient.utils.get_stack',
                autospec=True)
    @mock.patch(
        'tripleoclient.v1.overcloud_ceph_upgrade.CephUpgrade.log',
        autospec=True)
    @mock.patch('tripleoclient.workflows.package_update.update',
                autospec=True)
    @mock.patch('yaml.load')
    @mock.patch('shutil.copytree', autospec=True)
    @mock.patch('six.moves.builtins.open')
    @mock.patch('tripleoclient.v1.overcloud_deploy.DeployOvercloud.'
                '_deploy_tripleo_heat_templates', autospec=True)
    def test_ceph_upgrade(self, mock_deploy, mock_open, mock_copy, mock_yaml,
                          mock_ceph_upgrade, mock_logger,
                          mock_get_stack, mock_prepend_env,
                          ffwd_converge_nodes):
        mock_stack = mock.Mock()
        mock_stack.stack_name = 'mystack'
        mock_get_stack.return_value = mock_stack
        mock_yaml.return_value = {'fake_container': 'fake_value'}

        argslist = ['--stack', 'mystack', '--templates']
        verifylist = [
            ('stack', 'mystack'),
            ('templates', constants.TRIPLEO_HEAT_TEMPLATES)
        ]

        parsed_args = self.check_parser(self.cmd, argslist, verifylist)
        self.cmd.take_action(parsed_args)
        mock_ceph_upgrade.assert_called_once_with(
            self.app.client_manager,
            container='mystack',
            ceph_ansible_playbook='/usr/share/ceph-ansible'
                                  '/infrastructure-playbooks'
                                  '/rolling_update.yml',
        )
        with mock.patch('os.path.exists') as mock_exists:
            mock_exists.return_value = True
            ffwd_converge_nodes.assert_called_once_with(
                self.app.client_manager,
                container='mystack')

    @mock.patch('tripleoclient.utils.prepend_environment', autospec=True)
    @mock.patch('tripleoclient.workflows.package_update.update',
                autospec=True)
    @mock.patch('six.moves.builtins.open')
    @mock.patch('yaml.load')
    @mock.patch('shutil.copytree', autospec=True)
    @mock.patch('tripleoclient.v1.overcloud_deploy.DeployOvercloud.'
                '_deploy_tripleo_heat_templates', autospec=True)
    def test_ceph_upgrade_failed(
        self, mock_deploy, mock_copy, mock_yaml, mock_open,
            mock_ceph_upgrade, mock_prepend_env):
        mock_ceph_upgrade.side_effect = exceptions.DeploymentError()
        mock_yaml.return_value = {'fake_container': 'fake_value'}
        argslist = ['--stack', 'overcloud', '--templates']
        verifylist = [
            ('stack', 'overcloud'),
            ('templates', constants.TRIPLEO_HEAT_TEMPLATES)
        ]
        parsed_args = self.check_parser(self.cmd, argslist, verifylist)

        self.assertRaises(exceptions.DeploymentError,
                          self.cmd.take_action, parsed_args)

    @mock.patch('tripleoclient.workflows.package_update.update_ansible',
                autospec=True)
    @mock.patch('os.path.expanduser')
    @mock.patch('oslo_concurrency.processutils.execute')
    @mock.patch('six.moves.builtins.open')
    def test_upgrade_no_nodes_or_roles(self, mock_open, mock_execute,
                                       mock_expanduser, upgrade_ansible):
        mock_expanduser.return_value = '/home/fake/'
        argslist = ["--nodes", "controller-1", "--roles", "foo"]
        verifylist = []
        self.assertRaises(ParserException, lambda: self.check_parser(
            self.cmd, argslist, verifylist))