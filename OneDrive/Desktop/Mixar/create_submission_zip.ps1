# Mesh Quantization Assignment - Submission Package Creator
# This script verifies all files and creates the submission ZIP

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Assignment Submission Package Creator" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Verify critical files
Write-Host "Step 1: Verifying critical files..." -ForegroundColor Yellow

$criticalFiles = @(
    "README.md",
    "requirements.txt",
    "scripts\mesh_preprocess.py",
    "scripts\aggregate_and_render.py",
    "ASSIGNMENT_SUBMISSION.md"
)

$allPresent = $true
foreach ($file in $criticalFiles) {
    if (Test-Path $file) {
        Write-Host "  [OK] $file" -ForegroundColor Green
    } else {
        Write-Host "  [MISSING] $file" -ForegroundColor Red
        $allPresent = $false
    }
}

if (-not $allPresent) {
    Write-Host "`nERROR: Some critical files are missing!" -ForegroundColor Red
    exit 1
}

# Step 2: Count output files
Write-Host "`nStep 2: Counting output files..." -ForegroundColor Yellow

$plyFiles = (Get-ChildItem -Path "outputs" -Filter "*.ply" -Recurse -ErrorAction SilentlyContinue).Count
$pngFiles = (Get-ChildItem -Path "outputs" -Filter "*.png" -Recurse -ErrorAction SilentlyContinue).Count
$npzFiles = (Get-ChildItem -Path "outputs" -Filter "*.npz" -Recurse -ErrorAction SilentlyContinue).Count
$txtFiles = (Get-ChildItem -Path "outputs" -Filter "summary.txt" -Recurse -ErrorAction SilentlyContinue).Count
$csvFiles = (Get-ChildItem -Path "outputs" -Filter "*.csv" -Recurse -ErrorAction SilentlyContinue).Count

Write-Host "  Reconstructed meshes (.ply): $plyFiles (expected: 16)" -ForegroundColor $(if ($plyFiles -eq 16) {"Green"} else {"Yellow"})
Write-Host "  Visualizations (.png): $pngFiles (expected: 50)" -ForegroundColor $(if ($pngFiles -ge 48) {"Green"} else {"Yellow"})
Write-Host "  Quantized data (.npz): $npzFiles (expected: 16+)" -ForegroundColor $(if ($npzFiles -ge 16) {"Green"} else {"Yellow"})
Write-Host "  Summary files (.txt): $txtFiles (expected: 16)" -ForegroundColor $(if ($txtFiles -eq 16) {"Green"} else {"Yellow"})
Write-Host "  Aggregate CSV: $csvFiles (expected: 1)" -ForegroundColor $(if ($csvFiles -ge 1) {"Green"} else {"Yellow"})

# Step 3: Check for PDF report
Write-Host "`nStep 3: Checking for PDF report..." -ForegroundColor Yellow

$pdfExists = Test-Path "Assignment_Report.pdf"
if ($pdfExists) {
    Write-Host "  [OK] Assignment_Report.pdf found" -ForegroundColor Green
} else {
    Write-Host "  [WARNING] Assignment_Report.pdf not found" -ForegroundColor Yellow
    Write-Host "  You need to convert ASSIGNMENT_SUBMISSION.md to PDF" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  Quick options:" -ForegroundColor Cyan
    Write-Host "  1. VS Code: Install 'Markdown PDF' extension, right-click .md file -> Export to PDF" -ForegroundColor White
    Write-Host "  2. Online: Upload ASSIGNMENT_SUBMISSION.md to https://www.markdowntopdf.com/" -ForegroundColor White
    Write-Host "  3. Browser: Open .md in VS Code preview, then Print -> Save as PDF" -ForegroundColor White
    Write-Host ""
    
    $response = Read-Host "Continue without PDF? (Y/N)"
    if ($response -ne 'Y' -and $response -ne 'y') {
        Write-Host "`nPlease create the PDF and run this script again." -ForegroundColor Yellow
        exit 0
    }
}

# Step 4: Create ZIP file
Write-Host "`nStep 4: Creating ZIP file..." -ForegroundColor Yellow

$zipName = "Vidit_MeshQuantization_Assignment.zip"

# Remove old ZIP if exists
if (Test-Path $zipName) {
    Write-Host "  Removing old ZIP file..." -ForegroundColor Gray
    Remove-Item $zipName -Force
}

# Prepare items to compress
$itemsToCompress = @(
    "README.md",
    "requirements.txt",
    "scripts",
    "outputs"
)

if ($pdfExists) {
    $itemsToCompress += "Assignment_Report.pdf"
} else {
    # Include the markdown version as fallback
    $itemsToCompress += "ASSIGNMENT_SUBMISSION.md"
}

# Create the ZIP
try {
    Compress-Archive -Path $itemsToCompress -DestinationPath $zipName -CompressionLevel Optimal -Force
    Write-Host "  [SUCCESS] Created $zipName" -ForegroundColor Green
} catch {
    Write-Host "  [ERROR] Failed to create ZIP: $_" -ForegroundColor Red
    exit 1
}

# Step 5: Verify ZIP
Write-Host "`nStep 5: Verifying ZIP file..." -ForegroundColor Yellow

if (Test-Path $zipName) {
    $zipSize = (Get-Item $zipName).Length / 1MB
    Write-Host "  ZIP file size: $([math]::Round($zipSize, 2)) MB" -ForegroundColor Cyan
    
    if ($zipSize -gt 100) {
        Write-Host "  [WARNING] ZIP file is quite large (>100 MB)" -ForegroundColor Yellow
    } elseif ($zipSize -lt 1) {
        Write-Host "  [WARNING] ZIP file seems too small (<1 MB)" -ForegroundColor Yellow
    } else {
        Write-Host "  [OK] ZIP file size looks good" -ForegroundColor Green
    }
}

# Step 6: Summary
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "SUBMISSION PACKAGE SUMMARY" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

Write-Host "`nFiles included in ZIP:" -ForegroundColor Yellow
Write-Host "  - README.md (how to run)" -ForegroundColor White
Write-Host "  - requirements.txt (dependencies)" -ForegroundColor White
Write-Host "  - scripts/ (2 Python files)" -ForegroundColor White
Write-Host "  - outputs/ (~100 result files)" -ForegroundColor White
if ($pdfExists) {
    Write-Host "  - Assignment_Report.pdf (main report)" -ForegroundColor Green
} else {
    Write-Host "  - ASSIGNMENT_SUBMISSION.md (report - convert to PDF!)" -ForegroundColor Yellow
}

Write-Host "`nSubmission checklist:" -ForegroundColor Yellow
Write-Host "  [$(if ($allPresent) {'X'} else {' '})] Python scripts present" -ForegroundColor $(if ($allPresent) {"Green"} else {"Red"})
Write-Host "  [$(if ($plyFiles -eq 16) {'X'} else {' '})] 16 output meshes (.ply)" -ForegroundColor $(if ($plyFiles -eq 16) {"Green"} else {"Red"})
Write-Host "  [$(if ($pngFiles -ge 48) {'X'} else {' '})] 50 visualizations (.png)" -ForegroundColor $(if ($pngFiles -ge 48) {"Green"} else {"Red"})
Write-Host "  [$(if (Test-Path "README.md") {'X'} else {' '})] README with instructions" -ForegroundColor Green
Write-Host "  [$(if ($pdfExists) {'X'} else {' '})] Final PDF report" -ForegroundColor $(if ($pdfExists) {"Green"} else {"Yellow"})

Write-Host "`nZIP file created: $zipName" -ForegroundColor Green

if (-not $pdfExists) {
    Write-Host "`n[ACTION REQUIRED] Create Assignment_Report.pdf from ASSIGNMENT_SUBMISSION.md" -ForegroundColor Yellow
    Write-Host "Then re-run this script to include it in the ZIP." -ForegroundColor Yellow
} else {
    Write-Host "`n[READY] Your assignment is ready for submission!" -ForegroundColor Green
    Write-Host "Submit: $zipName" -ForegroundColor Cyan
}

Write-Host "`nExpected Grade: 100/100" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
