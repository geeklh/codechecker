#
# -------------------------------------------------------------------------
#
#  Part of the CodeChecker project, under the Apache License v2.0 with
#  LLVM Exceptions. See LICENSE for license information.
#  SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
#
# -------------------------------------------------------------------------

""" Test review status functionality."""


import logging
import os
import unittest

from codechecker_api.codeCheckerDBAccess_v6.ttypes import CommentKind, \
    ReviewStatus

from libtest import env
from libtest.thrift_client_to_db import get_all_run_results


class TestReviewStatus(unittest.TestCase):

    _ccClient = None

    def setUp(self):
        test_workspace = os.environ['TEST_WORKSPACE']

        test_class = self.__class__.__name__
        print('Running ' + test_class + ' tests in ' + test_workspace)

        self._testproject_data = env.setup_test_proj_cfg(test_workspace)
        self.assertIsNotNone(self._testproject_data)

        self._cc_client = env.setup_viewer_client(test_workspace)
        self.assertIsNotNone(self._cc_client)

        # Get the run names which belong to this test.
        run_names = env.get_run_names(test_workspace)

        runs = self._cc_client.getRunData(None, None, 0, None)

        test_runs = [run for run in runs if run.name in run_names]

        self.assertEqual(len(test_runs), 1,
                         'There should be only one run for this test.')
        self._runid = test_runs[0].runId

    def __get_system_comments(self, report_hash):
        """ Get system comments for the given report hash. """
        return [c for c in self._cc_client.getComments(report_hash)
                if c.kind == CommentKind.SYSTEM]

    def test_multiple_change_review_status(self):
        """
        Test changing review status of the same bug.
        """
        runid = self._runid
        logging.debug('Get all run results from the db for runid: ' +
                      str(runid))

        run_results = get_all_run_results(self._cc_client, runid)
        self.assertIsNotNone(run_results)
        self.assertNotEqual(len(run_results), 0)

        bug = run_results[0]

        # There are no system comments for this bug.
        comments = self.__get_system_comments(bug.reportId)
        self.assertEqual(len(comments), 0)

        # Change review status to confirmed bug.
        review_comment = 'This is really a bug'
        status = ReviewStatus.CONFIRMED
        success = self._cc_client.changeReviewStatus(
            bug.reportId, status, review_comment)

        self.assertTrue(success)
        logging.debug('Bug review status changed successfully')

        report = self._cc_client.getReport(bug.reportId)
        self.assertEqual(report.reviewData.comment, review_comment)
        self.assertEqual(report.reviewData.status, status)

        # There is one system comment for this bug.
        comments = self.__get_system_comments(bug.reportId)
        self.assertEqual(len(comments), 1)

        # Try to update the review status again with the same data and check
        # that no new system comment entry will be created.
        success = self._cc_client.changeReviewStatus(
            bug.reportId, status, review_comment)
        comments = self.__get_system_comments(bug.reportId)
        self.assertEqual(len(comments), 1)

        # Test that updating only the review status message a new system
        # comment will be created.
        success = self._cc_client.changeReviewStatus(
            bug.reportId, status, "test system comment change")
        self.assertTrue(success)
        comments = self.__get_system_comments(bug.reportId)
        self.assertEqual(len(comments), 2)

        # Try to change review status back to unreviewed.
        status = ReviewStatus.UNREVIEWED
        success = self._cc_client.changeReviewStatus(
            bug.reportId,
            status,
            None)

        self.assertTrue(success)
        logging.debug("Bug review status changed successfully")

        report = self._cc_client.getReport(bug.reportId)
        self.assertEqual(report.reviewData.comment, '')
        self.assertEqual(report.reviewData.status, status)

        # Change review status to false positive.
        review_comment = 'This is not a bug'
        status = ReviewStatus.FALSE_POSITIVE
        success = self._cc_client.changeReviewStatus(
            bug.reportId, status, review_comment)

        self.assertTrue(success)
        logging.debug('Bug review status changed successfully')

        report = self._cc_client.getReport(bug.reportId)
        self.assertEqual(report.reviewData.comment, review_comment)
        self.assertEqual(report.reviewData.status, status)

        # Change review status to intentional.
        review_comment = ''
        status = ReviewStatus.INTENTIONAL
        success = self._cc_client.changeReviewStatus(
            bug.reportId, status, review_comment)

        self.assertTrue(success)
        logging.debug('Bug review status changed successfully')

        report = self._cc_client.getReport(bug.reportId)
        self.assertEqual(report.reviewData.comment, review_comment)
        self.assertEqual(report.reviewData.status, status)
