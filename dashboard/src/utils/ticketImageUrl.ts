import { baseURL } from "../api/client";

/**
 * Resolve ticket `image_url` for use in <img src>. Handles absolute URLs and
 * API-relative paths (e.g. /uploads/...).
 */
export function normalizeTicketImageUrl(
  url?: string | null,
): string | undefined {
  if (!url?.trim()) return undefined;
  if (url.startsWith("http://") || url.startsWith("https://")) return url;

  const path = url.startsWith("/") ? url : `/${url}`;
  try {
    const api = new URL(
      baseURL,
      typeof window !== "undefined"
        ? window.location.origin
        : "http://localhost:8000",
    );
    return `${api.origin}${path}`;
  } catch {
    const base = baseURL.replace(/\/+$/, "");
    return base ? `${base}${path}` : path;
  }
}
