export const pages = ["overview", "sla", "risk", "triage", "quality", "about"] as const;

export type Page = (typeof pages)[number];

export function pageFromHash(hash: string): Page {
  const candidate = hash.replace(/^#/, "") as Page;
  return pages.includes(candidate) ? candidate : "overview";
}
