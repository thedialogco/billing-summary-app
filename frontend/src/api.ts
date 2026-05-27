const BASE = import.meta.env.VITE_API_URL ?? "";

export interface Project {
  id: number;
  name: string;
  agreement_number: string;
  work_order_number: string;
  created_at: string;
}

export interface ValidationItem {
  passed: boolean;
  message: string;
}

export interface ValidationResult {
  passed: boolean;
  items: ValidationItem[];
}

export interface GenerateResponse {
  pdf_b64: string;
  master_xlsx_b64: string;
  validation: ValidationResult;
}

// ---------------------------------------------------------------------------
// Generic localStorage store factory
// ---------------------------------------------------------------------------

function makeStore<T extends { id: number }>(key: string) {
  const load = (): T[] => {
    try { return JSON.parse(localStorage.getItem(key) ?? "[]"); } catch { return []; }
  };
  const save = (items: T[]) => localStorage.setItem(key, JSON.stringify(items));
  return {
    list: (): T[] => load(),
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    create: (data: Record<string, any>): T => {
      const next = { created_at: new Date().toISOString(), ...data, id: Date.now() } as unknown as T;
      save([...load(), next]);
      return next;
    },
    update: (id: number, data: Partial<Omit<T, "id">>): T => {
      const items = load().map((i) => i.id === id ? { ...i, ...data } : i);
      save(items);
      return items.find((i) => i.id === id)!;
    },
    delete: (id: number): void => save(load().filter((i) => i.id !== id)),
  };
}

// ---------------------------------------------------------------------------
// Project storage — saved in the browser (localStorage)
// ---------------------------------------------------------------------------

export const projectStorage = makeStore<Project>("bsg_projects");

// ---------------------------------------------------------------------------
// Personnel storage — name (as in Excel) + phase assignment
// ---------------------------------------------------------------------------

export interface Personnel {
  id: number;
  name: string;
  phase: "Highway" | "Bridge";
}

export const personnelStorage = makeStore<Personnel>("bsg_personnel");

// ---------------------------------------------------------------------------
// Task storage — code + description lookup
// ---------------------------------------------------------------------------

export interface TaskEntry {
  id: number;
  code: string;
  description: string;
}

export const taskStorage = makeStore<TaskEntry>("bsg_tasks");

// ---------------------------------------------------------------------------
// Generate API
// ---------------------------------------------------------------------------

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, init);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? `HTTP ${res.status}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  generate: (form: FormData) =>
    request<GenerateResponse>("/api/generate", { method: "POST", body: form }),
};

export function downloadBase64(b64: string, filename: string, mime: string) {
  const bytes = atob(b64);
  const arr = new Uint8Array(bytes.length);
  for (let i = 0; i < bytes.length; i++) arr[i] = bytes.charCodeAt(i);
  const blob = new Blob([arr], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
