"""Helper script to download all pull requests from GitHub.
Fetches all merged pull requests from the public DD repository
and saves a record of them to pull_requests.json
"""

import requests
import json


def get_pull_requests(page: int = 1):
    """Fetch merged pull requests from GitHub.
    
    GitHub API returns closed PRs (which includes merged PRs).
    We filter for merged PRs by checking the 'merged_at' field.
    No authentication required for public repositories.
    """
    url = "https://api.github.com/repos/iterorganization/IMAS-Data-Dictionary/pulls"

    response = requests.get(
        url,
        headers={
            "Accept": "application/vnd.github.v3+json",
        },
        params={"state": "closed", "sort": "updated", "direction": "desc", "page": page, "per_page": 100},
    )
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    page = 1
    prs = []
    while True:
        data = get_pull_requests(page)
        if not data:
            break
        # Filter for merged PRs only (merged_at is not null)
        merged_prs = [pr for pr in data if pr.get("merged_at") is not None]
        prs.extend(merged_prs)
        # Stop if we got less than 100 items (last page)
        if len(data) < 100:
            break
        page += 1

    with open("pull_requests.json", "w") as f:
        json.dump(prs, f)
