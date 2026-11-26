import sys
import unittest
from unittest.mock import patch
from aeris.distribution import frozen, translation_worker_available, application_lock
import main


class DistributionTests(unittest.TestCase):
    def test_source_mode(self):
        with patch.object(sys, 'frozen', False, create=True):
            self.assertFalse(frozen())
            self.assertTrue(translation_worker_available())
            with application_lock() as acquired:
                self.assertTrue(acquired)

    def test_frozen_mode(self):
        with patch.object(sys, 'frozen', True, create=True):
            self.assertTrue(frozen())
            self.assertFalse(translation_worker_available())

    def test_unknown_args_no_gui(self):
        with patch.object(sys, 'argv', ['Aeris', '--bad']), patch('aeris.hub.main') as hub:
            self.assertEqual(main.main(), 2)
            hub.assert_not_called()

    def test_self_test_dispatch(self):
        with patch.object(sys, 'argv', ['Aeris', '--self-test']), patch('main.self_test', return_value=0) as check:
            self.assertEqual(main.main(), 0)
            check.assert_called_once_with()
        with patch.object(sys, 'argv', ['Aeris', '--self-test']), patch('main.self_test', side_effect=RuntimeError):
            self.assertEqual(main.main(), 1)

    def test_full_self_test_dispatch(self):
        with patch.object(sys, 'argv', ['Aeris', '--self-test-full']), patch('main.self_test', return_value=0) as check:
            self.assertEqual(main.main(), 0)
            check.assert_called_once_with(full=True)

    @unittest.skipUnless(sys.platform == 'win32', 'Windows mutex required')
    def test_native_mutex(self):
        with patch.object(sys, 'frozen', True, create=True), patch('aeris.distribution.APP_MUTEX', r'Local\KGVision.Aeris.Test.' + str(__import__('uuid').uuid4())):
            with application_lock() as first:
                self.assertTrue(first)
                with application_lock() as second:
                    self.assertFalse(second)
            with application_lock() as reopened:
                self.assertTrue(reopened)
