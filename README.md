# AUDIT-ANSSI

A remote Linux security compliance auditing tool that checks whether a target system follows the [ANSSI](https://www.ssi.gouv.fr/) (French National Cybersecurity Agency) hardening recommendations.

The tool connects to a remote host over SSH and runs 142 shell commands that validate kernel configuration, network settings, file system permissions, boot security, and more — each mapped to a specific ANSSI rule ID.

---

## Requirements

- Python 3.8+
- A reachable Linux target with SSH enabled
- The audit user must have `sudo` access on the target

Install Python dependencies:

```bash
pip install -r requirements.txt
```

| Package | Purpose |
|---------|---------|
| `paramiko` | SSH connection and command execution |
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
          "password": "ubuntu"
        }
      ],
      "numberOfCommands": "142",
      "commands": [ ... ]
    }
  ]
}
```

| Field | Description |
|-------|-------------|
| `hostname` | IP address or hostname of the target machine |
| `username` | SSH username (must have sudo rights) |
| `password` | SSH password — stored here only for reference; the CLI prompts for it securely at runtime |
| `numberOfCommands` | Total number of audit commands (must match the length of `commands`) |

> **Security note**: Avoid committing real credentials into version control. The password in the config file is used only when passing `--json` mode; the default interactive mode prompts securely via `getpass`.

---

## Usage

```bash
python tester-ssh.py <username>
```

The password is prompted securely (not shown, not saved in shell history).

**Options:**

| Argument | Description |
|----------|-------------|
| `username` | SSH username for the target host |
| `--password PASSWORD` | Pass the password directly (for scripted/automated runs only) |

**Examples:**

```bash
# Interactive — password prompted securely
python tester-ssh.py ubuntu

# Automated (CI/pipeline use)
python tester-ssh.py ubuntu --password "$SSH_PASS"
```

---

## Output

Results are printed as a markdown table to stdout and as colored log lines to the terminal.

Each audit check reports either:

- `OK` — the system output matches the expected ANSSI rule value
- `KO` — the check failed (system is not compliant)

Example output:

```
# Resultats AUDIT ANSSI
Time: 2026-04-27 14:32:01

 recommended kernel configuration : configuration uefi recommandées | ANSII R1 | OK
 SecureBoot enabled                                                  | ANSII R2 | KO
 ...
```

---

## ANSSI Rules Covered

The 142 checks span the following ANSSI white paper sections:

| Domain | Rules |
|--------|-------|
| Boot & firmware (UEFI/BIOS, Secure Boot) | R1 – R5 |
| Kernel boot parameters | R7+ |
| Kernel sysctl hardening | R9+ |
| Network (IPv4 / IPv6) | R12 – R13 |
| File system protections | R14+ |
| Memory protection (ASLR, exec-shield) | R15+ |
| Kernel module signature verification | R18+ |
| Security primitives (AppArmor, SELinux…) | R20+ |
| Architecture hardening (ARM, x86_64) | R24 – R27 |
| File ownership & permissions | R53 – R54 |
| Setuid / setgid restrictions | R56 |
| Package management & integrity | R58 – R59 |
| System update status | R61 |
| Service hardening | R62 – R63 |

---

## Project Structure

```
AUDIT-ANSSI/
├── tester-ssh.py              # Main entry point
├── configDevice.json          # SSH target + 142 ANSSI audit rules
├── log_conf.ini               # Logging configuration
├── requirements.txt
├── Colorer/
│   └── colorer.py             # Cross-platform colored log output
├── configuration/
│   └── readConfiguration.py   # JSON config parser
├── connectivity/
│   └── device.py              # SSH session & command execution
└── database/
    └── database.py            # PostgreSQL / MongoDB connectors (optional)
```

---

## License

MIT — see [LICENSE](LICENSE).
