# Create Submission ZIP
# Run this script after converting Assignment_Report.md to PDF

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Assignment Submission ZIP Creator" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Check if we're in the right directory
if (-not (Test-Path "submission")) {
    Write-Host "ERROR: submission folder not found!" -ForegroundColor Red
    Write-Host "Please run this script from the Mixar directory." -ForegroundColor Yellow
    exit 1
}

# Check for PDF
$pdfExists = Test-Path "submission\Assignment_Report.pdf"
$mdExists = Test-Path "submission\Assignment_Report.md"

if ($pdfExists) {
    Write-Host "[OK] Assignment_Report.pdf found" -ForegroundColor Green
    
    # Remove the .md file if PDF exists
    if ($mdExists) {
        Remove-Item "submission\Assignment_Report.md" -Force
        Write-Host "[INFO] Removed Assignment_Report.md (PDF version exists)" -ForegroundColor Gray
    }
} else {
    Write-Host "[WARNING] Assignment_Report.pdf not found!" -ForegroundColor Yellow
    
    if ($mdExists) {
        Write-Host "" -ForegroundColor Yellow
        Write-Host "You need to convert Assignment_Report.md to PDF first:" -ForegroundColor Yellow
        Write-Host "  1. Go to https://www.markdowntopdf.com/" -ForegroundColor White
        Write-Host "  2. Upload submission\Assignment_Report.md" -ForegroundColor White
        Write-Host "  3. Download as Assignment_Report.pdf" -ForegroundColor White
        Write-Host "  4. Save it in the submission folder" -ForegroundColor White
        Write-Host "  5. Run this script again" -ForegroundColor White
        Write-Host ""
        
        $response = Read-Host "Continue creating ZIP without PDF? (Y/N)"
        if ($response -ne 'Y' -and $response -ne 'y') {
            Write-Host "Exiting. Please create the PDF and try again." -ForegroundColor Yellow
            exit 0
        }
    }
}

# Count files
$fileCount = (Get-ChildItem -Path "submission" -Recurse -File).Count
Write-Host "`nSubmission folder contains: $fileCount files" -ForegroundColor Cyan

# Create ZIP
$zipName = "Vidit_Mesh_Quantization_Assignment.zip"

if (Test-Path $zipName) {
    Write-Host "Removing old ZIP file..." -ForegroundColor Gray
    Remove-Item $zipName -Force
}

Write-Host "Creating ZIP file..." -ForegroundColor Yellow

try {
    Compress-Archive -Path "submission\*" -DestinationPath $zipName -CompressionLevel Optimal -Force
    
    $zipSize = [math]::Round((Get-Item $zipName).Length / 1MB, 2)
    
    Write-Host "`n[SUCCESS] Created: $zipName" -ForegroundColor Green
    Write-Host "Size: $zipSize MB" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "=====================================" -ForegroundColor Cyan
    Write-Host "READY TO SUBMIT!" -ForegroundColor Green
    Write-Host "=====================================" -ForegroundColor Cyan
    Write-Host "File: $zipName" -ForegroundColor White
    Write-Host ""
    
} catch {
    Write-Host "`n[ERROR] Failed to create ZIP: $_" -ForegroundColor Red
    exit 1
}
