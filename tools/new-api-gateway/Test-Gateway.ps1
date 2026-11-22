[CmdletBinding()]
param([uri]$BaseUrl = 'http://127.0.0.1:3000/v1', [string]$Model)
$ErrorActionPreference = 'Stop'
if ($BaseUrl.Scheme -notin 'http','https' -or $BaseUrl.AbsolutePath.TrimEnd('/') -ne '/v1' -or $BaseUrl.Query -or $BaseUrl.Fragment -or $BaseUrl.UserInfo) {
    throw '请填写完整的网关地址，例如 http://192.168.1.50:3000/v1'
}
Add-Type -AssemblyName System.Net.Http
$handler = [Net.Http.HttpClientHandler]::new()
$handler.UseProxy = $false
$handler.AllowAutoRedirect = $false
$client = [Net.Http.HttpClient]::new($handler)
try {
    $secret = Read-Host "请输入 $($BaseUrl.Authority) 的网关令牌" -AsSecureString
    $token = [Net.NetworkCredential]::new('', $secret).Password
    $client.DefaultRequestHeaders.Authorization = [Net.Http.Headers.AuthenticationHeaderValue]::new('Bearer', $token)
    $base = $BaseUrl.AbsoluteUri.TrimEnd('/')
    $json = $client.GetStringAsync("$base/models").GetAwaiter().GetResult() | ConvertFrom-Json
    if ($null -eq $json.data) { throw '模型列表响应缺少 data。' }
    Write-Host "网关可达，令牌可见的模型数为 $($json.data.Count)。"
    $json.data | ForEach-Object { $_.id }
    if ($Model) {
        $payload = @{ model = $Model; messages = @(@{ role = 'user'; content = 'Reply OK.' }) } | ConvertTo-Json -Depth 4
        $body = [Net.Http.StringContent]::new($payload, [Text.Encoding]::UTF8, 'application/json')
        $response = $client.PostAsync("$base/chat/completions", $body).GetAwaiter().GetResult()
        $null = $response.EnsureSuccessStatusCode()
        $reply = $response.Content.ReadAsStringAsync().GetAwaiter().GetResult() | ConvertFrom-Json
        if (!$reply.choices -or !$reply.choices[0].message) { throw '上游返回的响应中缺少对话结果。' }
        Write-Host "对话成功，响应模型 $($reply.model)。"
    }
} finally {
    $client.Dispose()
}
