$interfaces = [System.Net.NetworkInformation.NetworkInterface]::GetAllNetworkInterfaces()
$results = foreach ($nic in $interfaces) {
    $props = $nic.GetIPProperties()
    $ips = ($props.UnicastAddresses | ForEach-Object { $_.Address.ToString() }) -join ', '
    $gateways = ($props.GatewayAddresses | ForEach-Object { $_.Address.ToString() }) -join ', '
    [PSCustomObject]@{
        Name        = $nic.Name
        Description = $nic.Description
        Status      = $nic.OperationalStatus
        SpeedMbps   = [math]::Round($nic.Speed / 1000000, 2)
        Type        = $nic.NetworkInterfaceType
        Mac         = $nic.GetPhysicalAddress().ToString()
        IPs         = $ips
        Gateways    = $gateways
    }
}
$results | Format-List
