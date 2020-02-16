from git_trunk.git_trunk import GitTrunkRelease, RELEASE_SECTION
from . import common


class TestGitTrunkRelease(common.GitTrunkCommon):
    """Class to test git-trunk release command."""

    def _test_release(self, tag, target='HEAD'):
        rev_list = self.git.rev_list
        self.assertEqual(rev_list('-1', tag), rev_list('-1', target))
        # Check if tag exists on remote.
        remote_tags = self.git.ls_remote('--tags', 'origin')
        self.assertIn(tag, remote_tags)
        tag_header_msg = self.git.tag('-l', tag)
        self.assertEqual(tag_header_msg, tag)

    def test_01_git_release(self):
        """Try to release non semver existing and incorrect version.

        Case 1: Try to release existing version.
        Case 2: Try to release version without new changes.
        Case 3: Try to release existing version that is on remote only.
        Case 4: Try to release empty version.
        Case 5: Try to release version using custom not existing commit.
        """
        # Case 1.
        # By default, we use semver, so disabling semver checking.
        self.git_trunk_init._init_cfg[RELEASE_SECTION]['usesemver'] = False
        self.git_trunk_init.run()
        self.git.tag('-a', 'v1', '-m', 'tag msg')
        # Case 2.
        with self.assertRaises(ValueError):
            GitTrunkRelease(
                repo_path=self.dir_local.name,
                log_level=common.LOG_LEVEL
            ).run('v3')
        self.git.tag('-a', 'v2', '-m', 'tag msg')
        self.git.push('--tags')
        self._create_dummy_commit('dummy_dir1')
        with self.assertRaises(ValueError):
            GitTrunkRelease(
                repo_path=self.dir_local.name,
                log_level=common.LOG_LEVEL
            ).run(version='v2')
        # Case 3.
        # Remove tag locally, to make sure it will be fetched back.
        self.git.tag('-d', 'v2')
        with self.assertRaises(ValueError):
            GitTrunkRelease(
                repo_path=self.dir_local.name,
                log_level=common.LOG_LEVEL
            ).run(version='v2')
        # Case 4.
        with self.assertRaises(ValueError):
            GitTrunkRelease(
                repo_path=self.dir_local.name,
                log_level=common.LOG_LEVEL
            ).run()
        # Case 5.
        with self.assertRaises(ValueError):
            GitTrunkRelease(
                repo_path=self.dir_local.name,
                log_level=common.LOG_LEVEL
            ).run(version='v3', ref='not_existing_commit123')

    def test_02_git_release(self):
        """Try to release semver existing and incorrect version.

        Case 1: Try to release existing version.
        Case 2: Try to release version without new changes.
        Case 3: Try to release semver invalid version.
        """
        # Case 1.
        self.git.tag('-a', 'v1', '-m', 'tag msg')
        self.git.tag('-a', '0.1.0', '-m', 'tag msg')
        # Case 2.
        # Try to release, when there are no new changes to release.
        with self.assertRaises(ValueError):
            GitTrunkRelease(
                repo_path=self.dir_local.name,
                log_level=common.LOG_LEVEL
            ).run(part='major')
        self.git.tag('-a', '0.2.0', '-m', 'tag msg')
        self.git.push('--tags')
        self._create_dummy_commit('dummy_dir1')
        with self.assertRaises(ValueError):
            GitTrunkRelease(
                repo_path=self.dir_local.name,
                log_level=common.LOG_LEVEL
            ).run(version='0.2.0')
        # Case 3.
        with self.assertRaises(ValueError):
            GitTrunkRelease(
                repo_path=self.dir_local.name,
                log_level=common.LOG_LEVEL
            ).run(version='INCORRECT.0.2.0')

    def test_03_git_release(self):
        """Release non semver version.

        Case 1: Set initial custom version. No Prefix.
        Case 2: Set second custom version. No prefix.
        Case 3: Set third custom version. With prefix.
        Case 4: Release on specified commit. With prefix.
        Case 5: Release on same commit twice by forcing. With prefix.
        """
        self.git_trunk_init._init_cfg[RELEASE_SECTION]['usesemver'] = False
        self.git_trunk_init.run()
        trunk_release = GitTrunkRelease(
            repo_path=self.dir_local.name,
            log_level=common.LOG_LEVEL
        )
        trunk_release.run(version='v0')
        self._test_release('v0')
        self.git.tag('-a', 'v1', '-m', 'tag msg')
        self.git.tag('-a', 'v2', '-m', 'tag msg')
        self.git.push('--tags')
        self._create_dummy_commit('dummy_dir1')
        self._create_dummy_commit('dummy_dir2')
        trunk_release.config.section['version_prefix'] = 'X'
        trunk_release.run(version='v3')
        self._test_release('Xv3')
        self._create_dummy_commit('dummy_dir3')
        self._create_dummy_commit('dummy_dir4')
        # Get dummy_dir3 commit hash.
        commit = self.git.rev_list('master', '-1', '--skip=1')
        trunk_release.run(version='v4', ref=commit)
        self._test_release('Xv4', target=commit)
        trunk_release.run(version='v5', ref=commit, force=True)
        self._test_release('Xv5', target=commit)

    def test_04_git_release(self):
        """Release semver version.

        Case 1: bump initial minor version. No prefix.
        Case 2: bump second minor version. No prefix.
        Case 3: bump first major version. No prefix.
        Case 4. bump first patch version. With prefix.
        Case 5. Set custom version with RC. With prefix.
        Case 6. Set final version to remove RC. With prefix.
        """
        # Case 1.
        # By default, bumps minor version.
        trunk_release = GitTrunkRelease(
            repo_path=self.dir_local.name,
            log_level=common.LOG_LEVEL
        )
        trunk_release.run()
        self._test_release('0.1.0')
        # Case 2.
        # Adding tag to be invalid semver version, to check if its going
        # to be ignored.
        self.git.tag('-a', 'non-semver-version', '-m', 'tag msg')
        self.git.tag('-a', 'v1.0.1', '-m', 'tag msg1')
        self.git.tag('-a', '1.1.0', '-m', 'tag msg2')
        self.git.push('--tags')
        self._create_dummy_commit('dummy_dir1')
        trunk_release.run()
        self._test_release('1.2.0')
        # Case 3.
        self._create_dummy_commit('dummy_dir2')
        trunk_release.run(part='major')
        self._test_release('2.0.0')
        # Case 4.
        # Set prefix.
        trunk_release.config.section['version_prefix'] = 'v'
        self._create_dummy_commit('dummy_dir3')
        trunk_release.run(part='patch')
        self._test_release('v2.0.1')
        self._create_dummy_commit('dummy_dir4')
        trunk_release.run(version='3.0.0-rc')  # set custom version.
        self._test_release('v3.0.0-rc')
        # Case 6.
        self._create_dummy_commit('dummy_dir5')
        # Sanity check. Unset tracking branch, to make sure release
        # can proceed anyway.
        self.git.branch('--unset-upstream')
        trunk_release.run(part='final')
        self._test_release('v3.0.0')
