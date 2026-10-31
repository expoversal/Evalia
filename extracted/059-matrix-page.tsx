"use client";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

type Row = {
  id: string;
  bidder_id: string;
  bidder_name: string;
  clause_ref: string;
  requirement_text: string;
  mandatory: boolean;
  category: string;
  ai_status: "compliant" | "partial" | "non_compliant" | "not_addressed" | "not_applicable";
  ai_confidence: "high" | "medium" | "low";
  ai_flag: string;
  ai_gap_note: string | null;
  human_status: string | null;
  human_note: string | null;
  override_reason: string | null;
};

const STATUS_COLORS: Record<string, string> = {
  non_compliant: "bg-red-100 text-red-800",
  not_addressed: "bg-orange-100 text-orange-800",
  partial:       "bg-amber-100 text-amber-800",
  compliant:     "bg-green-100 text-green-800",
  not_applicable:"bg-gray-100 text-gray-700",
};

export default function MatrixPage({
  params,
}: { params: { id: string; envelope: "technical" | "commercial" } }) {
  const { id, envelope } = params;
  const qc = useQueryClient();
  const router = useRouter();
  const [bidderFilter, setBidderFilter] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [mandatoryOnly, setMandatoryOnly] = useState(true);

  const { data, isLoading, error } = useQuery({
    queryKey: ["matrix", id, envelope, bidderFilter],
    queryFn: () =>
      api.get(
        `/tenders/${id}/${envelope}/matrix${
          bidderFilter ? `?bidder_id=${bidderFilter}` : ""
        }`,
      ),
  });

  const rows: Row[] = useMemo(() => {
    if (!data?.rows) return [];
    return data.rows.filter((r: Row) => {
      if (mandatoryOnly && !r.mandatory) return false;
      if (statusFilter) {
        const s = r.human_status ?? r.ai_status;
        if (s !== statusFilter) return false;
      }
      return true;
    });
  }, [data, mandatoryOnly, statusFilter]);

  const bidders = useMemo(() => {
    const m = new Map<string, string>();
    data?.rows?.forEach((r: Row) => m.set(r.bidder_id, r.bidder_name));
    return Array.from(m.entries());
  }, [data]);

  const counts = useMemo(() => {
    const c = { non_compliant: 0, not_addressed: 0, partial: 0, compliant: 0 };
    data?.rows?.forEach((r: Row) => {
      const s = (r.human_status ?? r.ai_status) as keyof typeof c;
      if (s in c) c[s]++;
    });
    return c;
  }, [data]);

  if (isLoading) return <div className="p-8">Loading matrix…</div>;
  if (error) return <div className="p-8 text-red-600">Access denied or error.</div>;

  return (
    <div className="p-6">
      <header className="mb-4 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">
            {envelope === "technical" ? "Technical" : "Commercial"} compliance matrix
          </h1>
          <p className="text-sm text-gray-600">
            {data?.sealed ? "🔒 sealed" : "✏️ editable"} · {rows.length} rows
          </p>
        </div>
        <div className="flex gap-2 text-sm">
          <Badge label="Non-compliant" count={counts.non_compliant}
                 className="bg-red-100 text-red-800" />
          <Badge label="Not addressed" count={counts.not_addressed}
                 className="bg-orange-100 text-orange-800" />
          <Badge label="Partial" count={counts.partial}
                 className="bg-amber-100 text-amber-800" />
          <Badge label="Compliant" count={counts.compliant}
                 className="bg-green-100 text-green-800" />
        </div>
      </header>

      <div className="mb-3 flex gap-3 text-sm">
        <select
          value={bidderFilter}
          onChange={(e) => setBidderFilter(e.target.value)}
          className="border rounded px-2 py-1"
        >
          <option value="">All bidders</option>
          {bidders.map(([id, name]) => (
            <option key={id} value={id}>{name}</option>
          ))}
        </select>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="border rounded px-2 py-1"
        >
          <option value="">All statuses</option>
          <option value="non_compliant">Non-compliant</option>
          <option value="not_addressed">Not addressed</option>
          <option value="partial">Partial</option>
          <option value="compliant">Compliant</option>
        </select>
        <label className="flex items-center gap-1">
          <input type="checkbox" checked={mandatoryOnly}
                 onChange={(e) => setMandatoryOnly(e.target.checked)} />
          Mandatory only
        </label>
      </div>

      <table className="w-full text-sm border-collapse">
        <thead className="bg-gray-50 text-left">
          <tr>
            <th className="border-b p-2 w-24">Clause</th>
            <th className="border-b p-2 w-40">Bidder</th>
            <th className="border-b p-2">Requirement</th>
            <th className="border-b p-2 w-32">Status</th>
            <th className="border-b p-2 w-24">Confidence</th>
            <th className="border-b p-2 w-24">Flag</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => {
            const status = r.human_status ?? r.ai_status;
            return (
              <tr
                key={r.id}
                className="hover:bg-blue-50 cursor-pointer"
                onClick={() =>
                  router.push(`/tenders/${id}/${envelope}/rows/${r.id}`)
                }
              >
                <td className="border-b p-2 font-mono text-xs">{r.clause_ref}</td>
                <td className="border-b p-2">{r.bidder_name}</td>
                <td className="border-b p-2">
                  <span className={r.mandatory ? "font-medium" : ""}>
                    {r.requirement_text}
                  </span>
                  {r.human_status && (
                    <span className="ml-2 text-xs text-blue-600">(reviewed)</span>
                  )}
                </td>
                <td className="border-b p-2">
                  <span className={`px-2 py-0.5 rounded text-xs ${STATUS_COLORS[status]}`}>
                    {status.replace("_", " ")}
                  </span>
                </td>
                <td className="border-b p-2 text-xs">{r.ai_confidence}</td>
                <td className="border-b p-2 text-xs">
                  {r.ai_flag !== "none" ? `⚠ ${r.ai_flag}` : ""}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function Badge({ label, count, className }:
  { label: string; count: number; className: string }) {
  return (
    <span className={`px-2 py-1 rounded ${className}`}>
      {label}: <strong>{count}</strong>
    </span>
  );
}
