from fastapi.testclient import TestClient
from runtime.main import app

def test_rest_e2e_full_workflow():
    c=TestClient(app)
    wid='e2e-api-065'
    assert c.post('/work',json={'id':wid,'title':'API E2E'}).status_code==201
    for step in range(1,6):
        r=c.post(f'/work/{wid}/step/{step}',json={'expected':f'E{step}','actual':f'E{step}'})
        assert r.status_code==201 and r.json()['status']=='PASSED'
    r=c.post(f'/work/{wid}/verify',json={'expected':'MATCH','actual':'MATCH'})
    assert r.status_code==201 and r.json()['status']=='VERIFIED'
    assert c.get(f'/work/{wid}').json()['work']['status']=='DELIVERED'

def test_gate_blocks_skipping_step():
    c=TestClient(app); wid='e2e-gate-065'
    assert c.post('/work',json={'id':wid,'title':'Gate'}).status_code==201
    assert c.post(f'/work/{wid}/step/3',json={'expected':'x','actual':'x'}).status_code==409
