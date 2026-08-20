import { Check, Copy } from "lucide-react";
import { useState } from "react";

/** A read-only, copyable text/code block. Same copy-button pattern as JsonViewer, generalized
 * for arbitrary text (curl commands, Python snippets, a run ID) rather than only JSON. */
export function CopyBlock({ text, label }: { text: string; label?: string }) {
  const [copied, setCopied] = useState(false);

  const copy = async () => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <div>
      {label && (
        <p className="mb-1 text-xs font-medium uppercase tracking-wide text-gray-500">{label}</p>
      )}
      <div className="relative rounded-md bg-gray-950 dark:bg-black">
        <button
          onClick={copy}
          className="absolute right-2 top-2 rounded p-1.5 text-gray-400 hover:bg-gray-800 hover:text-gray-100"
          aria-label={label ? `Copy ${label}` : "Copy"}
        >
          {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
        </button>
        <pre className="max-h-72 overflow-auto whitespace-pre-wrap break-all p-4 pr-10 text-xs text-gray-100">
          <code>{text}</code>
        </pre>
      </div>
    </div>
  );
}
