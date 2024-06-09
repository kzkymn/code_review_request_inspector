import configparser
from abc import ABC, abstractmethod

import openai
import requests

# 設定ファイルを読み込む
config = configparser.ConfigParser()
config.read("./config.ini", encoding="utf-8")

# サービス設定
SERVICE_PROVIDER = config["service"]["provider"]

# OPENAI API設定
OPENAI_API_PROVIDER_TYPE = config["api"]["provider"]
OPENAI_API_KEY = config["api"]["openai_api_key"]
AZURE_OPENAI_API_KEY = config["api"]["azure_openai_api_key"]
AZURE_OPENAI_ENDPOINT = config["api"]["azure_openai_endpoint"]
AZURE_OPENAI_API_VERSION = config["api"]["azure_openai_api_version"]
CHATGPT_MODEL_NAME = config["api"]["chatgpt_model_name"]

# 言語設定
LANGUAGE = config["locale"]["language"]

# プロンプトの設定
PROMPT_FOR_REVIEW = "Please review the following code changes and provide feedback in {}. If necessary, please include suggestions for better code improvements in your feedback. :\n\n{}"


class CodeReviewService(ABC):
    def __init__(self, config):
        self.config = config

    @abstractmethod
    def get_commits(self):
        pass

    @abstractmethod
    def get_commit_diff(self, commit_id):
        pass


class GitLabService(CodeReviewService):
    def __init__(self, config):
        super().__init__(config)
        self.url = config["gitlab"]["url"]
        self.private_token = config["gitlab"]["private_token"]
        self.project_id = config["gitlab"]["project_id"]
        self.merge_request_iid = config["gitlab"]["merge_request_iid"]

    def get_commits(self):
        headers = {"Private-Token": self.private_token}
        api_url = f"{self.url}/api/v4/projects/{self.project_id}/merge_requests/{self.merge_request_iid}/commits"

        response = requests.get(api_url, headers=headers)

        if response.status_code == 200:
            commits = response.json()
            # GitHubのレスポンス形式に合わせてキーを変換
            for commit in commits:
                commit["sha"] = commit.pop("id")
                commit["commit"] = {
                    "message": commit.pop("title"),
                    "author": {
                        "name": commit.pop("author_name"),
                        "date": commit.pop("created_at"),
                    },
                }
            return commits
        else:
            print(f"Failed to retrieve commits from GitLab: {response.status_code}")
            return []

    def get_commit_diff(self, commit_id):
        headers = {"Private-Token": self.private_token}
        api_url = f"{self.url}/api/v4/projects/{self.project_id}/repository/commits/{commit_id}/diff"

        response = requests.get(api_url, headers=headers)

        if response.status_code == 200:
            diffs = response.json()
            for diff in diffs:
                if "diff" in diff:
                    diff["patch"] = diff.pop("diff")
            return diffs
        else:
            print(f"Failed to retrieve commit diff from GitLab: {response.status_code}")
            return []


class GitHubService(CodeReviewService):
    def __init__(self, config):
        super().__init__(config)
        self.url = config["github"]["url"]
        self.token = config["github"]["token"]
        self.owner = config["github"]["owner"]
        self.repo = config["github"]["repo"]
        self.pull_request_number = config["github"]["pull_request_number"]

    def get_commits(self):
        headers = {"Authorization": f"token {self.token}"}
        api_url = f"{self.url}/repos/{self.owner}/{self.repo}/pulls/{self.pull_request_number}/commits"

        response = requests.get(api_url, headers=headers)

        if response.status_code == 200:
            commits = response.json()
            return commits
        else:
            print(f"Failed to retrieve commits from GitHub: {response.status_code}")
            return []

    def get_commit_diff(self, commit_id):
        headers = {"Authorization": f"token {self.token}"}
        api_url = f"{self.url}/repos/{self.owner}/{self.repo}/commits/{commit_id}"

        response = requests.get(api_url, headers=headers)

        if response.status_code == 200:
            commit_data = response.json()
            diffs = commit_data.get("files", [])
            return diffs
        else:
            print(f"Failed to retrieve commit diff from GitHub: {response.status_code}")
            return []


def get_diff_texts(diffs):
    diff_texts = [diff.get("patch") for diff in diffs if "patch" in diff]
    return diff_texts


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
        model=CHATGPT_MODEL_NAME,
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


def get_commits_and_diffs(service):
    commits = service.get_commits()
    diffs = []

    if commits:
        for commit in commits:
            diffs.extend(
                service.get_commit_diff(
                    commit["id"] if "id" in commit else commit["sha"]
                )
            )

    return commits, diffs


def review_code(service, review_func):
    commits, diffs = get_commits_and_diffs(service)

    if commits:
        print("New commits in the pull/merge request:")
        for commit in commits:
            print(f"Commit ID: {commit.get('sha')}")
            print(f"Title: {commit['commit']['message']}")
            print(f"Author: {commit['commit']['author']['name']}")
            print(f"Date: {commit['commit']['author']['date']}")
            print("=" * 40)

        if diffs:
            diff_texts = get_diff_texts(diffs)
            diff_text = "\n".join(diff_texts)

            review = review_func(diff_text)

            print("Code Review for the Pull/Merge Request:")
            print(review)
            print("=" * 40)
    else:
        print("No commits found or failed to retrieve commits.")


if __name__ == "__main__":
    if SERVICE_PROVIDER == "gitlab":
        service = GitLabService(config)
    elif SERVICE_PROVIDER == "github":
        service = GitHubService(config)
    else:
        raise ValueError(f"Unsupported service provider: {SERVICE_PROVIDER}")

    if OPENAI_API_PROVIDER_TYPE == "azure":
        review_func = review_code_with_azure
    else:
        review_func = review_code_with_openai

    review_code(service=service, review_func=review_func)
