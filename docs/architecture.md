# Architecture and packet flow

## Nodes and networks

| Node | Platform role | Interface network | Static address | Access |
|---|---|---|---|---|
| `client` | Student workstation | `client-switch` | `192.168.30.5/24` | User-accessible |
| `server` | Student-configured VPN endpoint | `server-switch` | `192.168.20.5/24` | User-accessible |
| `router` | Inter-network router and target HTTP/TCP services | Both switches | `192.168.30.1/24`, `192.168.20.1/24` | Router node; no trainee account provisioned |

Both `client-switch` and `server-switch` are user-accessible. The CyberRangeCZ `user-access` role creates the trainee account on `client` and `server`. The `router` has no trainee account; it hosts the target services and applies the target-address source restriction.

## Baseline policy

The client has an OUTPUT rule equivalent to:

```bash
iptables -I OUTPUT 1 -o <client-physical-interface> \
  -d 192.168.20.1/32 -m comment --comment CRCZ-FW-AUDIT:<APG_VALUE> -j REJECT
```

The router's target-address INPUT policy allows packets destined to `192.168.20.1` only when sourced from `192.168.20.5`. This second control is intentional defense-in-depth: removing the client rule alone does not expose the target services. The target hosts an HTTP service on TCP/8080 and a diagnostic TCP banner/echo service on TCP/2323.

## VPN overlay

| Component | Value |
|---|---|
| Transport | UDP |
| Endpoint | `192.168.20.5:55555`/UDP |
| Server TUN | `192.168.53.1/24` |
| Client TUN | `192.168.53.5/24` |
| Target | `192.168.20.1:8080` (HTTP) and `192.168.20.1:2323` (TCP diagnostic) |

The server is provisioned with the VPN program but starts without a TUN interface or active forwarding/NAT configuration. Students must enable `net.ipv4.ip_forward=1` and add target-scoped rules to forward IP packets from `tun0` to the server-side network. A MASQUERADE rule rewrites the source address to `192.168.20.5`, so the router can return the reply to the VPN server. The forwarding and NAT rules are scoped to the target host rather than only the HTTP port, allowing the same tunnel to carry the non-web TCP service on port 2323. Conntrack reverses the translation and the server forwards the reply into `tun0`.

The client must add only this host route:

```bash
sudo ip route replace 192.168.20.1/32 dev tun0
```

The default route remains unchanged. That is essential: the outer UDP packet to `192.168.20.5:55555`/UDP must continue to use the physical network, while the inner packet for `192.168.20.1` is sent to `tun0`.

## Why this differs slightly from the SEED VirtualBox layout

The source lab emulates the Internet with a VirtualBox NAT Network and discusses a NAT return-path/ARP workaround. CyberRangeCZ provides routed sandbox networks through its router nodes, so this implementation uses two isolated routed networks instead of a VirtualBox NAT Network. The protected target is a service bound to the router's `192.168.20.1` interface. The VPN server still performs source NAT: without it, the target would see the inner source `192.168.53.5` and would not have a route back to that VPN overlay. With MASQUERADE, the target sees `192.168.20.5`, replies to the VPN server, and connection tracking restores the original tunnel destination. This preserves the learning objective while removing a VirtualBox-specific workaround that does not apply to this topology.

## Packet path

The following is the expected path after students complete the endpoint configuration.

1. `curl` creates an inner TCP packet addressed to `192.168.20.1:8080` (HTTP) and `192.168.20.1:2323` (TCP diagnostic).
2. The client routing table selects `tun0`, so the physical-interface egress rule does not match the inner packet.
3. `vpnclient` reads the IP packet from `/dev/net/tun` and sends its bytes as a UDP payload to `192.168.20.5:55555`/UDP.
4. The VPN server receives the UDP datagram, writes the inner packet to its TUN interface, and Linux forwards it toward `192.168.20.1`.
5. Server-side MASQUERADE changes the source to `192.168.20.5`.
6. The router permits target traffic only from `192.168.20.5`, serves the HTTP or TCP response, and sends it back to the VPN server.
7. Conntrack restores the destination `192.168.53.5`; the server's route sends the reply to `tun0`; `vpnserver` encapsulates it in UDP and sends it back to the client.
8. The client writes the returned packet to its TUN device; the TCP stack completes the HTTP exchange.

## Evidence expected

- On `tun0`: inner IP/TCP packets to `192.168.20.1:8080` (HTTP) and `192.168.20.1:2323` (TCP diagnostic), including the HTTP response.
- On the client's physical interface: outer UDP packets to `192.168.20.5:55555`/UDP.
- The tunnel is not encrypted. Inner traffic may be visible to an observer who can capture the tunnel endpoint traffic. This limitation is deliberate and is part of the final assessment.


## SEED program behavior

The deployed binaries are compiled from `seed-source/vpnserver.c` and `seed-source/vpnclient.c`, the sample pair linked by the SEED Firewall-VPN Lab. The server is started with no arguments; the client is started with the server IPv4 address as its only argument. Both programs create `tun0` themselves through `/dev/net/tun`. Students must therefore start the program first and configure the interface from another terminal. The sample programs use UDP port `55555` and are intentionally unencrypted.
