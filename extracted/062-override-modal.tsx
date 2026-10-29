"use client";
import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

const STATUSES = [
  ["compliant", "Compliant"],
  ["partial", "Partial"],
  ["non_compliant", "Non-compliant"],
  ["not_addressed", "Not addressed"],
  ["not_applicable", "N/A"],
] as const;

export function OverrideModal({
  tenderId, envelope, rowId, initialStatus, aiStatus, aiProposedAt, onClose,
}: {
  tenderId: string;
  envelope: "technical" | "commercial";
  rowId: string;
  initialStatus: string;
  aiStatus: string;
  aiProposedAt: string;
  onClose: () => void;
}) {
  const qc = useQueryClient();
  const [status, setStatus] = useState(initialStatus);
  const [note, setNote] = useState("");
  const [reason, setReason] = useState("");
  const isOverride = status !== aiStatus;

  const mut = useMutation({
    mutationFn: () =>
      api.post(`/tenders/${tenderId}/${envelope}/rows/${rowId}/override`, {
        status,
        note: note || null,
        reason: isOverride ? reason : "Accepted AI proposal",
        expected_version: aiProposedAt,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["matrix", tenderId, envelope] });
      qc.invalidateQueries({ queryKey: ["row", tenderId, envelope, rowId] });
      onClose();
    },
  });

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-[480px] shadow-xl">
        <h2 className="text-lg font-semibold mb-4">
          {isOverride ? "Override AI proposal" : "Accept AI proposal"}
        </h2>

        <label className="block text-sm font-medium mb-1">Status</label>
        <select
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          className="w-full border rounded px-2 py-1 mb-4"
        >
          {STATUSES.map(([v, l]) => (
            <option key={v} value={v}>{l}</option>
          ))}
        </select>

        <label className="block text-sm font-medium mb-1">Note (optional)</label>
        <textarea
          value={note}
          onChange={(e) => setNote(e.target.value)}
          className="w-full border rounded px-2 py-1 mb-4 h-20"
          placeholder="Context for other evaluators…"
        />

        {isOverride && (
          <>
            <label className="block text-sm font-medium mb-1">
              Override reason <span className="text-red-600">*</span>
            </label>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              className="w-full border rounded px-2 py-1 mb-2 h-24"
              placeholder="Required. Why does your judgment differ from the AI proposal?"
            />
            <p className="text-xs text-gray-500 mb-4">
              Written to the audit ledger with your identity and timestamp.
            </p>
          </>
        )}

        {mut.isError && (
          <div className="text-sm text-red-600 mb-2">
            {(mut.error as Error).message}
          </div>
        )}

        <div className="flex justify-end gap-2">
          <button className="px-3 py-1 border rounded" onClick={onClose}>
            Cancel
          </button>
          <button
            className="px-3 py-1 bg-blue-600 text-white rounded disabled:opacity-50"
            disabled={mut.isPending || (isOverride && !reason.trim())}
            onClick={() => mut.mutate()}
          >
            {mut.isPending ? "Saving…" : "Confirm"}
          </button>
        </div>
      </div>
    </div>
  );
}
