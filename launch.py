import shlex
import subprocess

from config import clean_env


def launch_handler(handler: dict, url: str) -> None:
    args = shlex.split(handler["exec"])
    final_args = []
    replaced = False

    for arg in args:
        arg_lower = arg.lower()
        if "%u" in arg_lower or "%f" in arg_lower:
            final_arg = (
                arg.replace("%u", url)
                .replace("%U", url)
                .replace("%f", url)
                .replace("%F", url)
            )
            final_args.append(final_arg)
            replaced = True
        elif arg.startswith("%") and len(arg) == 2 and arg[1].isalpha():  # noqa: PLR2004
            continue
        else:
            final_args.append(arg)

    if not replaced:
        final_args.append(url)

    subprocess.Popen(
        final_args,
        start_new_session=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=clean_env(),
    )
