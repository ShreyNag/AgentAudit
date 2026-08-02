import { Check, Copy } from "lucide-react";
import { useState } from "react";

/** A read-only, copyable JSON viewer (PROJECT_SPEC_4 SS84). No external editor dependency. */
export function JsonViewer({ data }: { data: unknown }) {
  const [copied, setCopied] = useState(false);
  const text = JSON.stringify(data, null, 2);

  const copy = async () => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <div className="relative rounded-md bg-gray-950 dark:bg-black">
      <button
        onClick={copy}
        className="absolute right-2 top-2 rounded p-1.5 text-gray-400 hover:bg-gray-800 hover:text-gray-100"
        aria-label="Copy JSON"
      >
        {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
      </button>
      <pre className="max-h-96 overflow-auto p-4 text-xs text-gray-100">
        <code>{text}</code>
      </pre>
    </div>
  );
}
