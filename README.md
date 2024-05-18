# gitlab_merge_request_reviewer

`gitlab_merge_request_reviewer` is a tool that allows ChatGPT to perform code reviews on GitLab merge requests. This tool uses the OpenAI or Azure OpenAI API to provide feedback on code changes.

## How to Run

### Preparing the Python Environment

1. **Install Python**:
    - This tool has been tested with Python 3.11. If Python is not installed, please install it from the [official site](https://www.python.org/downloads/).

2. **Install Dependencies**:
    - The required packages are listed in `requirements.txt`. After setting up a Python 3.11 environment for this tool using venv or similar, run the following command to install the packages:

    ```sh
    pip install -r requirements.txt
    ```

### Setting up config.ini

The `config.ini` file is used to configure the necessary settings for this tool. Refer to the following content and set appropriate values.

```ini:config.ini
[gitlab]
url = https://gitlab.com/  # Specify the GitLab URL. Usually, it is https://gitlab.com/.
private_token = your_private_token  # Specify your GitLab private token. You can obtain it from your GitLab user settings.
project_id = 11111111  # Specify the ID of the target project. You can check it on the project's settings page.
merge_request_iid = 1  # Specify the IID of the target merge request. It corresponds to the number at the end of the merge request URL.

[api]
provider = openai  # Specify the API provider to use. You can specify either openai or azure.
openai_api_key = your_openai_api_key  # Specify your OpenAI API key. You can obtain it from your OpenAI account.
azure_openai_api_key = your_azure_openai_api_key  # Specify your Azure OpenAI API key. You can obtain it from the Azure portal.
azure_openai_api_version = 2024-02-15-preview  # Specify the Azure OpenAI API version. Usually, the default value is fine.
azure_openai_endpoint = https://your-azure-endpoint  # Specify the Azure OpenAI endpoint. You can check it on the Azure portal.
azure_openai_model_name = gpt-4  # Specify the Azure OpenAI model name to use. Specify the model name deployed on Azure.

[locale]
language = Japanese  # Specify the language for providing code review feedback. Example: Japanese, English
```

### Running the Main Process

1. **Setting up config.ini**:
    - Refer to the above content and set up the `config.ini` file appropriately.

2. **Running the Script**:
    - Run the following command to start the code review of the merge request:

    ```sh
    python main.py
    ```

3. **Checking the Output**:
    - If the script runs successfully, the commit information of the merge request and the code review feedback will be displayed on the console.

## Notes

- **Managing API Keys**:
  - API keys are confidential information. Be careful not to leak them to third parties.
  - Do not expose the `config.ini` file to the public.

- **GitLab Access Permissions**:
  - The private token needs to have access permissions to the target project. Use a token with appropriate permissions.

- **API Usage Limits**:
  - OpenAI and Azure OpenAI APIs have usage limits. Refer to the documentation of each provider for details.
