$filePath = "F:\dons\demosample.tf"
$uri = "http://localhost:8000/api/upload"

$fileBytes = [System.IO.File]::ReadAllBytes($filePath)
$fileContent = [System.Text.Encoding]::GetEncoding('iso-8859-1').GetString($fileBytes)

$boundary = [System.Guid]::NewGuid().ToString()
$LF = "`r`n"

$bodyLines = (
    "--$boundary",
    "Content-Disposition: form-data; name=`"file`"; filename=`"demosample.tf`"",
    "Content-Type: application/octet-stream$LF",
    $fileContent,
    "--$boundary--$LF"
) -join $LF

try {
    $response = Invoke-RestMethod -Uri $uri -Method Post -ContentType "multipart/form-data; boundary=$boundary" -Body $bodyLines
    Write-Host "✅ Upload successful!"
    $response | ConvertTo-Json -Depth 10
} catch {
    Write-Host "❌ Upload failed:"
    Write-Host $_.Exception.Message
    if ($_.ErrorDetails) {
        Write-Host $_.ErrorDetails.Message
    }
}
