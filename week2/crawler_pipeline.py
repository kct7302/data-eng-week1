
from __future__ import annotations

import time
from datetime import datetime

import pymysql
import requests
from bs4 import BeautifulSoup

BASE = 'https://quotes.toscrape.com'
HEADERS = {'User-Agent': 'data-eng-class-crawler/1.0 (learning purpose)'}
DELAY_SEC = 1.0

# 1. DB 접속 정보 분리
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root',
    'password': 'dataeng123',
    'database': 'shop',
    'charset': 'utf8mb4'
}


# 2. 실패한 URL을 파일에 기록
def log_failed_url(url: str) -> None:
    with open('failed.log', 'a', encoding='utf-8') as f:
        f.write(f'{datetime.now()} | {url}\n')


def fetch(url: str, retries: int = 3) -> str:
    last_error = None

    for attempt in range(1, retries + 1):
        try:
            res = requests.get(url, headers=HEADERS, timeout=10)

            if res.status_code == 429:
                print(f'429 too many requests - {attempt}회차, 5초 대기')
                time.sleep(5)
                continue

            res.raise_for_status()
            return res.text

        except requests.RequestException as e:
            last_error = e
            print(f'요청 실패({attempt}/{retries}): {e}')
            time.sleep(2 * attempt)

    # 최종 실패한 URL 기록
    log_failed_url(url)
    raise RuntimeError(f'{url} 수집 실패') from last_error


def parse(html: str) -> tuple[list[dict], str | None]:
    soup = BeautifulSoup(html, 'html.parser')
    rows = []

    for q in soup.select('div.quote'):
        rows.append({
            'author': q.select_one('small.author').get_text(strip=True),
            'quote_text': q.select_one('span.text').get_text(strip=True),
            'tags': ','.join(
                t.get_text(strip=True) for t in q.select('a.tag')
            ),
        })

    next_link = soup.select_one('li.next a')
    next_url = BASE + next_link['href'] if next_link else None

    return rows, next_url


# 3. DB 연결을 인자로 받아 재사용
def load(conn, rows: list[dict]) -> int:
    saved = 0

    with conn.cursor() as cur:
        for r in rows:
            saved += cur.execute(
                'INSERT IGNORE INTO quotes '
                '(author, quote_text, tags, crawled_at) '
                'VALUES (%s, %s, %s, %s)',
                (
                    r['author'],
                    r['quote_text'],
                    r['tags'],
                    datetime.now()
                ),
            )

    conn.commit()
    return saved


def run(max_pages: int = 10) -> None:
    url = BASE + '/'

    # 4. DB 연결은 최초 한 번만 생성
    conn = pymysql.connect(**DB_CONFIG)

    try:
        for page in range(1, max_pages + 1):
            html = fetch(url)
            rows, next_url = parse(html)

            # 동일한 DB 연결 재사용
            saved = load(conn, rows)

            print(f'page {page}: parsed {len(rows)}, saved {saved}')

            if not next_url:
                break

            url = next_url
            time.sleep(DELAY_SEC)

    finally:
        # 모든 페이지 처리 후 연결 종료
        conn.close()


if __name__ == '__main__':
    run()
