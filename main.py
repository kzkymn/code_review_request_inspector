import configparser
import os

import openai
import requests

# 設定ファイルを読み込む
config = configparser.ConfigParser()
config.read("config.ini", encoding="utf-8")

# GitLabの設定
GITLAB_URL = config["gitlab"]["url"]
PRIVATE_TOKEN = config["gitlab"]["private_token"]
PROJECT_ID = config["gitlab"]["project_id"]
MERGE_REQUEST_IID = config["gitlab"]["merge_request_iid"]

# API設定
API_PROVIDER = config["api"]["provider"]
OPENAI_API_KEY = config["api"]["openai_api_key"]
AZURE_OPENAI_API_KEY = config["api"]["azure_openai_api_key"]
AZURE_OPENAI_ENDPOINT = config["api"]["azure_openai_endpoint"]
AZURE_OPENAI_API_VERSION = config["api"]["azure_openai_api_version"]
AZURE_OPENAI_MODEL_NAME = config["api"]["azure_openai_model_name"]

# 言語設定
LANGUAGE = config["locale"]["language"]

# プロンプトの設定
PROMPT_FOR_REVIEW = "Please review the following code changes and provide feedback in {}. If necessary, please include suggestions for better code improvements in your feedback. :\n\n{}"


def get_merge_request_commits():
    headers = {"Private-Token": PRIVATE_TOKEN}

    api_url = f"{GITLAB_URL}/api/v4/projects/{PROJECT_ID}/merge_requests/{MERGE_REQUEST_IID}/commits"

    response = requests.get(api_url, headers=headers)

    if response.status_code == 200:
        commits = response.json()
        return commits
    else:
        print(f"Failed to retrieve commits: {response.status_code}")
        return []


def get_commit_diff(commit_id):
    headers = {"Private-Token": PRIVATE_TOKEN}

    api_url = (
        f"{GITLAB_URL}/api/v4/projects/{PROJECT_ID}/repository/commits/{commit_id}/diff"
    )

    response = requests.get(api_url, headers=headers)

    if response.status_code == 200:
        diffs = response.json()
        return diffs
    else:
        print(f"Failed to retrieve commit diff: {response.status_code}")
        return []


def _create_messages(diff_text):
    return [
        {"role": "system", "content": "You are a helpful code reviewer."},
        {"role": "user", "content": PROMPT_FOR_REVIEW.format(LANGUAGE, diff_text)},
    ]


def _get_openai_client(api_key, api_version=None, azure_endpoint=None):
    if azure_endpoint:
        return openai.AzureOpenAI(
            api_key=api_key,
            api_version=api_version,
            azure_endpoint=azure_endpoint,
        )
    else:
        return openai.OpenAI(api_key=OPENAI_API_KEY)


def _review_code(client, diff_text):
    response = client.chat.completions.create(
        model=AZURE_OPENAI_MODEL_NAME,
        messages=_create_messages(diff_text),
        temperature=0.0,
    )
    review = response.choices[0].message.content
    return review


def review_code_with_openai(diff_text):
    client = _get_openai_client(api_key=OPENAI_API_KEY)
    return _review_code(client, diff_text)


def review_code_with_azure(diff_text):
    client = _get_openai_client(
        api_key=AZURE_OPENAI_API_KEY,
        api_version=AZURE_OPENAI_API_VERSION,
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
    )
    return _review_code(client, diff_text)


if __name__ == "__main__":
    commits = get_merge_request_commits()

    if commits:
        print("New commits in the merge request:")
        all_diffs = []
        for commit in commits:
            print(f"Commit ID: {commit['id']}")
            print(f"Title: {commit['title']}")
            print(f"Author: {commit['author_name']}")
            print(f"Date: {commit['created_at']}")
            print("=" * 40)

            diff = get_commit_diff(commit["id"])
            if diff:
                all_diffs.extend(diff)

        if all_diffs:
            diff_text = "\n".join([d["diff"] for d in all_diffs])
            if API_PROVIDER == "azure":
                review = review_code_with_azure(diff_text)
            else:
                review = review_code_with_openai(diff_text)

            print("Code Review for the Merge Request:")
            print(review)
            print("=" * 40)
    else:
        print("No commits found or failed to retrieve commits.")
