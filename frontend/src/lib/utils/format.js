/**
 * Format a datetime string to a readable date.
 */
export function formatDate(dateStr) {
    if (!dateStr) return '';
    return new Date(dateStr).toLocaleDateString(undefined, {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
    });
}

/**
 * Parse a comma-separated string of tags into a clean array.
 */
export function parseTags(str) {
    if (!str) return [];
    return str
        .split(',')
        .map((t) => t.trim())
        .filter(Boolean);
}

/**
 * Parse basic BBCode tags to HTML.
 * Supported: [b], [i], [u], [s], [color=x], [size=x], [url=x], [url]
 */
export function parseBBCode(str) {
    if (!str) return '';
    return str
        .replace(/<br\s*\/?>/gi, '\n') // Normalize existing <br> to \n first
        .replace(/\[b\](.*?)\[\/b\]/gis, '<strong>$1</strong>')
        .replace(/\[i\](.*?)\[\/i\]/gis, '<em>$1</em>')
        .replace(/\[u\](.*?)\[\/u\]/gis, '<u>$1</u>')
        .replace(/\[s\](.*?)\[\/s\]/gis, '<s>$1</s>')
        .replace(/\[color=(.*?)\](.*?)\[\/color\]/gis, '<span style="color:$1">$2</span>')
        .replace(
            /\[size=(\d+)\](.*?)\[\/size\]/gis,
            (_, size, content) => `<span style="font-size:${size * 4}px">${content}</span>`
        )
        .replace(
            /\[url=(.*?)\](.*?)\[\/url\]/gis,
            '<a href="$1" target="_blank" rel="noopener noreferrer">$2</a>'
        )
        .replace(
            /\[url\](.*?)\[\/url\]/gis,
            '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>'
        )
        .replace(/\r?\n/g, '<br>'); // Convert all \n to <br> at the end
}
