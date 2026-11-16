Add-Type -AssemblyName System.Drawing

$width = 1920
$height = 1200
$bmp = New-Object System.Drawing.Bitmap($width, $height)
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$g.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::ClearTypeGridFit

# Colors
$bgBrush = New-Object System.Drawing.SolidBrush([System.Drawing.ColorTranslator]::FromHtml('#F4F6F0'))
$g.FillRectangle($bgBrush, 0, 0, $width, $height)

$headerBgBrush = New-Object System.Drawing.SolidBrush([System.Drawing.ColorTranslator]::FromHtml('#1B4332'))
$cardBgBrush = New-Object System.Drawing.SolidBrush([System.Drawing.ColorTranslator]::FromHtml('#FFFFFF'))
$cardBorderPen = New-Object System.Drawing.Pen([System.Drawing.ColorTranslator]::FromHtml('#2D6A4F'), 2)
$textDarkBrush = New-Object System.Drawing.SolidBrush([System.Drawing.ColorTranslator]::FromHtml('#1A202C'))
$textMutedBrush = New-Object System.Drawing.SolidBrush([System.Drawing.ColorTranslator]::FromHtml('#4A5568'))
$pkBrush = New-Object System.Drawing.SolidBrush([System.Drawing.ColorTranslator]::FromHtml('#D97706'))
$fkBrush = New-Object System.Drawing.SolidBrush([System.Drawing.ColorTranslator]::FromHtml('#2563EB'))
$linePen = New-Object System.Drawing.Pen([System.Drawing.ColorTranslator]::FromHtml('#40916C'), 2)
$titleBrush = New-Object System.Drawing.SolidBrush([System.Drawing.ColorTranslator]::FromHtml('#081C15'))
$subtitleBrush = New-Object System.Drawing.SolidBrush([System.Drawing.ColorTranslator]::FromHtml('#52796F'))

# Fonts
$titleFont = New-Object System.Drawing.Font('Segoe UI', 22, [System.Drawing.FontStyle]::Bold)
$subFont = New-Object System.Drawing.Font('Segoe UI', 12, [System.Drawing.FontStyle]::Regular)
$headerFont = New-Object System.Drawing.Font('Segoe UI', 12, [System.Drawing.FontStyle]::Bold)
$attrFont = New-Object System.Drawing.Font('Segoe UI', 10, [System.Drawing.FontStyle]::Regular)
$typeFont = New-Object System.Drawing.Font('Consolas', 9, [System.Drawing.FontStyle]::Regular)
$relFont = New-Object System.Drawing.Font('Segoe UI', 10, [System.Drawing.FontStyle]::Bold)
$whiteBrush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::White)

# Title Banner
$g.DrawString('Smart Food Waste Reduction & Donation Management System', $titleFont, $titleBrush, 50, 30)
$g.DrawString('Relational Entity-Relationship (ER) Diagram -- Fully Normalized to 3NF', $subFont, $subtitleBrush, 52, 70)

# Legend Box
$g.FillRectangle($cardBgBrush, 1340, 25, 530, 75)
$g.DrawRectangle($cardBorderPen, 1340, 25, 530, 75)
$g.DrawString('LEGEND:', $headerFont, $titleBrush, 1355, 35)
$g.DrawString('[PK] Primary Key (Gold)', $attrFont, $pkBrush, 1355, 60)
$g.DrawString('[FK] Foreign Key (Blue)', $attrFont, $fkBrush, 1540, 60)
$g.DrawString('--- 1 : N / 1 : 1 Cardinality', $attrFont, $titleBrush, 1710, 60)

# Helper function to draw an entity
function Draw-Entity($title, $x, $y, $w, $attrs) {
    $headerH = 34
    $rowH = 22
    $totalH = $headerH + ($attrs.Count * $rowH) + 10
    
    # Shadow
    $shadowBrush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(25, 0, 0, 0))
    $g.FillRectangle($shadowBrush, $x + 4, $y + 4, $w, $totalH)
    
    # Body
    $g.FillRectangle($cardBgBrush, $x, $y, $w, $totalH)
    $g.DrawRectangle($cardBorderPen, $x, $y, $w, $totalH)
    
    # Header
    $g.FillRectangle($headerBgBrush, $x, $y, $w, $headerH)
    $g.DrawString($title, $headerFont, $whiteBrush, $x + 12, $y + 7)
    
    # Attributes
    $currY = $y + $headerH + 6
    foreach ($a in $attrs) {
        $parts = $a -split '\|'
        $keyType = $parts[0].Trim()
        $name = $parts[1].Trim()
        $datatype = $parts[2].Trim()
        
        $brush = $textDarkBrush
        if ($keyType -eq 'PK') {
            $g.DrawString('[PK]', $typeFont, $pkBrush, $x + 8, $currY)
            $brush = $titleBrush
        } elseif ($keyType -eq 'FK') {
            $g.DrawString('[FK]', $typeFont, $fkBrush, $x + 8, $currY)
        } else {
            $g.DrawString('    ', $typeFont, $textMutedBrush, $x + 8, $currY)
        }
        
        $g.DrawString($name, $attrFont, $brush, $x + 46, $currY)
        $g.DrawString($datatype, $typeFont, $textMutedBrush, $x + $w - 110, $currY)
        $currY += $rowH
    }
}

# Draw Entities
$uAttrs = @('PK|User_ID|INT AUTO', '  |Name|VARCHAR(100)', '  |Phone|VARCHAR(20)', '  |Email|VARCHAR(100) UQ', '  |Password|VARCHAR(255)', '  |Address|TEXT', '  |User_Type|ENUM', '  |Date_Joined|DATETIME')
Draw-Entity 'USER' 60 140 330 $uAttrs

$ngoAttrs = @('PK|NGO_ID|INT AUTO', 'FK|User_ID|INT (USER)', '  |NGO_Name|VARCHAR(150)', '  |Address|TEXT', '  |Contact_No|VARCHAR(20)', '  |License_No|VARCHAR(50) UQ', '  |NGO_Type|VARCHAR(50)', '  |Email|VARCHAR(100)', '  |Website|VARCHAR(150)')
Draw-Entity 'NGO_RECEIVER' 60 410 330 $ngoAttrs

$dAttrs = @('PK|Donation_ID|INT AUTO', 'FK|User_ID|INT (Donor)', 'FK|Claimed_By_NGO_ID|INT (NGO)', '  |Food_Type|VARCHAR(120)', '  |Quantity|DECIMAL(10,2)', '  |Unit|VARCHAR(20)', '  |Packaging_Type|VARCHAR(80)', '  |Pickup_Address|TEXT', '  |Food_Category|ENUM', '  |Prepared_On|DATETIME', '  |Expiry_Date|DATETIME', '  |Status|ENUM', '  |Donation_Time|DATETIME')
Draw-Entity 'DONATION' 500 140 370 $dAttrs

$pAttrs = @('PK|Pickup_ID|INT AUTO', 'FK|Donation_ID|INT (UQ)', 'FK|Center_ID|INT (CENTER)', '  |Pickup_Time|DATETIME', '  |Vehicle_No|VARCHAR(30)', '  |Driver_Name|VARCHAR(100)', '  |Notes|TEXT', '  |Status|ENUM', '  |Completed_At|DATETIME')
Draw-Entity 'PICKUP' 980 140 350 $pAttrs

$cAttrs = @('PK|Center_ID|INT AUTO', '  |Center_Name|VARCHAR(150)', '  |Address|TEXT', '  |Contact_No|VARCHAR(20)', '  |Capacity|DECIMAL(10,2)', '  |Current_Occupancy|DECIMAL(10,2)', '  |Center_Type|VARCHAR(50)')
Draw-Entity 'COLLECTION_CENTER' 1440 140 370 $cAttrs

$rAttrs = @('PK|Review_ID|INT AUTO', 'FK|Donation_ID|INT (DONATION)', 'FK|User_ID|INT (USER)', '  |Rating|INT (1..5)', '  |Comment|TEXT', '  |Review_Date|DATETIME')
Draw-Entity 'REVIEW' 500 560 370 $rAttrs

$wAttrs = @('PK|Waste_ID|INT AUTO', 'FK|Center_ID|INT (CENTER)', 'FK|Report_ID|INT (REPORT)', '  |Waste_Type|ENUM', '  |Quantity|DECIMAL(10,2)', '  |Unit|VARCHAR(20)', '  |Description|TEXT', '  |Recorded_Date|DATETIME', '  |Status|ENUM')
Draw-Entity 'WASTE_ITEM' 1440 430 370 $wAttrs

$prAttrs = @('PK|Process_ID|INT AUTO', 'FK|Center_ID|INT (CENTER)', 'FK|Waste_ID|INT (WASTE)', '  |Process_Type|ENUM', '  |Start_Date|DATETIME', '  |End_Date|DATETIME', '  |Input_Quantity|DECIMAL', '  |Output_Quantity|DECIMAL', '  |Remarks|TEXT', '  |Status|ENUM')
Draw-Entity 'PROCESS' 1440 730 370 $prAttrs

$repAttrs = @('PK|Report_ID|INT AUTO', 'FK|Center_ID|INT (CENTER)', 'FK|Generated_By_User_ID|INT (USER)', '  |Report_Type|ENUM', '  |Start_Date|DATE', '  |End_Date|DATE', '  |Generated_On|DATETIME', '  |Summary|TEXT')
Draw-Entity 'REPORT' 980 560 350 $repAttrs

# Draw Relationships
# 1. USER -> DONATION (1:N)
$g.DrawLine($linePen, 390, 200, 500, 200)
$g.DrawString('1 : N (Makes)', $relFont, $titleBrush, 400, 180)

# 2. USER -> NGO_RECEIVER (1:1)
$g.DrawLine($linePen, 225, 335, 225, 410)
$g.DrawString('1 : 1 (Specializes)', $relFont, $titleBrush, 230, 365)

# 3. DONATION -> NGO_RECEIVER (N:1 Claimed)
$g.DrawLine($linePen, 500, 300, 390, 480)
$g.DrawString('N : 1 (Claimed By)', $relFont, $titleBrush, 400, 390)

# 4. DONATION -> PICKUP (1:1 Scheduled)
$g.DrawLine($linePen, 870, 220, 980, 220)
$g.DrawString('1 : 1 (Scheduled For)', $relFont, $titleBrush, 875, 200)

# 5. PICKUP -> COLLECTION_CENTER (N:1 Routed Via)
$g.DrawLine($linePen, 1330, 220, 1440, 220)
$g.DrawString('N : 1 (Routed Via)', $relFont, $titleBrush, 1340, 200)

# 6. DONATION -> REVIEW (1:N Feedback)
$g.DrawLine($linePen, 685, 475, 685, 560)
$g.DrawString('1 : N (Evaluated In)', $relFont, $titleBrush, 690, 510)

# 7. USER -> REVIEW (1:N Submits)
$g.DrawLine($linePen, 390, 260, 440, 260)
$g.DrawLine($linePen, 440, 260, 440, 620)
$g.DrawLine($linePen, 440, 620, 500, 620)
$g.DrawString('1 : N (Submits)', $relFont, $titleBrush, 410, 580)

# 8. COLLECTION_CENTER -> WASTE_ITEM (1:N Logs)
$g.DrawLine($linePen, 1625, 345, 1625, 430)
$g.DrawString('1 : N (Receives Waste)', $relFont, $titleBrush, 1630, 380)

# 9. WASTE_ITEM -> PROCESS (1:N Treats)
$g.DrawLine($linePen, 1625, 665, 1625, 730)
$g.DrawString('1 : N (Processes In)', $relFont, $titleBrush, 1630, 690)

# 10. COLLECTION_CENTER -> REPORT (1:N Generates)
$g.DrawLine($linePen, 1440, 290, 1360, 290)
$g.DrawLine($linePen, 1360, 290, 1360, 660)
$g.DrawLine($linePen, 1360, 660, 1330, 660)
$g.DrawString('1 : N (Reports On)', $relFont, $titleBrush, 1340, 630)

# Save Bitmap
$outputPath = 'C:\Users\prath\.gemini\antigravity\scratch\food-waste-management\ER_Diagram_generated.png'
$bmp.Save($outputPath, [System.Drawing.Imaging.ImageFormat]::Png)
$g.Dispose()
$bmp.Dispose()
Write-Output "Successfully generated $outputPath (Canonical Chen ER Diagram is preserved at ER_Diagram.png and static/images/er_diagram.png)"
