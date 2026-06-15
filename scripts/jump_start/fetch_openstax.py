import os
import subprocess

def fetch_openstax_github(repo_url, output_dir):
    print(f"Fetching OpenStax data from GitHub: {repo_url}")
    
    if os.path.exists(output_dir) and os.path.exists(os.path.join(output_dir, ".git")):
        print(f"Repository already exists at {output_dir}. Pulling latest changes...")
        subprocess.run(["git", "-C", output_dir, "pull"], check=True)
    else:
        print(f"Cloning repository to {output_dir}...")
        subprocess.run(["git", "clone", "--depth", "1", repo_url, output_dir], check=True)
        
    print("GitHub fetch complete!")

if __name__ == "__main__":
    repo = "https://github.com/openstax/osbooks-prealgebra-bundle.git"
    output = "data/openstax/osbooks-prealgebra-bundle"
    fetch_openstax_github(repo, output)
