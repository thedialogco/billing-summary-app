import { useEffect, useState } from "react";
import { projectStorage, personnelStorage, taskStorage } from "../api";
import type { Project, Personnel, TaskEntry } from "../api";

// ---------------------------------------------------------------------------
// Shared inline-table helpers
// ---------------------------------------------------------------------------

function SectionHeader({ title, onAdd }: { title: string; onAdd: () => void }) {
  return (
    <div className="flex items-center justify-between mb-4">
      <h3 className="text-lg font-semibold text-gray-800">{title}</h3>
      <button
        onClick={onAdd}
        className="bg-brand-700 text-white px-4 py-2 rounded-lg hover:bg-brand-800 text-sm font-medium"
      >
        + Add
      </button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Projects
// ---------------------------------------------------------------------------

function ProjectsSection() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [editId, setEditId] = useState<number | null>(null);
  const [form, setForm] = useState({ name: "", agreement_number: "", work_order_number: "" });
  const [adding, setAdding] = useState(false);

  useEffect(() => { setProjects(projectStorage.list()); }, []);

  function startEdit(p: Project) {
    setEditId(p.id); setAdding(false);
    setForm({ name: p.name, agreement_number: p.agreement_number, work_order_number: p.work_order_number });
  }
  function startAdd() { setAdding(true); setEditId(null); setForm({ name: "", agreement_number: "", work_order_number: "" }); }
  function cancel() { setEditId(null); setAdding(false); }

  function save() {
    if (editId !== null) projectStorage.update(editId, form);
    else projectStorage.create(form);
    setEditId(null); setAdding(false);
    setProjects(projectStorage.list());
  }

  function remove(id: number) {
    if (!confirm("Delete this project?")) return;
    projectStorage.delete(id);
    setProjects(projectStorage.list());
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 mb-6">
      <SectionHeader title="Projects" onAdd={startAdd} />
      <div className="overflow-hidden rounded-lg border border-gray-200">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              <th className="text-left px-4 py-3 font-semibold text-gray-700">Project Name</th>
              <th className="text-left px-4 py-3 font-semibold text-gray-700">Agreement #</th>
              <th className="text-left px-4 py-3 font-semibold text-gray-700">Work Order #</th>
              <th className="px-4 py-3" />
            </tr>
          </thead>
          <tbody>
            {projects.map((p) => (
              <tr key={p.id} className="border-b border-gray-100 last:border-0">
                {editId === p.id ? (
                  <>
                    <td className="px-3 py-2"><input className="border border-gray-300 rounded px-2 py-1 w-full text-sm" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></td>
                    <td className="px-3 py-2"><input className="border border-gray-300 rounded px-2 py-1 w-full text-sm" value={form.agreement_number} onChange={(e) => setForm({ ...form, agreement_number: e.target.value })} /></td>
                    <td className="px-3 py-2"><input className="border border-gray-300 rounded px-2 py-1 w-full text-sm" value={form.work_order_number} onChange={(e) => setForm({ ...form, work_order_number: e.target.value })} /></td>
                    <td className="px-3 py-2 text-right space-x-2">
                      <button onClick={save} className="text-white bg-brand-700 hover:bg-brand-800 px-3 py-1 rounded text-xs font-medium">Save</button>
                      <button onClick={cancel} className="text-gray-600 hover:text-gray-800 px-3 py-1 rounded text-xs">Cancel</button>
                    </td>
                  </>
                ) : (
                  <>
                    <td className="px-4 py-3 font-medium text-gray-800">{p.name}</td>
                    <td className="px-4 py-3 text-gray-600">{p.agreement_number}</td>
                    <td className="px-4 py-3 text-gray-600">{p.work_order_number}</td>
                    <td className="px-4 py-3 text-right space-x-3">
                      <button onClick={() => startEdit(p)} className="text-brand-700 hover:text-brand-900 text-xs font-medium">Edit</button>
                      <button onClick={() => remove(p.id)} className="text-red-500 hover:text-red-700 text-xs font-medium">Delete</button>
                    </td>
                  </>
                )}
              </tr>
            ))}
            {projects.length === 0 && !adding && (
              <tr><td colSpan={4} className="px-4 py-8 text-center text-gray-400 text-sm">No projects yet. Add one to get started.</td></tr>
            )}
            {adding && (
              <tr className="bg-brand-50 border-b border-gray-100">
                <td className="px-3 py-2"><input autoFocus placeholder="Project name" className="border border-gray-300 rounded px-2 py-1 w-full text-sm" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></td>
                <td className="px-3 py-2"><input placeholder="e.g. E06216" className="border border-gray-300 rounded px-2 py-1 w-full text-sm" value={form.agreement_number} onChange={(e) => setForm({ ...form, agreement_number: e.target.value })} /></td>
                <td className="px-3 py-2"><input placeholder="e.g. Work Order 1" className="border border-gray-300 rounded px-2 py-1 w-full text-sm" value={form.work_order_number} onChange={(e) => setForm({ ...form, work_order_number: e.target.value })} /></td>
                <td className="px-3 py-2 text-right space-x-2">
                  <button onClick={save} disabled={!form.name} className="text-white bg-brand-700 hover:bg-brand-800 px-3 py-1 rounded text-xs font-medium disabled:opacity-50">Add</button>
                  <button onClick={cancel} className="text-gray-600 hover:text-gray-800 px-3 py-1 rounded text-xs">Cancel</button>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Personnel
// ---------------------------------------------------------------------------

function PersonnelSection() {
  const [people, setPeople] = useState<Personnel[]>([]);
  const [editId, setEditId] = useState<number | null>(null);
  const [form, setForm] = useState<{ name: string; phase: "Highway" | "Bridge" }>({ name: "", phase: "Highway" });
  const [adding, setAdding] = useState(false);

  useEffect(() => { setPeople(personnelStorage.list()); }, []);

  function startEdit(p: Personnel) { setEditId(p.id); setAdding(false); setForm({ name: p.name, phase: p.phase }); }
  function startAdd() { setAdding(true); setEditId(null); setForm({ name: "", phase: "Highway" }); }
  function cancel() { setEditId(null); setAdding(false); }

  function save() {
    if (editId !== null) personnelStorage.update(editId, form);
    else personnelStorage.create(form);
    setEditId(null); setAdding(false);
    setPeople(personnelStorage.list());
  }

  function remove(id: number) {
    if (!confirm("Delete this person?")) return;
    personnelStorage.delete(id);
    setPeople(personnelStorage.list());
  }

  function PhaseToggle({ value, onChange }: { value: "Highway" | "Bridge"; onChange: (v: "Highway" | "Bridge") => void }) {
    return (
      <div className="flex rounded-lg overflow-hidden border border-gray-300 w-fit">
        {(["Highway", "Bridge"] as const).map((opt) => (
          <button
            key={opt}
            type="button"
            onClick={() => onChange(opt)}
            className={`px-3 py-1 text-xs font-medium transition-colors ${value === opt ? "bg-brand-700 text-white" : "bg-white text-gray-600 hover:bg-gray-50"}`}
          >
            {opt}
          </button>
        ))}
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 mb-6">
      <SectionHeader title="Personnel" onAdd={startAdd} />
      <p className="text-xs text-gray-500 mb-3">Enter names exactly as they appear in your Excel file (e.g. "Arentz, Travis"). Assign each person to a phase.</p>
      <div className="overflow-hidden rounded-lg border border-gray-200">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              <th className="text-left px-4 py-3 font-semibold text-gray-700">Name (as in Excel)</th>
              <th className="text-left px-4 py-3 font-semibold text-gray-700">Phase</th>
              <th className="px-4 py-3" />
            </tr>
          </thead>
          <tbody>
            {people.map((p) => (
              <tr key={p.id} className="border-b border-gray-100 last:border-0">
                {editId === p.id ? (
                  <>
                    <td className="px-3 py-2"><input className="border border-gray-300 rounded px-2 py-1 w-full text-sm" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></td>
                    <td className="px-3 py-2"><PhaseToggle value={form.phase} onChange={(v) => setForm({ ...form, phase: v })} /></td>
                    <td className="px-3 py-2 text-right space-x-2">
                      <button onClick={save} className="text-white bg-brand-700 hover:bg-brand-800 px-3 py-1 rounded text-xs font-medium">Save</button>
                      <button onClick={cancel} className="text-gray-600 px-3 py-1 rounded text-xs">Cancel</button>
                    </td>
                  </>
                ) : (
                  <>
                    <td className="px-4 py-3 font-medium text-gray-800">{p.name}</td>
                    <td className="px-4 py-3">
                      <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${p.phase === "Bridge" ? "bg-blue-100 text-blue-700" : "bg-green-100 text-green-700"}`}>{p.phase}</span>
                    </td>
                    <td className="px-4 py-3 text-right space-x-3">
                      <button onClick={() => startEdit(p)} className="text-brand-700 hover:text-brand-900 text-xs font-medium">Edit</button>
                      <button onClick={() => remove(p.id)} className="text-red-500 hover:text-red-700 text-xs font-medium">Delete</button>
                    </td>
                  </>
                )}
              </tr>
            ))}
            {people.length === 0 && !adding && (
              <tr><td colSpan={3} className="px-4 py-8 text-center text-gray-400 text-sm">No personnel yet. Add people to assign phases.</td></tr>
            )}
            {adding && (
              <tr className="bg-brand-50 border-b border-gray-100">
                <td className="px-3 py-2"><input autoFocus placeholder="e.g. Arentz, Travis" className="border border-gray-300 rounded px-2 py-1 w-full text-sm" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></td>
                <td className="px-3 py-2"><PhaseToggle value={form.phase} onChange={(v) => setForm({ ...form, phase: v })} /></td>
                <td className="px-3 py-2 text-right space-x-2">
                  <button onClick={save} disabled={!form.name} className="text-white bg-brand-700 hover:bg-brand-800 px-3 py-1 rounded text-xs font-medium disabled:opacity-50">Add</button>
                  <button onClick={cancel} className="text-gray-600 px-3 py-1 rounded text-xs">Cancel</button>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tasks
// ---------------------------------------------------------------------------

function TasksSection() {
  const [tasks, setTasks] = useState<TaskEntry[]>([]);
  const [editId, setEditId] = useState<number | null>(null);
  const [form, setForm] = useState({ code: "", description: "" });
  const [adding, setAdding] = useState(false);

  useEffect(() => { setTasks(taskStorage.list()); }, []);

  function startEdit(t: TaskEntry) { setEditId(t.id); setAdding(false); setForm({ code: t.code, description: t.description }); }
  function startAdd() { setAdding(true); setEditId(null); setForm({ code: "", description: "" }); }
  function cancel() { setEditId(null); setAdding(false); }

  function save() {
    if (editId !== null) taskStorage.update(editId, form);
    else taskStorage.create(form);
    setEditId(null); setAdding(false);
    setTasks(taskStorage.list());
  }

  function remove(id: number) {
    if (!confirm("Delete this task?")) return;
    taskStorage.delete(id);
    setTasks(taskStorage.list());
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 mb-6">
      <SectionHeader title="Tasks" onAdd={startAdd} />
      <p className="text-xs text-gray-500 mb-3">Enter task codes exactly as they appear in your Excel file (e.g. "0046", "T102"). Add a description to display in reports.</p>
      <div className="overflow-hidden rounded-lg border border-gray-200">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              <th className="text-left px-4 py-3 font-semibold text-gray-700 w-32">Task Code</th>
              <th className="text-left px-4 py-3 font-semibold text-gray-700">Description</th>
              <th className="px-4 py-3" />
            </tr>
          </thead>
          <tbody>
            {tasks.map((t) => (
              <tr key={t.id} className="border-b border-gray-100 last:border-0">
                {editId === t.id ? (
                  <>
                    <td className="px-3 py-2"><input className="border border-gray-300 rounded px-2 py-1 w-full text-sm font-mono" value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} /></td>
                    <td className="px-3 py-2"><input className="border border-gray-300 rounded px-2 py-1 w-full text-sm" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} /></td>
                    <td className="px-3 py-2 text-right space-x-2">
                      <button onClick={save} className="text-white bg-brand-700 hover:bg-brand-800 px-3 py-1 rounded text-xs font-medium">Save</button>
                      <button onClick={cancel} className="text-gray-600 px-3 py-1 rounded text-xs">Cancel</button>
                    </td>
                  </>
                ) : (
                  <>
                    <td className="px-4 py-3 font-mono font-medium text-gray-800">{t.code}</td>
                    <td className="px-4 py-3 text-gray-600">{t.description}</td>
                    <td className="px-4 py-3 text-right space-x-3">
                      <button onClick={() => startEdit(t)} className="text-brand-700 hover:text-brand-900 text-xs font-medium">Edit</button>
                      <button onClick={() => remove(t.id)} className="text-red-500 hover:text-red-700 text-xs font-medium">Delete</button>
                    </td>
                  </>
                )}
              </tr>
            ))}
            {tasks.length === 0 && !adding && (
              <tr><td colSpan={3} className="px-4 py-8 text-center text-gray-400 text-sm">No tasks yet. Add task codes to show descriptions in reports.</td></tr>
            )}
            {adding && (
              <tr className="bg-brand-50 border-b border-gray-100">
                <td className="px-3 py-2"><input autoFocus placeholder="e.g. 0046" className="border border-gray-300 rounded px-2 py-1 w-full text-sm font-mono" value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} /></td>
                <td className="px-3 py-2"><input placeholder="e.g. Road Inspection" className="border border-gray-300 rounded px-2 py-1 w-full text-sm" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} /></td>
                <td className="px-3 py-2 text-right space-x-2">
                  <button onClick={save} disabled={!form.code} className="text-white bg-brand-700 hover:bg-brand-800 px-3 py-1 rounded text-xs font-medium disabled:opacity-50">Add</button>
                  <button onClick={cancel} className="text-gray-600 px-3 py-1 rounded text-xs">Cancel</button>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function Settings() {
  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-800">Settings</h2>
        <p className="text-gray-500 text-sm mt-1">Manage projects, personnel phase assignments, and task descriptions.</p>
      </div>
      <ProjectsSection />
      <PersonnelSection />
      <TasksSection />
    </div>
  );
}
