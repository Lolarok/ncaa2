import json
import os
import re
from datetime import datetime, timezone
import cloudscraper
from bs4 import BeautifulSoup

REALGM_URL = "https://basketball.realgm.com/national/teams/6/Italy/ncaa_players"
TANKATHON_URL = "https://www.tankathon.com/big-board"
GITHUB_REPO = os.environ.get("GITHUB_REPOSITORY", "Lolarok/ncaa-italiani")

def get_scraper():
    return cloudscraper.create_scraper(
        browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False}
    )

def to_float(val, default=0.0):
    try:
        cleaned = re.sub(r'[^\d.-]', '', str(val))
        return float(cleaned) if cleaned else default
    except:
        return default

def slugify(text):
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')

def compute_metrics(p):
    pts, fga, fgm = p.get('pts', 0.0), p.get('fga', 0.0), p.get('fgm', 0.0)
    tpa, tpm = p.get('tpa', 0.0), p.get('tpm', 0.0)
    fta, ftm = p.get('fta', 0.0), p.get('ftm', 0.0)
    ast, tov = p.get('ast', 0.0), p.get('tov', 0.0)
    mpg = p.get('mpg', 0.0)

    tsa = fga + 0.44 * fta
    ts_pct = round((pts / (2 * tsa)) * 100, 1) if tsa > 0 else 0.0
    efg_pct = round(((fgm + 0.5 * tpm) / fga) * 100, 1) if fga > 0 else 0.0
    tov_denom = fga + 0.44 * fta + tov
    tov_pct = round((tov / tov_denom) * 100, 1) if tov_denom > 0 else 0.0
    ast_to = round(ast / tov, 2) if tov > 0 else round(ast, 2)
    ftr = round((fta / fga) * 100, 1) if fga > 0 else 0.0
    poss_used = fga + 0.44 * fta + tov
    usg_est = round(min(42.0, max(10.0, (poss_used / mpg) * 38.0)), 1) if mpg > 0 else 18.0

    two_pa = max(0.0, fga - tpa)
    two_pm = max(0.0, fgm - tpm)
    two_p_pct = round((two_pm / two_pa) * 100, 1) if two_pa > 0 else 0.0
    three_p_pct = round((tpm / tpa) * 100, 1) if tpa > 0 else 0.0
    ft_pct = round((ftm / fta) * 100, 1) if fta > 0 else 0.0

    three_par = round((tpa / fga) * 100, 1) if fga > 0 else 0.0
    two_par = round(100.0 - three_par, 1) if fga > 0 else 0.0

    rim_ratio = 0.68 if ('C' in p.get('pos', '') or ftr > 35) else 0.54
    rim_freq = round(two_par * rim_ratio, 1)
    mid_freq = round(two_par * (1.0 - rim_ratio), 1)
    rim_fg_est = round(min(78.0, two_p_pct * 1.15), 1) if two_pa > 0 else 0.0
    mid_fg_est = round(max(28.0, two_p_pct * 0.78), 1) if two_pa > 0 else 0.0

    p['advanced'] = {
        'ts_pct': ts_pct, 'efg_pct': efg_pct, 'usg_pct': usg_est,
        'ast_to': ast_to, 'tov_pct': tov_pct, 'ftr': ftr
    }
    p['shot_selection'] = {
        'rim_freq': rim_freq, 'mid_freq': mid_freq, 'three_par': three_par,
        'rim_fg': rim_fg_est, 'mid_fg': mid_fg_est,
        'two_p_pct': two_p_pct, 'three_p_pct': three_p_pct, 'ft_pct': ft_pct,
        'two_pa': round(two_pa, 1), 'tpa': round(tpa, 1), 'fta': round(fta, 1)
    }
    return p

def scrape_realgm(scraper):
    players = {}
    try:
        res = scraper.get(REALGM_URL, timeout=20)
        soup = BeautifulSoup(res.text, 'html.parser')
        for table in soup.find_all('table'):
            headers = [th.get_text(strip=True).upper() for th in table.find_all('th')]
            if 'PLAYER' not in headers:
                continue
            for tr in table.find_all('tr')[1:]:
                tds = [td.get_text(strip=True) for td in tr.find_all('td')]
                if len(tds) < 4:
                    continue
                row = dict(zip(headers, tds))
                name = row.get('PLAYER', '').strip()
                if not name:
                    continue
                pid = slugify(name)
                if pid not in players:
                    players[pid] = {
                        'id': pid, 'name': name,
                        'team': row.get('TEAM', row.get('SCHOOL', 'NCAA')),
                        'pos': row.get('POS', 'G/F'), 'height': row.get('HT', '6-6'),
                        'class_year': row.get('CLASS', 'Fr.'),
                        'is_ita': True, 'is_nba_prospect': False, 'rank_nba': None,
                        'gp': int(to_float(row.get('GP', 0))),
                        'mpg': to_float(row.get('MPG', row.get('MIN', 0))),
                        'pts': to_float(row.get('PPG', row.get('PTS', 0))),
                        'reb': to_float(row.get('RPG', row.get('REB', 0))),
                        'ast': to_float(row.get('APG', row.get('AST', 0))),
                        'stl': to_float(row.get('SPG', row.get('STL', 0))),
                        'blk': to_float(row.get('BPG', row.get('BLK', 0))),
                        'tov': to_float(row.get('TOV', row.get('TO', 1.5))),
                        'fgm': to_float(row.get('FGM', 0)), 'fga': to_float(row.get('FGA', 0)),
                        'tpm': to_float(row.get('3PM', 0)), 'tpa': to_float(row.get('3PA', 0)),
                        'ftm': to_float(row.get('FTM', 0)), 'fta': to_float(row.get('FTA', 0))
                    }
                elif 'PPG' in row or 'PTS' in row:
                    players[pid].update({
                        'gp': int(to_float(row.get('GP', players[pid]['gp']))),
                        'mpg': to_float(row.get('MPG', row.get('MIN', players[pid]['mpg']))),
                        'pts': to_float(row.get('PPG', row.get('PTS', 0))),
                        'reb': to_float(row.get('RPG', row.get('REB', 0))),
                        'ast': to_float(row.get('APG', row.get('AST', 0))),
                        'fgm': to_float(row.get('FGM', 0)), 'fga': to_float(row.get('FGA', 0)),
                        'tpm': to_float(row.get('3PM', 0)), 'tpa': to_float(row.get('3PA', 0)),
                        'ftm': to_float(row.get('FTM', 0)), 'fta': to_float(row.get('FTA', 0))
                    })
    except Exception as e:
        print(f"Avviso RealGM: {e}")
    return players

def scrape_tankathon(scraper, players):
    try:
        res = scraper.get(TANKATHON_URL, timeout=20)
        soup = BeautifulSoup(res.text, 'html.parser')
        rank = 1
        for r in soup.select('.mock-row, .big-board-row, tr'):
            name_el = r.select_one('.mock-row-name, .player-name')
            if not name_el:
                continue
            name = name_el.get_text(strip=True)
            pid = slugify(name)
            info_el = r.select_one('.mock-row-school-position, .school-position')
            info_txt = info_el.get_text(strip=True) if info_el else "G/F | NCAA"
            parts = [x.strip() for x in info_txt.split('|')]
            pos = parts[0] if len(parts) > 0 else "G/F"
            team = parts[1] if len(parts) > 1 else "NCAA"

            if pid in players:
                players[pid]['is_nba_prospect'] = True
                players[pid]['rank_nba'] = rank
            else:
                players[pid] = {
                    'id': pid, 'name': name, 'team': team, 'pos': pos,
                    'height': '6-7', 'class_year': 'Fr.',
                    'is_ita': False, 'is_nba_prospect': True, 'rank_nba': rank,
                    'gp': 1, 'mpg': 28.0, 'pts': 15.0, 'reb': 5.5, 'ast': 3.2,
                    'stl': 1.2, 'blk': 0.8, 'tov': 2.1,
                    'fgm': 5.4, 'fga': 11.2, 'tpm': 1.6, 'tpa': 4.5, 'ftm': 2.6, 'fta': 3.4
                }
            rank += 1
    except Exception as e:
        print(f"Avviso Tankathon: {e}")
    return players

def get_seed_dataset():
    raw = [
        {"name": "Dame Sarr", "team": "Duke", "pos": "SG/SF", "height": "6-7", "class_year": "Fr.", "is_ita": True, "is_nba_prospect": True, "rank_nba": 40, "gp": 2, "mpg": 24.5, "pts": 12.5, "reb": 4.0, "ast": 2.5, "stl": 1.5, "blk": 0.5, "tov": 1.5, "fgm": 4.5, "fga": 9.5, "tpm": 2.0, "tpa": 5.0, "ftm": 1.5, "fta": 2.0},
        {"name": "Luigi Suigo", "team": "Villanova", "pos": "C", "height": "7-2", "class_year": "Fr.", "is_ita": True, "is_nba_prospect": True, "rank_nba": 18, "gp": 2, "mpg": 22.0, "pts": 11.0, "reb": 7.5, "ast": 1.0, "stl": 0.5, "blk": 2.5, "tov": 1.5, "fgm": 4.5, "fga": 7.5, "tpm": 0.5, "tpa": 1.5, "ftm": 1.5, "fta": 2.5},
        {"name": "Saliou Niang", "team": "LSU", "pos": "SF", "height": "6-6", "class_year": "Fr.", "is_ita": True, "is_nba_prospect": False, "rank_nba": None, "gp": 2, "mpg": 26.0, "pts": 13.0, "reb": 6.0, "ast": 2.0, "stl": 1.5, "blk": 1.0, "tov": 2.0, "fgm": 5.0, "fga": 9.5, "tpm": 1.0, "tpa": 3.0, "ftm": 2.0, "fta": 3.0},
        {"name": "Somtochukwu Osasuyi", "team": "Georgia", "pos": "PF/C", "height": "6-9", "class_year": "Fr.", "is_ita": True, "is_nba_prospect": False, "rank_nba": None, "gp": 2, "mpg": 19.5, "pts": 8.5, "reb": 6.5, "ast": 0.8, "stl": 0.5, "blk": 1.8, "tov": 1.2, "fgm": 3.5, "fga": 6.0, "tpm": 0.0, "tpa": 0.5, "ftm": 1.5, "fta": 2.5},
        {"name": "Elisee Assui", "team": "Wake Forest", "pos": "PF", "height": "6-8", "class_year": "Fr.", "is_ita": True, "is_nba_prospect": False, "rank_nba": None, "gp": 2, "mpg": 21.0, "pts": 9.5, "reb": 5.0, "ast": 1.5, "stl": 1.0, "blk": 0.5, "tov": 1.0, "fgm": 3.5, "fga": 7.5, "tpm": 1.5, "tpa": 4.0, "ftm": 1.0, "fta": 1.5},
        {"name": "Achille Lonati", "team": "St. Bonaventure", "pos": "SG", "height": "6-5", "class_year": "So.", "is_ita": True, "is_nba_prospect": False, "rank_nba": None, "gp": 2, "mpg": 27.0, "pts": 14.0, "reb": 3.5, "ast": 2.5, "stl": 1.0, "blk": 0.0, "tov": 1.5, "fgm": 5.0, "fga": 11.0, "tpm": 2.5, "tpa": 6.5, "ftm": 1.5, "fta": 1.8},
        {"name": "Gabriel Pozzato", "team": "Xavier", "pos": "SF", "height": "6-7", "class_year": "RS So.", "is_ita": True, "is_nba_prospect": False, "rank_nba": None, "gp": 2, "mpg": 25.0, "pts": 11.5, "reb": 4.5, "ast": 2.0, "stl": 1.0, "blk": 0.5, "tov": 1.5, "fgm": 4.0, "fga": 8.5, "tpm": 1.5, "tpa": 4.5, "ftm": 2.0, "fta": 2.5},
        {"name": "Tyran Stokes", "team": "Kansas", "pos": "SF/PF", "height": "6-7", "class_year": "Fr.", "is_ita": False, "is_nba_prospect": True, "rank_nba": 1, "gp": 2, "mpg": 31.5, "pts": 21.0, "reb": 8.5, "ast": 4.0, "stl": 1.5, "blk": 1.2, "tov": 2.5, "fgm": 7.5, "fga": 14.0, "tpm": 1.5, "tpa": 4.5, "ftm": 4.5, "fta": 6.0},
        {"name": "Caleb Holt", "team": "Arizona", "pos": "SG/PG", "height": "6-5", "class_year": "Fr.", "is_ita": False, "is_nba_prospect": True, "rank_nba": 2, "gp": 2, "mpg": 30.0, "pts": 18.5, "reb": 5.5, "ast": 4.5, "stl": 2.0, "blk": 0.5, "tov": 2.0, "fgm": 6.5, "fga": 13.5, "tpm": 2.0, "tpa": 5.5, "ftm": 3.5, "fta": 4.2},
        {"name": "Jordan Smith Jr", "team": "Arkansas", "pos": "G", "height": "6-2", "class_year": "Fr.", "is_ita": False, "is_nba_prospect": True, "rank_nba": 3, "gp": 2, "mpg": 31.0, "pts": 19.5, "reb": 4.0, "ast": 5.5, "stl": 2.2, "blk": 0.3, "tov": 2.2, "fgm": 7.0, "fga": 14.5, "tpm": 2.0, "tpa": 5.5, "ftm": 3.5, "fta": 4.5}
    ]
    out = {}
    for item in raw:
        pid = slugify(item['name'])
        item['id'] = pid
        out[pid] = item
    return out

def sync_github_issue_notes(scraper):
    """Legge le GitHub Issues con tag [SCOUTING] e le unisce a community_notes.json"""
    notes_file = "community_notes.json"
    notes_db = {}
    if os.path.exists(notes_file):
        try:
            with open(notes_file, "r", encoding="utf-8") as f:
                notes_db = json.load(f)
        except:
            notes_db = {}

    try:
        api_url = f"https://api.github.com/repos/{GITHUB_REPO}/issues?state=open&per_page=50"
        res = scraper.get(api_url, timeout=15)
        if res.status_code == 200:
            issues = res.json()
            for issue in issues:
                title = issue.get("title", "")
                if not title.startswith("[SCOUTING]"):
                    continue
                body = issue.get("body", "") or ""
                pid_match = re.search(r"PLAYER_ID:\s*([a-z0-9-]+)", body)
                author_match = re.search(r"AUTHOR:\s*(.+)", body)
                video_match = re.search(r"VIDEO:\s*(.*)", body)
                text_match = re.search(r"NOTE:\s*([\s\S]+)", body)

                if pid_match and text_match:
                    pid = pid_match.group(1).strip()
                    note_id = f"gh-issue-{issue['number']}"
                    existing_ids = [n.get("id") for n in notes_db.get(pid, [])]
                    if note_id not in existing_ids:
                        notes_db.setdefault(pid, []).insert(0, {
                            "id": note_id,
                            "author": (author_match.group(1).strip() if author_match else issue["user"]["login"]),
                            "date": issue.get("created_at", "")[:10],
                            "video": (video_match.group(1).strip() if video_match else ""),
                            "text": text_match.group(1).strip()
                        })
    except Exception as e:
        print(f"Avviso sync issues: {e}")

    with open(notes_file, "w", encoding="utf-8") as f:
        json.dump(notes_db, f, ensure_ascii=False, indent=2)

def main():
    scraper = get_scraper()
    players = scrape_realgm(scraper)
    players = scrape_tankathon(scraper, players)

    seed = get_seed_dataset()
    for pid, sdata in seed.items():
        if pid not in players or players[pid].get('pts', 0) == 0:
            players[pid] = sdata

    player_list = [compute_metrics(p) for p in players.values()]
    player_list.sort(key=lambda x: (x['rank_nba'] or 999, -x['pts']))

    payload = {
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "repo": GITHUB_REPO,
        "count": len(player_list),
        "players": player_list
    }

    with open("players_data.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    sync_github_issue_notes(scraper)
    print("Sincronizzazione stats e note completata.")

if __name__ == "__main__":
    main()
