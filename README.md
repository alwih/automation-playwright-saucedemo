# Playwright Python Starter Guide (SauceDemo)

This project is a beginner-friendly introduction to UI automation using [Playwright](https://playwright.dev/python/) and [Miniconda](https://docs.anaconda.com/miniconda/). We focus on simple login scenarios for `https://www.saucedemo.com`.

## 🛠️ 1. Setup Environment (Miniconda)

We use `conda` to manage a clean Python environment. Follow these steps to get started:

1. **Create the environment:**
   ```bash
   conda create -n playwright-py python=3.10 -y
   ```

2. **Activate the environment:**
   ```bash
   conda activate playwright-py
   ```

3. **Install dependencies:**
   ```bash
   pip install pytest-playwright playwright pytest-asyncio pytest-xdist
   ```

4. **Install Browsers:**
   Playwright needs to download the actual browser binaries:
   ```bash
   playwright install chromium
   ```

## 📂 2. Project Structure

For this beginner stage, we keep it to essential files:

```text
.
├── test_login.py          # Synchronous test logic (Step-by-step)
├── test_login_async.py    # Asynchronous test logic (Concurrent)
└── environment.yml        # (Optional) Exported conda environment config
```

## 🧪 3. Understanding the Code

Playwright offers two ways to write code: **Sync** and **Async**.

### Sync (Synchronous)
Used in `test_login.py`. The code waits for each line to finish before moving to the next.
- Easy to read and debug for beginners.
- No `await` keywords needed.

### Async (Asynchronous)
Used in `test_login_async.py`. The code pauses its execution to let other things happen while waiting for the browser.
- Required if you want to run many things in parallel or integrate with async apps.
- Uses `async def` and `await`.

### Key Selectors for SauceDemo:
- **Username:** `input#user-name`
- **Password:** `input#password`
- **Login Button:** `input#login-button`
- **Error Message:** `[data-test="error"]`

### How the test works (Sync vs Async):
- **Sync:** `page.goto("url")`
- **Async:** `await page.goto("url")`

## 🚀 4. Running the Tests

To run the tests and see the report:

```bash
# Run all tests
pytest

# Run tests in parallel (2 workers)
pytest -n 2 test_login.py

# Run with browser visible (headed Mode)
pytest --headed

# Run with custom slow motion (e.g., 500ms between actions)
pytest --headed --slowmo 500

# Run specific file
pytest test_login.py
```
