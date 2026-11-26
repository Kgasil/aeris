import queue
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from aeris.local_worker import LocalWorker, worker_for
from aeris.contextual_text import contextual_review
from aeris.intelligent_text import LANGUAGES

class LocalWorkerTests(unittest.TestCase):
    def test_exclusive_until_real_exit_and_delivery_after_release(self):
        worker=LocalWorker(); release=threading.Event(); results=queue.Queue()
        try:
            self.assertTrue(worker.start(lambda: release.wait(3), lambda result: results.put((result,worker.busy))))
            self.assertTrue(worker.busy)
            self.assertFalse(worker.start(lambda: self.fail('overlapping worker')))
        finally: release.set()
        self.assertEqual(results.get(timeout=3),(True,False))
        self.assertTrue(worker.start(lambda:42,results.put)); self.assertEqual(results.get(timeout=3),42)

    def test_failed_thread_start_releases_lease(self):
        worker=LocalWorker()
        with patch('aeris.local_worker.threading.Thread.start',side_effect=RuntimeError('failed')):
            with self.assertRaises(RuntimeError): worker.start(lambda:None)
        self.assertFalse(worker.busy)

    def test_lease_shared_by_hub_not_between_hubs(self):
        h=SimpleNamespace(); other=SimpleNamespace()
        self.assertIs(worker_for(h),worker_for(h)); self.assertIsNot(worker_for(h),worker_for(other))

    def test_inner_model_json_strict(self):
        for response in ('{"texto":"Olá","texto":"Outro"}', '{"texto":NaN}', '{"texto":"ok","x":1e999}', ' '*33000+'{"texto":"ok"}'):
            with self.subTest(response=response[:100]), self.assertRaises(ValueError):
                contextual_review('Ola',LANGUAGES[0],'local',request=lambda *a,**k:response)
