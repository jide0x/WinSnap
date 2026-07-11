from __future__ import annotations

from typing import Dict, Any
from winsnap.collectors.powershell import run_powershell_json


def verify_signature(path: str) -> Dict[str, Any]:
    """
    Verify Authenticode signature via PowerShell. Returns a normalized dict.
    """
    ps = (
        f"$sig = Get-AuthenticodeSignature -FilePath \"{path}\" -ErrorAction SilentlyContinue; "
        "if ($null -eq $sig) { $obj = [pscustomobject]@{ Status=$null; StatusMessage='Unavailable'; SignerCertificate=$null } } else { $obj = $sig } ; "
        "$out = [pscustomobject]@{ Status=$obj.Status; StatusMessage=$obj.StatusMessage; "
        " Publisher= if ($obj.SignerCertificate) { $obj.SignerCertificate.GetNameInfo('SimpleName', $false) } else { $null }; "
        " Subject= if ($obj.SignerCertificate) { $obj.SignerCertificate.Subject } else { $null }; "
        " Issuer= if ($obj.SignerCertificate) { $obj.SignerCertificate.Issuer } else { $null }; "
        " Thumbprint= if ($obj.SignerCertificate) { $obj.SignerCertificate.Thumbprint } else { $null }; "
        " Timestamped= $false } ; $out | ConvertTo-Json -Depth 4"
    )
    try:
        data = run_powershell_json(ps, timeout_seconds=15)
    except Exception as e:
        return {"status": "error", "error": str(e)}

    # Map Status to normalized status
    raw_status = (data.get("Status") or "").lower()
    status_map = {
        "valid": "verified",
        "notsigned": "unsigned",
        "hashmismatch": "invalid",
        "nottrusted": "untrusted",
        "": "unavailable",
    }
    status = status_map.get(raw_status, raw_status or "unavailable")

    return {
        "status": status,
        "publisher": data.get("Publisher"),
        "subject": data.get("Subject"),
        "issuer": data.get("Issuer"),
        "thumbprint": data.get("Thumbprint"),
        "timestamped": bool(data.get("Timestamped")),
        "error": None if status != "error" else data.get("StatusMessage"),
    }
