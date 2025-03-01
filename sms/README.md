# postmarketOS 环境配置

### 手机
- 目前在用 Redmi 5 Plus (xiaomi-vince)
- 最好是 OnePlus 6/6T


### 镜像准备
```toml
# cat ~/.config/pmbootstrap_v3.cfg
[pmbootstrap]
device = qcom-msm8953
extra_packages = vim,file,curl,zstd,msm-modem-uim-selection,modemmanager,networkmanager,alpine-sdk,python3-dev,py3-pip,avahi,dbus-dev,cmake,byobu
hostname = thb-sms-secondary
is_default_channel = False
locale = zh_CN.UTF-8
ssh_keys = True
timezone = Asia/Shanghai
user = proton

[providers]

[mirrors]
alpine = https://mirrors.tuna.tsinghua.edu.cn/alpine/
pmaports = https://mirrors.tuna.tsinghua.edu.cn/postmarketOS/
systemd = https://mirrors.tuna.tsinghua.edu.cn/postmarketOS/extra-repos/systemd/
```

### 配置

#### 初始化

```bash
function phone-net {
    IFACE=$(ls -t /sys/class/net | grep enx | head -n 1)
    sudo ip a add 172.16.42.2/24 dev $IFACE
    sudo ip l set $IFACE up
    ssh-keygen -f '/home/proton/.ssh/known_hosts' -R '172.16.42.1'
}

function phone-init {
    expect <<'EOF'
spawn ssh 172.16.42.1
send "sudo su\r"
expect "password:"
send "feisuzhu\r"
expect "# "
send "echo permit nopass keepenv :wheel > /etc/doas.conf\r"
send "rm -f /etc/doas.d/*\r"
send "exit\r"
send "exit\r"
expect eof
EOF
    ssh 172.16.42.1 sudo sh -x - <<EOF
ip r a default via 172.16.42.2
cat <<EOF2 | tee /etc/resolv.conf
nameserver 192.168.233.1
EOF2
cat <<EOF2 >> /etc/ssl/certs/ca-certificates.crt
-----BEGIN CERTIFICATE-----
MIIFazCCA1OgAwIBAgIRAIIQz7DSQONZRGPgu2OCiwAwDQYJKoZIhvcNAQELBQAw
TzELMAkGA1UEBhMCVVMxKTAnBgNVBAoTIEludGVybmV0IFNlY3VyaXR5IFJlc2Vh
cmNoIEdyb3VwMRUwEwYDVQQDEwxJU1JHIFJvb3QgWDEwHhcNMTUwNjA0MTEwNDM4
WhcNMzUwNjA0MTEwNDM4WjBPMQswCQYDVQQGEwJVUzEpMCcGA1UEChMgSW50ZXJu
ZXQgU2VjdXJpdHkgUmVzZWFyY2ggR3JvdXAxFTATBgNVBAMTDElTUkcgUm9vdCBY
MTCCAiIwDQYJKoZIhvcNAQEBBQADggIPADCCAgoCggIBAK3oJHP0FDfzm54rVygc
h77ct984kIxuPOZXoHj3dcKi/vVqbvYATyjb3miGbESTtrFj/RQSa78f0uoxmyF+
0TM8ukj13Xnfs7j/EvEhmkvBioZxaUpmZmyPfjxwv60pIgbz5MDmgK7iS4+3mX6U
A5/TR5d8mUgjU+g4rk8Kb4Mu0UlXjIB0ttov0DiNewNwIRt18jA8+o+u3dpjq+sW
T8KOEUt+zwvo/7V3LvSye0rgTBIlDHCNAymg4VMk7BPZ7hm/ELNKjD+Jo2FR3qyH
B5T0Y3HsLuJvW5iB4YlcNHlsdu87kGJ55tukmi8mxdAQ4Q7e2RCOFvu396j3x+UC
B5iPNgiV5+I3lg02dZ77DnKxHZu8A/lJBdiB3QW0KtZB6awBdpUKD9jf1b0SHzUv
KBds0pjBqAlkd25HN7rOrFleaJ1/ctaJxQZBKT5ZPt0m9STJEadao0xAH0ahmbWn
OlFuhjuefXKnEgV4We0+UXgVCwOPjdAvBbI+e0ocS3MFEvzG6uBQE3xDk3SzynTn
jh8BCNAw1FtxNrQHusEwMFxIt4I7mKZ9YIqioymCzLq9gwQbooMDQaHWBfEbwrbw
qHyGO0aoSCqI3Haadr8faqU9GY/rOPNk3sgrDQoo//fb4hVC1CLQJ13hef4Y53CI
rU7m2Ys6xt0nUW7/vGT1M0NPAgMBAAGjQjBAMA4GA1UdDwEB/wQEAwIBBjAPBgNV
HRMBAf8EBTADAQH/MB0GA1UdDgQWBBR5tFnme7bl5AFzgAiIyBpY9umbbjANBgkq
hkiG9w0BAQsFAAOCAgEAVR9YqbyyqFDQDLHYGmkgJykIrGF1XIpu+ILlaS/V9lZL
ubhzEFnTIZd+50xx+7LSYK05qAvqFyFWhfFQDlnrzuBZ6brJFe+GnY+EgPbk6ZGQ
3BebYhtF8GaV0nxvwuo77x/Py9auJ/GpsMiu/X1+mvoiBOv/2X/qkSsisRcOj/KK
NFtY2PwByVS5uCbMiogziUwthDyC3+6WVwW6LLv3xLfHTjuCvjHIInNzktHCgKQ5
ORAzI4JMPJ+GslWYHb4phowim57iaztXOoJwTdwJx4nLCgdNbOhdjsnvzqvHu7Ur
TkXWStAmzOVyyghqpZXjFaH3pO3JLF+l+/+sKAIuvtd7u+Nxe5AW0wdeRlN8NwdC
jNPElpzVmbUq4JUagEiuTDkHzsxHpFKVK7q4+63SM1N95R1NbdWhscdCb+ZAJzVc
oyi3B43njTOQ5yOf+1CceWxG1bQVs5ZufpsMljq4Ui0/1lvh+wjChP4kqKOJ2qxq
4RgqsahDYVvTH9w7jXbyLeiNdd8XM2w9U/t7y0Ff/9yi0GE44Za4rF2LN9d11TPA
mRGunUHBcnWEvgJBQl9nJEiU0Zsnvgc/ubhPgXRR4Xq37Z0j4r7g1SgEEzwxA57d
emyPxgcYxn/eR44/KJ4EBs+lVDR3veyJm+kXQ99b21/+jh5Xos1AnX5iItreGCc=
-----END CERTIFICATE-----
EOF2
date -s "$(date -R)"
apk update
rc-update add modemmanager default
rc-update add networkmanager default
rc-update add avahi-daemon default
rc-update add avahi-dnsconfd default
pip install dbus-python requests ipython --break-system-packages
EOF
}
```

#### Dual SIM 卡的配置

这个被 `msm-modem-uim-selection` 接管了，不需要再执行这个，放这里仅供参考

```bash
# qmicli -d qrtr://0 --uim-change-provisioning-session="slot=1,activate=yes,session-type=primary-gw-provisioning,aid=A0:00:00:00:87:10:02:FF:86:FF:FF:89:FF:FF:FF:FF"
```

#### 配置 Network Manager

```bash
# nmcli c add type gsm ifname qrtr0 con-name me apn 3gnet
```

之后使用 `nmtui` 激活 `me` 就可以

WiFi 也可以打开

### Quirks

- 需要完全重启一次 Modem 才能工作
