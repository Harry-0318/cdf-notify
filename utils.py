import requests
import os
import csv
import requests
import csv
import os

async def get_user_problem_status(handle: str):
    """
    Fetch Codeforces problemset and user submissions,
    then append rows to solved.csv with:
    handle, problemID ('1234A'), status ('solved', 'unsolved', 'not-tried')
    """

    # 1. Get problemset
    problems_url = "https://codeforces.com/api/problemset.problems"
    problems_data = requests.get(problems_url).json()
    if problems_data["status"] != "OK":
        raise Exception("Failed to fetch problemset")

    problems = problems_data["result"]["problems"]

    all_problem_ids = {
        f"{p['contestId']}{p['index']}" for p in problems
    }

    # 2. Get user submissions
    submissions_url = (
        f"https://codeforces.com/api/user.status?handle={handle}&from=1&count=100000"
    )
    sub_data = requests.get(submissions_url).json()
    if sub_data["status"] != "OK":
        raise Exception("Failed to fetch user submissions")

    submissions = sub_data["result"]

    solved = set()
    attempted_not_solved = set()

    # Process submissions
    for s in submissions:
        if "contestId" not in s or "problem" not in s:
            continue
        
        p = s["problem"]
        pid = f"{p['contestId']}{p['index']}"

        if s["verdict"] == "OK":
            solved.add(pid)
        else:
            attempted_not_solved.add(pid)

    # Open CSV file in append mode
    file_exists = os.path.isfile("solved.csv")
    with open("solved.csv", "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        # Write header only if file does not yet exist
        if not file_exists:
            writer.writerow(["handle", "problem", "status"])

        # Write rows for each problem
        for pid in all_problem_ids:
            if pid in solved:
                status = "solved"
            elif pid in attempted_not_solved:
                status = "unsolved"
            else:
                status = "not-tried"

            writer.writerow([handle, pid, status])

async def get_problems(rating: int, n: int, solved_file: str = "solved.csv",handle: str="") -> list:
    """
    Fetches n Codeforces problems with the given rating,
    skipping problems listed in solved.csv (format: 1234A).

    Parameters:
        rating (int): Desired problem rating.
        n (int): Number of problems to return.
        solved_file (str): Path to solved.csv.

    Returns:
        List[str]: List of Codeforces problem URLs.
    """

    # Load solved problem identifiers from solved.csv
    solved = set()
    if os.path.exists(solved_file):
        with open(solved_file, newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['handle']==handle and row['status']=='solved':
                    solved.add(row['problem'])
                    

    # Fetch Codeforces problems
    url = "https://codeforces.com/api/problemset.problems"
    response = requests.get(url)
    data = response.json()

    if data["status"] != "OK":
        raise Exception("Failed to fetch Codeforces problems.")

    problems = data["result"]["problems"]

    # Filter by rating and remove solved ones
    filtered = []
    for p in problems:
        if "rating" not in p:
            continue
        if p["rating"] != rating:
            continue

        problem_id = f"{p['contestId']}{p['index']}"  # e.g. 1234A

        if problem_id in solved:
            continue  # skip solved problems

        filtered.append(p)

        if len(filtered) == n:
            break

    # Convert problems to URLs
    links = [
        f"https://codeforces.com/problemset/problem/{p['contestId']}/{p['index']}"
        for p in filtered
    ]

    return links