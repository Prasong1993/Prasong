from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

try:
    from .database import init_db, many, get_connection, runtime_status, record_event
    from .controller import create_work, run_step, get_work, record_error, checkpoint
    from .model import STEP_DEFINITIONS, WORKING_STRUCTURE
except ImportError:
    from database import init_db, many, get_connection, runtime_status, record_event
    from controller import create_work, run_step, get_work, record_error, checkpoint
    from model import STEP_DEFINITIONS, WORKING_STRUCTURE

APP_VERSION = '0.6.5'

@asynccontextmanager
async def lifespan(app):
    init_db()
    yield

app = FastAPI(title='IRIS Controller', version=APP_VERSION,
              description='Evidence-first five-step controlled workflow.', lifespan=lifespan)

class EvidenceIn(BaseModel):
    id: str = Field(min_length=1, max_length=128)
    status: str = Field(min_length=1, max_length=32)
    topic: str = Field(min_length=1, max_length=200)
    fact: str = Field(min_length=1)
    source: str = Field(min_length=1, max_length=1000)
    verification_state: str = Field(min_length=1, max_length=32)

class WorkIn(BaseModel):
    id: str = Field(min_length=1, max_length=128)
    title: str = Field(min_length=1, max_length=300)

class StepIn(BaseModel):
    expected: str = Field(min_length=1)
    actual: str = Field(min_length=1)
    note: str = Field(default='', max_length=2000)
    fail_attempts: int = Field(default=0, ge=0, le=9)
    max_attempts: int = Field(default=10, ge=1, le=10)

class FinalVerifyIn(BaseModel):
    expected: str = Field(min_length=1)
    actual: str = Field(min_length=1)
    note: str = Field(default='', max_length=2000)

@app.get('/')
def root():
    return {'name':'IRIS','version':APP_VERSION,'status':'ACTIVE',
            'workflow':'CHECK→DO→VERIFY→RETRY_UNTIL_PASS→NEXT','steps':STEP_DEFINITIONS}

@app.get('/health')
def health():
    try:
        init_db()
        with get_connection() as conn:
            conn.execute('SELECT 1').fetchone()
        return {'status':'ok','database':'ok','db_path':str(__import__('database').get_db_path()) if __package__ in (None, '') else None,'version':APP_VERSION}
    except Exception as exc:
        raise HTTPException(503, f'database unavailable: {exc}')

@app.get('/runtime/status')
def query_runtime_status(work_id: str | None = Query(default=None, max_length=128)):
    """Read persisted runtime state. Empty fields mean no corresponding event exists."""
    try:
        status = runtime_status(work_id)
        if work_id:
            work = get_work(work_id)
            if not work:
                raise HTTPException(404, 'work not found')
            status['work'] = work['work']
            status['steps'] = work['steps']
        status['version'] = APP_VERSION
        return status
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(503, f'runtime status unavailable: {exc}')

@app.get('/structure')
def structure():
    return {'status':'WORKING_STRUCTURE','canonical_22_source':'UNPROVEN',
            'sections':[{'index':i+1,'name':x} for i,x in enumerate(WORKING_STRUCTURE)]}

@app.get('/evidence')
def evidence():
    return {'items':many('SELECT * FROM evidence ORDER BY created_at,id')}

@app.post('/evidence', status_code=201)
def create_evidence(item: EvidenceIn):
    try:
        with get_connection() as conn:
            conn.execute('INSERT INTO evidence(id,status,topic,fact,source,verification_state) VALUES(?,?,?,?,?,?)',
                         tuple(item.model_dump().values()))
    except Exception as exc:
        if 'UNIQUE' in str(exc):
            raise HTTPException(409, 'evidence id already exists')
        raise
    return item.model_dump()

@app.post('/work', status_code=201)
def create_work_endpoint(item: WorkIn):
    try:
        create_work(item.id, item.title)
    except Exception as exc:
        if 'UNIQUE' in str(exc):
            raise HTTPException(409, 'work id already exists')
        raise
    return {'id':item.id,'title':item.title,'status':'CREATED'}

@app.get('/work/{work_id}')
def inspect_work(work_id: str):
    result=get_work(work_id)
    if not result:
        raise HTTPException(404, 'work not found')
    return result

@app.post('/work/{work_id}/step/{step}', status_code=201)
def execute_step(work_id: str, step: int, item: StepIn):
    try:
        return run_step(work_id, step, item.expected, item.actual, item.note,
                        item.fail_attempts, item.max_attempts)
    except ValueError as exc:
        raise HTTPException(409, str(exc))
    except RuntimeError as exc:
        raise HTTPException(422, str(exc))

@app.post('/work/{work_id}/verify', status_code=201)
def final_verify(work_id: str, item: FinalVerifyIn):
    result=get_work(work_id)
    if not result:
        raise HTTPException(404, 'work not found')
    latest={}
    for row in result['steps']:
        latest[row['step']]=row
    if any(latest.get(i,{}).get('status')!='PASSED' for i in STEP_DEFINITIONS):
        raise HTTPException(409, 'final verification requires all five steps to PASS')
    status='VERIFIED' if item.expected.strip()==item.actual.strip() else 'MISMATCH'
    with get_connection() as conn:
        conn.execute('INSERT INTO verifications(work_id,expected,actual,status,note) VALUES(?,?,?,?,?)',
                     (work_id,item.expected,item.actual,status,item.note))
        conn.execute('INSERT INTO audit_log(work_id,action,details) VALUES(?,?,?)',
                     (work_id,'FINAL_VERIFICATION',status))
        if status=='VERIFIED':
            conn.execute("UPDATE work_units SET status='DELIVERED',updated_at=CURRENT_TIMESTAMP WHERE id=?",
                         (work_id,))
    record_event('VERIFICATION_PASSED' if status == 'VERIFIED' else 'VERIFICATION_FAILED',
                 work_id=work_id, status=status,
                 payload={'expected':item.expected,'actual':item.actual,'note':item.note})
    if status!='VERIFIED':
        record_error(work_id, 0, 0, 'FINAL_VERIFICATION_MISMATCH',
                     'final expected vs actual mismatch; result retained as unverified',
                     item.expected, item.actual, 'MISMATCH', 'work not delivered',
                     'correct output and retry final verification', 'MISMATCH',
                     'never promote mismatch to VERIFIED')
        checkpoint(work_id, 0, 'FINAL_MISMATCH',
                   {'expected':item.expected,'actual':item.actual,'retained':True})
        raise HTTPException(409, 'final verification mismatch; result retained as unverified')
    return {'status':'VERIFIED','work_id':work_id}
