import hashlib
import hmac
import importlib.util
import pathlib
import unittest
from unittest.mock import patch


MODULE_PATH = pathlib.Path(__file__).with_name('igc-arena-probe.py')
SPEC = importlib.util.spec_from_file_location('igc_arena_probe', MODULE_PATH)
probe_runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(probe_runner)


def valid_config():
    return {
        'job_id': '234911ff-aaaa-4111-8999-bbbbbbbbbbbb',
        'snapshot_sha256': 'a' * 64,
        'origin': 'https://workbench.example.workers.dev',
        'hmac_secret': 'h' * 32,
    }


class HMACRunnerRequestTests(unittest.TestCase):
    def test_artifact_manifest_binds_job_snapshot_and_result_hash(self):
        config = valid_config()
        result = {'job_id': config['job_id'], 'snapshot_sha256': config['snapshot_sha256'], 'status': 'PASS'}
        manifest = probe_runner.signed_artifact_manifest(result, config)
        encoded = manifest['result_json'].encode('utf-8')
        digest = hashlib.sha256(encoded).hexdigest()
        expected = hmac.new(
            config['hmac_secret'].encode(),
            f"IGC-ARENA-ARTIFACT-V1\n{config['job_id']}\n{config['snapshot_sha256']}\n{digest}".encode(),
            hashlib.sha256,
        ).hexdigest()
        self.assertEqual(manifest['schema_version'], 'igc.arena_probe_artifact.v1')
        self.assertEqual(manifest['result_sha256'], digest)
        self.assertEqual(manifest['signature'], 'v1=' + expected)

    def test_signed_get_includes_existing_hmac_without_access_headers(self):
        config = valid_config()
        response = type('Response', (), {
            '__enter__': lambda self: self,
            '__exit__': lambda self, *_: None,
            'read': lambda self: b'{}',
        })()
        captured = {}

        def fake_open(request, timeout):
            captured['request'] = request
            captured['timeout'] = timeout
            return response

        with patch.object(probe_runner.time, 'time', return_value=1_800_000_000):
            self.assertEqual(probe_runner.signed_request('GET', 'snapshot', config=config, open_url=fake_open), b'{}')

        request = captured['request']
        path = '/api/runner/jobs/' + config['job_id'] + '/snapshot'
        expected = hmac.new(
            config['hmac_secret'].encode(),
            f"1800000000\nGET\n{path}\n{hashlib.sha256(b'').hexdigest()}".encode(),
            hashlib.sha256,
        ).hexdigest()
        self.assertIsNone(request.get_header('Cf-access-client-id'))
        self.assertIsNone(request.get_header('Cf-access-client-secret'))
        self.assertEqual(request.get_header('X-igc-signature'), 'v1=' + expected)
        self.assertEqual(request.get_method(), 'GET')
        self.assertEqual(captured['timeout'], 35)

    def test_signed_post_keeps_body_hash_without_access_headers(self):
        config = valid_config()
        body = b'{"status":"PASS"}'
        captured = {}

        def fake_open(request, timeout):
            captured['request'] = request
            return type('Response', (), {
                '__enter__': lambda self: self,
                '__exit__': lambda self, *_: None,
                'read': lambda self: b'{"accepted":true}',
            })()

        probe_runner.signed_request('POST', 'result', body, config=config, open_url=fake_open)
        request = captured['request']
        self.assertIsNone(request.get_header('Cf-access-client-id'))
        self.assertIsNone(request.get_header('Cf-access-client-secret'))
        self.assertEqual(request.data, body)
        self.assertEqual(request.get_method(), 'POST')

    def test_missing_hmac_credential_is_rejected(self):
        config = valid_config()
        config['hmac_secret'] = ''
        self.assertRaisesRegex(
            ValueError,
            'Runner HMAC secret missing or too short',
            probe_runner.load_config,
            {
                'IGC_JOB_ID': config['job_id'],
                'IGC_SNAPSHOT_SHA256': config['snapshot_sha256'],
                'IGC_SERVICE_ORIGIN': config['origin'],
                'IGC_RUNNER_HMAC_SECRET': config['hmac_secret'],
            },
        )

    def test_redirects_are_rejected_without_requesting_another_origin(self):
        config = valid_config()
        other_origin = 'https://attacker.example/steal'

        for method, suffix in (('GET', 'snapshot'), ('POST', 'result')):
            for code in (301, 302, 303, 307, 308):
                with self.subTest(method=method, status=code):
                    requests = []

                    class FakeOpener:
                        def open(self, request, timeout):
                            requests.append(request.full_url)
                            # Simulate the opener handling the first 3xx. The
                            # rejecting handler must raise before a follow-up.
                            redirect = probe_runner.RejectHTTPRedirects()
                            redirect.redirect_request(
                                request, None, code, 'redirect',
                                {'Location': other_origin}, other_origin,
                            )

                    def fake_build_opener(handler):
                        self.assertIs(handler, probe_runner.RejectHTTPRedirects)
                        return FakeOpener()

                    with patch.object(probe_runner, 'build_opener', side_effect=fake_build_opener):
                        with self.assertRaisesRegex(probe_runner.RedirectRejected, f'HTTP redirect {code} rejected'):
                            probe_runner.signed_request(
                                method, suffix, b'{}' if method == 'POST' else b'', config=config,
                            )

                    self.assertEqual(requests, [config['origin'] + '/api/runner/jobs/' + config['job_id'] + '/' + suffix])


if __name__ == '__main__':
    unittest.main()
