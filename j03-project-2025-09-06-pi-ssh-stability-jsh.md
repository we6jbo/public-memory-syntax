# j03-project — 2025-09-06 — Pi SSH stability (j.sh / j2_fix.sh)

Symptom: LAN SSH timeouts / “22/tcp filtered”.
Cause: VPN (NordLynx 100.96.165.217) routing + no mDNS on client.
Fix: sshd ListenAddress 192.168.8.109, keys-only, UFW LAN-only; client binds -b 192.168.8.110.

Playbook:
- Collect: /tmp/moo/j.sh → chatgpt.txt (state + logs + placeholders uA/uB/uD/uW/uE)
- Compress: /tmp/moo/j2_fix.sh → chatgpt3.txt + chatgpt3_counts.txt (dedup; headers protected; one aggregated block)
- If broken: systemctl status ssh; ss -ltnp | grep :22; ip -4 addr | grep 192.168.8.; client: ssh -vv -b 192.168.8.110 pi@192.168.8.109

Prevent drift: DHCP reservation for 192.168.8.109; `sshd -t` before restarts; keep a backup config.
