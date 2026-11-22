# Windows PowerShell 5.1. Each request chooses its own route (including redirects).
function Invoke-ReleaseFetch {
    param([uri]$Url, [string]$OutputFile)
    [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
    foreach ($port in 7897,7890,0) {
        $route = if ($port) { "http://127.0.0.1:$port" } else { '直连' }
        $response = $null
        $stream = $null
        $output = $null
        try {
            Write-Host "请求 $($Url.Host) · $route"
            $request = [Net.HttpWebRequest]::Create($Url)
            $request.Proxy = if ($port) { [Net.WebProxy]::new($route) } else { $null }
            $request.UserAgent = 'yomihime-new-api-gateway'
            $request.Timeout = 20000
            $request.ReadWriteTimeout = 30000
            $response = $request.GetResponse()
            $stream = $response.GetResponseStream()
            if ($OutputFile) {
                $output = [IO.File]::Create($OutputFile)
                $stream.CopyTo($output)
                if ($response.ContentLength -ge 0 -and $response.ContentLength -ne $output.Length) {
                    throw '下载中断，文件长度不符。'
                }
                return
            }
            $reader = [IO.StreamReader]::new($stream)
            try { return $reader.ReadToEnd() } finally { $reader.Dispose() }
        } catch {
            Write-Warning "$route 请求失败：$($_.Exception.Message)"
        } finally {
            if ($output) { $output.Dispose() }
            if ($stream) { $stream.Dispose() }
            if ($response) { $response.Dispose() }
        }
    }
    throw '无法访问 GitHub。请检查本机代理的 HTTP/Mixed 监听端口，或使用离线导入。'
}

function Get-LatestWindowsAsset {
    $release = (Invoke-ReleaseFetch 'https://api.github.com/repos/QuantumNous/new-api/releases/latest') | ConvertFrom-Json
    $name = "new-api-$($release.tag_name).exe"
    $assets = @($release.assets | Where-Object { $_.name -ceq $name })
    if (!$release.tag_name -or $assets.Count -ne 1) { throw "Latest Release 缺少唯一的 Windows 程序 $name。" }
    $asset = $assets[0]
    if ($asset.digest -notmatch '^sha256:([0-9a-f]{64})$') { throw "$name 缺少官方 SHA256。" }
    [pscustomobject]@{ Name=$name; Url=$asset.browser_download_url; Hash=$Matches[1] }
}
