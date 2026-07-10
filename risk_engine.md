# WinSnap Risk Engine Design

## Purpose

The WinSnap risk engine is designed to help users understand which system changes may deserve closer review.

WinSnap should not declare that something is malicious. Instead, it should surface risk indicators, explain why they matter, and provide context so the user can investigate.

Core principle:

> WinSnap explains why a change is interesting, not whether it is definitively malicious.

---

## Current Scope

Current collectors:

* Processes
* Services
* Scheduled tasks
* Registry autoruns
* Startup folders
* Network listeners

Risk hints are currently archived pending filtering/noise-reduction work. The previous lightweight hint prototype is preserved in `archive/risk_hints.py` for future reuse.

Archived service risk hints:

* Auto-start service
* Runs as LocalSystem
* Path in user-writable location
* Missing/unknown PathName

Archived scheduled task risk hints:

* Enabled scheduled task
* Runs as SYSTEM
* Runs at logon
* Runs at startup
* Executes command or scripting host
* Action path in user-writable location

Archived registry autorun risk hints:

* Run key persistence location
* RunOnce persistence location
* Machine-wide autorun
* Executes command or scripting host
* Autorun path in user-writable location
* Missing/empty autorun command

These hints do not currently appear in active CLI output.

---

## Future Risk Model

WinSnap should eventually support a weighted scoring model.

Suggested internal scoring:

|  Score | Rating        |
| -----: | ------------- |
|   0–19 | Informational |
|  20–39 | Low           |
|  40–59 | Medium        |
|  60–79 | High          |
| 80–100 | Critical      |

The score should be used internally to prioritize findings. The user-facing output should emphasize the reasons behind the score.

---

## Process Risk Indicators

| Indicator                            | Suggested Weight | Why It Matters                                                   |
| ------------------------------------ | ---------------: | ---------------------------------------------------------------- |
| New executable observed              |                5 | Something new executed between snapshots.                        |
| Executable from Temp                 |               25 | Temp directories are commonly used for dropped payloads.         |
| Executable from AppData              |               15 | AppData is commonly abused for user-level persistence.           |
| Executable from Downloads            |               10 | May indicate user-downloaded or recently introduced software.    |
| Unsigned executable                  |               20 | Unsigned binaries may be less trustworthy, depending on context. |
| Running as SYSTEM                    |               15 | The process has high local privileges.                           |
| Suspicious parent-child relationship |               20 | Some parent-child chains are commonly associated with abuse.     |
| LOLBin execution                     |               20 | Built-in Windows tools are often abused by attackers.            |
| Encoded PowerShell command           |               30 | Encoded commands are commonly used to hide intent.               |
| Base64-like command argument         |               30 | May indicate obfuscation or encoded payloads.                    |
| Process count spike                  |               10 | Large process creation changes may indicate unusual activity.    |

---

## Service Risk Indicators

| Indicator                      | Suggested Weight | Why It Matters                                                 |
| ------------------------------ | ---------------: | -------------------------------------------------------------- |
| New service                    |               20 | Services are commonly used for persistence.                    |
| Auto-start service             |               10 | The service can run automatically after reboot.                |
| Delayed auto-start service     |                5 | Still persistent, but less immediately active.                 |
| Runs as LocalSystem            |               10 | LocalSystem is a highly privileged account.                    |
| Binary path changed            |               25 | The service may now execute a different binary.                |
| Start mode changed             |               15 | A manual service becoming automatic may indicate persistence.  |
| Service account changed        |               25 | A privilege change may alter security impact.                  |
| Path in user-writable location |               30 | Services should rarely execute from user-writable directories. |
| Missing or unknown PathName    |               15 | Could indicate a broken, hidden, or partially removed service. |
| Unsigned service binary        |               20 | Unsigned binaries deserve additional review.                   |
| Critical service disabled      |               30 | Could indicate defense evasion or system weakening.            |

---

## Scheduled Task Risk Indicators

| Indicator           | Suggested Weight | Why It Matters                                                  |
| ------------------- | ---------------: | --------------------------------------------------------------- |
| New scheduled task  |               20 | Scheduled tasks are commonly used for persistence.              |
| Runs at logon       |               15 | Executes when a user signs in.                                  |
| Runs at startup     |               20 | Executes when the system boots.                                 |
| Hidden task         |               20 | Hidden tasks may be used to reduce visibility.                  |
| Runs as SYSTEM      |               20 | Runs with elevated local privileges.                            |
| Executes PowerShell |               15 | PowerShell is frequently abused.                                |
| Executes cmd.exe    |               10 | Command shell execution may be suspicious depending on context. |
| Executes LOLBin     |               20 | Built-in Windows tools may be abused for execution.             |

---

## Registry Risk Indicators

| Indicator             | Suggested Weight | Why It Matters                                          |
| --------------------- | ---------------: | ------------------------------------------------------- |
| New Run key value     |               20 | Common user-level persistence location.                 |
| New RunOnce value     |               15 | Executes once at logon.                                 |
| Winlogon key modified |               40 | High-value persistence and logon behavior location.     |
| Shell value modified  |               35 | May alter user shell startup behavior.                  |
| IFEO modified         |               35 | Can be used for process hijacking or debugging abuse.   |
| Image hijack behavior |               40 | May redirect execution to attacker-controlled binaries. |

---

## Startup Folder Risk Indicators

Startup folder collection is implemented. Risk indicators remain archived until filtering/noise reduction is added.

| Indicator              | Suggested Weight | Why It Matters                                     |
| ---------------------- | ---------------: | -------------------------------------------------- |
| New startup executable |               20 | Runs when the user logs in.                        |
| New startup script     |               15 | Scripts may be used for persistence or automation. |
| Hidden startup file    |               15 | Hidden files may indicate attempted concealment.   |

---

## Driver Risk Indicators

Future collector.

| Indicator           | Suggested Weight | Why It Matters                                                    |
| ------------------- | ---------------: | ----------------------------------------------------------------- |
| New driver          |               30 | Drivers run at a sensitive system level.                          |
| Unsigned driver     |               40 | Unsigned drivers are highly suspicious on modern Windows systems. |
| Boot-start driver   |               40 | Loads early in the boot process.                                  |
| Driver path changed |               35 | May indicate tampering or replacement.                            |

---

## Filesystem Risk Indicators

Future collector.

| Indicator                      | Suggested Weight | Why It Matters                                       |
| ------------------------------ | ---------------: | ---------------------------------------------------- |
| New executable file            |               15 | A new runnable file appeared.                        |
| New DLL file                   |               10 | DLLs may be loaded by other processes.               |
| File created in Temp           |               15 | Temp is commonly used for staging.                   |
| File created in AppData        |               15 | AppData is commonly used for user-level persistence. |
| Hosts file modified            |               30 | Can redirect network traffic.                        |
| System directory file modified |               35 | Could indicate tampering with system components.     |

---

## Network Risk Indicators

Network listener collection is implemented. Risk indicators remain archived until filtering/noise reduction is added.

| Indicator                         | Suggested Weight | Why It Matters                                         |
| --------------------------------- | ---------------: | ------------------------------------------------------ |
| New listening port                |               25 | May indicate a new local server, backdoor, or service. |
| Firewall rule added               |               20 | May allow new inbound or outbound communication.       |
| RDP enabled                       |               30 | Remote access exposure increased.                      |
| New persistent network connection |               20 | May indicate background communication.                 |

---

## Scoring Philosophy

Risk should be based on combinations, not isolated facts.

Example:

A new service alone may be low-to-medium interest.

A new service that:

* starts automatically,
* runs as LocalSystem,
* points to AppData,
* and uses an unsigned binary

should be treated as high or critical priority.

Example calculation:

| Factor                         | Weight |
| ------------------------------ | -----: |
| New service                    |     20 |
| Auto-start                     |     10 |
| Runs as LocalSystem            |     10 |
| Path in user-writable location |     30 |
| Unsigned binary                |     20 |
| Total                          |     90 |

Result:

```text
Risk: Critical
```

---

## User-Facing Output

The risk engine should explain evidence clearly.

Example:

```text
Risk Summary
  Rating: High
  Score: 78

Contributing Factors
  ! New auto-start service
  ! Runs as LocalSystem
  ! Binary path is in a user-writable location

Explanation
  This service is configured to start automatically, runs with high privileges, and executes from a user-writable directory. Legitimate software can sometimes match one of these indicators, but this combination deserves investigation.
```

---

## Design Rules

1. Do not claim something is malware.
2. Prefer “risk indicator” over “malicious.”
3. Explain why the change matters.
4. Keep default output clean.
5. Put detailed indicators in `--details`.
6. Allow future suppression or allowlisting.
7. Make scoring transparent.
8. Treat combinations as more important than single indicators.

---

## Implementation Plan

Do not implement the full risk engine yet.

Recommended order:

1. Continue collecting core Windows artifacts.
2. Add filtering to reduce noisy baseline entries.
3. Reintroduce lightweight risk hints where filtering gives them enough signal.
4. Document each reintroduced hint in this file.
5. After processes, services, scheduled tasks, registry autoruns, startup folders, and network collectors exist, build the scoring engine.
6. Add AI summaries only after the deterministic risk engine is useful on its own.

---

## Current Status

Archived hints:

* Auto-start service
* Runs as LocalSystem
* Path in user-writable location
* Missing/unknown PathName
* Scheduled task hints
* Registry autorun hints

Not yet implemented:

* Filtering/noise reduction
* Numeric scoring
* Global risk summary
* Risk ranking
* Allowlisting
* AI explanation
