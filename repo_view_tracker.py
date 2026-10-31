import os
import json
from github import Github

# --- Configuration ---
# MUST be in 'username/repository_name' format
REPOSITORIES_TO_TRACK = [
    "om1002/PowerBI"  # <-- Change YOUR_GITHUB_USERNAME to your actual username
]
DATA_FILE = "repo_views.json"

# --- Utility Functions ---
def load_view_counts():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Warning: '{DATA_FILE}' contains invalid JSON. Starting fresh.")
    return {}

def save_view_counts(counts):
    with open(DATA_FILE, 'w') as f:
        json.dump(counts, f, indent=4)

# --- Main Functionality ---
def get_repository_views(repo_full_name, g):
    try:
        repo = g.get_repo(repo_full_name)
        traffic = repo.get_views_traffic()
        
        # Extract daily breakdown data instead of just the total sum
        daily_data = {}
        if traffic and hasattr(traffic, 'views'):
            for view in traffic.views:
                # Convert datetime object to string key "YYYY-MM-DD"
                date_str = view.timestamp.strftime("%Y-%m-%d")
                daily_data[date_str] = {
                    "count": view.count,
                    "uniques": view.uniques
                }
        return daily_data
    except Exception as e:
        print(f"Error fetching data for {repo_full_name}: {e}")
        return None

def main():
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("Error: GITHUB_TOKEN environment variable is missing.")
        return

    print("Connecting to GitHub...")
    g = Github(token)

    view_counts = load_view_counts()
    updated_any_repo = False

    for repo_full_name in REPOSITORIES_TO_TRACK:
        print(f"Processing: {repo_full_name}")
        
        # Get raw daily breakdown from last 14 days
        api_daily_views = get_repository_views(repo_full_name, g)

        if api_daily_views:
            if repo_full_name not in view_counts:
                view_counts[repo_full_name] = {
                    "daily_history": {},
                    "cumulative_views": 0
                }
            
            # Ensure modern key structure exists if migrating from your old format
            if "daily_history" not in view_counts[repo_full_name]:
                view_counts[repo_full_name]["daily_history"] = {}

            history = view_counts[repo_full_name]["daily_history"]

            # Merge new daily data into our permanent historical storage
            for date_str, metrics in api_daily_views.items():
                history[date_str] = metrics  # Overwrites/updates with latest exact stats for that day

            # Calculate total cumulative views from all historical daily records safely
            total_historical = sum(day["count"] for day in history.values())
            view_counts[repo_full_name]["cumulative_views"] = total_historical
            
            print(f"  Updated {repo_full_name}. Lifetime Cumulative Views recorded: {total_historical}")
            updated_any_repo = True

    if updated_any_repo or not os.path.exists(DATA_FILE):
        print(f"\nSaving updated view counts to '{DATA_FILE}'...")
        save_view_counts(view_counts)

    print("\n--- Current Cumulative Repository Statistics ---")
    for repo, data in view_counts.items():
        print(f"{repo}: Total Lifetime Views logged -> {data.get('cumulative_views')}")

if __name__ == "__main__":
    main()
