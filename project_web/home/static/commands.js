function ipaddress(web_part)
{
    var ip = location.host
    ip += '/' + web_part
    ip = 'http://' + ip
    document.location.href = ip

}