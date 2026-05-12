"""
CN_Spark_workflow.workflow

Implements the diagram-focused workflow:
- extract 3-5 research keywords from input text
- (optionally) visit provided URLs to collect candidate papers
- extract images from PDFs/pages and detect diagram-like images
- convert identified diagrams to a simple SVG flow representation

Notes:
- Network/page download and OCR/image-text extraction are optional features
  that require extra packages (`requests`, `beautifulsoup4`, `pytesseract`, etc.).
- System tool `pdftoppm` can be used to rasterize PDF pages if available.
"""
import os
import re
import json
import subprocess
from collections import Counter
from typing import List

from PIL import Image, ImageFilter

STOPWORDS = set(["the","and","of","in","to","a","for","with","on","by","is","are","this","that","we","our"])


def extract_keywords_from_text(text: str, top_n: int = 5) -> List[str]:
    tokens = re.findall(r"[A-Za-z\u4e00-\u9fff]+", text.lower())
    tokens = [t for t in tokens if t not in STOPWORDS and len(t) > 1]
    counts = Counter(tokens)
    common = [w for w, _ in counts.most_common(top_n)]
    return common


def pdf_to_images(pdf_path: str, out_dir: str) -> List[str]:
    """Use `pdftoppm` if present to convert each page to a PNG.
    Returns list of image paths."""
    os.makedirs(out_dir, exist_ok=True)
    base = os.path.splitext(os.path.basename(pdf_path))[0]
    out_pattern = os.path.join(out_dir, base)
    cmd = ["pdftoppm", "-png", pdf_path, out_pattern]
    try:
        subprocess.run(cmd, check=True)
    except Exception:
        raise RuntimeError("pdftoppm failed or not installed; install it or use another extractor")
    imgs = sorted([os.path.join(out_dir, f) for f in os.listdir(out_dir) if f.startswith(base) and f.endswith('.png')])
    return imgs


def is_diagram_image(image_path: str, edge_threshold: float = 0.07) -> bool:
    """Heuristic: compute edge density to detect diagrams (many straight edges)."""
    im = Image.open(image_path).convert('L')
    edges = im.filter(ImageFilter.FIND_EDGES)
    arr = edges.resize((200, 200))
    px = arr.getdata()
    mean = sum(px) / len(px) / 255.0
    return mean > edge_threshold


def generate_svg_flow(nodes: List[str], edges: List[tuple], out_path: str):
    """Write a minimal SVG flow: nodes as rounded rects, edges as lines with arrowheads."""
    from xml.etree.ElementTree import Element, SubElement, tostring

    width = 1200
    height = max(200, 120 * len(nodes))
    svg = Element('svg', xmlns='http://www.w3.org/2000/svg', width=str(width), height=str(height))

    node_w = 300
    node_h = 60
    gap = 30

    coords = {}
    for i, n in enumerate(nodes):
        x = (width - node_w) // 2
        y = gap + i * (node_h + gap)
        coords[i] = (x, y)
        g = SubElement(svg, 'g')
        rect = SubElement(g, 'rect', x=str(x), y=str(y), width=str(node_w), height=str(node_h), rx='8', ry='8', fill='#4472C4')
        text = SubElement(g, 'text', x=str(x + node_w/2), y=str(y + node_h/2 + 6), fill='#FFFFFF', **{'text-anchor':'middle', 'font-size':'14', 'font-family':'Arial'})
        text.text = n

    for (a, b) in edges:
        xa, ya = coords[a]
        xb, yb = coords[b]
        x1 = xa + node_w/2
        y1 = ya + node_h
        x2 = xb + node_w/2
        y2 = yb
        line = SubElement(svg, 'line', x1=str(x1), y1=str(y1), x2=str(x2), y2=str(y2), stroke='#333333', **{'stroke-width':'2'})

    xml = tostring(svg, encoding='utf-8')
    with open(out_path, 'wb') as f:
        f.write(xml)


# Default seed URLs (embedded JSON-like structure) — priority search targets
def _load_seed_sites_from_refs():
    data = []
    try:
        # Try a few likely locations for seed_sites.json so path changes don't break usage
        candidates = [
            os.path.join(os.path.dirname(__file__), '..', 'references', 'seed_sites.json'),
            os.path.join(os.path.dirname(__file__), '..', '..', 'references', 'seed_sites.json'),
            os.path.join(os.getcwd(), 'CN_Spark_workflow', 'references', 'seed_sites.json'),
            os.path.join(os.getcwd(), 'references', 'seed_sites.json'),
        ]
        for p in candidates:
            seed_file = os.path.normpath(p)
            if os.path.exists(seed_file):
                with open(seed_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Support two formats:
                    # 1) list of site objects (legacy)
                    # 2) object with 'sites' array and optional 'comment' (preferred)
                    if isinstance(data, dict) and 'sites' in data and isinstance(data['sites'], list):
                        return data['sites']
                    if isinstance(data, list) and data:
                        # legacy list format
                        return data
    except Exception:
        pass
    # If no JSON found or parse failed, return an empty list so callers can decide fallback behavior.
    return data


# Load DEFAULT_SEED_SITES from references/seed_sites.json if available
DEFAULT_SEED_SITES = _load_seed_sites_from_refs()


def _try_import_requests_bs4():
    try:
        import requests
        from bs4 import BeautifulSoup
        return requests, BeautifulSoup
    except Exception:
        return None, None


def search_seed_sites(keywords: List[str], seed_sites=None, max_results=20) -> List[dict]:
    """Attempt to query the priority seed sites for the given keywords.
    Returns a list of paper metadata dicts {title, url, source}.

    This function uses `requests` + `bs4` if available; otherwise it will
    return an empty list but still provide the constructed search URLs.
    """
    requests, BeautifulSoup = _try_import_requests_bs4()
    q = "+".join(keywords)
    # Normalize seed_sites: allow None, list of dicts, or list of url strings
    raw_sites = seed_sites if seed_sites is not None else DEFAULT_SEED_SITES
    sites = []
    if isinstance(raw_sites, list):
        for s in raw_sites:
            if isinstance(s, dict) and 'search_template' in s:
                sites.append(s)
            elif isinstance(s, str):
                url = s
                # If the template already contains {q}, keep it. Otherwise append query param.
                if '{q}' not in url:
                    if '?' in url:
                        url = url + '&q={q}'
                    else:
                        url = url + '?q={q}'
                name = re.sub(r"https?://(www\.)?", "", s).split('/')[0]
                sites.append({"name": name, "search_template": url})
    # If still empty, no seed sites available
    if not sites:
        sites = []
    results = []

    for site in sites:
        search_url = site["search_template"].format(q=q)
        # If requests not available, append the search URL as a reference and continue
        if not requests:
            results.append({"title": f"Search: {q}", "url": search_url, "source": site["name"]})
            continue

        try:
            headers = {"User-Agent": "Mozilla/5.0 (compatible; CN_Spark_Workflow/1.0)"}
            resp = requests.get(search_url, timeout=10, headers=headers)
            if resp.status_code != 200:
                results.append({"title": f"Search page (status {resp.status_code})", "url": search_url, "source": site["name"]})
                continue

            if not BeautifulSoup:
                results.append({"title": f"Search: {q}", "url": search_url, "source": site["name"]})
                continue

            soup = BeautifulSoup(resp.text, "html.parser")
            # Best-effort extraction of links and titles
            anchors = soup.find_all('a', href=True)
            count = 0
            for a in anchors:
                href = a['href']
                text = (a.get_text() or '').strip()
                if not text or len(text) < 8:
                    continue
                # Normalize relative links
                if href.startswith('/'):
                    base = requests.utils.urlparse(search_url)
                    href = f"{base.scheme}://{base.netloc}{href}"
                results.append({"title": text, "url": href, "source": site["name"]})
                count += 1
                if count >= max_results:
                    break
        except Exception:
            # On any failure, add the search URL as fallback reference
            results.append({"title": f"Search fallback: {q}", "url": search_url, "source": site["name"]})

    return results


def supplement_search_all_web(keywords: List[str], needed: int = 0, max_results: int = 50) -> List[dict]:
    """Supplemental web search when seed sites returned too few results.
    Uses a generic search (Bing) if available; otherwise returns empty list.
    """
    requests, BeautifulSoup = _try_import_requests_bs4()
    if not requests:
        return []
    q = "+".join(keywords)
    search_url = f"https://www.bing.com/search?q={q}"
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; CN_Spark_Workflow/1.0)"}
        resp = requests.get(search_url, timeout=10, headers=headers)
        if resp.status_code != 200:
            return []
        if not BeautifulSoup:
            return []
        soup = BeautifulSoup(resp.text, "html.parser")
        results = []
        for h in soup.select('li.b_algo h2 a'):
            title = h.get_text().strip()
            href = h.get('href')
            results.append({"title": title, "url": href, "source": "bing"})
            if needed and len(results) >= needed:
                break
            if len(results) >= max_results:
                break
        return results
    except Exception:
        return []


def run_workflow_extract_svg(input_text: str = None, pdf_paths: List[str] = None, seed_urls: List[str] = None, out_dir: str = 'workflow_output') -> dict:
    """High-level orchestration for the workflow.
    Returns a dict with keywords, candidate_images, svg_paths.
    """
    os.makedirs(out_dir, exist_ok=True)
    result = {'keywords': [], 'images': [], 'svgs': []}

    if input_text:
        kws = extract_keywords_from_text(input_text, top_n=5)
        result['keywords'] = kws

    # Determine seed sites to use for searching. Accepts either:
    # - seed_urls: a list of site objects (with 'search_template')
    # - seed_urls: a list of plain search URLs (strings)
    # - None: load from references/seed_sites.json automatically
    seed_sites = None
    if seed_urls:
        seed_sites = seed_urls
    else:
        seed_sites = _load_seed_sites_from_refs()

    image_candidates = []
    if pdf_paths:
        for p in pdf_paths:
            imgs = pdf_to_images(p, out_dir)
            for im in imgs:
                if is_diagram_image(im):
                    image_candidates.append(im)

    result['images'] = image_candidates

    # Search priority seed sites for related papers (if keywords available)
    found_papers = []
    if result.get('keywords'):
        found_papers = search_seed_sites(result['keywords'], seed_sites=seed_sites)

    # If found papers <= 8, supplement with a general web search
    if len(found_papers) <= 8:
        needed = max(0, 8 - len(found_papers))
        supplemental = supplement_search_all_web(result.get('keywords', []), needed=needed)
        found_papers.extend(supplemental)

    result['papers'] = found_papers

    # For each detected image, create a simple SVG placeholder (in practice you'd parse nodes/edges)
    for i, img in enumerate(image_candidates):
        svg_out = os.path.join(out_dir, f'detected_diagram_{i}.svg')
        generate_svg_flow([f'Node {j+1}' for j in range(3)], [(0,1),(1,2)], svg_out)
        result['svgs'].append(svg_out)

    return result
