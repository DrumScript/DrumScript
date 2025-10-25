## Contributing to `DrumScript`
<!--date_created: thurs-03-jul-2025-->
<!--date_updated: sat-25-oct-2025-->




🎉 First off, thank you for considering contributing to `DrumScript`! 🎉

We're thrilled to have you join us in transforming drum audio into sheet music. Your contributions are highly valued and help make this project even better.

This document outlines guidelines for contributing to DrumScript. By following these, you help us maintain code quality, consistency, and a smooth collaborative experience.


> **Code of Conduct**
> Please note that this project is released with a contributor **`Code of Conduct`**. By participating in this project, you agree to abide by its terms. 

---

### How to Get Started

#### 1. Prerequisites

Before you begin, ensure you have the following installed:

* **Git:** For version control.
* **Python 3.9+:** The language  `DrumScript` is built with.
* **`uv`:** A fast `Python` package installer and dependency resolver. If you don't have it, you can install it via `curl -LsSf https://astral.sh/uv/install.sh | sh` (macOS/Linux) or follow instructions on [uv's website](https://astral.sh/uv/install/).
* **`MuseScore`:** An external music notation software. Ensure it's installed and accessible from your command line (you've already configured its path in `pdf_exporter.py`).

### 2. Clone the Repository

Start by cloning the  `DrumScript` repository to your local machine:

```bash
git clone [https://github.com/your-username/digital-performance-dashboard.git](https://github.com/your-username/digital-performance-dashboard.git) # Replace with your actual repo URL
cd digital-performance-dashboard
```

### 3\. Set Up Your Development Environment

We use `uv` to manage our virtual environment and dependencies.

```bash
# Create a virtual environment (in .venv/)
uv venv

# Activate the virtual environment
source .venv/bin/activate # On macOS/Linux
# .venv\Scripts\activate # On Windows (Command Prompt)
# .venv\Scripts\Activate.ps1 # On Windows (PowerShell)

# Install project dependencies
uv pip install -r requirements.txt

# Install pre-commit hooks (for automatic formatting/linting before commits)
uv pip install pre-commit
pre-commit install
```

> **Note:** The repository structure includes a `.venv/` directory, which `uv venv` will create and manage.
 

### 4\. Run the Project (Optional, for testing setup)

You can run the main script to ensure everything is set up correctly:

```bash
uv run python3 main.py test_audio/reference_audio/test.mp3 output.pdf
```

This should generate `output.pdf` in your root directory.

---

## Development Workflow

We follow a **feature branch workflow** with **Pull Requests** to ensure code quality and a stable `main` branch.

1.  **Keep `main` updated:**
    Before starting new work, always pull the latest changes from the `main` branch to ensure your local `main` is up-to-date.

    ```bash
    git checkout main
    git pull origin main
    ```

2.  **Create a new feature branch:**
    For every new feature, bug fix, or significant change, create a new branch from `main`. Use descriptive names (e.g., `feature/add-hi-hat-detection`, `bugfix/fix-quantization-error`, `refactor/improve-pdf-export`).

    ```bash
    git checkout -b feature/your-awesome-feature-name
    ```

3.  **Make your changes:**
    Write your code, commit frequently, and use clear, concise commit messages.

    ```bash
    git add .
    git commit -m "feat: Implement a new feature for X"
    ```

    > **Tip:** Make sure to run `uv run python3 main.py` or specific module tests locally to ensure your changes work as expected.

4.  **Push your branch:**
    When you're ready to share your changes or open a Pull Request, push your feature branch to the remote repository.

    ```bash
    git push -u origin feature/your-awesome-feature-name
    ```

5.  **Create a Pull Request (PR):**

      * Go to the  `DrumScript` repository on GitHub (or your chosen platform).
      * You should see a prompt to create a new Pull Request from your recently pushed branch to `main`.
      * **Provide a clear PR title and detailed description** of your changes, including:
          * What problem does this PR solve?
          * How does it solve it?
          * Any relevant screenshots or output examples.
          * Any specific areas you'd like reviewed.
      * Assign a reviewer (e.g., your colleague or the project maintainer).

6.  **Code Review and Iteration:**

      * Your PR will be reviewed by another contributor. They might provide feedback, suggest improvements, or ask for clarifications.
      * Make any necessary changes in your feature branch and push them. They will automatically appear in the PR.
      * Once approved, your PR can be merged into `main`.

---
> ## Editing the project in package-editing mode:
>
> For the purpose of amending package elements it is **recommended** that, once you have completed **[setup per the instructions in the `README.md`]((README.md))**, that you **edit the package in pip package-editing mode**, in order to streamline modules etc. To do this:
>
> 1. Activate your `.venv`
> 2. Type `uv pip install -e .` in Terminal
>
> Unfortunately, you have to **run this command every time you commence/resume working on the project**. 
---
## Coding Standards

To maintain consistency and readability, please adhere to the following:

  * **Python Style:** Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) conventions.
  * **Formatting & Linting:** We use `ruff` to automatically format and lint our code.
      * Before committing, `pre-commit` hooks will automatically run `ruff format` and `ruff check`. If you encounter issues, resolve them locally.
      * You can manually run them:
        ```bash
        uv run ruff format .
        uv run ruff check .
        ```

---

## Testing
 (If you use `pytest`, you can add instructions here like `uv run pytest local_tests/`).
  * **New Contributions:** If you add new functionality, please consider adding corresponding tests.

---

## Reporting Issues & Feature Requests

If you find a bug or have an idea for a new feature, please open an issue on the [GitHub Issues page]()

  * **For Bugs:** Please provide a clear description of the problem, steps to reproduce it, expected behavior, and your environment details.
  * **For Features:** Describe the idea, why it would be useful, and any potential implementation details.

> **PLEASE NOTE:** All bug reports and feature requests must be filed as [GitHub Issues](https://github.com/DrumScript/DrumScript/issues). All code changes must be submitted as [Pull Requests](https://github.com/DrumScript/DrumScript/pulls). Please do not email us directly about the project, as keeping all communication public helps everyone.

---

## Questions & Support

If you have any questions or need further assistance, feel free to reach out at **[hello.drumscript@gmail.com](hello.drumscript@gmail.com)**

Thank you for using an contributing to `DrumScript` :D <3 :drum: !



---
<!--END-->