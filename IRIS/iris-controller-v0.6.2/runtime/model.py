from enum import Enum
class StepStatus(str, Enum):
    CREATED='CREATED'; CHECKING='CHECKING'; WORKING='WORKING'; VERIFYING='VERIFYING'; PASSED='PASSED'; FAILED='FAILED'; BLOCKED='BLOCKED'
STEP_DEFINITIONS={1:{'name':'แนวคิด','input':'evidence/source','output':'goal_and_conditions'},2:{'name':'ออกแบบ','input':'verified_step_1','output':'actionable_design'},3:{'name':'ทำงานจริง','input':'verified_step_2','output':'actual_result'},4:{'name':'ส่งผล','input':'verified_step_3','output':'verified_delivery'},5:{'name':'ตรวจสอบบนพื้นที่ ChatGPT','input':'delivered_step_4','output':'chatgpt_workspace_verified'}}
WORKING_STRUCTURE=['Project Core','System Architecture','Core Structure','Controller','Workflow','Execution','Execution State','Agent','Tool','Network','Client','Policy','Checkpoint','Recovery','Verification','Audit / Trace','Database','API','Folder Structure','ID Structure','IRIS Master Flow','Status old → new']
