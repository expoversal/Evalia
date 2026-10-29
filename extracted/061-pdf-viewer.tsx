"use client";
import { Document, Page } from "react-pdf";
import { useState, useEffect, useRef } from "react";
import "react-pdf/dist/Page/TextLayer.css";
import "react-pdf/dist/Page/AnnotationLayer.css";
import { api } from "@/lib/api";

// pdfjs worker registration
import { pdfjs } from "react-pdf";
pdfjs.GlobalWorkerOptions.workerSrc =
  `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.js`;

export default function PdfViewer({
  bundleKey, page, highlight,
}: { bundleKey: string; page: number; highlight: string | null }) {
  const [url, setUrl] = useState<string | null>(null);
  const [numPages, setNumPages] = useState(0);
  const [current, setCurrent] = useState(page);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // signed, short-lived URL from the storage layer
    api.get(`/storage/sign?key=${encodeURIComponent(bundleKey)}`)
      .then((r) => setUrl(r.url));
  }, [bundleKey]);

  useEffect(() => setCurrent(page), [page]);

  // after render, scroll the first highlighted text layer span into view
  useEffect(() => {
    if (!highlight || !containerRef.current) return;
    const timer = setTimeout(() => {
      const spans = containerRef.current!.querySelectorAll(".react-pdf__Page__textContent span");
      const needle = highlight.slice(0, 60).toLowerCase();
      for (const s of Array.from(spans)) {
        if ((s.textContent ?? "").toLowerCase().includes(needle)) {
          s.classList.add("bg-yellow-300");
          (s as HTMLElement).scrollIntoView({ behavior: "smooth", block: "center" });
          break;
        }
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [highlight, current]);

  if (!url) return <div className="p-6">Loading PDF…</div>;

  return (
    <div className="h-full overflow-auto p-4" ref={containerRef}>
      <Document
        file={url}
        onLoadSuccess={({ numPages }) => setNumPages(numPages)}
      >
        {Array.from({ length: numPages }, (_, i) => (
          <div key={i} className="mb-4 shadow">
            <Page pageNumber={i + 1} width={720} />
            <div className="text-xs text-center text-gray-500">p.{i + 1}</div>
          </div>
        ))}
      </Document>
    </div>
  );
}
