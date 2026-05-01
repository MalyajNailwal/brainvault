import { useCallback, useEffect, useState } from "react";
import { useDropzone } from "react-dropzone";
import { api } from "../api/client";
import type { FileStatus } from "../hooks/useSocket";

interface VaultFile {
  name: string;
  size: number;
  extension: string;
  modified: number;
}

interface Props {
  fileStatuses: Record<string, FileStatus>;
}

const EXT_ICONS: Record<string, string> = {
  ".pdf": "📄",
  ".docx": "📝",
  ".doc": "📝",
  ".pptx": "📑",
  ".ppt": "📑",
  ".xlsx": "📊",
  ".xls": "📊",
  ".png": "🖼",
  ".jpg": "🖼",
  ".jpeg": "🖼",
  ".webp": "🖼",
  ".gif": "🎞",
  ".bmp": "🖼",
  ".tiff": "🖼",
  ".txt": "📃",
  ".md": "📃",
};

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function VaultPanel({ fileStatuses }: Props) {
  const [files, setFiles] = useState<VaultFile[]>([]);
  const [vaultPath, setVaultPath] = useState("");
  const [uploading, setUploading] = useState(false);

  const fetchVault = useCallback(() => {
    api
      .get("/vault/info")
      .then((res) => {
        setFiles(res.data.files || []);
        setVaultPath(res.data.vault_path || "");
      })
      .catch((err) => console.error("Failed to fetch vault:", err));
  }, []);

  useEffect(() => {
    fetchVault();
  }, [fetchVault]);

  // Re-fetch when a file finishes processing
  useEffect(() => {
    const doneFiles = Object.values(fileStatuses).filter((s) => s.status === "done");
    if (doneFiles.length > 0) {
      fetchVault();
    }
  }, [fileStatuses, fetchVault]);

  const onDrop = useCallback(
    async (accepted: File[]) => {
      if (accepted.length === 0) return;
      setUploading(true);
      const form = new FormData();
      accepted.forEach((f) => form.append("files", f));
      try {
        await api.post("/upload", form, {
          headers: { "Content-Type": "multipart/form-data" },
        });
        fetchVault();
      } catch (err) {
        console.error("Upload failed:", err);
      } finally {
        setUploading(false);
      }
    },
    [fetchVault]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
      "application/vnd.openxmlformats-officedocument.*": [".docx", ".pptx", ".xlsx"],
      "application/msword": [".doc"],
      "image/*": [".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tiff"],
      "text/plain": [".txt"],
      "text/markdown": [".md"],
    },
  });

  const getStatusIcon = (filename: string) => {
    const s = fileStatuses[filename];
    if (!s) return <span className="text-vault-muted">⬜</span>;
    if (s.status === "processing") return <span className="text-vault-warning animate-pulse">⏳</span>;
    if (s.status === "done") return <span className="text-vault-success">✅</span>;
    if (s.status === "error") return <span className="text-vault-danger" title={s.error}>❌</span>;
    return <span className="text-vault-muted">⬜</span>;
  };

  return (
    <div className="flex flex-col h-full gap-3">
      {/* Vault path card */}
      <div className="bg-vault-panel rounded-lg p-3">
        <p className="text-[10px] text-vault-muted uppercase tracking-wider mb-1">Vault Location</p>
        <p className="text-[11px] text-vault-accent font-mono break-all">{vaultPath || "Loading..."}</p>
        <p className="text-[10px] text-vault-muted mt-2">
          Drop files here or put them in this folder manually
        </p>
      </div>

      {/* Drop zone */}
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-5 text-center cursor-pointer transition-all ${
          isDragActive
            ? "border-vault-accent bg-vault-accent/10"
            : "border-vault-border hover:border-vault-muted"
        }`}
      >
        <input {...getInputProps()} />
        <p className="text-2xl mb-2">{uploading ? "⏳" : isDragActive ? "📂" : "➕"}</p>
        <p className="text-xs text-vault-muted">
          {uploading ? "Uploading..." : "Drag files or click to browse"}
        </p>
        <p className="text-[10px] text-vault-muted mt-1">
          PDF · DOCX · PPTX · XLSX · PNG · JPG · TXT · MD
        </p>
      </div>

      {/* File list */}
      <div className="flex-1 overflow-y-auto min-h-0">
        <p className="text-[10px] text-vault-muted uppercase tracking-wider mb-2">
          Files ({files.length})
        </p>
        {files.length === 0 && (
          <div className="text-center mt-8">
            <p className="text-sm text-vault-muted">No files yet</p>
            <p className="text-xs text-vault-muted/60 mt-1">Add some documents!</p>
          </div>
        )}
        <div className="flex flex-col gap-1.5">
          {files.map((f) => (
            <div
              key={f.name}
              className="flex items-center gap-2.5 p-2 rounded-md bg-vault-panel hover:bg-vault-border/50 transition-colors"
            >
              <span className="text-base shrink-0">{EXT_ICONS[f.extension] || "📄"}</span>
              <div className="flex-1 min-w-0">
                <p className="text-xs text-vault-text truncate" title={f.name}>
                  {f.name}
                </p>
                <p className="text-[10px] text-vault-muted">{formatSize(f.size)}</p>
              </div>
              <div className="shrink-0 text-sm">{getStatusIcon(f.name)}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
