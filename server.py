#!/usr/bin/env python3
"""A dependency-free stdio MCP server for small agent project plans."""
import json, os, sqlite3, sys
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(os.environ.get("AGENT_GANTT_DB", Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state")) / "agent-gantt" / "projects.sqlite3"))
def db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True); c=sqlite3.connect(DB_PATH); c.row_factory=sqlite3.Row
    c.executescript("""CREATE TABLE IF NOT EXISTS projects (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, description TEXT, created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, project_id INTEGER NOT NULL, title TEXT NOT NULL, description TEXT, status TEXT NOT NULL DEFAULT 'todo', start_date TEXT, due_date TEXT, assignee TEXT, progress INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL, FOREIGN KEY(project_id) REFERENCES projects(id));
    CREATE TABLE IF NOT EXISTS dependencies (task_id INTEGER NOT NULL, depends_on_id INTEGER NOT NULL, PRIMARY KEY(task_id,depends_on_id));""")
    return c
def result(x): return {"content":[{"type":"text","text":json.dumps(x,ensure_ascii=False,indent=2)}],"structuredContent":x}
def tools():
    return [
      {"name":"create_project","description":"Create a project plan.","inputSchema":{"type":"object","required":["name"],"properties":{"name":{"type":"string"},"description":{"type":"string"}}}},
      {"name":"create_task","description":"Add a task to a project. Dates use YYYY-MM-DD.","inputSchema":{"type":"object","required":["project_id","title"],"properties":{"project_id":{"type":"integer"},"title":{"type":"string"},"description":{"type":"string"},"status":{"type":"string","enum":["todo","in_progress","blocked","done"]},"start_date":{"type":"string"},"due_date":{"type":"string"},"assignee":{"type":"string"},"progress":{"type":"integer","minimum":0,"maximum":100}}}},
      {"name":"update_task","description":"Update one or more task fields.","inputSchema":{"type":"object","required":["task_id"],"properties":{"task_id":{"type":"integer"},"title":{"type":"string"},"description":{"type":"string"},"status":{"type":"string","enum":["todo","in_progress","blocked","done"]},"start_date":{"type":"string"},"due_date":{"type":"string"},"assignee":{"type":"string"},"progress":{"type":"integer","minimum":0,"maximum":100}}}},
      {"name":"add_dependency","description":"State that task_id cannot start until depends_on_id is complete.","inputSchema":{"type":"object","required":["task_id","depends_on_id"],"properties":{"task_id":{"type":"integer"},"depends_on_id":{"type":"integer"}}}},
      {"name":"list_projects","description":"List available projects.","inputSchema":{"type":"object","properties":{}}},
      {"name":"project_view","description":"Return a project, its tasks, and dependency edges for rendering a Gantt chart.","inputSchema":{"type":"object","required":["project_id"],"properties":{"project_id":{"type":"integer"}}}},
    ]
def now(): return datetime.now(timezone.utc).isoformat()
def call(n,a):
    c=db()
    if n=="create_project":
      name=a.get("name","").strip()
      if not name: raise ValueError("name is required")
      cur=c.execute("INSERT INTO projects(name,description,created_at) VALUES(?,?,?)",(name,a.get("description",""),now())); c.commit(); return {"project_id":cur.lastrowid,"name":name}
    if n=="create_task":
      fields={"title":a.get("title","").strip(),"description":a.get("description",""),"status":a.get("status","todo"),"start_date":a.get("start_date"),"due_date":a.get("due_date"),"assignee":a.get("assignee"),"progress":int(a.get("progress",0))}
      if not fields["title"]: raise ValueError("title is required")
      if fields["status"] not in ("todo","in_progress","blocked","done") or not 0<=fields["progress"]<=100: raise ValueError("invalid status or progress")
      cur=c.execute("INSERT INTO tasks(project_id,title,description,status,start_date,due_date,assignee,progress,created_at) VALUES(?,?,?,?,?,?,?,?,?)",(int(a["project_id"]),*fields.values(),now())); c.commit(); return {"task_id":cur.lastrowid,"project_id":int(a["project_id"])}
    if n=="update_task":
      allowed=("title","description","status","start_date","due_date","assignee","progress"); sets=[]; vals=[]
      for key in allowed:
        if key in a:
          if key=="status" and a[key] not in ("todo","in_progress","blocked","done"): raise ValueError("invalid status")
          if key=="progress" and not 0<=int(a[key])<=100: raise ValueError("progress must be 0..100")
          sets.append(key+"=?"); vals.append(a[key])
      if not sets: raise ValueError("provide at least one field to update")
      vals.append(int(a["task_id"])); cur=c.execute("UPDATE tasks SET "+",".join(sets)+" WHERE id=?",vals); c.commit()
      if not cur.rowcount: raise ValueError("task not found")
      return {"task_id":int(a["task_id"]),"updated":sets}
    if n=="add_dependency":
      task,dep=int(a["task_id"]),int(a["depends_on_id"])
      if task==dep: raise ValueError("a task cannot depend on itself")
      c.execute("INSERT OR IGNORE INTO dependencies(task_id,depends_on_id) VALUES(?,?)",(task,dep)); c.commit(); return {"task_id":task,"depends_on_id":dep}
    if n=="list_projects": return {"projects":[dict(r) for r in c.execute("SELECT * FROM projects ORDER BY id").fetchall()]}
    if n=="project_view":
      project=c.execute("SELECT * FROM projects WHERE id=?",(int(a["project_id"]),)).fetchone()
      if not project: raise ValueError("project not found")
      tasks=[dict(r) for r in c.execute("SELECT * FROM tasks WHERE project_id=? ORDER BY COALESCE(start_date,'9999-12-31'),id",(project["id"],)).fetchall()]
      ids=[x["id"] for x in tasks]; edges=[]
      if ids: edges=[dict(r) for r in c.execute("SELECT task_id,depends_on_id FROM dependencies WHERE task_id IN ("+",".join("?"*len(ids))+")",ids).fetchall()]
      return {"project":dict(project),"tasks":tasks,"dependencies":edges}
    raise ValueError("unknown tool: "+str(n))
def respond(m):
    method,params,ident=m.get("method"),m.get("params",{}),m.get("id")
    if method=="initialize": return {"jsonrpc":"2.0","id":ident,"result":{"protocolVersion":"2025-06-18","capabilities":{"tools":{}},"serverInfo":{"name":"agent-gantt","version":"1.0.0"}}}
    if method=="tools/list": return {"jsonrpc":"2.0","id":ident,"result":{"tools":tools()}}
    if method=="tools/call":
      try: out=result(call(params.get("name"),params.get("arguments",{})))
      except Exception as e: out={"content":[{"type":"text","text":str(e)}],"isError":True}
      return {"jsonrpc":"2.0","id":ident,"result":out}
    if method=="notifications/initialized": return None
    return {"jsonrpc":"2.0","id":ident,"error":{"code":-32601,"message":"Method not found"}}
for line in sys.stdin:
  try:
    r=respond(json.loads(line))
    if r is not None: print(json.dumps(r),flush=True)
  except Exception as e: print(json.dumps({"jsonrpc":"2.0","id":None,"error":{"code":-32700,"message":str(e)}}),flush=True)
