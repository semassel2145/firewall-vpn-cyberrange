# Instructor deployment and validation guide

> **Confidentiality:** `training.json` contains instructor solutions and hints. Keep the repository private if CyberRangeCZ can clone it, or keep the instructor training JSON outside any student-visible repository. APG values are generated independently for each sandbox and are not committed as literals.

## Before deployment

1. Confirm the cloud contains the selected Ubuntu Noble and Debian 12 images.
2. Confirm the selected flavor exists and is small enough for the pool.
3. Ensure provisioning can install `build-essential`, `iproute2`, `iptables`, `tcpdump`, `curl`, and `python3`.
4. Ensure the provisioning environment has the CyberRangeCZ `user-access` Ansible role.
5. Confirm both `client-switch` and `server-switch` are user-accessible and that `user-access` is applied to `client` and `server`. The router intentionally has no trainee account.
6. Test one sandbox before allocating the pool of 25.

## Capacity planning for 25 students

The topology has three nodes per sandbox: one Ubuntu client, one Ubuntu VPN server, and one Debian router/target. At `standard.small` (1 vCPU, 2 GB RAM), 25 sandboxes require approximately 75 VMs, 75 vCPUs, and 150 GB RAM, plus storage and platform overhead. Verify the actual cloud quotas and flavor definitions before scaling.

## One-sandbox smoke test

On the client, verify the firewall is active and the token appears in its rule comment:

```bash
sudo systemctl status lab-egress-firewall.service
sudo iptables-save | grep CRCZ-FW-AUDIT
curl --connect-timeout 3 http://192.168.20.1:8080/
```

The direct HTTP request must fail before the tunnel is configured. On the server, start the sample VPN server in terminal 1:

```bash
sudo /usr/local/sbin/vpnserver
```

The SEED program creates `tun0` itself. In terminal 2 on the server, configure the interface and forwarding:

```bash
sudo ip addr add 192.168.53.1/24 dev tun0
sudo ip link set tun0 up
sudo sysctl -w net.ipv4.ip_forward=1
IFACE=$(ip -o route get 192.168.20.1 | awk '{for (i=1;i<=NF;i++) if ($i=="dev") {print $(i+1); exit}}')
sudo iptables -I INPUT 1 -p udp -s 192.168.30.5 --dport 55555 -j ACCEPT
sudo iptables -I FORWARD 1 -i tun0 -o "$IFACE" -d 192.168.20.1/32 -j ACCEPT
sudo iptables -I FORWARD 1 -i "$IFACE" -o tun0 -s 192.168.20.1/32 -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
sudo iptables -t nat -A POSTROUTING -s 192.168.53.0/24 -d 192.168.20.1/32 -o "$IFACE" -j MASQUERADE
```

On the client, start the VPN client in terminal 1:

```bash
sudo /usr/local/bin/vpnclient 192.168.20.5
```

In terminal 2 on the client, configure its automatically-created TUN interface and route only the blocked host through it:

```bash
sudo ip addr add 192.168.53.5/24 dev tun0
sudo ip link set tun0 up
sudo ip route replace 192.168.20.1/32 dev tun0
curl http://192.168.20.1:8080/flag
nc -nv 192.168.20.1 2323
curl -i http://192.168.20.1:8080/capture
```

The route lookup for `192.168.20.1` on the client must select `tun0`. The web body, TCP banner, and response header must contain their corresponding six-character APG flags. Confirm that the sample VPN server/client are not pre-started and `tun0` is not already present before students begin.

## Packet-capture evidence

On the client, capture both sides of encapsulation while making an HTTP request:

```bash
sudo tcpdump -ni tun0 -s0 'host 192.168.20.1 and tcp port 8080'
sudo tcpdump -ni <physical-interface> 'udp port 55555'
```

Expected: inner HTTP/TCP packets appear on `tun0`; outer UDP packets to `192.168.20.5:55555` appear on the physical NIC. Since the SEED sample does not encrypt its tunnel, packet content is visible after decapsulation.

## APG answer mapping

| Training level | APG variable | Where students find it |
|---|---|---|
| Inspect the egress filter | `flag_firewall` | Client iptables comment |
| Reach the protected web service | `flag_web` | HTTP body at `/flag` |
| Verify non-web traffic | `flag_tcp` | TCP banner on port `2323` |
| Prove the tunnel path | `flag_pcap` | HTTP response header at `/capture` |

The `variables.yml` names must match `answer_variable_name` in `training.json`. No literal flag values should be committed.

## Troubleshooting

**`tun0` already exists:** stop the previous VPN process and remove the old interface only as an instructor reset. Students should not manually pre-create `tun0`, because the SEED sample creates it when it starts.

**Client does not connect:** confirm that the server program is running, server UDP/55555 is reachable from `192.168.30.5`, and the server and client were started in the correct order. The simple sample sends a one-shot `Hello` datagram; start the server before starting the client.

**Target does not respond:** check the client route, server `ip_forward`, the FORWARD rules, the POSTROUTING MASQUERADE rule, and the router's target rule permitting source `192.168.20.5`.
