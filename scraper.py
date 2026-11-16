import json, os, re
from datetime import datetime, timezone
from urllib.parse import quote
import cloudscraper

GITHUB_REPO = "Lolarok/ncaa2"

BASE_PLAYERS = [
    {"name": "Dame Sarr", "team": "Duke", "pos": "SG/SF", "height": "6-7", "class_year": "Fr.", "is_ita": True, "is_nba_prospect": True, "rank_nba": 38, "gp": 4, "mpg": 24.5, "pts": 12.8, "reb": 4.2, "ast": 2.6, "tov": 1.5, "fgm": 4.6, "fga": 9.6, "tpm": 2.1, "tpa": 5.2, "ftm": 1.5, "fta": 2.0},
    {"name": "Luigi Suigo", "team": "Villanova", "pos": "C", "height": "7-2", "class_year": "Fr.", "is_ita": True, "is_nba_prospect": True, "rank_nba": 18, "gp": 4, "mpg": 22.4, "pts": 11.2, "reb": 7.8, "ast": 1.1, "tov": 1.4, "fgm": 4.5, "fga": 7.4, "tpm": 0.6, "tpa": 1.7, "ftm": 1.6, "fta": 2.4},
    {"name": "Saliou Niang", "team": "LSU", "pos": "SF", "height": "6-6", "class_year": "Fr.", "is_ita": True, "is_nba_prospect": False, "rank_nba": None, "gp": 4, "mpg": 26.2, "pts": 13.4, "reb": 6.1, "ast": 2.2, "tov": 1.9, "fgm": 5.1, "fga": 9.8, "tpm": 1.1, "tpa": 3.1, "ftm": 2.1, "fta": 3.0},
    {"name": "Somtochukwu Osasuyi", "team": "Georgia", "pos": "PF/C", "height": "6-9", "class_year": "Fr.", "is_ita": True, "is_nba_prospect": False, "rank_nba": None, "gp": 4, "mpg": 19.8, "pts": 8.8, "reb": 6.7, "ast": 0.9, "tov": 1.2, "fgm": 3.6, "fga": 5.9, "tpm": 0.0, "tpa": 0.4, "ftm": 1.6, "fta": 2.6},
    {"name": "Elisee Assui", "team": "Wake Forest", "pos": "PF", "height": "6-8", "class_year": "Fr.", "is_ita": True, "is_nba_prospect": False, "rank_nba": None, "gp": 4, "mpg": 21.5, "pts": 9.6, "reb": 5.2, "ast": 1.4, "tov": 1.1, "fgm": 3.5, "fga": 7.6, "tpm": 1.5, "tpa": 4.1, "ftm": 1.1, "fta": 1.5},
    {"name": "Achille Lonati", "team": "St. Bonaventure", "pos": "SG", "height": "6-5", "class_year": "So.", "is_ita": True, "is_nba_prospect": False, "rank_nba": None, "gp": 4, "mpg": 27.4, "pts": 14.3, "reb": 3.6, "ast": 2.4, "tov": 1.6, "fgm": 5.1, "fga": 11.2, "tpm": 2.6, "tpa": 6.6, "ftm": 1.5, "fta": 1.8},
    {"name": "Gabriel Pozzato", "team": "Xavier", "pos": "SF", "height": "6-7", "class_year": "RS So.", "is_ita": True, "is_nba_prospect": False, "rank_nba": None, "gp": 4, "mpg": 25.1, "pts": 11.7, "reb": 4.6, "ast": 1.9, "tov": 1.4, "fgm": 4.1, "fga": 8.7, "tpm": 1.6, "tpa": 4.5, "ftm": 1.9, "fta": 2.4},
    {"name": "Emmanuel Innocenti", "team": "UC Irvine", "pos": "F", "height": "6-5", "class_year": "So.", "is_ita": True, "is_nba_prospect": False, "rank_nba": None, "gp": 4, "mpg": 23.0, "pts": 7.4, "reb": 5.8, "ast": 2.7, "tov": 1.3, "fgm": 2.7, "fga": 5.8, "tpm": 0.9, "tpa": 2.5, "ftm": 1.1, "fta": 1.4},
    {"name": "Niccolo Moretti", "team": "Florida Atlantic", "pos": "PG", "height": "6-1", "class_year": "So.", "is_ita": True, "is_nba_prospect": False, "rank_nba": None, "gp": 4, "mpg": 20.5, "pts": 6.8, "reb": 2.3, "ast": 3.9, "tov": 1.5, "fgm": 2.4, "fga": 5.5, "tpm": 0.8, "tpa": 2.3, "ftm": 1.2, "fta": 1.5},
    {"name": "Timothy Van Der Knaap", "team": "Bradley", "pos": "PF", "height": "6-8", "class_year": "Jr.", "is_ita": True, "is_nba_prospect": False, "rank_nba": None, "gp": 4, "mpg": 22.8, "pts": 10.2, "reb": 6.0, "ast": 1.5, "tov": 1.2, "fgm": 3.9, "fga": 8.1, "tpm": 1.2, "tpa": 3.4, "ftm": 1.2, "fta": 1.6},
    {"name": "Leonardo Marangon", "team": "Providence", "pos": "G/F", "height": "6-6", "class_year": "Fr.", "is_ita": True, "is_nba_prospect": False, "rank_nba": None, "gp": 4, "mpg": 17.5, "pts": 6.5, "reb": 3.2, "ast": 1.6, "tov": 1.0, "fgm": 2.4, "fga": 5.4, "tpm": 0.9, "tpa": 2.7, "ftm": 0.8, "fta": 1.1},
    {"name": "Francesco Borra", "team": "UC Davis", "pos": "C", "height": "6-11", "class_year": "Sr.", "is_ita": True, "is_nba_prospect": False, "rank_nba": None, "gp": 4, "mpg": 18.2, "pts": 6.1, "reb": 5.4, "ast": 0.8, "tov": 1.1, "fgm": 2.5, "fga": 4.4, "tpm": 0.0, "tpa": 0.1, "ftm": 1.1, "fta": 1.8},
    {"name": "Tyran Stokes", "team": "Kansas", "pos": "SF/PF", "height": "6-7", "class_year": "Fr.", "is_ita": False, "is_nba_prospect": True, "rank_nba": 1, "gp": 4, "mpg": 31.8, "pts": 21.4, "reb": 8.6, "ast": 4.1, "tov": 2.4, "fgm": 7.6, "fga": 14.1, "tpm": 1.6, "tpa": 4.5, "ftm": 4.6, "fta": 6.1},
    {"name": "Caleb Holt", "team": "Arizona", "pos": "SG/PG", "height": "6-5", "class_year": "Fr.", "is_ita": False, "is_nba_prospect": True, "rank_nba": 2, "gp": 4, "mpg": 30.2, "pts": 18.8, "reb": 5.4, "ast": 4.6, "tov": 2.0, "fgm": 6.6, "fga": 13.6, "tpm": 2.1, "tpa": 5.6, "ftm": 3.5, "fta": 4.2},
    {"name": "Jordan Smith Jr", "team": "Arkansas", "pos": "G", "height": "6-2", "class_year": "Fr.", "is_ita": False, "is_nba_prospect": True, "rank_nba": 3, "gp": 4, "mpg": 31.0, "pts": 19.6, "reb": 4.1, "ast": 5.6, "tov": 2.2, "fgm": 7.0, "fga": 14.4, "tpm": 2.0, "tpa": 5.4, "ftm": 3.6, "fta": 4.5},
    {"name": "Cameron Williams", "team": "Duke", "pos": "PF/C", "height": "6-11", "class_year": "Fr.", "is_ita": False, "is_nba_prospect": True, "rank_nba": 4, "gp": 4, "mpg": 28.4, "pts": 16.8, "reb": 9.2, "ast": 1.8, "tov": 1.7, "fgm": 6.6, "fga": 11.4, "tpm": 1.0, "tpa": 2.9, "ftm": 2.6, "fta": 3.5},
    {"name": "Anthony Thompson", "team": "Ohio State", "pos": "SF", "height": "6-8", "class_year": "Fr.", "is_ita": False, "is_nba_prospect": True, "rank_nba": 5, "gp": 4, "mpg": 29.1, "pts": 17.2, "reb": 6.4, "ast": 2.3, "tov": 1.8, "fgm": 6.1, "fga": 12.6, "tpm": 2.5, "tpa": 6.1, "ftm": 2.5, "fta": 3.0},
    {"name": "Bruce Branch III", "team": "BYU", "pos": "SF", "height": "6-7", "class_year": "Fr.", "is_ita": False, "is_nba_prospect": True, "rank_nba": 6, "gp": 4, "mpg": 28.5, "pts": 16.1, "reb": 5.8, "ast": 2.5, "tov": 1.9, "fgm": 5.8, "fga": 12.0, "tpm": 2.2, "tpa": 5.7, "ftm": 2.3, "fta": 2.8},
    {"name": "Christian Collins", "team": "USC", "pos": "PF", "height": "6-8", "class_year": "Fr.", "is_ita": False, "is_nba_prospect": True, "rank_nba": 7, "gp": 4, "mpg": 27.6, "pts": 15.4, "reb": 7.9, "ast": 1.9, "tov": 1.6, "fgm": 5.9, "fga": 10.9, "tpm": 0.9, "tpa": 2.6, "ftm": 2.7, "fta": 3.6},
    {"name": "Babatunde Oladotun", "team": "Maryland", "pos": "SF", "height": "6-9", "class_year": "Fr.", "is_ita": False, "is_nba_prospect": True, "rank_nba": 8, "gp": 4, "mpg": 26.8, "pts": 14.9, "reb": 6.2, "ast": 2.1, "tov": 1.7, "fgm": 5.4, "fga": 11.5, "tpm": 1.8, "tpa": 4.8, "ftm": 2.3, "fta": 2.9},
    {"name": "Miikka Muurinen", "team": "Arizona", "pos": "PF", "height": "6-10", "class_year": "Fr.", "is_ita": False, "is_nba_prospect": True, "rank_nba": 9, "gp": 4, "mpg": 25.4, "pts": 13.8, "reb": 7.1, "ast": 1.6, "tov": 1.5, "fgm": 5.0, "fga": 10.2, "tpm": 1.7, "tpa": 4.6, "ftm": 2.1, "fta": 2.7},
    {"name": "Brandon McCoy Jr", "team": "Duke", "pos": "PG", "height": "6-4", "class_year": "Fr.", "is_ita": False, "is_nba_prospect": True, "rank_nba": 10, "gp": 4, "mpg": 29.5, "pts": 16.4, "reb": 4.3, "ast": 5.2, "tov": 2.1, "fgm": 5.9, "fga": 12.8, "tpm": 1.6, "tpa": 4.4, "ftm": 3.0, "fta": 3.8}
]

def slugify(text):
    return re.sub(r'[^a-z0-9]+', '-', str(text).lower()).strip('-')

def to_float(val, default=0.0):
    try:
        cleaned = re.sub(r'[^\d.-]', '', str(val))
        return float(cleaned) if cleaned else default
    except Exception:
        return default

def compute_metrics(p):
    pts = to_float(p.get('pts', 0))
    fga = to_float(p.get('fga', 0))
    fgm = to_float(p.get('fgm', 0))
    tpa = to_float(p.get('tpa', 0))
    tpm = to_float(p.get('tpm', 0))
    fta = to_float(p.get('fta', 0))
    ftm = to_float(p.get('ftm', 0))
    ast = to_float(p.get('ast', 0))
    tov = to_float(p.get('tov', 1.4))
    mpg = to_float(p.get('mpg', 20.0))

    if fga <= 0 and pts > 0:
        fg_p = to_float(p.get('fg_pct_raw', 46.5)) / 100.0
        tp_p = to_float(p.get('tp_pct_raw', 34.5)) / 100.0
        ft_p = to_float(p.get('ft_pct_raw', 74.0)) / 100.0
        fta = round(pts * 0.27, 2)
        ftm = round(fta * ft_p, 2)
        pts_fg = max(0.0, pts - ftm)
        tpm = round((pts_fg * 0.33) / 3.0, 2)
        tpa = round(tpm / max(0.20, tp_p), 2)
        two_pm = max(0.0, (pts_fg - tpm * 3.0) / 2.0)
        fgm = round(two_pm + tpm, 2)
        fga = round(fgm / max(0.30, fg_p), 2)
        p['fgm'], p['fga'], p['tpm'], p['tpa'], p['ftm'], p['fta'] = fgm, fga, tpm, tpa, ftm, fta

    tsa = fga + 0.44 * fta
    ts_pct = round((pts / (2.0 * tsa)) * 100.0, 1) if tsa > 0 else 0.0
    efg_pct = round(((fgm + 0.5 * tpm) / fga) * 100.0, 1) if fga > 0 else 0.0
    tov_denom = fga + 0.44 * fta + tov
    tov_pct = round((tov / tov_denom) * 100.0, 1) if tov_denom > 0 else 0.0
    ast_to = round(ast / tov, 2) if tov > 0 else round(ast, 2)
    ftr = round((fta / fga) * 100.0, 1) if fga > 0 else 0.0
    poss = fga + 0.44 * fta + tov
    usg_pct = round(min(42.0, max(10.0, (poss / mpg) * 38.0)), 1) if (mpg > 0 and poss > 0) else 18.0

    two_pa = max(0.0, fga - tpa)
    two_pm = max(0.0, fgm - tpm)
    two_p_pct = round((two_pm / two_pa) * 100.0, 1) if two_pa > 0 else 0.0
    three_p_pct = round((tpm / tpa) * 100.0, 1) if tpa > 0 else 0.0
    ft_pct = round((ftm / fta) * 100.0, 1) if fta > 0 else 0.0
    three_par = round((tpa / fga) * 100.0, 1) if fga > 0 else 0.0
    two_par = round(100.0 - three_par, 1) if fga > 0 else 0.0

    pos_str = str(p.get('pos', 'G/F')).upper()
    base_rim = 0.66 if 'C' in pos_str else (0.58 if 'F' in pos_str else 0.46)
    ftr_bonus = min(0.14, max(-0.10, (ftr - 30.0) * 0.003))
    rim_ratio = min(0.82, max(0.32, base_rim + ftr_bonus))
    rim_freq = round(two_par * rim_ratio, 1) if fga > 0 else 0.0
    mid_freq = round(max(0.0, two_par - rim_freq), 1) if fga > 0 else 0.0
    rim_fg = round(min(78.0, two_p_pct * 1.15), 1) if two_pa > 0 else 0.0
    mid_fg = round(max(26.0, two_p_pct * 0.78), 1) if two_pa > 0 else 0.0

    p['has_stats'] = bool(pts > 0 or fga > 0)
    p['advanced'] = {
        'ts_pct': ts_pct, 'efg_pct': efg_pct, 'usg_pct': usg_pct,
        'ast_to': ast_to, 'tov_pct': tov_pct, 'ftr': ftr
    }
    p['shot_selection'] = {
        'rim_freq': rim_freq, 'mid_freq': mid_freq, 'three_par': three_par,
        'rim_fg': rim_fg, 'mid_fg': mid_fg,
        'two_p_pct': two_p_pct, 'three_p_pct': three_p_pct, 'ft_pct': ft_pct,
        'two_pa': round(two_pa, 1), 'tpa': round(tpa, 1), 'fta': round(fta, 1)
    }
    return p

def update_from_espn(scraper, players):
    for pid, p in players.items():
        clean = re.sub(r'\b(Jr\.|Sr\.|III|II)\b', '', p['name'], flags=re.I).strip()
        try:
            s_url = f"https://site.web.api.espn.com/apis/common/v3/search?query={quote(clean)}&limit=5"
            res = scraper.get(s_url, timeout=8)
            if res.status_code != 200:
                continue
            aid = None
            for it in res.json().get('items', []):
                txt = json.dumps(it).lower()
                if 'college-basketball' in txt or 'l:41' in txt:
                    m = re.search(r'~a:(\d+)', str(it.get('uid', '')))
                    aid = m.group(1) if m else str(it.get('id', ''))
                    break
            if not aid or not aid.isdigit():
                continue

            ov_url = f"https://site.web.api.espn.com/apis/common/v3/sports/basketball/mens-college-basketball/athletes/{aid}/overview"
            ov_res = scraper.get(ov_url, timeout=8)
            if ov_res.status_code != 200:
                continue
            st = ov_res.json().get('statistics', {})
            labels = [x.upper() for x in st.get('labels', [])]
            splits = st.get('splits', [])
            if labels and splits:
                vals = splits[-1].get('stats', [])
                row = dict(zip(labels, vals))
                gp = int(to_float(row.get('GP', 0)))
                pts = to_float(row.get('PTS', 0))
                if gp > 0 and pts > 0:
                    p['gp'] = gp
                    p['mpg'] = to_float(row.get('MIN', p['mpg']))
                    p['pts'] = pts
                    p['reb'] = to_float(row.get('REB', p['reb']))
                    p['ast'] = to_float(row.get('AST', p['ast']))
                    p['tov'] = to_float(row.get('TO', p['tov']))
                    p['fg_pct_raw'] = to_float(row.get('FG%', 46.0))
                    p['tp_pct_raw'] = to_float(row.get('3P%', 34.0))
                    p['ft_pct_raw'] = to_float(row.get('FT%', 74.0))
                    p['fga'] = 0.0
        except Exception:
            continue

def sync_github_issue_notes(scraper):
    notes_file = "community_notes.json"
    notes_db = {}
    if os.path.exists(notes_file):
        try:
            with open(notes_file, "r", encoding="utf-8") as f:
                notes_db = json.load(f)
        except Exception:
            notes_db = {}
    try:
        api_url = f"https://api.github.com/repos/{GITHUB_REPO}/issues?state=open&per_page=50"
        res = scraper.get(api_url, timeout=12)
        if res.status_code == 200:
            for issue in res.json():
                title = issue.get("title", "")
                if not title.startswith("[SCOUTING]"):
                    continue
                body = issue.get("body", "") or ""
                pid_m = re.search(r"PLAYER_ID:\s*([a-z0-9-]+)", body)
                auth_m = re.search(r"AUTHOR:\s*(.+)", body)
                vid_m = re.search(r"VIDEO:\s*(.*)", body)
                txt_m = re.search(r"NOTE:\s*([\s\S]+)", body)
                if pid_m and txt_m:
                    pid = pid_m.group(1).strip()
                    nid = f"gh-issue-{issue['number']}"
                    if not any(n.get("id") == nid for n in notes_db.get(pid, [])):
                        notes_db.setdefault(pid, []).insert(0, {
                            "id": nid,
                            "author": auth_m.group(1).strip() if auth_m else issue["user"]["login"],
                            "date": issue.get("created_at", "")[:10],
                            "video": vid_m.group(1).strip() if vid_m else "",
                            "text": txt_m.group(1).strip()
                        })
    except Exception:
        pass
    with open(notes_file, "w", encoding="utf-8") as f:
        json.dump(notes_db, f, ensure_ascii=False, indent=2)

def main():
    scraper = cloudscraper.create_scraper()
    players = {}
    for item in BASE_PLAYERS:
        pid = slugify(item["name"])
        copy_item = dict(item)
        copy_item["id"] = pid
        players[pid] = copy_item

    update_from_espn(scraper, players)
    player_list = [compute_metrics(p) for p in players.values()]
    player_list.sort(key=lambda x: (x.get("rank_nba") or 999, -x.get("pts", 0)))

    payload = {
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "repo": GITHUB_REPO,
        "count": len(player_list),
        "players": player_list
    }
    with open("players_data.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    sync_github_issue_notes(scraper)
    print(f"Completato: salvati {len(player_list)} giocatori.")

if __name__ == "__main__":
    main()
