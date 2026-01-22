"use client";

interface Props {
  jobId: string;
}

export default function BilingualPreview({ jobId }: { jobId: string }) {
  const pdfUrl = `${process.env.NEXT_PUBLIC_API_BASE}/api/download/${jobId}`;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

      {/* Original */}
      <div className="rounded-xl bg-[#f8f8f6] shadow-lg overflow-hidden">
        <div className="px-4 py-2 text-xs font-medium text-gray-600 border-b">
          Original
        </div>
        <iframe
          src={pdfUrl}
          className="w-full h-[600px]"
        />
      </div>

      {/* Translated */}
      <div className="rounded-xl bg-[#f8f8f6] shadow-lg overflow-hidden">
        <div className="px-4 py-2 text-xs font-medium text-gray-600 border-b">
          Translated
        </div>
        <iframe
          src={pdfUrl}
          className="w-full h-[600px]"
        />
      </div>
    </div>
  );
}
