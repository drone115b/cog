#####################################################################
#
# Copyright 2015 SpinVFX 

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License. 
# 
#####################################################################

SUBM_STATE_NAME = ( 'subm', 'wait', 'run', 'hold', 'done', 'kill', 'fail' )
SUBM_STATE_NUM = dict((SUBM_STATE_NAME[i],i) for i in range(len(SUBM_STATE_NAME)))

EXEC_STATE_NAME = ( 'run', 'done', 'fail' )
EXEC_STATE_NUM = dict((EXEC_STATE_NAME[i],i) for i in range(len(EXEC_STATE_NAME)))

#####################################################################

VACUUM = 'VACUUM;'
ANALYZE = 'ANALYZE;'

#####################################################################

DATABASE_BEGIN="PRAGMA synchronous=NORMAL;"

#####################################################################

DATABASE_SCHEMA_LIST = [
"PRAGMA journal_mode=WAL;",         # sqlite > 3.7.x
"PRAGMA auto_vacuum=NONE;",         # don't risk this, use VACUUM
"PRAGMA temp_store=2;",             # in-memory temp tables

"""CREATE TABLE Submission (
 uid            TEXT PRIMARY KEY,
 priority       INTEGER,
 title          TEXT,
 user           TEXT,
 email          TEXT,
 document       BLOB,
 nodelist       TEXT,
 state          INTEGER
);""",

"""CREATE TABLE Execution (
 uid            TEXT PRIMARY KEY,
 submuid        TEXT,
 session        TEXT,
 argv           TEXT,
 document       BLOB,
 exception      TEXT,
 state          INTEGER
);""",

"""CREATE TABLE Log (
 born TIMESTAMP NOT NULL,
 execuid        TEXT,
 body           BLOB,
 PRIMARY KEY( born, execuid )
);""",

"""CREATE TABLE Submstate (
   id INTEGER PRIMARY KEY,
   name CHARACTER(4) NOT NULL
);""",

"""CREATE TABLE Execstate (
   id INTEGER PRIMARY KEY,
   name CHARACTER(4) NOT NULL
);""",

"CREATE INDEX ind_Execution_submid ON Execution( submuid );"

]

DATABASE_SCHEMA_LIST.extend( ['INSERT INTO Submstate (name,id) VALUES ("%s",%d);' % x for x in SUBM_STATE_NUM.items() ])
DATABASE_SCHEMA_LIST.extend( ['INSERT INTO Execstate (name,id) VALUES ("%s",%d);' % x for x in EXEC_STATE_NUM.items() ])

#####################################################################


INSERT_SUBMISSION = "INSERT INTO Submission (uid,priority,title,user,email,document,nodelist,state) VALUES(?,?,?,?,?,?,?,%d);" % SUBM_STATE_NUM['subm'] 

SUBMISSION_DONE = "UPDATE Submission SET state=%d WHERE uid=?;" % SUBM_STATE_NUM['done'] # (submid,)
SUBMISSION_RUN = "UPDATE Submission SET state=%d WHERE uid=?;" % SUBM_STATE_NUM['run'] # (submid,)
SUBMISSION_WAIT = "UPDATE Submission SET state=%d WHERE uid=?;" % SUBM_STATE_NUM['wait'] # (submid,)
SUBMISSION_FAIL = "UPDATE Submission SET state=%d WHERE uid=?;" % SUBM_STATE_NUM['fail'] # (submid,)

SELECT_SUBMISSION_RUNDATA = "SELECT document,nodelist FROM Submission WHERE uid=?;" # (submid,)

GET_SUBMISSION_LIST="SELECT uid,priority,title,user,state FROM Submission ORDER BY uid;"
GET_SUBMISSION = "SELECT * FROM Submission WHERE uid=?;" # (uid,)
 
#########
  
INSERT_EXECUTION = "INSERT INTO Execution (uid,submuid,session,argv,state,document,exception) VALUES (?,?,?,?,?,?,?);"
  
EXECUTION_FAIL = "UPDATE Execution SET state=%d, document=?, exception=? WHERE uid=?;" % EXEC_STATE_NUM['fail'] # (exc,doc,uid)
EXECUTION_DONE = "UPDATE Execution SET state=%d, document=? WHERE uid=?;" % EXEC_STATE_NUM['done'] # (document,uid)

EXECUTION_SUBMID = "SELECT submuid FROM Execution WHERE uid=?;" # (execid,)

EXECUTION_RUNDATA = "SELECT document FROM Execution WHERE submuid=? AND NOT( state=%d ) ORDER BY uid;" % EXEC_STATE_NUM['run'] # (submid,)

EXECUTION_ARGV="UPDATE Execution SET argv=? WHERE uid=?;" # (argv,uid)

#########
  
INSERT_LOG = "INSERT INTO Log (born,execuid,body) VALUES (?,?,?);" # (date,execid,body)

GET_EXEC_LOGS = "SELECT born,body FROM Log WHERE execuid=? ORDER BY born;" # (execid,)
GET_SUBM_LOGS = "SELECT Log.born AS born,Log.body as body FROM Log JOIN Execution ON Log.execuid=Execution.uid WHERE Execution.submuid=? ORDER BY Log.born;" # (submid,)

#########
  
# get submissions to run (in priority order):
GET_SCHEDULABLE_SUBM = """
  SELECT * FROM Submission WHERE 
    NOT EXISTS ( SELECT 1 FROM Execution WHERE Execution.submuid = Submission.uid AND Execution.state = %d )
    AND ( state=%d OR state=%d )
    ORDER BY priority, uid LIMIT 1;""" % ( EXEC_STATE_NUM['run'], SUBM_STATE_NUM['wait'], SUBM_STATE_NUM['subm'] )

#########
  
