"""Manual smoke test for the optional C++ extension.

Build in cpp/build or set POLARIS_CPP_BUILD_DIR to the extension directory.
"""

import os
from pathlib import Path
import sys


def extension_build_dir() -> Path:
    configured = os.environ.get("POLARIS_CPP_BUILD_DIR")
    if configured:
        return Path(configured).expanduser().resolve()
    return Path(__file__).resolve().parents[1] / "build"


def main() -> int:
    build_dir = extension_build_dir()
    if not build_dir.is_dir():
        raise SystemExit(
            f"C++ build directory not found: {build_dir}. "
            "Build with CMake or set POLARIS_CPP_BUILD_DIR."
        )

    sys.path.insert(0, str(build_dir))
    try:
        import my_module as mm
    except ModuleNotFoundError as exc:
        if exc.name == "my_module":
            raise SystemExit(
                f"my_module was not found in {build_dir}. "
                "Build the extension or set POLARIS_CPP_BUILD_DIR."
            ) from exc
        raise
    import streampu as spu

    bits = [0.0, 1.0, 0.0, 1.0]
    n = len(bits)
    modem = mm.Modem(n, mm.CanalType.BSC, 0.2)
    bits_in = spu.array([bits], dtype=spu.float64)
    bits_out = modem.modulate_BPSK(bits_in)
    print("Modulated:", bits_out)
    print("LLRs:", modem.demodulate_BPSK(bits_out))

    canal_bsc = mm.Canal(n, mm.CanalType.BSC, param_canal=0.0,
                         param_bob=0.1, param_eve=0.4)
    bob, eve = canal_bsc.canal(bits_out)
    print("Bob:", bob)
    print("Eve:", eve)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
