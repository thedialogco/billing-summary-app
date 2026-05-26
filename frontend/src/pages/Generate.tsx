import { useEffect, useRef, useState } from "react";
import { api, downloadBase64 } from "../api";
import type { GenerateResponse, Project, ValidationResult, ValidationItem } from "../api";

function formatCurrency(raw: string): string {
  const num = parseFloat(raw.replace(/[^0-9.]/g, ""));
  if (isNaN(num)) return raw;
  return "$" + num.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function CurrencyInput({
  value, onChange, placeholder,
}: { value: string; onChange: (v: string) => void; placeholder?: string }) {
  const [focused, setFocused] = useState(false);
  const displayValue = !focused && value ? formatCurrency(value) : value;

  return (
    <input
      type="text"
      inputMode="decimal"
      value={displayValue}
      placeholder={placeholder}
      onFocus={() => setFocused(true)}
      onBlur={() => { setFocused(false); }}
      onChange={(e) => {
        const raw = e.target.value.replace(/[^0-9.]/g, "");
        onChange(raw);
      }}
      className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
    />
  );
}

function FileField({
  label, accept, file, onChange,
}: {
  label: string;
  accept: string;
  file: File | null;
  onChange: (f: File) => void;
}) {
  const ref = useRef<HTMLInputElement>(null);
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      <div
        onClick={() => ref.current?.click()}
        className="border-2 border-dashed border-gray-300 rounded-lg px-4 py-5 text-center cursor-pointer hover:border-blue-400 hover:bg-blue-50 transition-colors"
      >
        {file ? (
          <span className="text-sm text-blue-700 font-medium">{file.name}</span>
        ) : (
          <span className="text-sm text-gray-400">Click to select file</span>
        )}
      </div>
      <input
        ref={ref}
        type="file"
        accept={accept}
        className="hidden"
        onChange={(e) => e.target.files?.[0] && onChange(e.target.files[0])}
      />
    </div>
  );
}

function ValidationPanel({ result }: { result: ValidationResult }) {
  return (
    <div className={`rounded-lg border px-4 py-4 ${result.passed ? "bg-green-50 border-green-200" : "bg-amber-50 border-amber-200"}`}>
      <p className={`font-semibold mb-3 text-sm ${result.passed ? "text-green-800" : "text-amber-800"}`}>
        {result.passed ? "✓ Validation Passed" : "Validation — some checks failed"}
      </p>
      <ul className="space-y-1">
        {result.items.map((item: ValidationItem, i: number) => (
          <li key={i} className="text-xs flex items-start gap-2">
            <span className={`mt-0.5 font-bold shrink-0 ${item.passed ? "text-green-600" : "text-red-600"}`}>
              {item.passed ? "✓" : "✗"}
            </span>
            <span className={item.passed ? "text-gray-700" : "text-red-700"}>
              {item.message}
            </span>
          </li>
        ))}
      </ul>
      {!result.passed && (
        <p className="mt-3 text-xs text-amber-700 border-t border-amber-200 pt-2">
          You can still download the outputs — review the issues above and confirm the dates match your invoice period.
        </p>
      )}
    </div>
  );
}

export default function Generate() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectId, setProjectId] = useState<string>("");
  const [prebillFile, setPrebillFile] = useState<File | null>(null);
  const [masterFile, setMasterFile] = useState<File | null>(null);
  const [invoiceNumber, setInvoiceNumber] = useState("");
  const [invoiceStart, setInvoiceStart] = useState("");
  const [invoiceEnd, setInvoiceEnd] = useState("");
  const [ecmsTotal, setEcmsTotal] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<GenerateResponse | null>(null);

  useEffect(() => {
    api.projects.list().then(setProjects).catch(() => {});
  }, []);

  const canSubmit =
    projectId && prebillFile && masterFile &&
    invoiceNumber && invoiceStart && invoiceEnd && ecmsTotal;

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!canSubmit) return;

    setLoading(true);
    setError("");
    setResult(null);

    const form = new FormData();
    form.append("prebill_file", prebillFile!);
    form.append("master_file", masterFile!);
    form.append("project_id", projectId);
    form.append("invoice_number", invoiceNumber);
    form.append("invoice_start", invoiceStart);
    form.append("invoice_end", invoiceEnd);
    form.append("ecms_total", ecmsTotal);

    try {
      const res = await api.generate(form);
      setResult(res);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  const selectedProject = projects.find((p) => p.id === Number(projectId));
  const invoiceLabel = invoiceNumber
    ? `Invoice_${invoiceNumber}`
    : "Invoice";

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-800">Generate Billing Summary</h2>
        <p className="text-gray-500 text-sm mt-1">Upload your Excel files and enter invoice details to generate the PDF report.</p>
      </div>

      <form onSubmit={submit} className="space-y-6">
        {/* Project selection */}
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h3 className="font-semibold text-gray-800 mb-4">1. Select Project</h3>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Project</label>
            <select
              value={projectId}
              onChange={(e) => setProjectId(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">— Select a project —</option>
              {projects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} — Agreement {p.agreement_number}, {p.work_order_number}
                </option>
              ))}
            </select>
            {projects.length === 0 && (
              <p className="text-xs text-amber-600 mt-1">No projects found. Add one in the Settings tab first.</p>
            )}
          </div>
          {selectedProject && (
            <div className="mt-3 flex gap-6 text-sm text-gray-600 bg-gray-50 rounded-lg px-4 py-2">
              <span><span className="font-medium">Agreement:</span> {selectedProject.agreement_number}</span>
              <span><span className="font-medium">Work Order:</span> {selectedProject.work_order_number}</span>
            </div>
          )}
        </div>

        {/* File uploads */}
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h3 className="font-semibold text-gray-800 mb-4">2. Upload Excel Files</h3>
          <div className="grid grid-cols-2 gap-4">
            <FileField
              label="Prebill Data (.xlsx)"
              accept=".xlsx,.xls"
              file={prebillFile}
              onChange={setPrebillFile}
            />
            <FileField
              label="Master Billing Summary Report (.xlsx)"
              accept=".xlsx,.xls"
              file={masterFile}
              onChange={setMasterFile}
            />
          </div>
        </div>

        {/* Invoice details */}
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h3 className="font-semibold text-gray-800 mb-4">3. Invoice Details</h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Invoice Number</label>
              <input
                type="number"
                min="1"
                value={invoiceNumber}
                onChange={(e) => setInvoiceNumber(e.target.value)}
                placeholder="e.g. 1, 2, 3..."
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">ECMS Invoice Total Amount</label>
              <CurrencyInput
                value={ecmsTotal}
                onChange={setEcmsTotal}
                placeholder="e.g. $20,139.64"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Invoice Period — Start Date</label>
              <input
                type="date"
                value={invoiceStart}
                onChange={(e) => setInvoiceStart(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Invoice Period — End Date</label>
              <input
                type="date"
                value={invoiceEnd}
                onChange={(e) => setInvoiceEnd(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 text-sm">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={!canSubmit || loading}
          className="w-full bg-blue-600 text-white py-3 rounded-xl font-semibold text-sm hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? "Generating…" : "Generate Billing Summary"}
        </button>
      </form>

      {result && (
        <div className="mt-8 space-y-4">
          <h3 className="font-semibold text-gray-800 text-lg">Results</h3>
          <ValidationPanel result={result.validation} />
          <div className="grid grid-cols-2 gap-4">
            <button
              onClick={() => downloadBase64(result.pdf_b64, `${invoiceLabel}_Billing_Summary.pdf`, "application/pdf")}
              className="bg-white border-2 border-blue-600 text-blue-700 py-3 rounded-xl font-semibold text-sm hover:bg-blue-50 transition-colors"
            >
              Download PDF Report
            </button>
            <button
              onClick={() => downloadBase64(result.master_xlsx_b64, `Master_Billing_Summary_Updated.xlsx`, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
              className="bg-white border-2 border-green-600 text-green-700 py-3 rounded-xl font-semibold text-sm hover:bg-green-50 transition-colors"
            >
              Download Updated Master Excel
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
