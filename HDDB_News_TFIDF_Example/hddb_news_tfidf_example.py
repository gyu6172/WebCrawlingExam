"""HDDB news crawling + TF-IDF example.

Purpose:
1. Crawl real news articles from RSS feeds.
2. Keep articles that match HDDB's nature categories.
3. Print crawled article previews.
4. Compute a TF-IDF matrix and print top_keywords for each article.

This is an experiment file, not HDDB production backend code yet. Later, the
functions here can be split into backend/app/crawler and backend/app/tasks.
"""

from __future__ import annotations

import argparse
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from html import escape
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import pandas as pd
import requests
from bs4 import BeautifulSoup, FeatureNotFound
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer

USER_AGENT = (
    "HDDB-News-TFIDF-Example/0.2 "
    "(student prototype; respectful RSS/article crawling)"
)

RSS_FEEDS = [
    {
        "source": "NASA News Releases",
        "url": "https://www.nasa.gov/news-release/feed/",
    },
    {
        "source": "ScienceDaily Oceanography",
        "url": "https://www.sciencedaily.com/rss/earth_climate/oceanography.xml",
    },
    {
        "source": "ScienceDaily Earth & Climate",
        "url": "https://www.sciencedaily.com/rss/earth_climate.xml",
    },
    {
        "source": "ScienceDaily Plants & Animals",
        "url": "https://www.sciencedaily.com/rss/plants_animals.xml",
    },
    {
        "source": "ScienceDaily Marine Biology",
        "url": "https://www.sciencedaily.com/rss/plants_animals/marine_biology.xml",
    },
    {
        "source": "ScienceDaily Space & Time",
        "url": "https://www.sciencedaily.com/rss/space_time.xml",
    },
]

HDDB_KEYWORDS = {
    "sky": {
        "새": [
            "bird",
            "birds",
            "avian",
            "migration",
            "migratory",
            "nest",
            "habitat",
            "철새",
            "조류",
            "새",
        ],
        "우주": [
            "space",
            "planet",
            "exoplanet",
            "asteroid",
            "comet",
            "telescope",
            "galaxy",
            "mars",
            "moon",
            "solar",
            "우주",
            "행성",
            "망원경",
        ],
        "대기오염": [
            "air pollution",
            "air quality",
            "particulate",
            "aerosol",
            "smog",
            "ozone",
            "fine dust",
            "미세먼지",
            "초미세먼지",
            "황사",
            "대기질",
        ],
        "기상": [
            "weather",
            "climate",
            "climate change",
            "storm",
            "hurricane",
            "typhoon",
            "rainfall",
            "heat wave",
            "temperature",
            "forecast",
            "태풍",
            "폭염",
            "호우",
            "장마",
            "기온",
        ],
    },
    "land": {
        "자연재해": [
            "wildfire",
            "flood",
            "drought",
            "landslide",
            "disaster",
            "hazard",
            "산불",
            "홍수",
            "가뭄",
            "산사태",
            "자연재해",
        ],
        "동식물": [
            "wildlife",
            "animal",
            "animals",
            "plant",
            "plants",
            "forest",
            "biodiversity",
            "species",
            "ecosystem",
            "conservation",
            "fossil",
            "fossils",
            "dinosaur",
            "paleontology",
            "evolution",
            "동물",
            "식물",
            "숲",
            "생태계",
            "멸종",
        ],
        "화산/지진": [
            "earthquake",
            "earthquakes",
            "volcano",
            "volcanic",
            "eruption",
            "magma",
            "seismic",
            "fault",
            "지진",
            "화산",
            "분화",
            "마그마",
        ],
        "환경오염": [
            "pollution",
            "waste",
            "toxic",
            "chemical",
            "environment",
            "environmental",
            "soil contamination",
            "contamination",
            "환경오염",
            "토양오염",
            "폐기물",
            "화학물질",
        ],
    },
    "sea": {
        "물고기": [
            "fish",
            "fisheries",
            "fishing",
            "salmon",
            "tuna",
            "aquaculture",
            "spawn",
            "물고기",
            "어류",
            "어획",
            "양식",
        ],
        "심해": [
            "deep sea",
            "deep-sea",
            "seafloor",
            "underwater",
            "submersible",
            "trench",
            "hydrothermal",
            "심해",
            "해구",
            "해저",
            "잠수정",
        ],
        "해양오염": [
            "marine pollution",
            "ocean pollution",
            "plastic",
            "microplastic",
            "microplastics",
            "oil spill",
            "marine debris",
            "algal bloom",
            "해양오염",
            "미세플라스틱",
            "해양쓰레기",
            "기름 유출",
            "적조",
        ],
        "해양생물": [
            "ocean",
            "marine",
            "coral",
            "reef",
            "whale",
            "dolphin",
            "plankton",
            "sea turtle",
            "coastal",
            "해양생물",
            "산호",
            "고래",
            "돌고래",
            "플랑크톤",
        ],
    },
}

STOP_WORDS = [
    "about",
    "after",
    "also",
    "and",
    "are",
    "because",
    "been",
    "being",
    "but",
    "can",
    "could",
    "from",
    "had",
    "has",
    "have",
    "into",
    "its",
    "may",
    "more",
    "news",
    "not",
    "over",
    "said",
    "says",
    "science",
    "scientists",
    "study",
    "than",
    "that",
    "the",
    "their",
    "them",
    "these",
    "they",
    "this",
    "those",
    "through",
    "was",
    "were",
    "which",
    "while",
    "with",
    "world",
    "연구",
    "이번",
    "관련",
    "따르면",
    "밝혔다",
    "대한",
    "위해",
]


@dataclass
class NewsArticle:
    title: str
    source: str
    source_url: str
    published_at: str
    rss_summary: str
    body: str
    category: str
    subcategory: str
    confidence: float

    @property
    def analysis_text(self) -> str:
        return " ".join([self.title, self.rss_summary, self.body]).strip()


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def clean_html_text(text: str) -> str:
    return normalize_space(BeautifulSoup(text or "", "html.parser").get_text(" "))


def canonicalize_url(url: str) -> str:
    """Remove tracking parameters so duplicate article URLs compare better."""
    parsed = urlsplit(url.strip())
    clean_query = urlencode(
        [
            (key, value)
            for key, value in parse_qsl(parsed.query, keep_blank_values=True)
            if not key.lower().startswith("utm_")
            and key.lower() not in {"fbclid", "gclid", "mc_cid", "mc_eid"}
        ]
    )
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, clean_query, ""))


def get_text_or_empty(tag) -> str:
    return clean_html_text(tag.get_text(" ")) if tag else ""


def fetch_url(url: str, timeout: int = 15) -> str:
    response = requests.get(
        url,
        headers={"User-Agent": USER_AGENT},
        timeout=timeout,
    )
    response.raise_for_status()
    return response.text


def parse_rss_entries(
    source: str, feed_url: str, per_feed: int
) -> list[dict[str, str]]:
    """Read one RSS feed and return normalized article metadata."""
    try:
        feed_text = fetch_url(feed_url)
    except requests.RequestException as exc:
        print(f"[warn] RSS fetch failed: {source} ({exc})", file=sys.stderr)
        return []

    try:
        soup = BeautifulSoup(feed_text, "xml")
    except FeatureNotFound:
        print(
            "[warn] XML parser is missing. Install lxml for cleaner RSS parsing: "
            "pip install lxml. Falling back to html.parser.",
            file=sys.stderr,
        )
        soup = BeautifulSoup(feed_text, "html.parser")
    nodes = soup.find_all("item") or soup.find_all("entry")
    entries = []

    for node in nodes[:per_feed]:
        title = get_text_or_empty(node.find("title"))
        link_tag = node.find("link")
        link = ""
        if link_tag:
            link = link_tag.get("href") or normalize_space(link_tag.get_text(" "))

        summary = get_text_or_empty(
            node.find("description") or node.find("summary") or node.find("content")
        )
        published_at = get_text_or_empty(
            node.find("pubDate") or node.find("published") or node.find("updated")
        )

        if title and link:
            entries.append(
                {
                    "title": title,
                    "source": source,
                    "source_url": canonicalize_url(link),
                    "published_at": published_at,
                    "rss_summary": summary,
                }
            )

    return entries


def count_keyword(text: str, keyword: str) -> int:
    text = text.lower()
    keyword = keyword.lower()

    if re.fullmatch(r"[a-z0-9][a-z0-9 -]*", keyword):
        pattern = r"(?<![a-z0-9])" + re.escape(keyword) + r"(?![a-z0-9])"
        return len(re.findall(pattern, text))

    return text.count(keyword)


def classify_hddb_category(
    title: str, summary: str, body: str = ""
) -> tuple[str, str, float, float]:
    """Classify text into HDDB category/subcategory using weighted keyword scores."""
    scores = {}

    for category, subcategories in HDDB_KEYWORDS.items():
        for subcategory, keywords in subcategories.items():
            score = 0.0
            for keyword in keywords:
                score += count_keyword(title, keyword) * 3.0
                score += count_keyword(summary, keyword) * 2.0
                score += count_keyword(body, keyword) * 1.0
            scores[(category, subcategory)] = score

    (category, subcategory), best_score = max(scores.items(), key=lambda item: item[1])
    if best_score <= 0:
        return "", "", 0.0, 0.0

    confidence = best_score / sum(scores.values())
    return category, subcategory, confidence, best_score


def fetch_article_body(url: str, max_paragraphs: int = 8) -> str:
    """Fetch article HTML and extract readable paragraph text."""
    try:
        html = fetch_url(url)
    except requests.RequestException as exc:
        print(f"[warn] article fetch failed: {url} ({exc})", file=sys.stderr)
        return ""

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()

    paragraphs = [
        normalize_space(p.get_text(" "))
        for p in soup.find_all("p")
        if len(normalize_space(p.get_text(" "))) >= 80
    ]
    return "\n".join(paragraphs[:max_paragraphs])


def crawl_articles(
    *,
    max_articles: int,
    per_feed: int,
    min_score: float,
    include_body: bool,
    polite_delay: float,
) -> list[NewsArticle]:
    """Collect RSS entries, filter them, optionally fetch full article bodies."""
    feed_entries = [
        (feed["source"], parse_rss_entries(feed["source"], feed["url"], per_feed))
        for feed in RSS_FEEDS
    ]
    seen_urls = set()
    articles = []

    for index in range(per_feed):
        for source, entries in feed_entries:
            if index >= len(entries):
                continue

            entry = entries[index]
            if entry["source_url"] in seen_urls:
                continue
            seen_urls.add(entry["source_url"])

            first_category, first_subcategory, first_confidence, first_score = (
                classify_hddb_category(entry["title"], entry["rss_summary"])
            )
            if first_score < min_score:
                continue

            body = fetch_article_body(entry["source_url"]) if include_body else ""
            if include_body and polite_delay > 0:
                time.sleep(polite_delay)

            category, subcategory, confidence, score = classify_hddb_category(
                entry["title"],
                entry["rss_summary"],
                body,
            )
            if not body:
                category, subcategory, confidence, score = (
                    first_category,
                    first_subcategory,
                    first_confidence,
                    first_score,
                )
            if score < min_score:
                continue

            articles.append(
                NewsArticle(
                    title=entry["title"],
                    source=source,
                    source_url=entry["source_url"],
                    published_at=entry["published_at"],
                    rss_summary=entry["rss_summary"],
                    body=body,
                    category=category,
                    subcategory=subcategory,
                    confidence=confidence,
                )
            )

            if len(articles) >= max_articles:
                return articles

    return articles


def build_tfidf(articles: list[NewsArticle], max_features: int):
    """Compute TF-IDF matrix using the same core idea as the previous notebook."""
    corpus = [article.analysis_text for article in articles]
    vectorizer = TfidfVectorizer(
        max_features=max_features,
        stop_words=list(ENGLISH_STOP_WORDS.union(STOP_WORDS)),
        token_pattern=r"(?u)\b[a-zA-Z][a-zA-Z-]{2,}\b|[가-힣]{2,}",
        lowercase=True,
    )
    tfidf_matrix = vectorizer.fit_transform(corpus)
    feature_names = vectorizer.get_feature_names_out()
    return vectorizer, tfidf_matrix, feature_names


def extract_top_keywords(
    tfidf_matrix, feature_names, top_k: int
) -> list[list[tuple[str, float]]]:
    top_keywords = []

    for row_index in range(tfidf_matrix.shape[0]):
        row = tfidf_matrix[row_index].toarray().flatten()
        top_indices = row.argsort()[-top_k:][::-1]
        keywords = [
            (feature_names[index], row[index])
            for index in top_indices
            if row[index] > 0
        ]
        top_keywords.append(keywords)

    return top_keywords


def build_result_rows(
    articles: list[NewsArticle],
    top_keywords: list[list[tuple[str, float]]],
) -> list[dict[str, object]]:
    rows = []
    for article, keywords in zip(articles, top_keywords, strict=True):
        preview = normalize_space(article.body or article.rss_summary)[:500]
        rows.append(
            {
                "title": article.title,
                "source": article.source,
                "source_url": article.source_url,
                "published_at": article.published_at,
                "category": article.category,
                "subcategory": article.subcategory,
                "confidence": round(article.confidence, 2),
                "top_keywords": ", ".join(word for word, _score in keywords),
                "top_keywords_with_scores": ", ".join(
                    f"{word}({score:.4f})" for word, score in keywords
                ),
                "preview": preview,
            }
        )
    return rows


def save_outputs(
    articles: list[NewsArticle],
    tfidf_matrix,
    top_keywords: list[list[tuple[str, float]]],
    output_dir: Path,
) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    rows = build_result_rows(articles, top_keywords)

    df = pd.DataFrame(rows)
    csv_path = output_dir / f"hddb_news_tfidf_results_{timestamp}.csv"
    html_path = output_dir / f"hddb_news_tfidf_report_{timestamp}.html"

    df.to_csv(csv_path, index=False, encoding="utf-8-sig")

    cards = []
    for idx, (article, keywords) in enumerate(
        zip(articles, top_keywords, strict=True), 1
    ):
        preview = normalize_space(article.body or article.rss_summary)[:900]
        keyword_badges = "\n".join(
            f'<span class="keyword">{escape(word)} <b>{score:.4f}</b></span>'
            for word, score in keywords
        )
        cards.append(f"""
            <article class="card">
              <div class="card-header">
                <span class="number">{idx}</span>
                <div>
                  <h2>{escape(article.title)}</h2>
                  <p class="meta">
                    {escape(article.source)} · {escape(article.published_at or "-")}
                  </p>
                </div>
              </div>
              <div class="category">
                <span>{escape(article.category)}</span>
                <span>{escape(article.subcategory)}</span>
                <span>confidence {article.confidence:.2f}</span>
              </div>
              <p class="preview">{escape(preview)}</p>
              <div class="keywords">{keyword_badges}</div>
              <a href="{escape(article.source_url)}" target="_blank" rel="noreferrer">
                원문 열기
              </a>
            </article>
            """)

    html_text = f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>HDDB News TF-IDF Report</title>
  <style>
    body {{
      margin: 0;
      font-family: Arial, "Malgun Gothic", sans-serif;
      color: #17202a;
      background: #f6f8fb;
    }}
    main {{
      max-width: 1080px;
      margin: 0 auto;
      padding: 32px 20px 48px;
    }}
    h1 {{
      margin: 0 0 8px;
      font-size: 28px;
    }}
    .summary {{
      margin: 0 0 24px;
      color: #52616f;
    }}
    .grid {{
      display: grid;
      gap: 16px;
    }}
    .card {{
      background: #ffffff;
      border: 1px solid #dfe7ef;
      border-radius: 8px;
      padding: 18px;
    }}
    .card-header {{
      display: flex;
      gap: 12px;
      align-items: flex-start;
    }}
    .number {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 32px;
      height: 32px;
      border-radius: 50%;
      background: #123c69;
      color: #ffffff;
      font-weight: 700;
      flex: 0 0 auto;
    }}
    h2 {{
      margin: 0;
      font-size: 20px;
      line-height: 1.35;
    }}
    .meta {{
      margin: 6px 0 0;
      color: #64748b;
      font-size: 14px;
    }}
    .category {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin: 14px 0;
    }}
    .category span {{
      padding: 5px 9px;
      border-radius: 999px;
      background: #eaf3f7;
      color: #154360;
      font-size: 13px;
      font-weight: 700;
    }}
    .preview {{
      line-height: 1.65;
      margin: 0 0 14px;
    }}
    .keywords {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 14px;
    }}
    .keyword {{
      padding: 6px 9px;
      border: 1px solid #cbd5e1;
      border-radius: 6px;
      background: #f8fafc;
      font-size: 13px;
    }}
    a {{
      color: #0f5f8f;
      font-weight: 700;
      text-decoration: none;
    }}
  </style>
</head>
<body>
  <main>
    <h1>HDDB News TF-IDF Report</h1>
    <p class="summary">
      TF-IDF matrix: {tfidf_matrix.shape[0]} documents x {tfidf_matrix.shape[1]} terms ·
      generated at {escape(timestamp)}
    </p>
    <section class="grid">
      {"".join(cards)}
    </section>
  </main>
</body>
</html>
"""
    html_path.write_text(html_text, encoding="utf-8")
    return html_path, csv_path


def print_results(
    articles: list[NewsArticle],
    tfidf_matrix,
    top_keywords: list[list[tuple[str, float]]],
    html_path: Path | None,
    csv_path: Path | None,
    show_details: bool,
) -> None:
    print("\n=== TF-IDF Matrix ===")
    print(f"shape: {tfidf_matrix.shape[0]} documents x {tfidf_matrix.shape[1]} terms")

    rows = build_result_rows(articles, top_keywords)
    df = pd.DataFrame(rows)
    print("\n=== Crawled Articles Summary ===")
    print(
        df[["title", "source", "category", "subcategory", "confidence", "top_keywords"]]
    )

    if html_path and csv_path:
        print("\n=== Saved Files ===")
        print(f"HTML report: {html_path}")
        print(f"CSV results: {csv_path}")

    if not show_details:
        print(
            "\nTip: 자세한 기사 미리보기와 키워드 점수는 HTML report에서 보는 편이 편합니다."
        )
        return

    print("\n=== Article Previews ===")
    for idx, (article, keywords) in enumerate(
        zip(articles, top_keywords, strict=True), 1
    ):
        preview = normalize_space(article.body or article.rss_summary)[:260]
        keyword_text = ", ".join(f"{word}({score:.4f})" for word, score in keywords)

        print(f"\n[{idx}] {article.title}")
        print(f"source: {article.source}")
        print(f"url: {article.source_url}")
        print(f"published_at: {article.published_at or '-'}")
        print(
            "hddb_category: "
            f"{article.category} / {article.subcategory} "
            f"(confidence={article.confidence:.2f})"
        )
        print(f"preview: {preview}")
        print(f"top_keywords: {keyword_text}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Crawl real nature-related news and print TF-IDF top_keywords."
    )
    parser.add_argument("--max-articles", type=int, default=8)
    parser.add_argument("--per-feed", type=int, default=5)
    parser.add_argument("--top-k", type=int, default=8)
    parser.add_argument("--max-features", type=int, default=500)
    parser.add_argument(
        "--min-score",
        type=float,
        default=2.0,
        help="Minimum HDDB keyword score. Lower values keep more articles.",
    )
    parser.add_argument(
        "--skip-body",
        action="store_true",
        help="Use RSS title/summary only. Faster and gentler to news sites.",
    )
    parser.add_argument(
        "--polite-delay",
        type=float,
        default=0.5,
        help="Seconds to wait between article page requests.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs"),
        help="Directory for HTML/CSV result files.",
    )
    parser.add_argument(
        "--no-files",
        action="store_true",
        help="Do not create HTML/CSV files; print summary only.",
    )
    parser.add_argument(
        "--console-details",
        action="store_true",
        help="Print long article previews in the terminal.",
    )
    return parser.parse_args()


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    args = parse_args()
    articles = crawl_articles(
        max_articles=args.max_articles,
        per_feed=args.per_feed,
        min_score=args.min_score,
        include_body=not args.skip_body,
        polite_delay=args.polite_delay,
    )

    if not articles:
        print("No articles were crawled. Try --skip-body or lower --min-score.")
        return 1

    _vectorizer, tfidf_matrix, feature_names = build_tfidf(
        articles,
        max_features=args.max_features,
    )
    top_keywords = extract_top_keywords(tfidf_matrix, feature_names, args.top_k)

    html_path = None
    csv_path = None
    if not args.no_files:
        html_path, csv_path = save_outputs(
            articles,
            tfidf_matrix,
            top_keywords,
            args.output_dir,
        )

    print_results(
        articles,
        tfidf_matrix,
        top_keywords,
        html_path,
        csv_path,
        args.console_details,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
