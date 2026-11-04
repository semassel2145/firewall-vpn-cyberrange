# SEED sample VPN source

This directory contains the two unencrypted TUN-over-UDP sample programs used by the SEED Firewall-VPN exercise: `vpnserver.c` and `vpnclient.c`. They create their TUN devices with `TUNSETIFF`, use UDP port **55555**, and preserve the original command interface:

```bash
sudo ./vpnserver
sudo ./vpnclient <VPN_SERVER_IP>
```

The canonical SEED download is linked from the official [Firewall-VPN Lab page](https://seedsecuritylabs.org/Labs_16.04/Networking/Firewall_VPN/) as **Sample VPN client and server programs (without encryption)**. The official link currently resolves to `https://seedsecuritylabs.org/Labs_16.04/Networking/VPN/files/vpn.zip`.

The checked-in files were sourced from a publicly accessible mirror of the SEED sample pair at [adam-mcdaniel/vpn `src/vpnserver.c`](https://raw.githubusercontent.com/adam-mcdaniel/vpn/main/src/vpnserver.c) and [`src/vpnclient.c`](https://raw.githubusercontent.com/adam-mcdaniel/vpn/main/src/vpnclient.c). Use `scripts/fetch-official-seed-vpn.sh` to replace these mirror-sourced copies with the canonical files from SEED's downloadable archive before publishing. I could not retrieve the binary ZIP through this environment, so byte-for-byte parity with the official ZIP has not been independently verified here.

These programs are intentionally simple teaching code. They do not encrypt or authenticate the tunnel and should only be used in this isolated educational sandbox. Do not expose the UDP listener to the public Internet.
