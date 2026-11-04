# Firewall Evasion Lab - CyberRangeCZ Platform

A CyberRangeCZ sandbox and linear training definition that adapts the SEED **Firewall-VPN Lab** to a three-node routed sandbox. It uses the SEED-provided `vpnclient.c` and `vpnserver.c` sample programs (unencrypted UDP/TUN), with CyberRangeCZ provisioning, isolated target services, per-sandbox flags, and student exercises.

The lab is based on the learning objectives of the SEED Labs *Firewall Evasion Lab: Bypassing Firewalls using VPN*. It does **not** replace the SEED VPN implementation with a custom tunnel. The two programs in `seed-source/` preserve the SEED sample interface: `sudo ./vpnserver` and `sudo ./vpnclient <server-ip>`. The official SEED download is linked on the [Firewall-VPN Lab page](https://seedsecuritylabs.org/Labs_16.04/Networking/Firewall_VPN/).

> **Safety boundary:** The tunnel is deliberately unencrypted and unauthenticated, as in the SEED Firewall-VPN exercise, to demonstrate tunnelling separately from encryption. Use it only inside the isolated CyberRangeCZ sandbox. Never deploy it on a production network or expose it to the public Internet.

## Repository contents

```text
.
├── topology.yml                # CyberRangeCZ topology (3 nodes, 2 networks)
├── variables.yml               # Four per-sandbox six-character APG flags
├── training.json               # Importable CyberRangeCZ linear training definition
├── seed-source/
│   ├── vpnclient.c              # SEED sample VPN client (UDP/TUN)
│   ├── vpnserver.c              # SEED sample VPN server (UDP/TUN)
│   └── README.md                # Source provenance and upstream link
├── provisioning/
│   ├── playbook.yml              # CyberRangeCZ Ansible provisioning entrypoint
│   ├── group_vars/all.yml        # Lab addresses and ports
│   └── roles/
│       ├── client/               # Student account, tools, egress filter, VPN binary
│       ├── server/               # VPN binary and student access; students configure IP forwarding/NAT
│       └── router/               # Isolated target HTTP/TCP services and source restriction
├── docs/
│   ├── architecture.md
│   ├── instructor-guide.md
│   └── student-brief.md
├── scripts/
│   ├── fetch-official-seed-vpn.sh # Refresh C samples from SEED official ZIP
│   ├── validate.py                # Static checks for YAML, JSON and APG wiring
│   └── test_target.py             # HTTP/TCP service smoke test
├── .github/workflows/validate.yml
├── LICENSE
└── NOTICE.md
```

## Network design

Each sandbox contains three small nodes and two isolated networks:

```text
                         CyberRangeCZ sandbox (one student)

   Student access                                                    Protected side
   client-switch                                                     server-switch
   192.168.30.0/24                                                   192.168.20.0/24

   +-----------------------+          +---------------------------+
   | client                |          | server                    |
   | 192.168.30.5          |          | 192.168.20.5              |
   | student shell         |          | VPN server UDP/55555      |
   | egress deny rule      |          | SEED server creates tun0; student configures 192.168.53.1/24 |
   +-----------+-----------+          +-------------+-------------+
               |                                    |
               |         +--------------------------+ 
               +---------| router                   |
                         | 192.168.30.1 / 192.168.20.1
                         | target HTTP :8080 + TCP :2323
                         | only accepts source 192.168.20.5
                         +--------------------------+

   VPN client TUN: 192.168.53.5/24
   Target site:    http://192.168.20.1:8080
```

The target services run on the protected-side address of the router. The router only accepts connections to that target address when they are sourced from the VPN server (`192.168.20.5`). The client also has an egress OUTPUT rule that rejects direct packets to the target when they leave its physical interface. After students configure the server TUN, IP forwarding, firewall rules, and MASQUERADE, the VPN server forwards packets arriving on `tun0` toward the target.

This deliberately uses a fixed lab target and a separate, permitted VPN endpoint. It avoids relying on public websites, DNS answers, or Internet routing during the student exercise. CyberRangeCZ's routed network topology replaces the VirtualBox NAT Network from the source handout, so the original VirtualBox-specific ARP return-path workaround is not needed; the VPN server still performs MASQUERADE so the target returns packets to the server.

See [`docs/architecture.md`](docs/architecture.md) for the packet flow and assumptions.

## What is automated and what students do

**Automated during sandbox provisioning:**

- Compile the SEED `vpnclient.c` and `vpnserver.c` programs on their respective endpoints.
- Create the student login (`user` / `Password123`) on the client and VPN server.
- Install the client egress rule and embed the sandbox-specific firewall audit token in its comment.
- Install and compile the VPN server binary on the server; students start `vpnserver`, configure its automatically-created `tun0`, enable forwarding, and add NAT/forwarding rules themselves.
- Install the required IP forwarding and firewall tools on the server; students enable IPv4 forwarding and create target-host-scoped forwarding/MASQUERADE rules as part of the exercise.
- Start the target website on `192.168.20.1:8080` and restrict it to traffic source-NATed by the VPN server.
- Generate and place three APG flags in target-service responses (HTTP body, HTTP header, and TCP banner) and one in the client firewall rule comment.

**Students complete:**

1. Inspect the client firewall and submit the audit token.
2. Configure the server TUN interface, enable IPv4 forwarding, add UDP/55555 and target-scoped FORWARD/MASQUERADE rules, and start the VPN server.
3. Configure the client TUN interface, start the VPN client, add a host route to the target, and retrieve the web flag.
4. Use netcat to verify non-web TCP traffic through the same tunnel.
5. Capture the inner HTTP exchange on `tun0`, inspect the response header, and submit the packet-capture flag.

Both the client and VPN server are user-accessible, and each receives a trainee account. Students configure both TUN endpoints, server-side forwarding and NAT, client routing, and packet-capture verification. The target router is not provisioned with a trainee account.

## Instructor repository confidentiality

`training.json` includes solution text and hints so the platform can reveal them when a trainee requests help. Treat this as an instructor-side repository. Prefer a private Git repository when your CyberRangeCZ instance is configured to clone it; otherwise, do not publish the instructor JSON and solution material in a repository students can browse. The APG flag values themselves are generated per sandbox and are not committed here. The `user` / `Password123` account is a disposable classroom login only and must not be reused outside these isolated sandboxes.

## SEED source files and local compilation

The lab uses the SEED sample C programs rather than a locally rewritten tunnel. They bind the SEED sample UDP port `55555`, create `tun0` using `/dev/net/tun`, and use the original commands:

```bash
sudo ./vpnserver
sudo ./vpnclient 192.168.20.5
```

The programs create `tun0` themselves. Start each program first, then assign its TUN address from a second terminal; do **not** pre-create `tun0` with `ip tuntap add`.

The canonical source archive is linked on the [official SEED Firewall-VPN page](https://seedsecuritylabs.org/Labs_16.04/Networking/Firewall_VPN/). To refresh the two checked-in C files directly from that archive, run:

```bash
scripts/fetch-official-seed-vpn.sh
```

Compile locally with:

```bash
gcc -O2 -o vpnserver seed-source/vpnserver.c
gcc -O2 -o vpnclient seed-source/vpnclient.c
```

## Deploy on CyberRangeCZ

This repository follows the CyberRangeCZ **Sandbox Definition** structure (`topology.yml`, optional `variables.yml`, and `provisioning/playbook.yml`). Both `client` and `server` are user-accessible, because students perform configuration on both endpoints; the `router` is not granted trainee credentials. See the official documentation:

- [Sandbox Definition](https://docs.platform.cyberrange.cz/user-guide-advanced/sandboxes/sandbox-definition/)
- [Topology Definition](https://docs.platform.cyberrange.cz/user-guide-advanced/sandboxes/topology-definition/)
- [Sandbox Provisioning](https://docs.platform.cyberrange.cz/user-guide-advanced/sandboxes/sandbox-provisioning/)
- [APG Variables](https://docs.platform.cyberrange.cz/user-guide-advanced/sandboxes/apg-variables/)
- [Training workflow](https://docs.platform.cyberrange.cz/basic-concepts/typical-training-workflow/training-workflow-cloud/)

### 1. Publish the repository

1. Create an empty GitHub repository (public or otherwise readable by the CyberRangeCZ sandbox service).
2. From the extracted repository directory, publish the contents:

   ```bash
   git init
   git add .
   git commit -m "Add CyberRangeCZ firewall VPN lab"
   git branch -M main
   git remote add origin https://github.com/<YOUR-ORG>/<YOUR-REPO>.git
   git push -u origin main
   ```

3. Make sure the default branch contains `topology.yml` at its root.

### 2. Register the sandbox definition

In the CyberRangeCZ portal, open **Sandboxes → Sandbox Definitions → Create** and enter:

- **Git URL:** `https://github.com/<YOUR-ORG>/<YOUR-REPO>.git`
- **Revision:** `main` (or the commit/tag you want to pin)

The platform clones the Git repository and processes the topology and provisioning definition.

### 3. Create and allocate the 25-sandbox pool

1. Open the new sandbox definition and create a pool.
2. Set the pool size to **25**.
3. Allocate the pool and wait until all 25 sandboxes finish provisioning.
4. Before giving students the access token, test one allocated sandbox using the instructor checklist in [`docs/instructor-guide.md`](docs/instructor-guide.md).

**Capacity warning:** This topology uses three `standard.small` instances per sandbox. At the documented `standard.small` size of 1 vCPU and 2 GB RAM, a 25-sandbox pool needs approximately **75 vCPUs and 150 GB RAM**, plus cloud/platform overhead. The two host VMs explicitly request 16-GB root volumes; the router uses the flavor-defined disk. Under the documented 80-GB `standard.small` disk size, that is approximately **2.8 TB of nominal root-disk capacity** across 25 sandboxes. Check how your cloud handles root volumes and verify quota before allocating all 25. If your cloud uses different flavor names or smaller allowed flavors, edit the three `flavor` values in `topology.yml` to match the flavors available to your platform.

### 4. Import the training definition

1. Open **Training → Linear Training Definitions**.
2. Use **Upload** and select `training.json` from this repository.
3. Confirm that the definition is recognized as APG / variant-sandbox training. The JSON sets `variant_sandboxes: true`; the four `answer_variable_name` fields must exactly match the names in `variables.yml`.
4. Preview the levels, adjust the wording if needed, then **Release** the definition.

The official platform documentation describes uploading a linear training definition from JSON and using `Correct Answer - Variable Name` with APG variables. Keep `training.json` and `variables.yml` together in this repository so they stay synchronized.

### 5. Create a training instance

1. Open **Training → Training Instances → Create**.
2. Select this released training definition.
3. Select the allocated pool created in step 3.
4. Choose the cloud sandbox environment and set the training start/end window.
5. Create the instance with **local environment disabled**.
6. Open the instance for editing and, in the **Assign Pool** panel, assign the unlocked pool created in step 3.
7. Save the instance and share its access token with the 25 students.

Students start separate training runs; each run is assigned a sandbox from the pool. Do not share one sandbox login or one terminal session among students.

## Per-student flags

`variables.yml` defines four APG variables, each generated as a six-character random password value:

| Variable | Where students find it | Purpose |
|---|---|---|
| `flag_firewall` | Comment on the client's iptables egress rule | Firewall inspection |
| `flag_web` | Body returned by `/flag` on the blocked target | Successful VPN + route |
| `flag_tcp` | Banner returned by the TCP service on port `2323` | Non-web traffic through the same tunnel |
| `flag_pcap` | `X-CRCZ-Lab-Flag` header returned by `/capture` | Packet-capture evidence |

The corresponding training levels use `answer_variable_name` and `variant_answers: true`. This makes the correct answers sandbox-specific; no literal flag values are stored in Git. Six characters keep submissions short. The random value space is intentionally much larger than a 25-student pool, but APG answers should still be treated as training tokens—not credentials or production secrets.

## Local checks before pushing

The static validator needs Python 3 and PyYAML:

```bash
python3 -m pip install -r requirements-dev.txt
python3 scripts/validate.py
```

Compile the VPN program locally on Linux:

```bash
gcc -O2 -o /tmp/vpnserver seed-source/vpnserver.c
gcc -O2 -o /tmp/vpnclient seed-source/vpnclient.c
```

The GitHub Actions workflow runs the static validator, smoke-tests both target services, and compiles both SEED C programs on pushes and pull requests. These local checks do not replace a first CyberRangeCZ allocation and an end-to-end test: the connected cloud must contain the selected images/flavor, have package-repository access, and permit the sandbox's routed UDP/TCP traffic. Validate one sandbox before scaling the pool to 25.

## Important compatibility notes

- The current topology documentation describes `base_box.mgmt_user`. The topology in this repository follows that documented field and the Ubuntu Noble / Debian 12 image names. The exact image and flavor names must exist in your connected cloud.
- The official platform's own sample repositories also use the `topology.yml` + `provisioning/playbook.yml` pattern. The `user-access` Ansible role is provided by the CyberRangeCZ provisioning environment and is used to create the trainee account on both the client and VPN server.
- The `vpn:` field in recent CyberRangeCZ topology documentation configures the platform's NetBird access VPN. This lab does **not** use that field: it builds a separate teaching VPN inside the emulated network.
- Package installation during provisioning requires the sandbox nodes to reach their configured OS package repositories. If your deployment is isolated from package mirrors, pre-build a compatible base image or mirror the required packages.

## Credits and license

The learning objectives are adapted from Wenliang Du's SEED Labs *Firewall Evasion Lab: Bypassing Firewalls using VPN*. The original handout states that its materials are free to use for non-commercial educational purposes and prohibits commercial use; see [`NOTICE.md`](NOTICE.md). The SEED sample code is included under the conditions described in `NOTICE.md`; the original SEED project remains copyrighted by its author.

Original code and configuration created for this repository are offered under the MIT License; see [`LICENSE`](LICENSE).
