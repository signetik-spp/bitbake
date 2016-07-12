#! /usr/bin/env python
# ex:ts=4:sw=4:sts=4:et
# -*- tab-width: 4; c-basic-offset: 4; indent-tabs-mode: nil -*-
#
# BitBake Toaster Implementation
#
# Copyright (C) 2013-2016 Intel Corporation
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

from django.core.urlresolvers import reverse
from django.utils import timezone

from tests.browser.selenium_helpers import SeleniumTestCase

from orm.models import Project, Release, BitbakeVersion, Build, Target
from orm.models import Target_Image_File, TargetSDKFile, TargetKernelFile

class TestBuildDashboardPageArtifacts(SeleniumTestCase):
    """ Tests for artifacts on the build dashboard /build/X """

    def setUp(self):
        bbv = BitbakeVersion.objects.create(name='bbv1', giturl='/tmp/',
                                            branch='master', dirpath="")
        release = Release.objects.create(name='release1',
                                         bitbake_version=bbv)
        self.project = Project.objects.create_project(name='test project',
                                                      release=release)

    def _get_build_dashboard(self, build):
        """
        Navigate to the build dashboard for build
        """
        url = reverse('builddashboard', args=(build.id,))
        self.get(url)

    def _has_build_artifacts_heading(self):
        """
        Check whether the "Build artifacts" heading is visible (True if it
        is, False otherwise).
        """
        return self.element_exists('[data-heading="build-artifacts"]')

    def _has_images_menu_option(self):
        """
        Try to get the "Images" list element from the left-hand menu in the
        build dashboard, and return True if it is present, False otherwise.
        """
        return self.element_exists('li.nav-header[data-menu-heading="images"]')

    def test_no_artifacts(self):
        """
        If a build produced no artifacts, the artifacts heading and images
        menu option shouldn't show.
        """
        now = timezone.now()
        build = Build.objects.create(project=self.project,
            started_on=now, completed_on=now, outcome=Build.SUCCEEDED)

        Target.objects.create(is_image=False, build=build, task='',
            target='mpfr-native')

        self._get_build_dashboard(build)

        # check build artifacts heading
        msg = 'Build artifacts heading should not be displayed for non-image' \
            'builds'
        self.assertFalse(self._has_build_artifacts_heading(), msg)

        # check "Images" option in left-hand menu (should not be there)
        msg = 'Images option should not be shown in left-hand menu'
        self.assertFalse(self._has_images_menu_option(), msg)

    def test_sdk_artifacts(self):
        """
        If a build produced SDK artifacts, they should be shown, but the section
        for image files and the images menu option should be hidden.
        """
        now = timezone.now()
        build = Build.objects.create(project=self.project,
            started_on=now, completed_on=timezone.now(),
            outcome=Build.SUCCEEDED)

        target = Target.objects.create(is_image=True, build=build,
            task='populate_sdk', target='core-image-minimal')

        sdk_file1 = TargetSDKFile.objects.create(target=target,
            file_size=100000,
            file_name='/home/foo/core-image-minimal.toolchain.sh')

        sdk_file2 = TargetSDKFile.objects.create(target=target,
            file_size=120000,
            file_name='/home/foo/x86_64.toolchain.sh')

        self._get_build_dashboard(build)

        # check build artifacts heading
        msg = 'Build artifacts heading should be displayed for SDK ' \
            'builds which generate artifacts'
        self.assertTrue(self._has_build_artifacts_heading(), msg)

        # check "Images" option in left-hand menu (should not be there)
        msg = 'Images option should not be shown in left-hand menu for ' \
            'builds which didn\'t generate an image file'
        self.assertFalse(self._has_images_menu_option(), msg)

        # check links to SDK artifacts
        sdk_artifact_links = self.find_all('[data-links="sdk-artifacts"] li')
        self.assertEqual(len(sdk_artifact_links), 2,
            'should be links to 2 SDK artifacts')

    def test_image_artifacts(self):
        """
        If a build produced image files, kernel artifacts, and manifests,
        they should all be shown, as well as the image link in the left-hand
        menu.
        """
        now = timezone.now()
        build = Build.objects.create(project=self.project,
            started_on=now, completed_on=timezone.now(),
            outcome=Build.SUCCEEDED)

        target = Target.objects.create(is_image=True, build=build,
            task='', target='core-image-minimal',
            license_manifest_path='/home/foo/license.manifest',
            package_manifest_path='/home/foo/package.manifest')

        image_file = Target_Image_File.objects.create(target=target,
            file_name='/home/foo/core-image-minimal.ext4', file_size=9000)

        kernel_file1 = TargetKernelFile.objects.create(target=target,
            file_name='/home/foo/bzImage', file_size=2000)

        kernel_file2 = TargetKernelFile.objects.create(target=target,
            file_name='/home/foo/bzImage', file_size=2000)

        self._get_build_dashboard(build)

        # check build artifacts heading
        msg = 'Build artifacts heading should be displayed for image ' \
            'builds'
        self.assertTrue(self._has_build_artifacts_heading(), msg)

        # check "Images" option in left-hand menu (should be there)
        msg = 'Images option should be shown in left-hand menu for image builds'
        self.assertTrue(self._has_images_menu_option(), msg)

        # check link to image file
        selector = '[data-links="image-artifacts"] li'
        self.assertTrue(self.element_exists(selector),
            'should be a link to the image file (selector %s)' % selector)

        # check links to kernel artifacts
        kernel_artifact_links = \
            self.find_all('[data-links="kernel-artifacts"] li')
        self.assertEqual(len(kernel_artifact_links), 2,
            'should be links to 2 kernel artifacts')

        # check manifest links
        selector = 'a[data-link="license-manifest"]'
        self.assertTrue(self.element_exists(selector),
            'should be a link to the license manifest (selector %s)' % selector)

        selector = 'a[data-link="package-manifest"]'
        self.assertTrue(self.element_exists(selector),
            'should be a link to the package manifest (selector %s)' % selector)
