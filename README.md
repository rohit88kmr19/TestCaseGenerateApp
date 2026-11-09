# 🧪 AI Test Case Generator

An AI-powered test case generation application built with **Python, Streamlit, LangChain, and OpenRouter**.

The application converts software requirements, user stories, and acceptance criteria into structured test cases. It helps QA engineers generate, review, filter, analyze, and export test scenarios across different application types.

---

## 1. Key Features

### AI-Powered Test Case Generation
- Generate test cases from requirements and user stories.
- Analyze business rules and acceptance criteria.
- Identify assumptions and open questions.
- Generate structured test scenarios with requirement traceability.

### Supported Application Types
- Web Application
- Mobile Application
- API
- POS / Retail Application
- Desktop Application

### Supported Testing Types
- All Types
- Functional Testing
- Positive Testing
- Negative Testing
- Boundary Value Testing
- Regression Testing
- API Testing
- Accessibility Testing

### Test Configuration
- Priority Focus: High, Medium, Low, or All Priorities.
- Test Case Detail Level: Standard or Detailed.
- Application Type selection.
- Testing Type selection.

### Test Case Management
- View individual test cases.
- Review preconditions and test data.
- View detailed execution steps.
- Review expected results.
- View requirement coverage.
- Search test cases.
- Filter by priority and test type.
- Expand or collapse test case details.

### Coverage Dashboard
- Total generated test cases.
- High-priority test cases.
- Medium-priority test cases.
- Low-priority test cases.
- Test type distribution.
- Priority distribution charts.

### Export Options
Download generated test cases in:
- JSON
- CSV (Excel-compatible)
- Markdown

### Recent Generation History
- View the five most recent generations during the active Streamlit session.
- Reload previously generated results within the current session.

---

## 2. Technology Stack

| Component | Technology |
|---|---|
| Programming Language | Python |
| Frontend / UI | Streamlit |
| AI Provider | OpenRouter |
| LLM Integration | LangChain |
| Output Parser | LangChain StrOutputParser |
| Data Processing | Pandas |
| Configuration Management | python-dotenv |
| Prompt Management | LangChain JSON Prompt |
| Export Formats | JSON, CSV, Markdown |
| Environment Management | UV |
| Source Control | Git / GitHub |
| Deployment | Streamlit Community Cloud |

---

## 3. Project Structure

Recommended repository structure:

```text
AI-Test-Case-Generator/
│
├── app.py
├── test_case_template.json
├── requirements.txt
├── pyproject.toml
├── uv.lock
├── README.md
├── .env
├── .gitignore
│
└── .streamlit/
    └── secrets.toml
```

### File Descriptions

| File | Description |
|---|---|
| `app.py` | Main Streamlit application and application workflow. |
| `test_case_template.json` | LangChain prompt template used for AI test case generation. |
| `requirements.txt` | Python dependencies used by Streamlit Cloud. |
| `pyproject.toml` | Project metadata and dependency configuration for UV. |
| `uv.lock` | Locked dependency versions for reproducible local installations. |
| `.env` | Local environment variables and API configuration. |
| `.gitignore` | Files and folders excluded from Git tracking. |
| `.streamlit/secrets.toml` | Local Streamlit secrets configuration. |
| `README.md` | Project documentation and setup instructions. |

---

## 4. Prerequisites

Install the following tools before setting up the application:

1. Python 3.10 or later.
2. UV package manager.
3. Git.
4. GitHub account.
5. OpenRouter account.
6. OpenRouter API key.

### Install UV

Official installation documentation:

https://docs.astral.sh/uv/getting-started/installation/

Verify installation:

```bash
uv --version
```

Verify Python:

```bash
python --version
```

---

## 5. Local Installation and Setup Using UV

### Step 1: Clone the Repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
```

Navigate to the project directory:

```bash
cd AI-Test-Case-Generator
```

### Step 2: Create a Virtual Environment

Create the environment using UV:

```bash
uv venv
```

This creates a `.venv` directory inside your project.

### Step 3: Activate the Virtual Environment

**Windows:**

```bash
.venv\Scripts\activate
```

**Mac / Linux:**

```bash
source .venv/bin/activate
```

### Step 4: Install Dependencies

Create a `requirements.txt` file with the following dependencies:

```txt
streamlit
pandas
python-dotenv
langchain-core
langchain-openrouter
```

Install the dependencies using UV:

```bash
uv pip install -r requirements.txt
```

### Step 5: Configure Environment Variables

Create a `.env` file in the project root.

```env
Model=YOUR_OPENROUTER_MODEL_NAME
OPENROUTER_API_KEY=YOUR_OPENROUTER_API_KEY
```

Replace the placeholders with your actual OpenRouter model name and API key.

**Important:** Never upload your API key or `.env` file to a public GitHub repository.

### Step 6: Configure the Prompt Template

Ensure that the following file exists in the project root:

```text
test_case_template.json
```

The application loads the prompt using:

```python
prompt = load_prompt(str(PROMPT_PATH))
```

The prompt template must support the following input variables:

| Variable | Description |
|---|---|
| `requirement` | User story, requirement, or acceptance criteria. |
| `application_type` | Selected application type. |
| `testing_type` | Selected testing scope. |
| `priority` | Priority focus. |
| `detail_level` | Standard or Detailed. |

The prompt should instruct the AI model to return valid JSON.

The generated JSON should contain:

- `test_cases`
- `assumptions`
- `open_questions`

Each test case should support the fields consumed by the application:

- `test_case_id`
- `scenario`
- `test_type`
- `priority`
- `preconditions`
- `test_data`
- `steps`
- `expected_result`
- `requirement_coverage`

### Step 7: Run the Application

Start the Streamlit application:

```bash
uv run streamlit run app.py
```

Alternatively, when the virtual environment is activated:

```bash
streamlit run app.py
```

### Step 8: Open the Application

Open the following URL in your browser:

```text
http://localhost:8501
```

The AI Test Case Generator application should now be available.

---

## 6. OpenRouter Configuration

The application uses `ChatOpenRouter` to connect to an AI model through OpenRouter.

Current implementation:

```python
def get_chain(model_name: str, prompt_mtime: float):
    prompt = load_prompt(str(PROMPT_PATH))
    model = ChatOpenRouter(model=model_name)
    return prompt | model | StrOutputParser()
```

### Environment Configuration

The application reads the model name using:

```python
MODEL_NAME = os.getenv("Model")
```

The OpenRouter API key must also be configured for the installed `langchain-openrouter` client.

For local development, configure it through `.env`.

For Streamlit Cloud, configure it through Streamlit Secrets and pass the key to the client using the configuration supported by your installed package version.

Example environment variables:

```env
Model=YOUR_OPENROUTER_MODEL_NAME
OPENROUTER_API_KEY=YOUR_OPENROUTER_API_KEY
```

---

## 7. UV Dependency Management

UV is used for local virtual environment and dependency management.

### Create Virtual Environment

```bash
uv venv
```

### Install Dependencies

```bash
uv pip install -r requirements.txt
```

### Add a New Dependency

If you maintain a `pyproject.toml`:

```bash
uv add PACKAGE_NAME
```

For example:

```bash
uv add requests
```

### Remove a Dependency

```bash
uv remove PACKAGE_NAME
```

### Update Dependencies

```bash
uv lock --upgrade
uv sync
```

### Generate Requirements File from UV Project

If dependencies are managed through `pyproject.toml` and `uv.lock`, generate the deployment requirements file using:

```bash
uv export --format requirements-txt --no-dev --output-file requirements.txt
```

### Reinstall Dependencies from Lock File

```bash
uv sync
```

**Recommendation:** Maintain `pyproject.toml` and `uv.lock` for local development and keep `requirements.txt` in GitHub for Streamlit Community Cloud compatibility.

---

## 8. GitHub Configuration

Before pushing the application to GitHub, create a `.gitignore` file.

```gitignore
# Environment
.env
.venv/
venv/

# Streamlit secrets
.streamlit/secrets.toml

# Python cache
__pycache__/
*.pyc

# IDE files
.vscode/
.idea/

# OS files
.DS_Store
Thumbs.db
```

### Push Project to GitHub

```bash
git init
git add .
git commit -m "Initial AI Test Case Generator"
git branch -M main
git remote add origin YOUR_GITHUB_REPOSITORY_URL
git push -u origin main
```

Before pushing, verify that `.env` and `.streamlit/secrets.toml` are not tracked.

---

## 9. Deploy on Streamlit Community Cloud

The application can be deployed using Streamlit Community Cloud.

### Step 1: Open Streamlit Community Cloud

https://share.streamlit.io/

Sign in using your GitHub account.

### Step 2: Create a New Application

1. Click **Create app**.
2. Select your GitHub repository.
3. Select the deployment branch, normally `main`.
4. Set the main application file path to:

```text
app.py
```

5. Click **Deploy**.

### Step 3: Configure Streamlit Secrets

After deployment:

1. Open your deployed application.
2. Navigate to application settings.
3. Open the Secrets section.
4. Add your OpenRouter configuration.

Example:

```toml
Model = "YOUR_OPENROUTER_MODEL_NAME"
OPENROUTER_API_KEY = "YOUR_OPENROUTER_API_KEY"
```

Save the configuration and restart the application if required.

### Step 4: Verify Deployment

Verify the following:

- Application loads successfully.
- Model configuration is available.
- OpenRouter authentication works.
- Prompt template loads successfully.
- Test cases can be generated.
- JSON export works.
- CSV export works.
- Markdown export works.

### Important: Streamlit Secrets Integration

Streamlit Cloud Secrets are not automatically available through `os.getenv()`.

The current application uses:

```python
load_dotenv()
MODEL_NAME = os.getenv("Model")
```

Update the configuration to support both local `.env` and Streamlit Cloud Secrets.

For example:

```python
load_dotenv()

MODEL_NAME = (
    st.secrets["Model"]
    if "Model" in st.secrets
    else os.getenv("Model")
)

OPENROUTER_API_KEY = (
    st.secrets["OPENROUTER_API_KEY"]
    if "OPENROUTER_API_KEY" in st.secrets
    else os.getenv("OPENROUTER_API_KEY")
)
```

Then configure `ChatOpenRouter` with the retrieved API key using the supported constructor parameter or environment-variable mechanism for your installed package version.

---

## 10. Application Workflow

### Step 1: Enter Requirement

Enter a requirement, user story, or acceptance criteria.

Example:

```text
As a registered user, I want to log in using my
email and password so that I can access my account.

After 5 failed login attempts, the account should
be locked for 15 minutes.
```

### Step 2: Configure Test Generation

Select:

- Application Type
- Testing Type
- Priority Focus
- Test Case Detail Level

### Step 3: Generate Test Cases

Click:

```text
Generate Test Cases
```

The application sends the requirement and selected configuration to the AI model.

### Step 4: Review Generated Results

The generated results include:

- Test Case ID
- Scenario
- Test Type
- Priority
- Preconditions
- Test Data
- Execution Steps
- Expected Result
- Requirement Coverage

### Step 5: Review Assumptions and Questions

Review the assumptions and open questions identified by the AI.

This helps QA engineers identify missing business rules and unclear acceptance criteria.

### Step 6: Filter Test Cases

Use the available filters:

- Search by scenario or test steps.
- Filter by priority.
- Filter by test type.
- Expand all test cases.

### Step 7: Export Results

Download the generated test cases in:

| Format | Purpose |
|---|---|
| JSON | Integration with other applications and automation tools. |
| CSV | Excel review and test management imports. |
| Markdown | Documentation and requirement reviews. |

---

## 11. Troubleshooting

| Issue | Possible Cause | Resolution |
|---|---|---|
| Model environment variable is not set | Missing `Model` configuration | Configure the model in `.env` or Streamlit Secrets. |
| Prompt template not found | Missing JSON prompt file | Add `test_case_template.json` to the repository root. |
| OpenRouter authentication error | Missing or invalid API key | Verify the API key and client configuration. |
| Invalid JSON response | AI returned an unexpected response | Review the prompt template and retry. |
| Module not found | Missing dependency | Run `uv pip install -r requirements.txt`. |
| Streamlit command not found | Environment not activated or package missing | Activate `.venv` and install dependencies. |
| Deployment failed | Dependency or configuration issue | Review Streamlit deployment logs. |
| Application returns no test cases | Unexpected AI response structure | Review the model output and prompt instructions. |
| Secrets not detected | Application only reads environment variables | Add Streamlit Secrets integration. |

---

## 12. Current Application Limitations

The current implementation has the following limitations:

- No database integration.
- No user authentication or role-based access.
- Recent generation history is maintained in Streamlit session state only.
- History is limited to the five most recent generations in the active session.
- Generated results are not permanently stored.
- AI-generated test cases require manual QA review.
- No direct Jira or TestRail integration.
- No automated Selenium or Playwright script execution.

---

## 13. Future Enhancements

Potential improvements for future releases:

### Test Management
- PostgreSQL integration.
- Persistent generation history.
- User login and role-based access.
- Test suite management.
- Requirement-to-test traceability matrix.

### AI Capabilities
- AI-based test case quality scoring.
- Duplicate test case detection.
- Improved edge-case identification.
- Requirement ambiguity detection.
- Test data generation.
- Risk-based test coverage.

### Automation
- Selenium automation script generation.
- Playwright test script generation.
- API automation script generation.
- Test execution integration.
- Automation framework integration.

### Integrations
- Jira integration.
- TestRail integration.
- Azure DevOps integration.
- GitHub integration.
- CI/CD pipeline integration.

### Reporting
- Advanced QA dashboards.
- Test coverage reports.
- Requirement coverage analysis.
- Export to formatted Excel workbooks.
- Test execution reporting.

---

## 14. Security and Best Practices

- Never commit API keys to GitHub.
- Keep `.env` and `secrets.toml` excluded from Git.
- Use Streamlit Secrets for cloud deployment.
- Avoid exposing sensitive business requirements to external AI services without authorization.
- Review AI-generated test cases before execution.
- Pin and test dependency versions before production deployment.
- Monitor OpenRouter API usage and costs.
- Use appropriate access controls before making the application publicly available.

---

## 15. Quick Start Commands

For Windows development:

```bash
# Clone repository
git clone YOUR_GITHUB_REPOSITORY_URL

# Navigate to project
cd AI-Test-Case-Generator

# Create virtual environment
uv venv

# Activate environment
.venv\Scripts\activate

# Install dependencies
uv pip install -r requirements.txt

# Run Streamlit application
uv run streamlit run app.py
```

Open:

```text
http://localhost:8501
```

---

## 16. Project Information

**Project Name:** AI Test Case Generator

**Application Type:** AI-Powered QA Productivity Tool

**Frontend:** Streamlit

**Backend / Application Logic:** Python

**LLM Integration:** LangChain + OpenRouter

**Package Manager:** UV

**Deployment Platform:** Streamlit Community Cloud

**Export Formats:** JSON, CSV, Markdown

**Primary Objective:** Convert software requirements into structured, traceable, and reviewable test cases using AI.

---

*Disclaimer: AI-generated test cases are suggestions. A qualified QA engineer should validate business logic, test data, expected results, and coverage before execution.*
