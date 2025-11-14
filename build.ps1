<<<<<<< HEAD
# Healthcare Chatbot - Complete Build Script
# This script sets up the entire project including backend, frontend, and database

param(
    [switch]$SkipFrontend,
    [switch]$SkipBackend,
    [switch]$SkipPrisma,
    [switch]$SkipRAGIndex,
=======
# Healthcare Chatbot - Build Script
# This script builds and sets up the entire project

param(
    [switch]$SkipPrisma,
    [switch]$SkipRAG,
    [switch]$SkipFrontend,
    [switch]$SkipDatabase,
>>>>>>> d7aa492267f2f7267160e8aa40fbb9593b835803
    [string]$PythonVersion = "python"
)

$ErrorActionPreference = "Stop"
<<<<<<< HEAD

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Healthcare Chatbot - Build Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Function to check if a command exists
function Test-Command {
    param([string]$Command)
    $null = Get-Command $Command -ErrorAction SilentlyContinue
    return $?
}

# Check prerequisites
Write-Host "Checking prerequisites..." -ForegroundColor Yellow

$prerequisitesMet = $true

# Detect Python command
$pythonCmd = $null
if (Test-Command "python") {
    $pythonCmd = "python"
} elseif (Test-Command "python3") {
    $pythonCmd = "python3"
} elseif (Test-Command "py") {
    $pythonCmd = "py"
} else {
    Write-Host "❌ Python not found. Please install Python 3.8+" -ForegroundColor Red
    $prerequisitesMet = $false
}

if ($pythonCmd) {
    $pythonVersion = & $pythonCmd --version 2>&1
    Write-Host "✅ Found: $pythonVersion" -ForegroundColor Green
    $PythonVersion = $pythonCmd  # Update the variable for later use
}

if (-not $SkipFrontend) {
    if (-not (Test-Command "node")) {
        Write-Host "❌ Node.js not found. Please install Node.js 18+" -ForegroundColor Red
        $prerequisitesMet = $false
    } else {
        $nodeVersion = node --version
        Write-Host "✅ Found: Node.js $nodeVersion" -ForegroundColor Green
    }

    if (-not (Test-Command "npm") -and -not (Test-Command "pnpm")) {
        Write-Host "❌ npm or pnpm not found. Please install npm or pnpm" -ForegroundColor Red
        $prerequisitesMet = $false
    } else {
        if (Test-Command "pnpm") {
            $packageManager = "pnpm"
            $packageVersion = pnpm --version
            Write-Host "✅ Found: pnpm $packageVersion" -ForegroundColor Green
        } else {
            $packageManager = "npm"
            $packageVersion = npm --version
            Write-Host "✅ Found: npm $packageVersion" -ForegroundColor Green
        }
    }
}

if (-not $prerequisitesMet) {
    Write-Host ""
    Write-Host "Please install missing prerequisites and run the script again." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "All prerequisites met!" -ForegroundColor Green
Write-Host ""

# Get the script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

# ============================================
# Backend Setup
# ============================================
if (-not $SkipBackend) {
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Setting up Backend (Python/FastAPI)" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""

    $apiDir = Join-Path $scriptDir "api"
    
    if (-not (Test-Path $apiDir)) {
        Write-Host "❌ API directory not found: $apiDir" -ForegroundColor Red
        exit 1
    }

    Set-Location $apiDir

    # Create virtual environment if it doesn't exist
    $venvPath = Join-Path $apiDir ".venv"
    if (-not (Test-Path $venvPath)) {
        Write-Host "Creating Python virtual environment..." -ForegroundColor Yellow
        & $PythonVersion -m venv .venv
        Write-Host "✅ Virtual environment created" -ForegroundColor Green
    } else {
        Write-Host "✅ Virtual environment already exists" -ForegroundColor Green
    }

    # Activate virtual environment
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    $activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
    if (Test-Path $activateScript) {
        & $activateScript
        Write-Host "✅ Virtual environment activated" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Could not activate virtual environment. Continuing..." -ForegroundColor Yellow
    }

    # Upgrade pip
    Write-Host "Upgrading pip..." -ForegroundColor Yellow
    & $PythonVersion -m pip install --upgrade pip --quiet
    Write-Host "✅ pip upgraded" -ForegroundColor Green

    # Install Python dependencies
    Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
    if (Test-Path "requirements.txt") {
        & $PythonVersion -m pip install -r requirements.txt
        Write-Host "✅ Python dependencies installed" -ForegroundColor Green
    } else {
        Write-Host "⚠️  requirements.txt not found. Skipping..." -ForegroundColor Yellow
    }

    # Check for .env file
    $envFile = Join-Path $apiDir ".env"
    if (-not (Test-Path $envFile)) {
        Write-Host ""
        Write-Host "⚠️  .env file not found in api/ directory" -ForegroundColor Yellow
        Write-Host "Creating template .env file..." -ForegroundColor Yellow
        
        $envTemplate = @"
# Database Configuration
NEON_DB_URL=postgresql://user:password@host:port/database?sslmode=require

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Neo4j Configuration (optional)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password

# ElevenLabs Configuration (optional, for TTS)
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here

# ChromaDB Configuration
CHROMADB_DISABLE_TELEMETRY=1

# JWT Configuration
JWT_SECRET_KEY=your_secret_key_here_change_in_production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
"@
        Set-Content -Path $envFile -Value $envTemplate
        Write-Host "✅ Template .env file created. Please update it with your actual values." -ForegroundColor Green
    } else {
        Write-Host "✅ .env file found" -ForegroundColor Green
    }

    Write-Host ""
}

# ============================================
# Prisma Setup
# ============================================
if (-not $SkipPrisma) {
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Setting up Prisma Database" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""

    $apiDir = Join-Path $scriptDir "api"
    Set-Location $apiDir

    # Check if Prisma is installed
    Write-Host "Checking Prisma installation..." -ForegroundColor Yellow
    try {
        $prismaVersion = & $PythonVersion -m prisma --version 2>&1
        Write-Host "✅ Prisma is installed" -ForegroundColor Green
    } catch {
        Write-Host "Installing Prisma..." -ForegroundColor Yellow
        & $PythonVersion -m pip install prisma
        Write-Host "✅ Prisma installed" -ForegroundColor Green
    }

    # Check for Prisma schema
    $schemaPath = Join-Path $apiDir "prisma\schema.prisma"
    if (-not (Test-Path $schemaPath)) {
        Write-Host "❌ Prisma schema not found: $schemaPath" -ForegroundColor Red
        Write-Host "Skipping Prisma setup..." -ForegroundColor Yellow
    } else {
        # Check for NEON_DB_URL in environment
        $envContent = Get-Content $envFile -ErrorAction SilentlyContinue
        $hasDbUrl = $envContent | Where-Object { $_ -match "NEON_DB_URL" -and $_ -notmatch "^#" -and $_ -notmatch "^\s*$" }
        
        if (-not $hasDbUrl) {
            Write-Host "⚠️  NEON_DB_URL not found in .env file" -ForegroundColor Yellow
            Write-Host "Skipping Prisma database push. Please set NEON_DB_URL in .env file first." -ForegroundColor Yellow
        } else {
            # Generate Prisma client
            Write-Host "Generating Prisma client..." -ForegroundColor Yellow
            try {
                & $PythonVersion -m prisma generate --schema prisma/schema.prisma
                Write-Host "✅ Prisma client generated" -ForegroundColor Green
            } catch {
                Write-Host "⚠️  Error generating Prisma client: $_" -ForegroundColor Yellow
                Write-Host "You may need to run this manually: python -m prisma generate --schema prisma/schema.prisma" -ForegroundColor Yellow
            }

            # Push schema to database
            Write-Host "Pushing schema to database..." -ForegroundColor Yellow
            Write-Host "⚠️  This will create/modify database tables. Continue? (Y/N)" -ForegroundColor Yellow
            $response = Read-Host
            if ($response -eq "Y" -or $response -eq "y") {
                try {
                    & $PythonVersion -m prisma db push --schema prisma/schema.prisma --accept-data-loss
                    Write-Host "✅ Database schema pushed successfully" -ForegroundColor Green
                } catch {
                    Write-Host "⚠️  Error pushing schema: $_" -ForegroundColor Yellow
                    Write-Host "You may need to run this manually: python -m prisma db push --schema prisma/schema.prisma" -ForegroundColor Yellow
                }
            } else {
                Write-Host "Skipping database push. You can run it later with:" -ForegroundColor Yellow
                Write-Host "  python -m prisma db push --schema prisma/schema.prisma" -ForegroundColor Yellow
            }
        }
    }

    Write-Host ""
}

# ============================================
# RAG Index Build
# ============================================
if (-not $SkipRAGIndex) {
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Building RAG Index" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""

    $apiDir = Join-Path $scriptDir "api"
    Set-Location $apiDir

    $buildIndexScript = Join-Path $apiDir "rag\build_index.py"
    if (Test-Path $buildIndexScript) {
        Write-Host "Building RAG index from markdown files..." -ForegroundColor Yellow
        try {
            & $PythonVersion rag\build_index.py
            Write-Host "✅ RAG index built successfully" -ForegroundColor Green
        } catch {
            Write-Host "⚠️  Error building RAG index: $_" -ForegroundColor Yellow
            Write-Host "You can run this manually later: python rag/build_index.py" -ForegroundColor Yellow
        }
    } else {
        Write-Host "⚠️  RAG build script not found: $buildIndexScript" -ForegroundColor Yellow
        Write-Host "Skipping RAG index build..." -ForegroundColor Yellow
    }

    Write-Host ""
}

# ============================================
# Frontend Setup
# ============================================
if (-not $SkipFrontend) {
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Setting up Frontend (Next.js)" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""

    $frontendDir = Join-Path $scriptDir "frontend"
    
    if (-not (Test-Path $frontendDir)) {
        Write-Host "❌ Frontend directory not found: $frontendDir" -ForegroundColor Red
        Write-Host "Skipping frontend setup..." -ForegroundColor Yellow
    } else {
        Set-Location $frontendDir

        # Install dependencies
        Write-Host "Installing frontend dependencies..." -ForegroundColor Yellow
        if ($packageManager -eq "pnpm") {
            if (-not (Test-Path "node_modules")) {
                pnpm install
                Write-Host "✅ Frontend dependencies installed (pnpm)" -ForegroundColor Green
            } else {
                Write-Host "✅ Frontend dependencies already installed" -ForegroundColor Green
            }
        } else {
            if (-not (Test-Path "node_modules")) {
                npm install
                Write-Host "✅ Frontend dependencies installed (npm)" -ForegroundColor Green
            } else {
                Write-Host "✅ Frontend dependencies already installed" -ForegroundColor Green
            }
        }

        # Build frontend
        Write-Host "Building frontend..." -ForegroundColor Yellow
        try {
            if ($packageManager -eq "pnpm") {
                pnpm run build
            } else {
                npm run build
            }
            Write-Host "✅ Frontend built successfully" -ForegroundColor Green
        } catch {
            Write-Host "⚠️  Error building frontend: $_" -ForegroundColor Yellow
            Write-Host "You can build it manually later with: npm run build (or pnpm run build)" -ForegroundColor Yellow
        }

        Write-Host ""
    }
}

# ============================================
# Summary
# ============================================
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Build Complete!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Update api/.env file with your actual configuration values" -ForegroundColor White
Write-Host "2. Start the backend server:" -ForegroundColor White
Write-Host "   cd api" -ForegroundColor Gray
Write-Host "   python start_server.py" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Start the frontend (in a new terminal):" -ForegroundColor White
Write-Host "   cd frontend" -ForegroundColor Gray
if ($packageManager -eq "pnpm") {
    Write-Host "   pnpm dev" -ForegroundColor Gray
} else {
    Write-Host "   npm run dev" -ForegroundColor Gray
}
Write-Host ""

Write-Host "For more information, check the documentation in the api/ directory." -ForegroundColor Cyan
Write-Host ""
=======
$ProgressPreference = "SilentlyContinue"

# Colors for output
function Write-Info {
    param([string]$Message)
    Write-Host "`n[INFO] $Message" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

function Write-Step {
    param([string]$Message)
    Write-Host "`n========================================" -ForegroundColor Magenta
    Write-Host "  $Message" -ForegroundColor Magenta
    Write-Host "========================================`n" -ForegroundColor Magenta
}

# Get project root directory
$ProjectRoot = $PSScriptRoot
if (-not $ProjectRoot) {
    $ProjectRoot = Get-Location
}

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "  Healthcare Chatbot - Build Script" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Green

Write-Info "Project root: $ProjectRoot"

# Check if Python is available
Write-Step "Checking Prerequisites"
$pythonFound = $false
$pythonCommands = @("python", "python3", "py")
foreach ($cmd in $pythonCommands) {
    try {
        $pythonOutput = & $cmd --version 2>&1
        if ($?) {
            $PythonVersion = $cmd
            Write-Success "Python found: $pythonOutput (using '$cmd')"
            $pythonFound = $true
            break
        }
    } catch {
        # Continue to next command
    }
}

if (-not $pythonFound) {
    Write-Error "Python not found. Please install Python 3.8+ and ensure it's in PATH."
    exit 1
}

# Check if Node.js is available (for frontend)
if (-not $SkipFrontend) {
    try {
        $nodeVersion = & node --version 2>&1
        Write-Success "Node.js found: $nodeVersion"
    } catch {
        Write-Warning "Node.js not found. Frontend build will be skipped."
        $SkipFrontend = $true
    }
}

# Check if npm/pnpm is available
if (-not $SkipFrontend) {
    $packageManager = "npm"
    try {
        $npmVersion = & npm --version 2>&1
        Write-Success "npm found: $npmVersion"
    } catch {
        try {
            $pnpmVersion = & pnpm --version 2>&1
            Write-Success "pnpm found: $pnpmVersion"
            $packageManager = "pnpm"
        } catch {
            Write-Warning "Neither npm nor pnpm found. Frontend build will be skipped."
            $SkipFrontend = $true
        }
    }
}

# Step 1: Backend Setup
Write-Step "Step 1: Backend Setup (Python/FastAPI)"

$ApiDir = Join-Path $ProjectRoot "api"
if (-not (Test-Path $ApiDir)) {
    Write-Error "API directory not found: $ApiDir"
    exit 1
}

Set-Location $ApiDir

# 1.0: Setup Virtual Environment
Write-Info "Setting up virtual environment..."
$SystemPython = $PythonVersion  # Save system Python for venv creation
$VenvDir = Join-Path $ApiDir ".venv"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
$VenvActivate = Join-Path $VenvDir "Scripts\Activate.ps1"

if (-not (Test-Path $VenvDir)) {
    Write-Info "Creating virtual environment at $VenvDir..."
    try {
        & $SystemPython -m venv $VenvDir
        if ($?) {
            Write-Success "Virtual environment created successfully"
            # Wait a moment for venv to be fully created
            Start-Sleep -Seconds 2
        } else {
            Write-Error "Failed to create virtual environment"
            exit 1
        }
    } catch {
        Write-Error "Error creating virtual environment: $_"
        exit 1
    }
} else {
    Write-Success "Virtual environment already exists"
}

# Verify venv Python exists
if (-not (Test-Path $VenvPython)) {
    Write-Warning "Virtual environment Python not found at $VenvPython"
    Write-Info "Attempting to recreate virtual environment..."
    if (Test-Path $VenvDir) {
        Remove-Item -Path $VenvDir -Recurse -Force
    }
    & $SystemPython -m venv $VenvDir
    Start-Sleep -Seconds 2
    if (-not (Test-Path $VenvPython)) {
        Write-Error "Failed to create virtual environment. Please check Python installation."
        exit 1
    }
}

# Use venv Python for all operations
$PythonVersion = $VenvPython
Write-Info "Using virtual environment Python: $PythonVersion"

# 1.1: Install Python dependencies
Write-Info "Installing Python dependencies into virtual environment..."
try {
    Write-Info "Upgrading pip..."
    & $PythonVersion -m pip install --upgrade pip 2>&1 | Out-Null
    if (-not $?) {
        Write-Warning "Failed to upgrade pip, continuing anyway..."
    }
    
    Write-Info "Installing requirements from requirements.txt..."
    & $PythonVersion -m pip install -r requirements.txt
    if ($?) {
        Write-Success "Python dependencies installed successfully"
    } else {
        Write-Error "Failed to install Python dependencies"
        exit 1
    }
} catch {
    Write-Error "Error installing Python dependencies: $_"
    exit 1
}

# 1.2: Check for .env file
Write-Info "Checking for .env file..."
$EnvFile = Join-Path $ApiDir ".env"
$EnvFileRoot = Join-Path $ProjectRoot ".env"

if (-not (Test-Path $EnvFile) -and -not (Test-Path $EnvFileRoot)) {
    Write-Warning ".env file not found. Creating template..."
    $envTemplate = @"
# Database Configuration
NEON_DB_URL=postgresql://user:password@host:port/database?sslmode=require

# JWT Configuration
JWT_SECRET_KEY=your-secret-key-change-in-production-minimum-32-characters
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Environment
ENVIRONMENT=development
LOG_LEVEL=INFO

# LLM Configuration (at least one required)
OPENROUTER_API_KEY=your-openrouter-api-key
# OR
DEEPSEEK_API_KEY=your-deepseek-api-key
# OR
OPENAI_API_KEY=your-openai-api-key

# LLM Model Configuration
DEEPSEEK_MODEL=deepseek/deepseek-r1-0528:free
DEEPSEEK_BASE_URL=https://api.deepseek.com
# OR
OPENROUTER_MODEL=deepseek/deepseek-r1-0528:free
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_SITE_URL=http://localhost
OPENROUTER_SITE_NAME=Healthcare Chatbot

# Neo4j Configuration (Optional)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=testpass
NEO4J_DATABASE=neo4j
NEO4J_TRUST_ALL_CERTS=false

# TTS Configuration (Optional)
ELEVENLABS_API_KEY=your-elevenlabs-api-key
ELEVENLABS_MODEL=eleven_multilingual_v2
ELEVENLABS_VOICE=Bella
ELEVENLABS_VOICE_EN=Bella
ELEVENLABS_VOICE_HI=Neha
ELEVENLABS_VOICE_TA=Priya
ELEVENLABS_VOICE_TE=Preethi
ELEVENLABS_VOICE_KN=Kavya
ELEVENLABS_VOICE_ML=Meera

# Indic Transliteration (Optional)
INDIC_TRANS_HF_TOKEN=your-huggingface-token
HF_TOKEN=your-huggingface-token
HUGGINGFACE_TOKEN=your-huggingface-token
TRANS_HF_TOKEN=your-huggingface-token

# CORS Configuration
CORS_ORIGINS=http://localhost:3000,http://localhost:3001

# Rate Limiting
RATE_LIMIT=30
RATE_WINDOW=60
DISABLE_RATE_LIMIT=0

# ChromaDB
CHROMADB_DISABLE_TELEMETRY=1
ANONYMIZED_TELEMETRY=False
"@
    Set-Content -Path $EnvFile -Value $envTemplate
    Write-Warning "Created .env template file at $EnvFile"
    Write-Warning "Please edit .env file and set your actual configuration values before continuing."
    Write-Warning "At minimum, you need to set:"
    Write-Warning "  - NEON_DB_URL (database connection string)"
    Write-Warning "  - JWT_SECRET_KEY (for authentication)"
    Write-Warning "  - One of: OPENROUTER_API_KEY, DEEPSEEK_API_KEY, or OPENAI_API_KEY"
} else {
    Write-Success ".env file found"
}

# 1.3: Setup Prisma
if (-not $SkipPrisma) {
    Write-Info "Setting up Prisma..."
    $PrismaSchema = Join-Path $ApiDir "prisma\schema.prisma"
    if (Test-Path $PrismaSchema) {
        try {
            # Check if prisma is installed
            & $PythonVersion -m pip show prisma 2>&1 | Out-Null
            if (-not $?) {
                Write-Info "Installing Prisma..."
                & $PythonVersion -m pip install prisma 2>&1 | Out-Null
                if (-not $?) {
                    Write-Warning "Failed to install Prisma. You may need to install it manually."
                }
            }

            # Generate Prisma client
            Write-Info "Generating Prisma client..."
            & $PythonVersion -m prisma generate --schema $PrismaSchema
            if ($?) {
                Write-Success "Prisma client generated successfully"
            } else {
                Write-Warning "Failed to generate Prisma client. You may need to run this manually."
            }

            # Check if NEON_DB_URL is set
            if (-not $SkipDatabase) {
                $dbUrl = $env:NEON_DB_URL
                if (-not $dbUrl) {
                    # Try to load from .env file
                    $envFiles = @($EnvFile, $EnvFileRoot)
                    foreach ($envFilePath in $envFiles) {
                        if (Test-Path $envFilePath) {
                            Get-Content $envFilePath | ForEach-Object {
                                if ($_ -match '^\s*NEON_DB_URL\s*=\s*(.+)$') {
                                    $dbUrl = $matches[1].Trim().Trim('"').Trim("'")
                                }
                            }
                            if ($dbUrl) {
                                break
                            }
                        }
                    }
                }

                if ($dbUrl -and $dbUrl -notmatch '^postgresql://user:password@') {
                    Write-Info "Pushing Prisma schema to database..."
                    & $PythonVersion -m prisma db push --schema $PrismaSchema --accept-data-loss
                    if ($?) {
                        Write-Success "Prisma schema pushed to database successfully"
                    } else {
                        Write-Warning "Failed to push schema to database. Check your NEON_DB_URL in .env file."
                    }
                } else {
                    Write-Warning "NEON_DB_URL not set or using default value. Skipping database push."
                    Write-Warning "Please set NEON_DB_URL in .env file to push schema to database."
                }
            }
        } catch {
            Write-Warning "Error setting up Prisma: $_"
            Write-Warning "You may need to run Prisma setup manually."
        }
    } else {
        Write-Warning "Prisma schema not found: $PrismaSchema"
    }
} else {
    Write-Info "Skipping Prisma setup (--SkipPrisma flag set)"
}

# 1.4: Build RAG Index (Optional)
if (-not $SkipRAG) {
    Write-Info "Building RAG index (this may take a while)..."
    $BuildIndexScript = Join-Path $ApiDir "rag\build_index.py"
    if (Test-Path $BuildIndexScript) {
        try {
            # Set environment variable to disable telemetry
            $env:CHROMADB_DISABLE_TELEMETRY = "1"
            & $PythonVersion $BuildIndexScript
            if ($?) {
                Write-Success "RAG index built successfully"
            } else {
                Write-Warning "Failed to build RAG index. You may need to run this manually."
            }
        } catch {
            Write-Warning "Error building RAG index: $_"
            Write-Warning "You can build it later by running: python api/rag/build_index.py"
        }
    } else {
        Write-Warning "RAG build script not found: $BuildIndexScript"
    }
} else {
    Write-Info "Skipping RAG index build (--SkipRAG flag set)"
}

# Step 2: Frontend Setup
if (-not $SkipFrontend) {
    Write-Step "Step 2: Frontend Setup (Next.js)"
    
    $FrontendDir = Join-Path $ProjectRoot "frontend"
    if (Test-Path $FrontendDir) {
        Set-Location $FrontendDir
        
        # 2.1: Install Node.js dependencies
        Write-Info "Installing Node.js dependencies..."
        try {
            if ($packageManager -eq "pnpm") {
                pnpm install
            } else {
                npm install
            }
            if ($?) {
                Write-Success "Frontend dependencies installed successfully"
            } else {
                Write-Error "Failed to install frontend dependencies"
                exit 1
            }
        } catch {
            Write-Error "Error installing frontend dependencies: $_"
            exit 1
        }
        
        # 2.2: Build frontend (optional, for production)
        Write-Info "Frontend dependencies installed. To build for production, run:"
        if ($packageManager -eq "pnpm") {
            Write-Info "  cd frontend && pnpm build"
        } else {
            Write-Info "  cd frontend && npm run build"
        }
    } else {
        Write-Warning "Frontend directory not found: $FrontendDir"
    }
} else {
    Write-Info "Skipping frontend setup (--SkipFrontend flag set or Node.js not found)"
}

# Step 3: Summary
Write-Step "Build Summary"

Write-Success "Build completed successfully!`n"

Write-Info "Next steps:"
Write-Host "  1. Edit api/.env file and set your configuration values" -ForegroundColor Yellow
Write-Host "  2. Make sure NEON_DB_URL is set correctly" -ForegroundColor Yellow
Write-Host "  3. Make sure JWT_SECRET_KEY is set (minimum 32 characters)" -ForegroundColor Yellow
Write-Host "  4. Make sure at least one LLM API key is set (OPENROUTER_API_KEY, DEEPSEEK_API_KEY, or OPENAI_API_KEY)" -ForegroundColor Yellow
Write-Host "  5. Start the backend server (using the virtual environment):" -ForegroundColor Yellow
Write-Host "     cd api" -ForegroundColor Cyan
Write-Host "     .venv\Scripts\activate  # Activate virtual environment (optional)" -ForegroundColor Cyan
Write-Host "     python start_server.py  # OR: python -m uvicorn main:app --reload" -ForegroundColor Cyan
Write-Host "  6. Start the frontend (in a new terminal):" -ForegroundColor Yellow
if ($packageManager -eq "pnpm") {
    Write-Host "     cd frontend && pnpm dev" -ForegroundColor Cyan
} else {
    Write-Host "     cd frontend && npm run dev" -ForegroundColor Cyan
}

Write-Host "`nOptional steps:"
Write-Host "  - Set up Neo4j for graph database features" -ForegroundColor Gray
Write-Host "  - Configure ElevenLabs for TTS" -ForegroundColor Gray
Write-Host "  - Configure HuggingFace token for indic transliteration" -ForegroundColor Gray

Write-Host "`nFor more information, see:"
Write-Host "  - api/PRISMA_SETUP.md - Database setup"
Write-Host "  - api/SECURITY_SETUP.md - Security setup"
Write-Host "  - api/README_PRISMA.md - Prisma documentation"

Set-Location $ProjectRoot

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "  Build Complete!" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Green
>>>>>>> d7aa492267f2f7267160e8aa40fbb9593b835803

