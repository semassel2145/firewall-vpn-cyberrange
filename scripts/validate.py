#!/usr/bin/env python3
"""Static validation for the CyberRangeCZ sandbox/training repository."""
from __future__ import annotations
import json, pathlib, re, sys
try:
    import yaml
except ImportError:
    print("Missing dependency: PyYAML. Install with: python3 -m pip install PyYAML", file=sys.stderr)
    raise SystemExit(2)
ROOT = pathlib.Path(__file__).resolve().parents[1]
def load_yaml(path):
    with path.open(encoding="utf-8") as stream: return yaml.safe_load(stream)
def main() -> int:
    errors=[]
    topology=load_yaml(ROOT/"topology.yml")
    apg=load_yaml(ROOT/"variables.yml")
    playbook=load_yaml(ROOT/"provisioning/playbook.yml")
    with (ROOT/"training.json").open(encoding="utf-8") as stream: training=json.load(stream)
    if topology.get("name") != "firewall-vpn-evasion": errors.append("topology.yml: unexpected topology name")
    hosts={x["name"] for x in topology.get("hosts",[])}; routers={x["name"] for x in topology.get("routers",[])}
    if hosts != {"client","server"}: errors.append(f"topology.yml: expected client/server hosts, got {sorted(hosts)}")
    if routers != {"router"}: errors.append(f"topology.yml: expected router node, got {sorted(routers)}")
    networks={x["name"]:x for x in topology.get("networks",[])}
    for name in ("server-switch","client-switch"):
        if networks.get(name,{}).get("accessible_by_user") is not True: errors.append(f"topology.yml: {name} must be user-accessible")
    required={"flag_firewall","flag_web","flag_tcp","flag_pcap"}
    if set(apg)!=required: errors.append(f"variables.yml: expected {sorted(required)}, got {sorted(apg)}")
    for name,value in apg.items():
        if value.get("type")!="password" or value.get("length")!=6: errors.append(f"variables.yml: {name} must be a six-character password variable")
    if not training.get("variant_sandboxes"): errors.append("training.json: variant_sandboxes must be true")
    used=set()
    for level in training.get("levels",[]):
        if level.get("level_type")=="TRAINING_LEVEL":
            variable=level.get("answer_variable_name")
            if not level.get("variant_answers"): errors.append(f"training level {level.get('title')}: variant_answers must be true")
            if variable:
                used.add(variable)
                if variable not in apg: errors.append(f"training.json: missing APG variable {variable!r}")
    if used!=required: errors.append(f"training.json: expected APG references {sorted(required)}, got {sorted(used)}")
    required_files=["seed-source/vpnclient.c","seed-source/vpnserver.c","seed-source/README.md","provisioning/roles/router/files/target_server.py","provisioning/roles/client/templates/lab-firewall.sh.j2","provisioning/roles/router/templates/target-site.service.j2","provisioning/roles/router/templates/target-config.json.j2","provisioning/roles/router/templates/lab-target-firewall.sh.j2","provisioning/roles/router/templates/lab-target-firewall.service.j2","scripts/test_target.py","scripts/fetch-official-seed-vpn.sh"]
    for rel in required_files:
        if not (ROOT/rel).is_file(): errors.append(f"missing required file: {rel}")
    # SEED source behavior that this topology depends on.
    cclient=(ROOT/"seed-source/vpnclient.c").read_text(encoding="utf-8")
    cserver=(ROOT/"seed-source/vpnserver.c").read_text(encoding="utf-8")
    for label,source in (("vpnclient.c",cclient),("vpnserver.c",cserver)):
        if "IFF_TUN | IFF_NO_PI" not in source: errors.append(f"{label}: expected TUN device creation code")
        if "PORT_NUMBER 55555" not in source: errors.append(f"{label}: expected SEED UDP port 55555")
    if "inet_addr(server_ip)" not in cclient: errors.append("vpnclient.c: expected server IPv4 command-line argument")
    if "recvfrom(sockfd, buff, 100" not in cserver: errors.append("vpnserver.c: expected SEED hello/peer registration")
    play_hosts={str(p.get("hosts")) for p in playbook if isinstance(p,dict)}
    for expected in ("hosts,routers","server","router","client"):
        if expected not in play_hosts: errors.append(f"playbook.yml: missing play for {expected}")
    for endpoint in ("client","server"):
        plays=[p for p in playbook if isinstance(p,dict) and p.get("hosts")==endpoint]
        if not plays: errors.append(f"playbook.yml: missing {endpoint} play"); continue
        roles=[r.get("role") if isinstance(r,dict) else r for r in plays[-1].get("roles",[])]
        if "user-access" not in roles: errors.append(f"playbook.yml: {endpoint} must receive user-access")
    fw=(ROOT/"provisioning/roles/client/templates/lab-firewall.sh.j2").read_text(encoding="utf-8")
    if "VPN_ENDPOINT_IP" not in fw or "ip -o route get" not in fw: errors.append("client firewall must derive physical interface via VPN endpoint route")
    if "-d \"${TARGET_IP}/32\"" not in fw or "-j REJECT" not in fw: errors.append("client firewall must reject direct target egress")
    router_plays=[p for p in playbook if isinstance(p,dict) and p.get("hosts")=="router"]
    if router_plays and any((r.get("role") if isinstance(r,dict) else r)=="user-access" for r in router_plays[-1].get("roles",[])): errors.append("router must not receive trainee user-access")
    joined=json.dumps(training,ensure_ascii=False)
    if re.search(r"FLAG\{[A-Za-z0-9]{6}\}",joined): errors.append("training.json appears to contain literal flags")
    # Ensure no accidental references to the superseded custom tunnel remain.
    for path in [ROOT/"README.md", ROOT/"docs/architecture.md", ROOT/"docs/student-brief.md", ROOT/"docs/instructor-guide.md"]:
        if "tunvpn" in path.read_text(encoding="utf-8"): errors.append(f"{path.relative_to(ROOT)} still references the removed custom tunvpn binary")
    if errors:
        print("Validation failed:"); [print(" - "+e) for e in errors]; return 1
    print("Validation passed:")
    print(f" - {len(hosts)} hosts and {len(routers)} router defined")
    print(f" - {len(networks)} isolated networks defined")
    print(f" - {len(apg)} per-sandbox APG flags wired to training levels")
    print(" - SEED VPN client/server source signatures and provisioning files present")
    return 0
if __name__=="__main__": raise SystemExit(main())
