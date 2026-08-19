#!/usr/bin/env python3
import os
import sys
import re
import json
import ssl
import html
import argparse
import urllib.request
import urllib.parse
from datetime import datetime, timezone, timedelta

# KST Timezone (+09:00)
KST = timezone(timedelta(hours=9))


def load_env(env_path=None):
    """Load environment variables from .env file"""
    if env_path is None:
        # Search in current directory and parent directory
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        env_path = os.path.join(base_dir, ".env")
        if not os.path.exists(env_path):
            env_path = os.path.join(os.getcwd(), ".env")

    env_vars = {}
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                env_vars[k.strip()] = v.strip().strip("\"'")
    return env_vars


def fetch_json(url, headers=None):
    """Fetch JSON response from URL using standard library"""
    ctx = ssl.create_default_context()
    default_headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json",
    }
    if headers:
        default_headers.update(headers)
    req = urllib.request.Request(url, headers=default_headers)
    with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def parse_contest_id(input_str):
    """Extract contest ID from URL or numeric string"""
    input_str = input_str.strip()
    match = re.search(r"contest(?:s)?/(\d+)", input_str)
    if match:
        return int(match.group(1))
    match = re.search(r"problemset/problem/(\d+)", input_str)
    if match:
        return int(match.group(1))
    if input_str.isdigit():
        return int(input_str)
    raise ValueError(f"Could not parse contest ID from input: {input_str}")


def format_rating_html(rating):
    """Format Codeforces rating with HTML color span (supports Nutella / LGM >= 3000)"""
    if rating is None or rating == 0:
        return "-"
    
    r_str = str(rating)
    if rating < 1200:
        color = "#999999"  # Gray
    elif rating < 1400:
        color = "#33cc33"  # Green
    elif rating < 1600:
        color = "#44ddaa"  # Cyan
    elif rating < 1900:
        color = "#2222ff"  # Blue
    elif rating < 2200:
        color = "#aa00ff"  # Purple
    elif rating < 2400:
        color = "#ff9900"  # Orange
    elif rating < 3000:
        color = "#ff2222"  # Red
    else:
        # Nutella (>= 3000): First character inherits theme text color (dark/white theme), rest is #ff2222
        first_char = r_str[0]
        rest_chars = r_str[1:]
        return f'<span style="font-weight: bold;">{first_char}</span><span style="color: #ff2222; font-weight: bold;">{rest_chars}</span>'

    return f'<span style="color: {color}; font-weight: bold;">{r_str}</span>'

def get_cf_rating_color(rating):
    """Return Codeforces rating color hex and Solved.ac tier image / name"""
    if rating is None or rating == 0:
        return "#999999", 0, "Unrated"

    # Rating color
    if rating < 1200:
        color = "#999999"  # Gray
    elif rating < 1400:
        color = "#33cc33"  # Green
    elif rating < 1600:
        color = "#44ddaa"  # Cyan
    elif rating < 1900:
        color = "#2222ff"  # Blue
    elif rating < 2200:
        color = "#aa00ff"  # Purple
    elif rating < 2400:
        color = "#ff9900"  # Orange
    else:
        color = "#ff2222"  # Red

    # Solved.ac Tier approximation (1 ~ 30)
    # B5..B1 (1..5), S5..S1 (6..10), G5..G1 (11..15), P5..P1 (16..20), D5..D1 (21..25), R5..R1 (26..30)
    tier_mapping = [
        (800, 5, "B1"),
        (900, 6, "S5"),
        (1000, 7, "S4"),
        (1100, 8, "S3"),
        (1200, 9, "S2"),
        (1300, 10, "S1"),
        (1400, 11, "G5"),
        (1500, 12, "G4"),
        (1600, 13, "G3"),
        (1700, 14, "G2"),
        (1800, 15, "G1"),
        (1900, 16, "P5"),
        (2000, 17, "P4"),
        (2100, 18, "P3"),
        (2200, 19, "P2"),
        (2300, 20, "P1"),
        (2400, 21, "D5"),
        (2500, 22, "D4"),
        (2600, 23, "D3"),
        (2700, 24, "D2"),
        (2800, 25, "D1"),
        (3000, 26, "R5"),
    ]
    tier_num = 1
    tier_name = "B5"
    for threshold, t_num, t_name in tier_mapping:
        if rating >= threshold:
            tier_num = t_num
            tier_name = t_name
        else:
            break

    return color, tier_num, tier_name


def fetch_clist_ratings(contest_id, username, api_key):
    """Fetch problem ratings from CLIST API"""
    if not username or not api_key:
        return {}
    url = f"https://clist.by/api/v4/problem/?resource=codeforces.com&url__regex=^https://codeforces.com/contest/{contest_id}/problem/&limit=50"
    headers = {"Authorization": f"ApiKey {username}:{api_key}"}
    try:
        data = fetch_json(url, headers=headers)
        ratings = {}
        for obj in data.get("objects", []):
            p_url = obj.get("url", "")
            match = re.search(r"/problem/([A-Za-z0-9]+)", p_url)
            if match:
                p_index = match.group(1).upper()
                r = obj.get("rating")
                if r is not None:
                    ratings[p_index] = int(r)
        return ratings
    except Exception as e:
        print(f"[Warning] Failed to fetch CLIST problem ratings: {e}", file=sys.stderr)
        return {}


def format_relative_time(seconds):
    """Format seconds into HH:MM or MM:SS"""
    if seconds is None or seconds < 0:
        return "-"
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return f"{hours:02d}:{minutes:02d}"

def format_duration(seconds):
    """Format contest duration into human readable Korean string (e.g. 2시간, 2시간 15분)"""
    if not seconds:
        return "2시간"
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    if hours > 0 and minutes > 0:
        return f"{hours}시간 {minutes}분"
    elif hours > 0:
        return f"{hours}시간"
    else:
        return f"{minutes}분"


def find_local_solution_code(contest_id, problem_index, search_dir=None):
    """Search for local C++ / Python solution file matching the problem"""
    search_dirs = []
    if search_dir:
        search_dirs.append(search_dir)

    # Common local search locations
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    search_dirs.extend(
        [
            os.getcwd(),
            os.path.join(base_dir, "solutions"),
            os.path.join(base_dir, "ps"),
            os.path.join(base_dir, f"contest_{contest_id}"),
            os.path.join(base_dir, str(contest_id)),
            os.path.expanduser(f"~/Desktop/ps/{contest_id}"),
            os.path.expanduser(f"~/Desktop/ps"),
        ]
    )

    # Possible candidate filenames
    idx = problem_index
    idx_lower = problem_index.lower()
    candidates = [
        f"{idx}.cpp",
        f"{idx_lower}.cpp",
        f"{contest_id}{idx}.cpp",
        f"{contest_id}{idx_lower}.cpp",
        f"{contest_id}_{idx}.cpp",
        f"{contest_id}_{idx_lower}.cpp",
        f"{contest_id}-{idx}.cpp",
        f"{contest_id}-{idx_lower}.cpp",
        f"{idx}.py",
        f"{idx_lower}.py",
    ]

    for s_dir in search_dirs:
        if not os.path.exists(s_dir):
            continue
        for cand in candidates:
            cand_path = os.path.join(s_dir, cand)
            if os.path.isfile(cand_path):
                try:
                    with open(cand_path, "r", encoding="utf-8", errors="ignore") as f:
                        return f.read().strip()
                except Exception:
                    pass
    return ""


def format_verdict_badge(verdict, passed_test_count=0):
    """Format Codeforces verdict into styled badge with test details"""
    if verdict == "OK":
        return '<span style="color:#33cc33; font-weight:bold;">AC</span>'
    elif verdict == "WRONG_ANSWER":
        test_info = f" (test {passed_test_count + 1})" if passed_test_count is not None else ""
        return f'<span style="color:#ff2222; font-weight:bold;">WA{test_info}</span>'
    elif verdict == "TIME_LIMIT_EXCEEDED":
        test_info = f" (test {passed_test_count + 1})" if passed_test_count is not None else ""
        return f'<span style="color:#ff9900; font-weight:bold;">TLE{test_info}</span>'
    elif verdict == "MEMORY_LIMIT_EXCEEDED":
        return '<span style="color:#ff9900; font-weight:bold;">MLE</span>'
    elif verdict == "RUNTIME_ERROR":
        return '<span style="color:#ff2222; font-weight:bold;">RTE</span>'
    elif verdict == "COMPILATION_ERROR":
        return '<span style="color:#999999; font-weight:bold;">CE</span>'
    elif verdict == "CHALLENGED":
        return '<span style="color:#ff2222; font-weight:bold;">HACKED</span>'
    elif verdict:
        return f'<span>{verdict}</span>'
    return '-'

def generate_post_slug_and_title(contest_name, contest_id):
    """Generate nice blog post title, filename slug, and image folder name"""
    # e.g., "Codeforces Round 1113 (Div. 2)" -> "Round 1113 Div. 2"
    m_round_div = re.search(r'Round\s*(\d+)\s*\((Div\.\s*\d+[^)]*)\)', contest_name, re.I)
    if m_round_div:
        round_num = m_round_div.group(1)
        div_num = re.search(r'\d+', m_round_div.group(2)).group(0) if re.search(r'\d+', m_round_div.group(2)) else "2"
        slug = f"cf-r{round_num}-div{div_num}"
        img_folder = f"R{round_num}Div{div_num}"
        short_title = f"[Codeforces] Round {round_num} {m_round_div.group(2)}"
        desc = f"코드포스 라운드 {round_num} {m_round_div.group(2)} 풀이와 후기"
        return slug, img_folder, short_title, desc

    m_edu = re.search(r'Educational\s*Codeforces\s*Round\s*(\d+)', contest_name, re.I)
    if m_edu:
        edu_num = m_edu.group(1)
        slug = f"cf-edu-{edu_num}"
        img_folder = f"Edu{edu_num}"
        short_title = f"[Codeforces] Educational Round {edu_num}"
        desc = f"코드포스 에듀케이셔널 라운드 {edu_num} 풀이와 후기"
        return slug, img_folder, short_title, desc

    m_global = re.search(r'Codeforces\s*Global\s*Round\s*(\d+)', contest_name, re.I)
    if m_global:
        g_num = m_global.group(1)
        slug = f"cf-global-{g_num}"
        img_folder = f"Global{g_num}"
        short_title = f"[Codeforces] Global Round {g_num}"
        desc = f"코드포스 글로벌 라운드 {g_num} 풀이와 후기"
        return slug, img_folder, short_title, desc

    # Fallback
    safe_name = re.sub(r'[^a-zA-Z0-9]+', '-', contest_name.strip()).lower().strip('-')
    slug = f"cf-{safe_name[:30]}"
    img_folder = f"contest_{contest_id}"
    short_title = f"[Codeforces] {contest_name}"
    desc = f"코드포스 {contest_name} 풀이와 후기"
    return slug, img_folder, short_title, desc


def main():
    parser = argparse.ArgumentParser(description="Generate Codeforces Contest Review Post for Jekyll")
    parser.add_argument("contest", help="Contest ID or Codeforces contest URL (e.g. 2257 or https://codeforces.com/contest/2257)")
    parser.add_argument("--handle", help="Codeforces handle (defaults to CF_HANDLE in .env)")
    parser.add_argument("--output-dir", help="Output directory for posts (defaults to _posts/Codeforces)")
    parser.add_argument("--code-dir", help="Directory where solution files (.cpp) are stored")
    parser.add_argument("-f", "--force", action="store_true", help="Overwrite existing post file without asking")
    args = parser.parse_args()

    env = load_env()
    handle = args.handle or env.get("CF_HANDLE")
    if not handle:
        print("[Error] Codeforces handle not provided. Set CF_HANDLE in .env or pass --handle <handle>", file=sys.stderr)
        sys.exit(1)

    clist_user = env.get("CLIST_USERNAME")
    clist_key = env.get("CLIST_API_KEY")

    contest_id = parse_contest_id(args.contest)
    print(f"[*] Processing Contest ID: {contest_id} for handle: {handle}")

    # 1. Fetch Contest Standings & Metadata from Codeforces API
    cf_standings_url = f"https://codeforces.com/api/contest.standings?contestId={contest_id}"
    print(f"[*] Fetching contest data from Codeforces API...")
    standings_data = fetch_json(cf_standings_url)
    if standings_data.get("status") != "OK":
        print(f"[Error] Codeforces API returned error: {standings_data.get('comment')}", file=sys.stderr)
        sys.exit(1)

    contest_info = standings_data["result"]["contest"]
    problems = standings_data["result"]["problems"]
    contest_name = contest_info.get("name", f"Contest {contest_id}")
    contest_duration = contest_info.get("durationSeconds", 7200)
    print(f"[+] Contest: {contest_name} ({len(problems)} problems)")

    # 2. Fetch User Submissions from Codeforces API
    cf_status_url = f"https://codeforces.com/api/contest.status?contestId={contest_id}&handle={handle}"
    print(f"[*] Fetching submissions for {handle}...")
    status_data = fetch_json(cf_status_url)
    submissions = status_data.get("result", [])
    print(f"[+] Found {len(submissions)} submissions.")

    # 3. Fetch CLIST Problem Ratings
    print(f"[*] Fetching CLIST problem ratings...")
    clist_ratings = fetch_clist_ratings(contest_id, clist_user, clist_key)
    if clist_ratings:
        print(f"[+] Loaded {len(clist_ratings)} ratings from CLIST.")
    else:
        print(f"[-] CLIST ratings not available, falling back to Codeforces official ratings.")

    # 4. Analyze Submissions Problem by Problem
    # Sort submissions chronologically (oldest first)
    submissions.sort(key=lambda s: s.get("creationTimeSeconds", 0))

    # Group submissions by problem index
    prob_subs = {p["index"]: [] for p in problems}
    for sub in submissions:
        idx = sub["problem"]["index"]
        if idx in prob_subs:
            prob_subs[idx].append(sub)

    problem_analysis = {}
    for p in problems:
        idx = p["index"]
        name = p.get("name", "")
        cf_rating = p.get("rating")
        clist_r = clist_ratings.get(idx)
        final_rating = clist_r if clist_r is not None else cf_rating

        subs = prob_subs.get(idx, [])
        ac_sub = None
        contest_tries = 0
        contest_wa = 0
        upsolve_tries = 0
        solved_in_contest = False
        solved_upsolve = False
        ac_time_str = "-"

        for sub in subs:
            verdict = sub.get("verdict")
            rel_time = sub.get("relativeTimeSeconds", 2147483647)
            is_in_contest = rel_time <= contest_duration

            if is_in_contest:
                contest_tries += 1
                if verdict == "OK":
                    if not solved_in_contest:
                        solved_in_contest = True
                        ac_sub = sub
                        ac_time_str = format_relative_time(rel_time)
                else:
                    if not solved_in_contest:
                        contest_wa += 1
            else:
                upsolve_tries += 1
                if verdict == "OK":
                    if not solved_in_contest and not solved_upsolve:
                        solved_upsolve = True
                        ac_sub = sub

        # Summarize problem stats
        if solved_in_contest:
            verdict_badge = '<span style="color:#33cc33; font-weight:bold;">AC</span>'
            status_desc = "대회 중"
            tries_desc = f"{contest_tries}트" + (f" ({contest_wa} WA)" if contest_wa > 0 else "")
            table_result = f'<span style="color:#33cc33; font-weight:bold;">{ac_time_str} AC</span> ({tries_desc})'
        elif solved_upsolve:
            verdict_badge = '<span style="color:#33cc33; font-weight:bold;">AC</span>'
            status_desc = '<span style="color:#aa00ff; font-weight:bold;">Upsolved</span>'
            tries_desc = f"{contest_tries + upsolve_tries}트"
            table_result = f'<span style="color:#aa00ff; font-weight:bold;">Upsolved</span> ({tries_desc})'
        elif contest_tries > 0:
            verdict_badge = '<span style="color:#ff2222; font-weight:bold;">WA</span>'
            status_desc = "대회 중"
            tries_desc = f"{contest_tries}트"
            table_result = f'<span style="color:#ff2222; font-weight:bold;">{contest_tries} WA</span>'
        else:
            verdict_badge = "-"
            status_desc = "-"
            tries_desc = "-"
            table_result = "-"

        color, tier_num, tier_name = get_cf_rating_color(final_rating)
        rating_html = format_rating_html(final_rating)

        problem_analysis[idx] = {
            "problem": p,
            "rating": final_rating,
            "rating_str": str(final_rating) if final_rating else "-",
            "rating_color": color,
            "rating_html": rating_html,
            "tier_num": tier_num,
            "tier_name": tier_name,
            "verdict_badge": verdict_badge,
            "time_str": ac_time_str,
            "tries_desc": tries_desc,
            "status_desc": status_desc,
            "table_result": table_result,
            "solved": (solved_in_contest or solved_upsolve),
            "ac_sub": ac_sub,
        }

    # 5. Build Markdown Content
    slug, img_folder, short_title, desc = generate_post_slug_and_title(contest_name, contest_id)
    now_kst = datetime.now(KST)
    date_str = now_kst.strftime("%Y-%m-%d %H:%M:%S +0900")
    file_date = now_kst.strftime("%Y-%m-%d")

    # Auto-create image folder for this post
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    img_dir = os.path.join(base_dir, "assets", "img", "posts", "codeforces", img_folder)
    os.makedirs(img_dir, exist_ok=True)
    img_relative_path = f"/assets/img/posts/codeforces/{img_folder}"

    # Determine virtual start time (or official start time) and contest mode (실전 vs 버추얼)
    official_start = contest_info.get("startTimeSeconds")
    start_ts = None
    has_contest_subs = False
    for sub in submissions:
        rel = sub.get("relativeTimeSeconds", 2147483647)
        if rel <= contest_duration and rel >= 0:
            has_contest_subs = True
            start_ts = sub.get("creationTimeSeconds", 0) - rel
            break

    if not start_ts:
        start_ts = official_start

    if start_ts:
        start_dt = datetime.fromtimestamp(start_ts, tz=KST)
        start_time_str = start_dt.strftime("%Y-%m-%d %H:%M")
    else:
        start_time_str = "-"

    # Determine tag: 실전 vs 버추얼
    if has_contest_subs and official_start and abs(start_ts - official_start) <= 300:
        contest_mode_tag = "실전"
    else:
        contest_mode_tag = "버추얼"

    duration_str = format_duration(contest_duration)

    md_lines = []
    # Front matter
    md_lines.append("---")
    md_lines.append(f'title: "{short_title}"')
    md_lines.append(f"date: {date_str}")
    md_lines.append("last_modified_at:")
    md_lines.append("categories: [Codeforces]")
    md_lines.append(f"tags: [Codeforces, {contest_mode_tag}]")
    md_lines.append(f"description: {desc}")
    md_lines.append("math: true")
    md_lines.append("---")
    md_lines.append("")
    md_lines.append("<!-- #999999 #33cc33 #44ddaa #2222ff #aa00ff #ff9900 #ff2222 -->")
    md_lines.append("")
    md_lines.append("## 개요")
    md_lines.append("")
    md_lines.append(f"* **일시**: {start_time_str} (KST)")
    md_lines.append(f"* **진행 시간**: {duration_str}")
    md_lines.append("")
    
    # Timeline Table (Individual submission logs in chronological order)
    if submissions:
        md_lines.append("| 제출 시간 | 문제 | 결과 | 시도 | 구분 |")
        md_lines.append("| :---: | :---: | :---: | :---: | :---: |")
        
        prob_try_counter = {p["index"]: 0 for p in problems}
        for sub in submissions:
            p_idx = sub["problem"]["index"]
            prob_try_counter[p_idx] = prob_try_counter.get(p_idx, 0) + 1
            current_try = prob_try_counter[p_idx]
            
            verdict = sub.get("verdict")
            passed_tests = sub.get("passedTestCount", 0)
            verdict_badge = format_verdict_badge(verdict, passed_tests)
            
            rel_time = sub.get("relativeTimeSeconds", 2147483647)
            is_in_contest = (rel_time <= contest_duration)
            time_str = f"`{format_relative_time(rel_time)}`" if is_in_contest else "-"
            
            if is_in_contest:
                status_desc = "대회 중"
            else:
                if verdict == "OK":
                    status_desc = '<span style="color:#aa00ff; font-weight:bold;">Upsolved</span>'
                else:
                    status_desc = "업솔빙"
            
            md_lines.append(f"| {time_str} | **{p_idx}** | {verdict_badge} | {current_try}트 | {status_desc} |")
    else:
        md_lines.append("> 제출 기록이 없습니다.")

    md_lines.append("")
    md_lines.append("## 문제")
    md_lines.append("")

    # Problem Sections
    for p in problems:
        idx = p["index"]
        pa = problem_analysis[idx]
        p_name = p.get("name", "")
        p_tags = ", ".join(p.get("tags", [])) or "분류"
        prob_url = f"https://codeforces.com/contest/{contest_id}/problem/{idx}"
        has_submissions = len(prob_subs.get(idx, [])) > 0

        # Try to find local solution code
        code_content = find_local_solution_code(contest_id, idx, args.code_dir)

        md_lines.append(f"### [{idx}번 - {p_name}]({prob_url})")
        md_lines.append("")
        md_lines.append("")

        if has_submissions:
            md_lines.append("* 설명")
            md_lines.append(f"* **분류**: {p_tags}")
            md_lines.append("")
            md_lines.append(
                "|                            체감 난이도                             |                    레이팅 (CLIST) 난이도                     | 대회 결과 |"
            )
            md_lines.append(
                "| :----------------------------------------------------------------: | :----------------------------------------------------------: | :-------: |"
            )
            md_lines.append(
                f"| <img src=\"/assets/img/tier/{pa['tier_num']}.png\" alt=\"{pa['tier_name']}\" width=\"20\"> | {pa['rating_html']} | {pa['table_result']} |"
            )
        else:
            md_lines.append("* 미래의 내가 업솔빙한다면 업데이트 예정")
            md_lines.append("* **분류**: ")
            md_lines.append("")
            md_lines.append(
                "|                             체감 난이도                             |                    레이팅 (CLIST) 난이도                     | 대회 결과 |"
            )
            md_lines.append(
                "| :-----------------------------------------------------------------: | :----------------------------------------------------------: | :-------: |"
            )
            md_lines.append(
                f"| <img src=\"/assets/img/tier/0.png\" alt=\"??\" width=\"20\"> | {pa['rating_html']} |     -     |"
            )

        md_lines.append("")
        md_lines.append("<details>")
        md_lines.append("<summary>코드</summary>")
        md_lines.append('<div markdown="1">')
        md_lines.append("")
        md_lines.append("{% raw %}")
        md_lines.append("```cpp")
        if code_content:
            md_lines.append(code_content)
        else:
            md_lines.append("")
        md_lines.append("```")
        md_lines.append("{% endraw %}")
        md_lines.append("")
        md_lines.append("</div>")
        md_lines.append("</details>")
        md_lines.append("")
        md_lines.append("")

    md_lines.append("## 후기")
    md_lines.append("")
    md_lines.append(f"![score]({img_relative_path}/score.png)")
    md_lines.append(f"![rating]({img_relative_path}/rating.png)")
    md_lines.append("")
    md_lines.append("* ")
    md_lines.append("")

    # 6. Save File
    target_dir = args.output_dir or os.path.join(base_dir, "_posts", "Codeforces")
    os.makedirs(target_dir, exist_ok=True)

    filename = f"{file_date}-{slug}.md"
    file_path = os.path.join(target_dir, filename)

    if os.path.exists(file_path) and not args.force:
        print(f"[!] File already exists: {file_path}")
        overwrite = input("Overwrite? (y/N): ").strip().lower()
        if overwrite != "y":
            # Append timestamp to filename
            filename = f"{file_date}-{slug}-{now_kst.strftime('%H%M%S')}.md"
            file_path = os.path.join(target_dir, filename)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    print(f"\n[🎉 Success] Post generated successfully!")
    print(f"📝 Post File : {file_path}")
    print(f"🖼️  Image Dir : {img_dir} ({img_relative_path})\n")


if __name__ == "__main__":
    main()
