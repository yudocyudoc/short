"""Validate contract schemas and fixtures. Offline, no Cloudflare or LLM calls."""
import json
from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker, ValidationError
from referencing import Registry, Resource

ROOT=Path(__file__).resolve().parents[1]
contracts=ROOT/'contracts'
store={}
for filename in ('investigation_intake.schema.json','arena_input.schema.json','arena_output.schema.json'):
    data=json.loads((contracts/filename).read_text(encoding='utf-8'))
    Draft202012Validator.check_schema(data)
    store[data['$id']]=data
    store['https://example.invalid/igc/contracts/'+filename]=data

registry=Registry().with_resources((uri,Resource.from_contents(schema)) for uri,schema in store.items())

for filename in ('arena_output_not_run.json',):
    data=json.loads((ROOT/'examples'/filename).read_text(encoding='utf-8'))
    schema=store['https://example.invalid/igc/contracts/arena_output.schema.json']
    Draft202012Validator(schema,format_checker=FormatChecker()).validate(data)

for filename,key in [('investigation_intake_demo.json','investigation_intake.schema.json'),('arena_input_demo.json','arena_input.schema.json')]:
    path=ROOT/'examples'/filename
    if not path.exists():continue
    schema=store['https://example.invalid/igc/contracts/'+key]
    Draft202012Validator(schema,registry=registry,format_checker=FormatChecker()).validate(json.loads(path.read_text(encoding='utf-8')))

# Deliberate negative: a page must never claim it has proved holdout isolation.
example=ROOT/'examples'/'investigation_intake_demo.json'
if example.exists():
    data=json.loads(example.read_text(encoding='utf-8'))
    data['evidence']['holdout']['server_isolation_verified']=True
    try:
        Draft202012Validator(store['https://example.invalid/igc/contracts/investigation_intake.schema.json']).validate(data)
        raise AssertionError('An unverified isolation claim should have failed')
    except ValidationError:
        pass

print('IGC contract schemas, fixtures and negative leakage guard: PASS (zero provider calls)')

