"""Helper script to download all pull requests from GitHub.
Optionally uses environment variable GITHUB_TOKEN for authentication
(not required for public repositories, but recommended to avoid rate limits).
Saves all pull requests to pull_requests.json
"""

import requests
import json


def get_pull_requests(page: int = 1):
    """Fetch merged pull requests from GitHub API"""
    url = "https://api.github.com/repos/iterorganization/IMAS-Data-Dictionary/pulls"

    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    response = requests.get(
        url,
        headers=headers,
        params={"state": "closed", "per_page": 100, "page": page},
    )

    return response.json(), response.links


if __name__ == "__main__":
    page = 1
    prs = []
    while True:
        data, links = get_pull_requests(page)
        # Filter to only merged PRs (closed PRs with merged_at timestamp)
        merged_prs = [pr for pr in data if pr.get("merged_at") is not None]
        prs.extend(merged_prs)
        
        # Check if there's a next page
        if "next" not in links:
            break
        page += 1

    with open("pull_requests.json", "w") as f:
        json.dump(prs, f)
