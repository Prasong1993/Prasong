import json
import uuid
try:
    from .database import get_connection, many, one, record_event
    from .model import STEP_DEFINITIONS, StepStatus
except ImportError:
    from database import get_connection, many, one, record_event
    from model import STEP_DEFINITIONS, StepStatus


def create_work(work_id, title):
    with get_connection() as conn:
        conn.execute('INSERT INTO work_units(id,title) VALUES(?,?)', (work_id, title))
        conn.execute('INSERT INTO audit_log(work_id,action,details) VALUES(?,?,?)',
                     (work_id, 'WORK_CREATED', title))
    record_event('WORK_CREATED', work_id=work_id, status='CREATED',
                 payload={'title': title})


def _record_step(work_id, step, attempt, status, expected, actual, note):
    with get_connection() as conn:
        conn.execute(
            'INSERT INTO step_runs(work_id,step,attempt,status,expected,actual,note) VALUES(?,?,?,?,?,?,?)',
            (work_id, step, attempt, status, expected, actual, note))
        conn.execute(
            'UPDATE work_units SET current_step=?,status=?,updated_at=CURRENT_TIMESTAMP WHERE id=?',
            (step, status, work_id))
        conn.execute(
            'INSERT INTO audit_log(work_id,action,details) VALUES(?,?,?)',
            (work_id, 'STEP_' + status, f'step={step};attempt={attempt}'))
    record_event('STEP_' + status, work_id=work_id, status=status,
                 payload={'step': step, 'attempt': attempt, 'expected': expected,
                          'actual': actual, 'note': note})


def record_error(work_id, step, attempt, error_type, message, expected=None,
                 actual=None, root_cause='UNKNOWN/UNPROVEN', impact='UNKNOWN',
                 correction='PENDING', verification='PENDING',
                 prevention_rule='PENDING'):
    with get_connection() as conn:
        cur = conn.execute(
            'INSERT INTO errors(work_id,step,attempt,error_type,message,expected,actual,root_cause,impact,correction,verification,prevention_rule) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',
            (work_id, step, attempt, error_type, message, expected, actual,
             root_cause, impact, correction, verification, prevention_rule))
        error_id = cur.lastrowid
        conn.execute('INSERT INTO audit_log(work_id,action,details) VALUES(?,?,?)',
                     (work_id, 'ERROR_RECORDED',
                      f'error_id={error_id};step={step};attempt={attempt}'))
    record_event('TOOL_FAILED' if step == 0 else 'ERROR_RECORDED',
                 work_id=work_id, status='FAILED',
                 payload={'error_id': error_id, 'step': step, 'attempt': attempt,
                          'error_type': error_type, 'message': message})
    return error_id


def checkpoint(work_id, step, state, snapshot):
    encoded = json.dumps(snapshot, ensure_ascii=False, sort_keys=True)
    with get_connection() as conn:
        cur = conn.execute(
            'INSERT INTO checkpoints(work_id,step,state,snapshot) VALUES(?,?,?,?)',
            (work_id, step, state, encoded))
        checkpoint_id = cur.lastrowid
        conn.execute('INSERT INTO audit_log(work_id,action,details) VALUES(?,?,?)',
                     (work_id, 'CHECKPOINT', f'step={step};state={state}'))
    record_event('CHECKPOINT_SAVED', work_id=work_id, status=state,
                 payload={'checkpoint_id': checkpoint_id, 'step': step, 'snapshot': snapshot})
    return checkpoint_id


def verify_pair(expected, actual):
    return str(expected).strip() == str(actual).strip()


def run_step(work_id, step, expected, actual, note='', fail_attempts=0, max_attempts=10):
    if step not in STEP_DEFINITIONS:
        raise ValueError('step must be 1..5')
    if not one('SELECT * FROM work_units WHERE id=?', (work_id,)):
        raise ValueError('work not found')
    if not one('SELECT 1 FROM work_units WHERE id=?', (work_id,)):
        raise ValueError('work not found')
    if step > 1:
        prev = one('SELECT status FROM step_runs WHERE work_id=? AND step=? ORDER BY id DESC LIMIT 1',
                   (work_id, step - 1))
        if not prev or prev['status'] != StepStatus.PASSED.value:
            raise ValueError(f'step {step} requires step {step - 1} to PASS')
    if max_attempts < 1 or max_attempts > 10 or fail_attempts < 0 or fail_attempts > 9:
        raise ValueError('attempt limits are out of range')
    for attempt in range(1, max_attempts + 1):
        _record_step(work_id, step, attempt, StepStatus.CHECKING.value, expected, actual, note)
        if attempt <= fail_attempts:
            _record_step(work_id, step, attempt, StepStatus.FAILED.value, expected, actual,
                         'condition not met')
            record_error(work_id, step, attempt, 'CONDITION_NOT_MET',
                         'verification condition failed before progression', expected, actual,
                         'UNKNOWN/UNPROVEN', 'step cannot progress',
                         'retry with corrected condition', 'NOT VERIFIED',
                         'recorded failure must be corrected before progression')
            checkpoint(work_id, step, StepStatus.FAILED.value,
                       {'attempt': attempt, 'expected': expected, 'actual': actual,
                        'errors_retained': True})
            continue
        _record_step(work_id, step, attempt, StepStatus.WORKING.value, expected, actual, note)
        _record_step(work_id, step, attempt, StepStatus.VERIFYING.value, expected, actual, note)
        if not verify_pair(expected, actual):
            _record_step(work_id, step, attempt, StepStatus.FAILED.value, expected, actual,
                         'expected != actual')
            record_error(work_id, step, attempt, 'MISMATCH',
                         'expected and actual do not match', expected, actual,
                         'UNKNOWN/UNPROVEN', 'step result is not verified',
                         'correct output and retry', 'NOT VERIFIED',
                         'never promote mismatch to PASS')
            checkpoint(work_id, step, StepStatus.FAILED.value,
                       {'attempt': attempt, 'expected': expected, 'actual': actual,
                        'errors_retained': True})
            continue
        _record_step(work_id, step, attempt, StepStatus.PASSED.value, expected, actual, note)
        checkpoint(work_id, step, StepStatus.PASSED.value,
                   {'attempt': attempt, 'expected': expected, 'actual': actual,
                    'errors_retained': True})
        return {'step': step, 'status': 'PASSED', 'attempt': attempt, 'errors_retained': True}
    raise RuntimeError(f'step {step} did not pass within {max_attempts} attempts')


def get_work(work_id):
    work = one('SELECT * FROM work_units WHERE id=?', (work_id,))
    if not work:
        return None
    return {
        'work': work,
        'steps': many('SELECT * FROM step_runs WHERE work_id=? ORDER BY id', (work_id,)),
        'errors': many('SELECT * FROM errors WHERE work_id=? ORDER BY id', (work_id,)),
        'checkpoints': many('SELECT * FROM checkpoints WHERE work_id=? ORDER BY id', (work_id,)),
        'audit': many('SELECT * FROM audit_log WHERE work_id=? ORDER BY id', (work_id,)),
        'verifications': many('SELECT * FROM verifications WHERE work_id=? ORDER BY id', (work_id,)),
        'events': many('SELECT * FROM work_events WHERE work_id=? ORDER BY recorded_at,event_id', (work_id,)),
        'tool_calls': many('SELECT * FROM tool_calls WHERE work_id=? ORDER BY created_at', (work_id,)),
    }
