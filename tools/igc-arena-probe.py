#!/usr/bin/env python3
"""GitHub runner: metadata-only deterministic probe, not a CEI research inference.

Exchanges requests only with the configured Cloudflare origin.
"""
import hashlib, hmac, json, os, pathlib, re, sys, time
from urllib.request import Request, urlopen

def load_config(environ=os.environ):
    config = {
        'job_id': environ.get('IGC_JOB_ID', ''),
        'snapshot_sha256': environ.get('IGC_SNAPSHOT_SHA256', ''),
        'origin': environ.get('IGC_SERVICE_ORIGIN', '').strip().rstrip('/'),
        'hmac_secret': environ.get('IGC_RUNNER_HMAC_SECRET', ''),
        'access_client_id': environ.get('CF_ACCESS_CLIENT_ID', '').strip(),
        'access_client_secret': environ.get('CF_ACCESS_CLIENT_SECRET', ''),
    }
    if not re.fullmatch(r'[0-9a-f-]{36}', config['job_id']):
        raise ValueError('Invalid opaque job ID')
    if not re.fullmatch(r'[0-9a-f]{64}', config['snapshot_sha256']):
        raise ValueError('Invalid snapshot hash')
    if not config['origin'].startswith('https://') or '/' in config['origin'][8:]:
        raise ValueError('Invalid service origin')
    if len(config['hmac_secret']) < 24:
        raise ValueError('Runner HMAC secret missing or too short')
    if not config['access_client_id'] or not config['access_client_secret']:
        raise ValueError('Cloudflare Access service token credentials are required')
    return config


def signed_request(method, suffix, payload=b'', *, config, open_url=urlopen):
    # Domain fixed in GitHub repository variable; never from dispatch input.
    ts = str(int(time.time()))
    path = '/api/runner/jobs/' + config['job_id'] + '/' + suffix
    digest = hashlib.sha256(payload).hexdigest()
    msg = f'{ts}\n{method}\n{path}\n{digest}'.encode('utf-8')
    signature = hmac.new(config['hmac_secret'].encode('utf-8'), msg, hashlib.sha256).hexdigest()
    req = Request(config['origin'] + path, data=payload if method == 'POST' else None,
                  method=method, headers={
                      'X-IGC-Timestamp': ts,
                      'X-IGC-Signature': 'v1=' + signature,
                      'CF-Access-Client-Id': config['access_client_id'],
                      'CF-Access-Client-Secret': config['access_client_secret'],
                      'Accept': 'application/json',
                      'Content-Type': 'application/json'
                  })
    with open_url(req, timeout=35) as res:
        return res.read()


def probe(data, job_id):
    issues=[]
    if data.get('schema_version') != 'igc.runner_snapshot.v0.2': issues.append('bad snapshot schema')
    if data.get('job_id') != job_id: issues.append('job mismatch')
    if data.get('data_class') != 'VISIBLE_METADATA_ONLY' or data.get('holdout_contents_included') is not False:
        issues.append('holdout guard violated')
    intake=data.get('intake') or {}
    if intake.get('case_id') != data.get('case_id'): issues.append('case mismatch')
    obs=intake.get('observability') or []
    if not isinstance(obs, list): obs=[]; issues.append('bad observability')
    if not (intake.get('inquiry') or {}).get('research_question'): issues.append('missing question')
    if not (intake.get('evidence') or {}).get('as_known_at'): issues.append('missing as_known_at')
    if not obs: issues.append('no observable variables')
    if len({x.get('id') for x in obs if isinstance(x,dict)}) != len(obs):issues.append('repeated observable IDs')
    return issues, len(obs)

def run(config):
    result={
      'schema_version':'igc.arena_probe.v0.2', 'job_id':config['job_id'],'snapshot_sha256':config['snapshot_sha256'],
      'status':'FAIL','modelica_executed':False,'inference_calls':0,
      'gates':{'g1':'NOT_RUN','g2':'NOT_RUN','g3':'NOT_RUN'},
      'probe_only':True,'issues':[],'observable_count':0
    }
    try:
        raw=signed_request('GET','snapshot',config=config)
        if hashlib.sha256(raw).hexdigest()!=config['snapshot_sha256']:
            raise ValueError('SHA-256 mismatch of immutable snapshot')
        data=json.loads(raw)
        errors, count=probe(data, config['job_id'])
        result['issues']=errors
        result['observable_count']=count
        result['status']='PASS' if not errors else 'FAIL'
    except Exception as exc:
        result['issues']=[type(exc).__name__+': '+str(exc)[:150]]

    path=pathlib.Path('output/igc-arena-probe-result.json')
    path.parent.mkdir(parents=True,exist_ok=True)
    raw_result=(json.dumps(result,sort_keys=True,ensure_ascii=False,separators=(',',':'))+'\n').encode()
    path.write_bytes(raw_result)
    try:
        signed_request('POST','result',raw_result,config=config)
    except Exception as exc:
        print('Result callback failed (the artifact is retained):',type(exc).__name__,str(exc)[:200],file=sys.stderr)
        return 2
    print('Deterministic probe:',result['status'],'observables:',result['observable_count'],'AI calls: 0')
    return 0 if result['status']=='PASS' else 1


def main():
    try:
        config = load_config()
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return run(config)


if __name__ == '__main__':
    sys.exit(main())


