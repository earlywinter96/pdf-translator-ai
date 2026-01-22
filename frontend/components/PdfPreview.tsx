"use client";

interface Props {
  jobId: string;
}

export default function PdfPreview({ jobId }: Props) {
  const pdfUrl = `${process.env.NEXT_PUBLIC_API_BASE}/download/${jobId}`;

  return (
    <div className="w-full h-[70vh] border border-white/10 rounded-lg overflow-hidden bg-black">
      <iframe
        src={pdfUrl}
        className="w-full h-full"
        title="Translated PDF Preview"
      />
    </div>
  );
}
