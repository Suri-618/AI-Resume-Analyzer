// Links and skill groups inside resume text. Same rules as app/services/rich_text.py,
// so the preview, the PDF and the Word download agree.
//  - [text](url) anywhere in a line becomes a link
//  - an entry can have its own link (code, demo, certificate)
//  - a skill starting with a label ("Languages: Python") starts a group; the next
//    unlabelled skills ("Java") join it

const INLINE_LINK = /\[([^\]\n]{1,200})\]\(([^)\s]{1,500})\)/g;
const SKILL_LABEL = /^([^:,]{1,40}):\s*(.*)$/;
const EMAIL = /^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$/;

/** A clickable URL for what the user typed, or null to keep it as plain text. */
export function safeUrl(value) {
  const url = String(value || '').trim();
  if (!url || /\s/.test(url)) return null;
  if (EMAIL.test(url)) return `mailto:${url}`;
  if (/^(https?:\/\/|mailto:|tel:)/i.test(url)) return url;
  if (/^[a-z][a-z0-9+.-]*:/i.test(url) && !/^[^:/]+:\d/.test(url)) return null; // javascript:, data:…
  return url.split('/')[0].includes('.') ? `https://${url}` : null;
}

/** A URL as it reads best on a resume: no scheme, no www, no trailing slash. */
export const shortUrl = (value) =>
  String(value || '')
    .trim()
    .replace(/^(?:https?:\/\/)?(?:www\.)?/i, '')
    .replace(/\/$/, '');

/** Split text into [{ text, url }] parts; url is null for plain text and unsafe links. */
export function splitLinks(text) {
  const value = String(text || '');
  const parts = [];
  let last = 0;
  for (const match of value.matchAll(INLINE_LINK)) {
    if (match.index > last) parts.push({ text: value.slice(last, match.index), url: null });
    const url = safeUrl(match[2]);
    parts.push(url ? { text: match[1], url } : { text: match[0], url: null });
    last = match.index + match[0].length;
  }
  if (last < value.length) parts.push({ text: value.slice(last), url: null });
  return parts;
}

/** ['Languages: Python', 'Java', 'Tools: Git'] → [{ label: 'Languages', items: ['Python', 'Java'] }, …] */
export function groupSkills(skills) {
  const groups = [];
  for (const raw of skills || []) {
    const item = String(raw || '').trim();
    if (!item) continue;
    const match = item.match(SKILL_LABEL);
    if (match) groups.push({ label: match[1].trim(), items: match[2].trim() ? [match[2].trim()] : [] });
    else if (groups.length) groups[groups.length - 1].items.push(item);
    else groups.push({ label: '', items: [item] });
  }
  return groups;
}
