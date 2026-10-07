"use client";

import { useRef, useState } from "react";
import { UploadCloud, Loader2 } from "lucide-react";

interface UploadZoneProps {
  onUpload: (files: File[]) => Promise<void>;
}

export default function UploadZone({ onUpload }: UploadZoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);

  async function handleFiles(fileList: FileList | null) {
    if (!fileList || fileList.length === 0) return;
    const pdfFiles = Array.from(fileList).filter((f) => f.type === "application/pdf" || f.name.toLowerCase().endsWith(".pdf"));
    if (pdfFiles.length === 0) return;

    setIsUploading(true);
    try {
      await onUpload(pdfFiles);
    } finally {
      setIsUploading(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  }

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setIsDragging(true);
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={(e) => {
        e.preventDefault();
        setIsDragging(false);
        handleFiles(e.dataTransfer.files);
      }}
      onClick={() => inputRef.current?.click()}
      className={`flex cursor-pointer flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed p-6 text-center transition-colors ${
        isDragging ? "border-brand-500 bg-brand-50" : "border-slate-300 bg-white hover:border-brand-400"
      }`}
    >
      <input
        ref={inputRef}
        type="file"
        accept="application/pdf"
        multiple
        className="hidden"
        onChange={(e) => handleFiles(e.target.files)}
      />
      {isUploading ? (
        <Loader2 className="h-6 w-6 animate-spin text-brand-600" />
      ) : (
        <UploadCloud className="h-6 w-6 text-brand-600" />
      )}
      <p className="text-sm font-medium text-slate-700">
        {isUploading ? "Processing document…" : "Click or drag PDFs here"}
      </p>
      <p className="text-xs text-slate-400">Lecture notes, textbooks, assignments</p>
    </div>
  );
}
