from __future__ import annotations

import subprocess
from pathlib import Path

# Marker used to recognize (and safely remove) a hook written by becwright.
_HOOK_MARK = "# >>> becwright hook >>>"

_HOOK_CONTENT = f"""#!/bin/sh
{_HOOK_MARK}
# Generado por `becwright install`. No editar a mano: usá `becwright uninstall`.
exec becwright check
# <<< becwright hook <<<
"""


class NotAGitRepo(RuntimeError):
    pass


def repo_root() -> Path:
    res = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True, text=True,
    )
    if res.returncode != 0:
        raise NotAGitRepo("No estás dentro de un repositorio git.")
    return Path(res.stdout.strip())


def files_to_check(root: Path, *, all_files: bool) -> list[str]:
    if all_files:
        cmd = ["git", "ls-files"]
    else:
        cmd = ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"]
    res = subprocess.run(cmd, cwd=root, capture_output=True, text=True)
    return [line for line in res.stdout.splitlines() if line.strip()]


def _hook_path(root: Path) -> Path:
    return root / ".git" / "hooks" / "pre-commit"


def install_hook(root: Path) -> tuple[bool, str]:
    hook = _hook_path(root)
    if hook.exists():
        content = hook.read_text(encoding="utf-8")
        if _HOOK_MARK in content:
            return False, "El hook de becwright ya estaba instalado."
        # Never clobber a pre-commit hook we did not write.
        return False, (
            f"Ya existe un pre-commit que no es de becwright en {hook}. "
            "No lo toco; quitalo o intégralo a mano."
        )
    hook.parent.mkdir(parents=True, exist_ok=True)
    hook.write_text(_HOOK_CONTENT, encoding="utf-8")
    hook.chmod(0o755)
    return True, f"Hook instalado en {hook}."


def uninstall_hook(root: Path) -> tuple[bool, str]:
    hook = _hook_path(root)
    if not hook.exists():
        return False, "No hay hook pre-commit que quitar."
    if _HOOK_MARK not in hook.read_text(encoding="utf-8"):
        return False, "El pre-commit existente no es de becwright; no lo toco."
    hook.unlink()
    return True, "Hook de becwright desinstalado."
