import { useEffect, useState } from "react";
import { projectStorage } from "../api";
import type { Project } from "../api";

export default function Settings() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [editId, setEditId] = useState<number | null>(null);
  const [form, setForm] = useState({ name: "", agreement_number: "", work_order_number: "" });
  const [adding, setAdding] = useState(false);

  useEffect(() => { setProjects(projectStorage.list()); }, []);

  function startEdit(p: Project) {
    setEditId(p.id);
    setForm({ name: p.name, agreement_number: p.agreement_number, work_order_number: p.work_order_number });
  }

  function startAdd() {
    setAdding(true);
    setEditId(null);
    setForm({ name: "", agreement_number: "", work_order_number: "" });
  }

  function save() {
    if (editId !== null) {
      projectStorage.update(editId, form);
    } else {
      projectStorage.create(form);
    }
    setEditId(null);
    setAdding(false);
    setProjects(projectStorage.list());
  }

  function remove(id: number) {
    if (!confirm("Delete this project?")) return;
    projectStorage.delete(id);
    setProjects(projectStorage.list());
  }

  function cancel() {
    setEditId(null);
    setAdding(false);
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">Projects</h2>
          <p className="text-gray-500 text-sm mt-1">Manage PennDOT agreement and work order numbers for each project.</p>
        </div>
        <button
          onClick={startAdd}
          className="bg-brand-700 text-white px-4 py-2 rounded-lg hover:bg-brand-800 text-sm font-medium"
        >
          + Add Project
        </button>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              <th className="text-left px-4 py-3 font-semibold text-gray-700">Project Name</th>
              <th className="text-left px-4 py-3 font-semibold text-gray-700">Agreement #</th>
              <th className="text-left px-4 py-3 font-semibold text-gray-700">Work Order #</th>
              <th className="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody>
            {projects.map((p) => (
              <tr key={p.id} className="border-b border-gray-100 last:border-0">
                {editId === p.id ? (
                  <>
                    <td className="px-3 py-2">
                      <input
                        className="border border-gray-300 rounded px-2 py-1 w-full text-sm"
                        value={form.name}
                        onChange={(e) => setForm({ ...form, name: e.target.value })}
                      />
                    </td>
                    <td className="px-3 py-2">
                      <input
                        className="border border-gray-300 rounded px-2 py-1 w-full text-sm"
                        value={form.agreement_number}
                        onChange={(e) => setForm({ ...form, agreement_number: e.target.value })}
                      />
                    </td>
                    <td className="px-3 py-2">
                      <input
                        className="border border-gray-300 rounded px-2 py-1 w-full text-sm"
                        value={form.work_order_number}
                        onChange={(e) => setForm({ ...form, work_order_number: e.target.value })}
                      />
                    </td>
                    <td className="px-3 py-2 text-right space-x-2">
                      <button
                        onClick={save}
                        className="text-white bg-brand-700 hover:bg-brand-800 px-3 py-1 rounded text-xs font-medium"
                      >
                        Save
                      </button>
                      <button onClick={cancel} className="text-gray-600 hover:text-gray-800 px-3 py-1 rounded text-xs">
                        Cancel
                      </button>
                    </td>
                  </>
                ) : (
                  <>
                    <td className="px-4 py-3 font-medium text-gray-800">{p.name}</td>
                    <td className="px-4 py-3 text-gray-600">{p.agreement_number}</td>
                    <td className="px-4 py-3 text-gray-600">{p.work_order_number}</td>
                    <td className="px-4 py-3 text-right space-x-3">
                      <button
                        onClick={() => startEdit(p)}
                        className="text-brand-700 hover:text-brand-900 text-xs font-medium"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => remove(p.id)}
                        className="text-red-500 hover:text-red-700 text-xs font-medium"
                      >
                        Delete
                      </button>
                    </td>
                  </>
                )}
              </tr>
            ))}

            {projects.length === 0 && !adding && (
              <tr>
                <td colSpan={4} className="px-4 py-8 text-center text-gray-400 text-sm">
                  No projects yet. Add one to get started.
                </td>
              </tr>
            )}

            {adding && (
              <tr className="bg-brand-50 border-b border-gray-100">
                <td className="px-3 py-2">
                  <input
                    autoFocus
                    placeholder="Project name"
                    className="border border-gray-300 rounded px-2 py-1 w-full text-sm"
                    value={form.name}
                    onChange={(e) => setForm({ ...form, name: e.target.value })}
                  />
                </td>
                <td className="px-3 py-2">
                  <input
                    placeholder="e.g. E06216"
                    className="border border-gray-300 rounded px-2 py-1 w-full text-sm"
                    value={form.agreement_number}
                    onChange={(e) => setForm({ ...form, agreement_number: e.target.value })}
                  />
                </td>
                <td className="px-3 py-2">
                  <input
                    placeholder="e.g. Work Order 1"
                    className="border border-gray-300 rounded px-2 py-1 w-full text-sm"
                    value={form.work_order_number}
                    onChange={(e) => setForm({ ...form, work_order_number: e.target.value })}
                  />
                </td>
                <td className="px-3 py-2 text-right space-x-2">
                  <button
                    onClick={save}
                    disabled={!form.name}
                    className="text-white bg-brand-700 hover:bg-brand-800 px-3 py-1 rounded text-xs font-medium disabled:opacity-50"
                  >
                    Add
                  </button>
                  <button onClick={cancel} className="text-gray-600 hover:text-gray-800 px-3 py-1 rounded text-xs">
                    Cancel
                  </button>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
