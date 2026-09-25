$src = "C:\Users\digit\GriotApps\Cinopsis\.prism\shared\harvest_slugs.txt"
$out = "C:\Users\digit\GriotApps\Cinopsis\.prism\shared\harvest_verified.json"
$res = @()
foreach ($s in (Get-Content $src | Where-Object { $_.Trim() })) {
  $s = $s.Trim()
  try {
    $j = gh api "repos/$s" 2>$null | ConvertFrom-Json
    if ($j.full_name) {
      $res += [pscustomobject]@{ slug=$s; ok=$true; full=$j.full_name; stars=$j.stargazers_count; desc=$j.description; lang=$j.language }
    } else { $res += [pscustomobject]@{ slug=$s; ok=$false } }
  } catch { $res += [pscustomobject]@{ slug=$s; ok=$false } }
}
$res | ConvertTo-Json -Depth 4 | Set-Content $out -Encoding UTF8
"VERIFIED_DONE ok=$(($res | Where-Object ok).Count) fail=$(($res | Where-Object {-not $_.ok}).Count) total=$($res.Count)" | Set-Content "C:\Users\digit\GriotApps\Cinopsis\.prism\shared\VERIFY_DONE.txt"
