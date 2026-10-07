import sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'runtime'))
import database
database.DB_PATH=Path(tempfile.mkdtemp())/'iris.db'; database.init_db()
from controller import create_work,run_step,get_work

def test_five_steps_pass_and_errors_retained():
 create_work('W1','five-step loop')
 for i in range(1,6):
  r=run_step('W1',i,f'ok-{i}',f'ok-{i}',fail_attempts=1); assert r['status']=='PASSED' and r['attempt']==2
 rec=get_work('W1'); assert len(rec['errors'])==5
 for i in range(1,6): assert [s for s in rec['steps'] if s['step']==i][-1]['status']=='PASSED'

def test_cannot_skip_step():
 create_work('W2','dependency gate')
 try: run_step('W2',2,'x','x'); assert False
 except ValueError as exc: assert 'requires step 1' in str(exc)

def test_mismatch_retries_then_passes():
 create_work('W3','mismatch recovery'); assert run_step('W3',1,'expected','expected',fail_attempts=1)['attempt']==2
 rec=get_work('W3'); assert len(rec['errors'])==1 and rec['checkpoints'][-1]['state']=='PASSED'
