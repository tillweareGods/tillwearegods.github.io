#!/usr/bin/env python3
"""
new-post.py — Convert a Markdown file into a blog post and update index.html

Usage:
    python new-post.py post.md
    python new-post.py post.md --date 2024-12-14

Input md structure:
| You write | It becomes |
|---|---|
| `# Title` | `<h1>` (also used as page title + slug) |
| `## Subtitle` | `<h2>` with muted heading style |
| `### Sub-subtitle` | `<h3>` |
| `` `code` `` | Inline `<code>` with dark bg pill |
| Triple backtick blocks | `<pre><code>` with rounded border box |
| `**bold**` | `<strong>` with brighter text |
| `*italic*` | `<em>` |
| `> quote` | Left-bordered blockquote |
| `- item` / `* item` | `<ul>` |
| `1. item` | `<ol>` |
| `[text](url)` | `<a>` with underline |
| `![alt](url)` | `<img>` with rounded corners |
| `---` or `***` | `<hr>` divider |
| Plain paragraphs | `<p>` with relaxed line-height |


"""
import re
import sys
import os
from datetime import date

POSTS_DIR = "posts"
INDEX_FILE = "index.html"
BLOG_NAME = "Till we are Gods blog"

# ─── Post HTML template ───────────────────────────────────────────────

TEMPLATE = '''<!DOCTYPE html>
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>__TITLE__ — __BLOG_NAME__</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/lucide@latest"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
    <script>
    tailwind.config = {
        darkMode: 'class',
        theme: {
            extend: {
                fontFamily: { sans: ['Inter', 'sans-serif'] },
                colors: {
                    surface:  { dark: '#110d0b', light: '#faf5ee' },
                    card:     { dark: '#1d1714', light: '#ffffff' },
                    subtle:   { dark: 'rgba(255,145,110,0.08)', light: 'rgba(33,26,21,0.1)' },
                    muted:    { dark: 'rgba(242,236,229,0.4)',  light: 'rgba(33,26,21,0.5)' },
                },
            }
        }
    }
    </script>
    <style>
    html { scroll-behavior: smooth; }
    :root { --accent: #ff5c33; }
    .glow { position: fixed; border-radius: 50%; background: var(--accent); pointer-events: none; z-index: -1; }
    .glow-1 { top: -80px; right: -80px; width: 280px; height: 280px; opacity: 0.18; }
    .glow-2 { bottom: -100px; left: -100px; width: 320px; height: 320px; opacity: 0.18; }
    .glow-3 { top: 40%; left: -60px; width: 180px; height: 180px; opacity: 0.15; }
    .glow-4 { top: 15%; right: 10%; width: 90px; height: 90px; opacity: 0.16; }
    .glow-5 { bottom: 20%; right: -40px; width: 140px; height: 140px; opacity: 0.15; }
    html.dark .glow-1 { opacity: 0.12; }
    html.dark .glow-2 { opacity: 0.08; }
    html.dark .glow-3 { opacity: 0.07; }
    html.dark .glow-4 { opacity: 0.09; }
    html.dark .glow-5 { opacity: 0.08; }
    body { font-family: 'Inter', sans-serif; }
    html.transitioning, html.transitioning *, html.transitioning *::before, html.transitioning *::after {
        transition: background-color 400ms ease, color 400ms ease, border-color 400ms ease !important;
    }
    ::-webkit-scrollbar { width: 5px; }
    ::-webkit-scrollbar-track { background: transparent; }
    .dark ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.08); border-radius: 3px; }
    html:not(.dark) ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.12); border-radius: 3px; }
    .prose p { margin-bottom: 1.5em; }
    .prose h2 { font-size: 1.375rem; font-weight: 500; margin-top: 2.5em; margin-bottom: 0.75em; letter-spacing: -0.01em; color: rgba(255,255,255,0.85); }
    .prose h3 { font-size: 1.125rem; font-weight: 500; margin-top: 2em; margin-bottom: 0.5em; color: rgba(255,255,255,0.8); }
    .prose a { color: var(--accent); text-decoration: underline; text-decoration-color: rgba(255,92,51,0.4); text-underline-offset: 2px; }
    .prose a:hover { text-decoration-color: var(--accent); opacity: 1; }
    .prose blockquote { border-left: 2px solid var(--accent); padding-left: 1.25em; margin: 1.5em 0; font-style: italic; }
    .prose code { font-family: 'SF Mono', 'Fira Code', monospace; font-size: 0.875em; color: var(--accent); background: rgba(255,92,51,0.1); padding: 0.15em 0.4em; border-radius: 4px; }
    .prose pre { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.06); border-radius: 12px; padding: 1.25em; overflow-x: auto; margin: 1.5em 0; }
    .prose pre code { background: none; padding: 0; font-size: 0.8125rem; }
    .prose ul, .prose ol { padding-left: 1.5em; margin-bottom: 1.5em; }
    .prose li { margin-bottom: 0.4em; }
    .prose img { border-radius: 12px; margin: 2em 0; width: 100%; }
    .prose hr { border: none; border-top: 1px solid rgba(255,255,255,0.06); margin: 2.5em 0; }
    .prose strong { color: rgba(255,255,255,0.85); font-weight: 500; }
    html:not(.dark) body,
    html:not(.dark) .prose { color: #211a15; }
    html:not(.dark) .text-white\\/85 { color: rgba(33,26,21,0.85) !important; }
    html:not(.dark) .text-white\\/80 { color: rgba(33,26,21,0.8) !important; }
    html:not(.dark) .text-white\\/70 { color: rgba(33,26,21,0.7) !important; }
    html:not(.dark) .text-white\\/60 { color: rgba(33,26,21,0.6) !important; }
    html:not(.dark) .text-white\\/40 { color: rgba(33,26,21,0.45) !important; }
    html:not(.dark) .text-white\\/30 { color: rgba(33,26,21,0.35) !important; }
    html:not(.dark) .text-white\\/25 { color: rgba(33,26,21,0.3) !important; }
    html:not(.dark) .border-white\\/10 { border-color: rgba(33,26,21,0.15) !important; }
    html:not(.dark) .hover\\:text-white\\/70:hover { color: rgba(33,26,21,0.85) !important; }
    html:not(.dark) .group:hover .group-hover\\:text-white { color: #211a15 !important; }
    html:not(.dark) .brand-link { position: relative; display: inline-flex; }
    html:not(.dark) .brand-link::after {
        content: ''; position: absolute; left: 0; bottom: -10px;
        width: 32px; height: 2px; background: #ff5c33;
    }
    html:not(.dark) .font-mono { color: #ff5c33 !important; }
    html:not(.dark) .prose pre { background: #ffffff; border-color: rgba(33,26,21,0.08); }
    html:not(.dark) .prose h2 { color: rgba(33,26,21,0.85); }
    html:not(.dark) .prose h3 { color: rgba(33,26,21,0.8); }
    html:not(.dark) .prose strong { color: rgba(33,26,21,0.85); }
    html:not(.dark) body {
        background-image: radial-gradient(rgba(33,26,21,0.06) 1px, transparent 1px);
        background-size: 22px 22px;
    }
    html:not(.dark) .prose h2::before {
        content: ''; display: inline-block; width: 8px; height: 8px;
        background: var(--accent); margin-right: 8px; border-radius: 2px;
    }
    </style>
</head>
<body class="bg-surface-dark text-white min-h-screen">
    <div class="glow glow-1" aria-hidden="true"></div>
    <div class="glow glow-2" aria-hidden="true"></div>
    <div class="glow glow-3" aria-hidden="true"></div>
    <div class="glow glow-4" aria-hidden="true"></div>
    <div class="glow glow-5" aria-hidden="true"></div>
    <header class="max-w-2xl mx-auto px-6 pt-16 pb-12 flex items-center justify-between">
        <a href="../" class="brand-link flex items-center gap-2.5">
            <div class="w-7 h-7 bg-[#ff5c33] rounded-full flex items-center justify-center">
                <span class="text-white text-xs font-semibold">S</span>
            </div>
            <span class="font-medium text-sm tracking-tight">__BLOG_NAME__</span>
        </a>
        <div class="flex items-center gap-4">
            <a href="../" class="text-sm text-white/40 hover:text-white/70 transition-colors hidden sm:inline">Posts</a>
            <button id="theme-toggle" class="w-9 h-9 rounded-full border border-white/10 flex items-center justify-center hover:bg-white/10 transition-colors" aria-label="Toggle theme">
                <i data-lucide="sun" class="w-4 h-4 hidden dark:block"></i>
                <i data-lucide="moon" class="w-4 h-4 block dark:hidden"></i>
            </button>
        </div>
    </header>
    <main class="max-w-2xl mx-auto px-6 pb-24">
        <a href="../" class="inline-flex items-center gap-1.5 text-xs text-white/30 hover:text-[#ff5c33] transition-colors mb-12">
            <i data-lucide="arrow-left" class="w-3.5 h-3.5"></i> Back to posts
        </a>
        <header class="mb-12">
            <p class="text-[10px] font-mono uppercase tracking-widest text-[#ff5c33] mb-4">__DATE__</p>
            <h1 class="text-3xl sm:text-4xl font-medium tracking-tight leading-[1.15]">__TITLE__</h1>
        </header>
        <article class="prose text-white/60 font-light leading-[1.75] text-[15px]">
__BODY__
        </article>
    </main>
    <footer class="border-t border-subtle-dark">
        <div class="max-w-2xl mx-auto px-6 py-10 flex items-center justify-between">
            <a href="../" class="text-xs text-white/25 hover:text-white/50 transition-colors">&larr; All posts</a>
            <a href="https://github.com" class="text-white/25 hover:text-white/60 transition-colors"><i data-lucide="github" class="w-4 h-4"></i></a>
        </div>
    </footer>
    <script>
    lucide.createIcons();
    var html = document.documentElement;
    var body = document.body;
    function applyTheme(dark) {
        if (dark) {
            html.classList.add('dark');
            body.className = body.className.replace('bg-surface-light','bg-surface-dark');
        } else {
            html.classList.remove('dark');
            body.className = body.className.replace('bg-surface-dark','bg-surface-light');
        }
        document.querySelector('footer').classList.toggle('border-subtle-dark', dark);
        document.querySelector('footer').classList.toggle('border-subtle-light', !dark);
        lucide.createIcons();
    }
    if (localStorage.getItem('theme') === 'light') applyTheme(false);
    document.getElementById('theme-toggle').addEventListener('click', function() {
        html.classList.add('transitioning');
        applyTheme(!html.classList.contains('dark'));
        localStorage.setItem('theme', html.classList.contains('dark') ? 'dark' : 'light');
        setTimeout(function() { html.classList.remove('transitioning'); }, 450);
    });
    </script>
</body>
</html>'''


# ─── Helpers ──────────────────────────────────────────────────────────

def slugify(text):
    slug = text.lower().strip()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[\s_]+', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    return slug.strip('-')


def esc(text):
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def extract_title(md):
    m = re.search(r'^#\s+(.+)$', md, re.MULTILINE)
    return m.group(1).strip() if m else 'Untitled'


UL_PREFIX = re.compile(r"^[-*+]\s+")
OL_PREFIX = re.compile(r"^\d+\.\s+")
BQ_PREFIX  = re.compile(r"^>\s?")

IC_OPEN  = '\xa7IC_'
IC_CLOSE = '\xa7'


# ─── Markdown parser ─────────────────────────────────────────────────

def parse_md(md):
    md = md.replace('\r\n', '\n').replace('\r', '\n')

    blocks = []
    def grab_block(m):
        content = m.group(1)
        if content.startswith('\n'):
            content = content[1:]
        if content.endswith('\n'):
            content = content[:-1]
        blocks.append(content)
        return '\n__CB_%d__\n' % (len(blocks) - 1)
    md = re.sub(r'```[^\n]*\n(.*?)```', grab_block, md, flags=re.DOTALL)

    inlines = []
    def grab_inline(m):
        inlines.append(m.group(1))
        return '%s%d%s' % (IC_OPEN, len(inlines) - 1, IC_CLOSE)
    md = re.sub(r'`([^`\n]+)`', grab_inline, md)

    md = md.replace('`', '')

    lines = md.split('\n')
    out = []
    i = 0
    while i < len(lines):
        s = lines[i].strip()

        cm = re.match(r'^__CB_(\d+)__$', s)
        if cm:
            out.append('<pre><code>%s</code></pre>' % esc(blocks[int(cm.group(1))]))
            i += 1
            continue

        if re.match(r'^(\*{3,}|-{3,}|_{3,})$', s):
            out.append('<hr>')
            i += 1
            continue

        hm = re.match(r'^(#{1,6})\s+(.+)$', s)
        if hm:
            lvl = len(hm.group(1))
            out.append('<h%d>%s</h%d>' % (lvl, inline(hm.group(2), inlines), lvl))
            i += 1
            continue

        if s.startswith('>'):
            rows = []
            while i < len(lines) and lines[i].strip().startswith('>'):
                clean = BQ_PREFIX.sub('', lines[i].strip())
                if clean == '':
                    rows.append('<br><br>')
                else:
                    rows.append(inline(clean, inlines))
                i += 1
            out.append('<blockquote>%s</blockquote>' % ''.join(rows))
            continue

        if UL_PREFIX.match(s):
            items = []
            while i < len(lines) and UL_PREFIX.match(lines[i].strip()):
                clean = UL_PREFIX.sub('', lines[i].strip())
                items.append('<li>%s</li>' % inline(clean, inlines))
                i += 1
            out.append('<ul>%s</ul>' % ''.join(items))
            continue

        if OL_PREFIX.match(s):
            items = []
            while i < len(lines) and OL_PREFIX.match(lines[i].strip()):
                clean = OL_PREFIX.sub('', lines[i].strip())
                items.append('<li>%s</li>' % inline(clean, inlines))
                i += 1
            out.append('<ol>%s</ol>' % ''.join(items))
            continue

        if s == '':
            i += 1
            continue

        para = []
        while i < len(lines):
            s2 = lines[i].strip()
            if s2 == '':
                break
            if (re.match(r'^#{1,6}\s', s2) or UL_PREFIX.match(s2) or
                OL_PREFIX.match(s2) or s2.startswith('>') or
                re.match(r'^(\*{3,}|-{3,}|_{3,})$', s2) or
                re.match(r'^__CB_\d+__$', s2)):
                break
            para.append(inline(s2, inlines))
            i += 1
        if para:
            out.append('<p>%s</p>' % ' '.join(para))

    return '\n'.join(out)


def inline(text, inlines):
    text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', r'<img src="\2" alt="\1">', text)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'(?<!\w)__(.+?)__(?!\w)', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    text = re.sub(r'(?<!\w)_(.+?)_(?!\w)', r'<em>\1</em>', text)
    def restore(m):
        return '<code>%s</code>' % esc(inlines[int(m.group(1))])
    pattern = '%s(\\d+)%s' % (re.escape(IC_OPEN), re.escape(IC_CLOSE))
    text = re.sub(pattern, restore, text)
    return text


# ─── Index updater ────────────────────────────────────────────────────

def update_index(title, slug, post_date):
    if not os.path.exists(INDEX_FILE):
        print("  Warning: %s not found, skipping index update." % INDEX_FILE)
        return

    with open(INDEX_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    if slug in content:
        print("  '%s' already in %s, skipping." % (slug, INDEX_FILE))
        return

    entry = '\n        {\n            title: "%s",\n            date: "%s",\n            slug: "%s"\n        },' % (title, post_date, slug)

    marker = 'const posts = ['
    if marker not in content:
        print("  Warning: posts array not found in %s." % INDEX_FILE)
        return

    idx = content.index(marker)
    bracket = content.index(']', idx)
    between = content[idx + len(marker):bracket].strip()

    if between == '':
        entry = entry.rstrip(',')
        insert = content[:bracket] + entry + '\n    ' + content[bracket:]
    else:
        insert = content[:bracket] + entry + '\n    ' + content[bracket:]

    with open(INDEX_FILE, 'w', encoding='utf-8') as f:
        f.write(insert)

    print("  Updated %s" % INDEX_FILE)


# ─── Main ─────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Usage: python new-post.py <file.md> [--date YYYY-MM-DD]")
        sys.exit(1)

    path = sys.argv[1]
    if not os.path.exists(path):
        print("Error: '%s' not found." % path)
        sys.exit(1)

    post_date = date.today().isoformat()
    if '--date' in sys.argv:
        di = sys.argv.index('--date')
        if di + 1 < len(sys.argv):
            post_date = sys.argv[di + 1]

    with open(path, 'r', encoding='utf-8') as f:
        md = f.read()

    title = extract_title(md)
    slug = slugify(title)
    body = parse_md(md)
    date_display = date.fromisoformat(post_date).strftime('%B %d, %Y')

    html = TEMPLATE.replace('__TITLE__', title)
    html = html.replace('__DATE__', date_display)
    html = html.replace('__BODY__', body)
    html = html.replace('__BLOG_NAME__', BLOG_NAME)

    os.makedirs(POSTS_DIR, exist_ok=True)
    out = os.path.join(POSTS_DIR, '%s.html' % slug)

    with open(out, 'w', encoding='utf-8') as f:
        f.write(html)

    print("  Created: %s" % out)
    print("  Title:   %s" % title)
    print("  Slug:    %s" % slug)
    print("  Date:    %s" % post_date)

    update_index(title, slug, post_date)
    print("  Done. Review the files, then commit and push.")


if __name__ == '__main__':
    main()