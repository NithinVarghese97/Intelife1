# Create virtual environment
python3.11 -m venv myenv

# Activate virtual environment
.\myenv\Scripts\activate

# Verify activation
if (-not $env:VIRTUAL_ENV) {
    Write-Host "Failed to activate the virtual environment!" -ForegroundColor Red
    exit
}

# Define required packages
$packages = @(
    "bertopic==0.16.4",
    "docx2pdf==0.1.8",
    "expecttest==0.2.1",
    "Flask==3.1.0",
    "Flask-WTF==1.2.2",
    "hdbscan==0.8.40",
    "matplotlib==3.9.3",
    "nltk==3.9.1",
    "openai",
    "PyMuPDF==1.24.13",
    "pymupdf4llm==0.0.17",
    "python-docx==1.1.2",
    "scikit-learn",
    "sentence-transformers",
    "gensim",
    "tiktoken",
    "python-dotenv"
)

# Install each package
foreach ($package in $packages) {
    Write-Host "Installing $package..."
    pip install $package
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to install $package!" -ForegroundColor Red
        exit
    }
}

Write-Host "All packages installed successfully!" -ForegroundColor Green

# Verify run.py exists
if (-Not (Test-Path "run.py")) {
    Write-Host "run.py not found in the current directory!" -ForegroundColor Red
    exit
}

# Run the Python script
Write-Host "Running run.py..."
python run.py

# Check if the script ran successfully
if ($LASTEXITCODE -eq 0) {
    Write-Host "Script ran successfully!" -ForegroundColor Green
} else {
    Write-Host "Script failed to run!" -ForegroundColor Red
}
