# Student brief: SEED Firewall-VPN Lab on CyberRangeCZ

## Scenario

You are a workstation inside a restricted network. An egress firewall blocks a target host, but the VPN endpoint is reachable. Inspect the filter, start the SEED VPN server and client sample programs, configure their TUN interfaces, add server-side forwarding/NAT, route only the target through the tunnel, and prove the packet path.

## Access

Open both `client` and `server` from the CyberRangeCZ topology. Login on each node with `user` / `Password123`. The `router` hosts the target services and has no trainee login.

## Addresses

| Item | Address |
|---|---|
| Client | `192.168.30.5/24` |
| VPN server | `192.168.20.5:55555/UDP` |
| Target HTTP site | `http://192.168.20.1:8080` |
| Target TCP diagnostic service | `192.168.20.1:2323` |
| Client TUN | `192.168.53.5/24` |
| Server TUN | `192.168.53.1/24` |

## Rules

- Do not disable, flush, or remove the client's egress firewall rule.
- Do not change the client default route.
- Start each SEED VPN program **before** assigning its TUN interface address. The program creates `tun0` itself. Do not create `tun0` manually with `ip tuntap add`.
- Configure the server's TUN interface, IPv4 forwarding, forwarding rules, and MASQUERADE.
- Identify the server-side interface with `ip route get 192.168.20.1`; do not assume a fixed NIC name.
- Route only `192.168.20.1/32` through the client `tun0`.
- Keep all activity inside this sandbox.
- The SEED sample tunnel is unencrypted and unauthenticated; this is intentional.

## Work to complete

1. Inspect the client firewall and submit the audit token.
2. On `server`, run `/usr/local/sbin/vpnserver` in a terminal. In another terminal configure `tun0` as `192.168.53.1/24`, enable IPv4 forwarding, add UDP/55555 INPUT and target-scoped FORWARD/MASQUERADE rules.
3. On `client`, run `/usr/local/bin/vpnclient 192.168.20.5` in a terminal. In another terminal configure `tun0` as `192.168.53.5/24`, add the target host route, and retrieve the HTTP flag.
4. Use netcat to reach the non-web TCP service on port `2323` and submit its banner token.
5. Capture the HTTP response on `tun0`, inspect the `X-CRCZ-Lab-Flag` header, and submit that token.

## Useful tools

`ip`, `sysctl`, `iptables-save`, `iptables`, `curl`, `nc`, `tcpdump`, and the supplied `/usr/local/sbin/vpnserver` / `/usr/local/bin/vpnclient` programs.
