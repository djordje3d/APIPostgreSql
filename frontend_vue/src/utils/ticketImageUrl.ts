const fileserverBase =
  import.meta.env.VITE_FILESERVER_URL || "http://localhost:9009";

/**
 * Resolve ticket `image_url` for use in <img src>. Handles absolute URLs and
 * relative paths (e.g. /uploads/...) by prepending the file server origin.
 */
export function normalizeTicketImageUrl(
  url?: string | null,
): string | undefined {
  if (!url?.trim()) return undefined;
  if (url.startsWith("http://") || url.startsWith("https://")) return url;

  const path = url.startsWith("/") ? url : `/${url}`;
  return `${fileserverBase}${path}`;
}
