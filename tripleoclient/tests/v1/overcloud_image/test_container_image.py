#   Copyright 2015 Red Hat, Inc.
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
import os
import shutil
import tempfile
import yaml

from tripleoclient.tests.v1.test_plugin import TestPluginV1
from tripleoclient.v1 import container_image


class TestContainerImageUpload(TestPluginV1):

    def setUp(self):
        super(TestContainerImageUpload, self).setUp()

        # Get the command object to test
        self.cmd = container_image.UploadImage(self.app, None)

    @mock.patch('sys.exit')
    @mock.patch('tripleo_common.image.image_uploader.ImageUploadManager',
                autospec=True)
    def test_container_image_upload_noargs(self, mock_manager, exit_mock):
        arglist = []
        verifylist = []

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        self.cmd.take_action(parsed_args)
        # argparse will complain that --config-file is missing and exit with 2
        exit_mock.assert_called_with(2)

    @mock.patch('tripleo_common.image.image_uploader.ImageUploadManager',
                autospec=True)
    def test_container_image_upload_conf_files(self, mock_manager):
        arglist = [
            '--config-file',
            '/tmp/foo.yaml',
            '--config-file',
            '/tmp/bar.yaml'
        ]
        verifylist = []

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        self.cmd.take_action(parsed_args)

        mock_manager.assert_called_once_with(
            ['/tmp/foo.yaml', '/tmp/bar.yaml'])
        mock_manager.return_value.upload.assert_called_once_with()


class TestContainerImagePrepare(TestPluginV1):

    def setUp(self):
        super(TestContainerImagePrepare, self).setUp()

        # Get the command object to test
        self.cmd = container_image.PrepareImageFiles(self.app, None)

    @mock.patch('tripleo_common.image.kolla_builder.KollaImageBuilder')
    def test_container_image_prepare_noargs(self, mock_builder):
        arglist = []
        verifylist = []
        cift = mock.MagicMock()
        cift.return_value = {}

        mock_builder.return_value.container_images_from_template = cift

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        self.cmd.take_action(parsed_args)

        mock_builder.assert_called_once_with([parsed_args.template_file])
        cift.assert_called_once_with(
            filter=mock.ANY,
            name_prefix='centos-binary-',
            name_suffix='',
            namespace='tripleoupstream',
            tag='latest'
        )

    @mock.patch('tripleo_common.image.kolla_builder.KollaImageBuilder')
    def test_container_image_prepare(self, mock_builder):

        temp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, temp)
        images_file = os.path.join(temp, 'overcloud_containers.yaml')
        env_file = os.path.join(temp, 'containers_env.yaml')
        tmpl_file = os.path.join(temp, 'overcloud_containers.yaml.j2')

        arglist = [
            '--template-file',
            tmpl_file,
            '--tag',
            'passed-ci',
            '--namespace',
            'tripleo',
            '--prefix',
            'os-',
            '--suffix',
            'foo',
            '--images-file',
            images_file,
            '--env-file',
            env_file,
        ]
        self.cmd.app.command_options = arglist
        verifylist = []
        cift = mock.MagicMock()
        cift.return_value = [{
            'imagename': 'tripleo/os-aodh-apifoo:passed-ci',
            'params': ['DockerAodhApiImage', 'DockerAodhConfigImage'],
        }, {
            'imagename': 'tripleo/os-heat-apifoo:passed-ci',
            'params': ['DockerHeatApiImage'],
        }]

        mock_builder.return_value.container_images_from_template = cift

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        self.cmd.take_action(parsed_args)

        mock_builder.assert_called_once_with([tmpl_file])
        cift.assert_called_once_with(
            filter=mock.ANY,
            name_prefix='os-',
            name_suffix='foo',
            namespace='tripleo',
            tag='passed-ci'
        )
        ci_data = {
            'container_images': [{
                'imagename': 'tripleo/os-aodh-apifoo:passed-ci',
            }, {
                'imagename': 'tripleo/os-heat-apifoo:passed-ci',
            }]
        }
        env_data = {
            'parameter_defaults': {
                'DockerAodhApiImage': 'tripleo/os-aodh-apifoo:passed-ci',
                'DockerAodhConfigImage': 'tripleo/os-aodh-apifoo:passed-ci',
                'DockerHeatApiImage': 'tripleo/os-heat-apifoo:passed-ci',
            }
        }
        with open(images_file) as f:
            self.assertEqual(ci_data, yaml.safe_load(f))
        with open(env_file) as f:
            self.assertEqual(env_data, yaml.safe_load(f))


class TestContainerImageBuild(TestPluginV1):

    def setUp(self):
        super(TestContainerImageBuild, self).setUp()

        # Get the command object to test
        self.cmd = container_image.BuildImage(self.app, None)

    @mock.patch('sys.exit')
    @mock.patch('tripleo_common.image.kolla_builder.KollaImageBuilder',
                autospec=True)
    def test_container_image_build_noargs(self, mock_builder, exit_mock):
        arglist = []
        verifylist = []

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        self.cmd.take_action(parsed_args)
        # argparse will complain that --config-file and --kolla-config are
        # missing exit with 2
        exit_mock.assert_called_with(2)

    @mock.patch('tripleo_common.image.kolla_builder.KollaImageBuilder',
                autospec=True)
    def test_container_image_build(self, mock_builder):
        arglist = [
            '--config-file',
            '/tmp/foo.yaml',
            '--config-file',
            '/tmp/bar.yaml',
            '--kolla-config-file',
            '/tmp/kolla.conf'
        ]
        verifylist = []

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        self.cmd.take_action(parsed_args)

        mock_builder.assert_called_once_with([
            '/tmp/foo.yaml', '/tmp/bar.yaml'])
        mock_builder.return_value.build_images.assert_called_once_with([
            '/tmp/kolla.conf'
        ])
