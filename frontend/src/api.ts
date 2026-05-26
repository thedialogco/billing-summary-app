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
// Project storage — saved in the browser (localStorage)
// ---------------------------------------------------------------------------

const STORAGE_KEY = "bsg_projects";

function loadProjects(): Project[] {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) ?? "[]");
  } catch {
    return [];
  }
}

function saveProjects(projects: Project[]): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(projects));
}

export const projectStorage = {
  list: (): Project[] => loadProjects(),

  create: (data: Omit<Project, "id" | "created_at">): Project => {
    const projects = loadProjects();
    const next: Project = {
      ...data,
      id: Date.now(),
      created_at: new Date().toISOString(),
    };
    saveProjects([...projects, next]);
    return next;
  },

  update: (id: number, data: Partial<Omit<Project, "id" | "created_at">>): Project => {
    const projects = loadProjects().map((p) =>
      p.id === id ? { ...p, ...data } : p
    );
    saveProjects(projects);
    return projects.find((p) => p.id === id)!;
  },

  delete: (id: number): void => {
    saveProjects(loadProjects().filter((p) => p.id !== id));
  },
};

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
