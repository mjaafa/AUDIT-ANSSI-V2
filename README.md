# AUDIT-ANSSI

A remote Linux security compliance auditing tool that checks whether a target system follows the [ANSSI](https://cyber.gouv.fr/) (French National Cybersecurity Agency) hardening guide [*Configuration recommendations of a GNU/Linux system* (ANSSI-BP-028 v2.0)](https://messervices.cyber.gouv.fr/documents-guides/linux_configuration-en-v2.pdf).

The tool connects to a remote host over SSH and runs 228 checks covering **all 80 recommendations (R1 – R80)** of the guide: boot chain, kernel command line and sysctl options, kernel build options, partitioning, accounts, sudo, MAC (AppArmor / SELinux), file permissions, packages, services, PAM, logging / auditd, integrity and network exposure. Each check is mapped to its ANSSI rule ID. After the audit, it generates a timestamped Markdown file and a color-coded PDF report.

---

## Requirements

- Python 3.8+
- A reachable Linux target with SSH enabled
- The audit user must have `sudo` access on the target
- On the target: `bash` and the usual GNU tools (`sed -E`, `sort -V`, `awk`, `find`, `stat`), plus `ss` (iproute2) or `netstat` (net-tools) for the network checks, `systemctl`, `auditctl`, `mokutil` when available. A missing tool makes the related check report it (for example `no socket tool available (ss or netstat)`) rather than pass.

Install Python dependencies:

```bash
pip install -r requirements.txt
```

| Package | Purpose |
|---------|---------|
| `paramiko` | SSH connection and command execution |
| `fpdf2` | PDF report generation |
| `psycopg2-binary` | PostgreSQL storage *(optional, unused by default)* |
| `pymongo` | MongoDB storage *(optional, unused by default)* |

---

## Configuration

Edit `configDevice.json` before running an audit.

```json
{
  "device": [
    {
      "configuration": [
        {
          "hostname": "192.168.1.3",
          "username": "ubuntu",
          "password": "ubuntu",
          "port": "22",
          "key_filename": "~/.ssh/id_ed25519",
          "certificate": "~/.ssh/id_ed25519-cert.pub"
        }
      ],
      "numberOfCommands": "228",
      "commands": [ ... ]
    }
  ]
}
```

| Field | Description |
|-------|-------------|
| `hostname` | IP address or hostname of the target machine (the only way to choose the target) |
| `username` | SSH username (must have sudo rights) |
| `password` | SSH password — stored here only for reference; the CLI prompts for it securely at runtime |
| `port` | SSH port *(optional, default `22`)* |
| `key_filename` | Private key for public-key authentication *(optional; when set, no password is prompted)* |
| `certificate` | OpenSSH certificate (`*-cert.pub`) signed for `key_filename` *(optional)* |
| `numberOfCommands` | Total number of audit commands (must match the length of `commands`) |

> **Security note**: Avoid committing real credentials into version control. The password in the config file is used only when passing `--json` mode; the default interactive mode prompts securely via `getpass`.

### Check format

Each entry of `commands` is one check:

```json
{
    "command":"sysctl kernel.sysrq",
    "Name":"kernel.sysrq",
    "Description": " recommended kernel configuration : configuration du noyau recommandées | ANSII R9.8 |",
    "rule":"kernel.sysrq = 0",
    "dialog":"No",
    "Store":"info"
}
```

| Field | Description |
|-------|-------------|
| `command` | Shell command run as root on the target (`sudo bash -c`) |
| `Name` | Short name shown in the report |
| `Description` | `<section> : <recommendation title> \| ANSII <rule id> \|` — the section groups the report, the rule id is shown in the *Rule* column |
| `rule` | Expected output: the check is **OK** when the command prints exactly this text |
| `dialog` | `Yes` for a recommendation decided by the auditor (see [Manual recommendations](#manual-recommendations)) |

A command prints `not applicable` when the check does not apply to the target (other CPU architecture, kernel option removed from recent kernels, SELinux check on an AppArmor system…).

---

## Usage

```bash
python tester-ssh.py <username> [--port PORT] [--key KEY [--cert CERT]] [--sudo-password PWD] [--non-interactive] [--answers FILE] [--out OUTPUT_DIR]
```

The password is prompted securely (not shown, not saved in shell history). When a key is given (`--key` or `key_filename` in `configDevice.json`), public-key authentication is used instead and no password is asked; the key passphrase is prompted only if the key is encrypted, then the sudo password is asked (leave it empty for `NOPASSWD`).

**Options:**

| Argument | Description |
|----------|-------------|
| `username` | SSH username for the target host |
| `--password PASSWORD` | Pass the password directly (for scripted/automated runs only) |
| `--port PORT` | SSH port (default: `port` in `configDevice.json`, else `22`) |
| `--key KEY` | Private key file for public-key auth (default: `key_filename` in `configDevice.json`) |
| `--cert CERT` | OpenSSH certificate signed for that key, e.g. `~/.ssh/id_ed25519-cert.pub` (default: `certificate` in `configDevice.json`) |
| `--sudo-password PWD` | sudo password on the target (default: the SSH password; prompted when using a key) |
| `--non-interactive` | Do not ask the auditor; manual recommendations reuse the answers of `--answers` when their evidence is unchanged, else they are reported as `MANUAL` |
| `--answers FILE` | File keeping the auditor answers and the evidence they were based on (default: `answers.json`) |
| `--out DIR` | Directory where reports are saved (default: `reports/`) |

**Examples:**

```bash
# Interactive — password prompted securely, manual recommendations asked to the auditor
python tester-ssh.py ubuntu

# Public key + OpenSSH certificate (servers allowing only publickey)
python tester-ssh.py admin --port 2222 --key ~/.ssh/id_ed25519 --cert ~/.ssh/id_ed25519-cert.pub

# Custom output directory
python tester-ssh.py ubuntu --out /tmp/audit-results

# Automated (CI/pipeline use): no prompt, manual recommendations taken from answers.json
python tester-ssh.py ubuntu --password "$SSH_PASS" --non-interactive --out /tmp/audit-results
```

When the standard input is not a terminal (pipeline, cron), the manual recommendations are not asked, as with `--non-interactive`.

---

## Manual recommendations

Most recommendations that need judgement are checked automatically with a strict rule:

| Rec. | Automatic rule |
|------|----------------|
| R36.2 | every running service (login sessions excluded) has a `UMask` of 0027 or stricter; exceptions can be listed in the `allow=""` variable of the command |
| R41 | no sudo rule uses `EXEC:` and no `Defaults` line disables `noexec` |
| R43 | no sudo rule contains `*` or allows `ALL` commands |
| R52 | no socket or named pipe directly in `/tmp`, `/var/tmp` or `/dev/shm` |
| R66 / R70 | `N/A` when no container/virtualisation component, or no directory bind account, is present |

13 recommendations remain a decision of the auditor because they depend on the purpose of the system (R1, R30, R40, R51, R58, R60, R63, R64, R66, R70, R72, R78, R79). Their command collects **evidence** on the target (accounts with a shell, sudo rules, SSH host key fingerprints, services running as root, listening services, installed packages…) and the tool asks the auditor:

```
==============================================================================
ANSII R51 - Default secrets changed
recommended files and directories : Changer les secrets et droits d'accès dès l'installation
------------------------------------------------------------------------------
SSH host keys (a key shared by every device built from the same image must be regenerated):
  256 SHA256:52hG... root@device (ED25519) created 2026-07-03 10:28:28
machine-id: 3f1c...
------------------------------------------------------------------------------
Compliant? [o]k / [k]o / [n]ot applicable / [s]kip: k
Comment (optional): host keys baked in the image
```

The answer becomes the status of the check (`OK`, `KO`, `N/A`, or `MANUAL` when skipped) and the comment is added to its description in the reports. No `expect` script is needed: the remote side is driven by paramiko and the answers are read from the auditor's terminal.

### Reusing the answers (non-interactive audits)

Each answer is saved in `answers.json` (option `--answers`) with the evidence it was based on and its SHA-256 fingerprint. The evidence commands are written to give the same output from one run to the next (sorted, no PID, size, date or ephemeral port), so:

- a **non-interactive** run reuses the saved status when the evidence is unchanged (comment `reviewed <date>: <comment>`), and reports `MANUAL` with `evidence changed since review of <date>` otherwise;
- an **interactive** run shows the previous answer: *Enter* keeps it when the evidence is unchanged; when it changed, the difference is displayed before asking again.

Devices built from the same image give the same evidence, so one interactive review of the image covers the whole fleet, and any later drift (new account, sudo rule, package, listening port…) is flagged.

> The answers file contains evidence from the target (account names, host key fingerprints, listening services): keep it with the audit reports, not in a public repository.

---

## Output

### Terminal

Live results are printed as colored log lines during the audit. Each check reports:

- `OK` — the system output matches the expected ANSSI value
- `KO` — the check failed (system is not compliant); the command output says why, e.g. `kernel.sysrq = 176` or `kernel.dmesg_restrict = 1 (not set in sysctl config or kernel cmdline)`
- `N/A` — the check does not apply to this target
- `MANUAL` — a recommendation left to the auditor (skipped, or `--non-interactive` with no valid saved answer)

### Generated reports

After the audit completes, two files are written to the output directory:

```
reports/
├── audit_20260427_143201.md   ← Markdown tables, one per section
└── audit_20260427_143201.pdf  ← Styled PDF with summary and color-coded results
```

The file names are timestamped so successive audits never overwrite each other.

**Markdown report** — one table per section:

```markdown
# AUDIT ANSSI - Security Compliance Report

**Date:** 2026-04-27 14:32:01
**Host:** 192.168.1.3
**Total:** 228 | **Passed:** 124 | **Failed:** 70 | **N/A:** 21 | **Manual:** 13

## recommended kernel configuration

| # | Rule | Test | Description | Status |
|---|------|------|-------------|--------|
| 1 | ANSII R1 | Hardware configuration (x86 hardware note) | Choisir et configurer son matériel | MANUAL |
| 2 | ANSII R2 | UEFI boot mode | Configurer le BIOS/UEFI | OK |
...
```

**PDF report** — same data in a printable format:
- Header with host and generation timestamp
- Summary line (total / passed / failed / not applicable / manual)
- Color-coded table: green for OK, red for KO, grey for N/A, orange for MANUAL

---

## ANSSI Rules Covered

| Section in the report | Rules |
|--------|-------|
| Kernel configuration — hardware, UEFI, Secure Boot, bootloader | R1 – R7 |
| Kernel configuration — boot command line memory options | R8 |
| Kernel configuration — sysctl (kernel, Yama, IPv4, IPv6, file systems) | R9 – R14 |
| Kernel configuration — kernel build options (memory, modules, LSM, compiler plugins, IP stack, architectures) | R15 – R27 |
| Disk partitioning | R28 – R29 |
| Users and accounts | R30 – R36 |
| Access control (MAC, sudo, AppArmor, SELinux) | R37 – R49 |
| Files and directories | R50 – R57 |
| Package management | R58 – R61 |
| Services | R62 – R66 |
| Authentication (PAM, password storage, NSS) | R67 – R70 |
| Logging and integrity (syslog, auditd, mail, sealing) | R71 – R77 |
| Network services | R78 – R80 |

### How some checks are evaluated

- **sysctl (R9)** — the running value must be compliant **and** persistent: set in the sysctl configuration (`systemd-analyze cat-config sysctl.d`, or the `sysctl.d` folders) or as `sysctl.<key>=` on the kernel command line. `kernel.pid_max` only has to be set explicitly (65536 is an example value in the guide). Stricter values are accepted where the guide allows it (`perf_event_paranoid >= 2`, `yama.ptrace_scope >= 1`).
- **Kernel build options (R15 – R27)** — read from `/boot/config-$(uname -r)` or `/proc/config.gz`. Options removed from recent kernels are `N/A` (e.g. `CONFIG_REFCOUNT_FULL` from 5.5), renamed ones accept both names (`CONFIG_MITIGATION_RETPOLINE`), and R24 – R27 only run on their architecture. `CONFIG_MODULES` is checked either by R18 (modules enabled) or by R23.5 (modules disabled).
- **Integrity (R76 – R77)** — a dm-verity protected root file system is accepted, as well as AIDE / Tripwire.
- **setuid / setgid (R56 – R57)** — R56 lists the files that do not belong to a package (dpkg, rpm or opkg); R57 lists the setuid root / setgid root executables other than `su`, `sudo`, `passwd` and `unix_chkpwd`, to be reviewed by the auditor.
- **Read-only images** — on a read-only root file system (squashfs), every fix must be applied to the image itself (e.g. `/usr/lib/sysctl.d/99-anssi.conf`) or on the kernel command line.

---

## Project Structure

```
AUDIT-ANSSI/
├── tester-ssh.py              # Main entry point
├── configDevice.json          # SSH target + 228 ANSSI audit checks
├── log_conf.ini               # Logging configuration
├── requirements.txt
├── Colorer/
│   └── colorer.py             # Cross-platform colored log output
├── configuration/
│   └── readConfiguration.py   # JSON config parser
├── connectivity/
│   └── device.py              # SSH session, command execution and auditor prompts
├── report/
│   └── report.py              # Markdown and PDF report generation
└── database/
    └── database.py            # PostgreSQL / MongoDB connectors (optional)
```

---

## License

MIT — see [LICENSE](LICENSE).
