# Notices and attribution

This CyberRangeCZ adaptation is based on Wenliang Du's **SEED Labs – Firewall Evasion Lab: Bypassing Firewalls using VPN**. The supplied SEED handout states that the SEED materials are free to use for non-commercial educational purposes and that commercial uses are prohibited.

The SEED Firewall-VPN page links the sample VPN client and server programs without encryption: <https://seedsecuritylabs.org/Labs_16.04/Networking/Firewall_VPN/>. The canonical downloadable archive is `https://seedsecuritylabs.org/Labs_16.04/Networking/VPN/files/vpn.zip`. The two programs in `seed-source/` are mirror-sourced copies of the SEED sample pair. `scripts/fetch-official-seed-vpn.sh` replaces them with the canonical files from that official archive. The archive itself was not downloadable by the tooling used to prepare this repository, so byte-for-byte parity should be confirmed by running that script before publishing. Do not remove SEED attribution. This educational adaptation should be treated as non-commercial unless separate permission is obtained from the rights holder.

The MIT license in `LICENSE` applies only to original CyberRangeCZ topology/provisioning/configuration scripts and documentation created for this repository. It does not override or expand the terms applying to SEED sample source code or SEED lab materials.
