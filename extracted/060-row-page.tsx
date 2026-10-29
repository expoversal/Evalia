"use client";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import dynamic from "next/dynamic";
import { api } from "@/lib/api";
import { OverrideModal } from "@/components/OverrideModal";

const PdfViewer = dynamic(() => import("@/components/PdfViewer"), { ssr: false });

type Row = {
  id: string;
  bidder_id: string;
  bidder_name: string;
  bundle_key: string;
  clause_ref: string;
  requirement_text: string;
  evidence_expected: string[];
  conditional: boolean;
  condition: string | null;
  ai_status: string;
  ai_confidence: string;
  ai_flag: string;
  ai_evidence: { quote: string; doc_id: string; page: number }[];
  ai_gap_note: string | null;
  ai_model: string;
  ai_proposed_at: string;
  human_status: string | null;
  human_note: string | null;
  override_reason: string | null;
};

export default function RowPage({
  params,
}: { params: { id: string; envelope: "technical" | "commercial"; rowId: string } }) {
  const { id, envelope, rowId } = params;
  const { data: row, isLoading } = useQuery<Row>({
    queryKey: ["row", id, envelope, rowId],
    queryFn: () => api.get(`/tenders/${id}/${envelope}/rows/${rowId}`),
  });
  const [activePage, setActivePage] = useState<number | null>(null);
  const [activeQuote, setActiveQuote] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [suggestedStatus, setSuggestedStatus] = useState<string | undefined>();

  if (isLoading || !row) return <div className="p-8">Loading…</div>;

  const status = row.human_status ?? row.ai_status;
  const isDecided = !!row.human_status;

  return (
    <div className="h-screen grid grid-cols-2">
      {/* Left: evidence panel */}
      <div className="p-6 overflow-y-auto border-r">
        <div className="mb-4">
          <div className="text-xs font-mono text-gray-500">{row.clause_ref}</div>
          <h1 className="text-lg font-semibold">{row.requirement_text}</h1>
          {row.conditional && (
            <div className="mt-2 text-sm bg-blue-50 p-2 rounded">
              <strong>Conditional:</strong> {row.condition}
            </div>
          )}
          {row.evidence_expected.length > 0 && (
            <div className="mt-2 text-sm text-gray-600">
              Expected evidence: {row.evidence_expected.join(", ")}
            </div>
          )}
        </div>

        <div className="mb-4 p-4 border rounded bg-gray-50">
          <div className="flex items-center justify-between mb-2">
            <h2 className="font-semibold">AI proposal</h2>
            <span className="text-xs text-gray-500">
              {row.ai_model} · {new Date(row.ai_proposed_at).toLocaleString()}
            </span>
          </div>
          <div className="text-sm space-y-2">
            <div>
              <strong>Status:</strong>{" "}
              <span className="font-mono">{row.ai_status.replace("_", " ")}</span>{" "}
              <span className="text-xs text-gray-500">({row.ai_confidence})</span>
            </div>
            {row.ai_flag !== "none" && (
              <div className="text-amber-700">⚠ {row.ai_flag}</div>
            )}
            {row.ai_gap_note && (
              <div><strong>Gap:</strong> {row.ai_gap_note}</div>
            )}
            <div className="mt-2">
              <strong>Evidence ({row.ai_evidence.length}):</strong>
              <ul className="mt-1 space-y-1">
                {row.ai_evidence.map((e, i) => (
                  <li key={i} className="border-l-2 border-blue-400 pl-2">
                    <button
                      className="text-left w-full hover:bg-blue-50"
                      onClick={() => {
                        setActivePage(e.page);
                        setActiveQuote(e.quote);
                      }}
                    >
                      <div className="text-xs text-gray-500">
                        p.{e.page} · {e.doc_id}
                      </div>
                      <div className="text-sm italic">&ldquo;{e.quote}&rdquo;</div>
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>

        {isDecided ? (
          <div className="p-4 border rounded bg-blue-50">
            <h2 className="font-semibold mb-2">Human decision</h2>
            <div className="text-sm">
              <div><strong>Status:</strong> {row.human_status}</div>
              {row.human_note && <div><strong>Note:</strong> {row.human_note}</div>}
              {row.override_reason && (
                <div><strong>Override reason:</strong> {row.override_reason}</div>
              )}
            </div>
            <button
              className="mt-3 px-3 py-1 border rounded text-sm"
              onClick={() => { setSuggestedStatus(row.human_status!); setModalOpen(true); }}
            >
              Amend decision
            </button>
          </div>
        ) : (
          <DecisionBar
            onAccept={() => {
              setSuggestedStatus(row.ai_status);
              setModalOpen(true);
            }}
            onOverride={(s) => { setSuggestedStatus(s); setModalOpen(true); }}
          />
        )}
      </div>

      {/* Right: PDF with page + quote highlight */}
      <div className="bg-gray-100 overflow-hidden">
        <PdfViewer
          bundleKey={row.bundle_key}
          page={activePage ?? 1}
          highlight={activeQuote}
        />
      </div>

      {modalOpen && (
        <OverrideModal
          tenderId={id}
          envelope={envelope}
          rowId={rowId}
          initialStatus={suggestedStatus ?? row.ai_status}
          aiStatus={row.ai_status}
          aiProposedAt={row.ai_proposed_at}
          onClose={() => setModalOpen(false)}
        />
      )}
    </div>
  );
}

function DecisionBar({
  onAccept, onOverride,
}: { onAccept: () => void; onOverride: (s: string) => void }) {
  return (
    <div className="p-4 border rounded">
      <h2 className="font-semibold mb-2">Your decision</h2>
      <div className="flex flex-wrap gap-2">
        <button className="px-3 py-1 bg-green-600 text-white rounded text-sm"
                onClick={onAccept}>
          Accept AI proposal
        </button>
        <button className="px-3 py-1 border rounded text-sm"
                onClick={() => onOverride("compliant")}>
          Compliant
        </button>
        <button className="px-3 py-1 border rounded text-sm"
                onClick={() => onOverride("partial")}>
          Partial
        </button>
        <button className="px-3 py-1 border rounded text-sm"
                onClick={() => onOverride("non_compliant")}>
          Non-compliant
        </button>
        <button className="px-3 py-1 border rounded text-sm"
                onClick={() => onOverride("not_addressed")}>
          Not addressed
        </button>
        <button className="px-3 py-1 border rounded text-sm"
                onClick={() => onOverride("not_applicable")}>
          N/A
        </button>
      </div>
    </div>
  );
}
