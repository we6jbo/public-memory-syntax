#!/usr/bin/env python3

"""
n O'n birthday-book source-file protection utility.

Reference comment:
AP16NDDfsmD6

The program identifies files by MD5 checksum, regardless of filename.

Commands:

    moms-book-guard.py scan
    moms-book-guard.py usb /media/we6jbo/USBNAME
    moms-book-guard.py ssh user@computer:/destination/
    moms-book-guard.py finalize
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path


TARGETS = {
    "77e1f203a1b6854bc317a60e7ce659fc":
        "DONT-OPEN-UNTIL-DEC31-2026.pdf",

    "061273aa663036439e4e4c6b93af5b20":
        "DONT-OPEN-UNTIL-DEC31-2026-PRESENT.docx",

    "0d999b21d48b7a6ffa83a233232c603d":
        "Open.txt",
}


NOT_BEFORE = datetime.date(2026, 7, 26)

COMMENT = "AP16NDDfsmD6"


# Directories that will be searched for matching files.
#
# The program checks file contents by MD5, so a renamed file will still match.
#
# Add additional directories here when needed.
SEARCH_ROOTS = [
    Path("/home/we6jbo"),
    Path("/tmp"),
    Path("/var/tmp"),
    Path("/media/we6jbo"),
    Path("/mnt"),
]


# Virtual and system directories that should never be recursively scanned.
EXCLUDED_PREFIXES = (
    Path("/proc"),
    Path("/sys"),
    Path("/dev"),
    Path("/run"),
    Path("/lost+found"),
)


# The password must be the only line in this file.
KEY_FILE = Path(
    "/home/we6jbo/.temp-delete-after-aug2026/encryption-key"
)


# Encrypted archives will be stored here.
ENCRYPTED_DIRECTORY = Path(
    "/home/we6jbo/Moms-Birthday-Book-Encrypted"
)


def md5_file(path: Path) -> str | None:
    """Calculate a file's MD5 checksum."""

    digest = hashlib.md5()

    try:
        with path.open("rb") as file_handle:
            while True:
                chunk = file_handle.read(1024 * 1024)

                if not chunk:
                    break

                digest.update(chunk)

    except (PermissionError, FileNotFoundError, IsADirectoryError, OSError):
        return None

    return digest.hexdigest()


def path_is_within(path: Path, parent: Path) -> bool:
    """Return True when path is located inside parent."""

    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except (ValueError, OSError):
        return False


def is_excluded(path: Path) -> bool:
    """Determine whether a path should be excluded from scanning."""

    try:
        resolved = path.resolve()
    except OSError:
        return True

    for prefix in EXCLUDED_PREFIXES:
        if path_is_within(resolved, prefix):
            return True

    # Do not scan encrypted output files as possible source files.
    if path_is_within(resolved, ENCRYPTED_DIRECTORY):
        return True

    return False


def find_matches(
    roots: list[Path],
) -> dict[str, list[Path]]:
    """
    Search directories for files whose MD5 checksum matches a target.

    The filename does not need to match the expected filename.
    """

    matches: dict[str, list[Path]] = {
        digest: []
        for digest in TARGETS
    }

    seen_paths: set[Path] = set()

    for root in roots:
        if not root.exists():
            continue

        if not root.is_dir():
            continue

        if is_excluded(root):
            continue

        for current_directory, directory_names, filenames in os.walk(
            root,
            followlinks=False,
        ):
            current_path = Path(current_directory)

            directory_names[:] = [
                directory_name
                for directory_name in directory_names
                if not is_excluded(current_path / directory_name)
            ]

            for filename in filenames:
                path = current_path / filename

                try:
                    resolved = path.resolve()
                except OSError:
                    continue

                if resolved in seen_paths:
                    continue

                seen_paths.add(resolved)

                if path.is_symlink():
                    continue

                if not path.is_file():
                    continue

                if is_excluded(path):
                    continue

                digest = md5_file(path)

                if digest in matches:
                    matches[digest].append(path)

    for digest in matches:
        matches[digest].sort(key=lambda item: str(item))

    return matches


def print_matches(
    matches: dict[str, list[Path]],
) -> None:
    """Display discovered files."""

    total = 0

    for digest, expected_name in TARGETS.items():
        print()
        print(f"{digest}  {expected_name}")

        paths = matches[digest]

        if not paths:
            print("  No matching files found.")
            continue

        for path in paths:
            print(f"  {path}")
            total += 1

    print()
    print(f"Total matching file locations: {total}")


def ask_yes_no(question: str) -> bool:
    """Ask a yes-or-no question."""

    while True:
        try:
            answer = input(
                f"{question} [yes/no]: "
            ).strip().lower()
        except EOFError:
            return False

        if answer in {"yes", "y"}:
            return True

        if answer in {"no", "n"}:
            return False

        print("Please answer yes or no.")


def checklist_complete() -> bool:
    """Run the dated birthday-book checklist."""

    today = datetime.date.today()

    if today < NOT_BEFORE:
        print(
            "The birthday-book completion checklist cannot run before "
            f"{NOT_BEFORE.isoformat()}."
        )
        print(f"Today's date is {today.isoformat()}.")

        return False

    questions = [
        "Did you receive n O'n's birthday book?",

        "Did you check the birthday book?",

        "Did you approve the birthday book?",

        "Did you wrap the birthday book?",

        "Did you place the birthday book under the Christmas tree?",

        "Did you buy your mom the $30 Christmas gift card?",
    ]

    print()
    print("n O'n Birthday Book Completion Checklist")
    print("--------------------------------------------------")

    for question in questions:
        if not ask_yes_no(question):
            print()
            print(
                "At least one requirement is incomplete."
            )
            print(
                "The source files may still be needed to recreate the book."
            )
            print(
                "No files will be encrypted or removed."
            )

            return False

    return True


def ensure_required_programs() -> None:
    """Verify that required external programs are installed."""

    if shutil.which("openssl") is None:
        raise RuntimeError(
            "OpenSSL is not installed.\n"
            "Install it with:\n"
            "sudo apt update && sudo apt install openssl"
        )

    if shutil.which("scp") is None:
        print(
            "Warning: scp is not installed. "
            "The SSH-copy command will not work.",
            file=sys.stderr,
        )


def ensure_key_file() -> None:
    """Verify the encryption-password file and its permissions."""

    if not KEY_FILE.exists():
        raise RuntimeError(
            "The encryption-key file does not exist:\n"
            f"{KEY_FILE}\n\n"
            "Create it and place only the encryption password inside it."
        )

    if not KEY_FILE.is_file():
        raise RuntimeError(
            f"The encryption-key path is not a regular file: {KEY_FILE}"
        )

    mode = KEY_FILE.stat().st_mode & 0o777

    if mode & 0o077:
        raise RuntimeError(
            "The encryption-key file permissions are too open.\n"
            f"Current mode: {oct(mode)}\n"
            f"Run:\nchmod 600 {KEY_FILE}"
        )

    key_text = KEY_FILE.read_text(
        encoding="utf-8",
        errors="strict",
    ).strip()

    if not key_text:
        raise RuntimeError(
            f"The encryption-key file is empty: {KEY_FILE}"
        )


def make_note(
    source: Path,
    digest: str,
) -> str:
    """Create the explanatory note stored with an encrypted source file."""

    return f"""n O'n Birthday Book Source Archive

This encrypted archive contains a source file used to produce
n O'n's birthday present for December 31, 2026.

Original discovered path:
{source}

Original MD5 checksum:
{digest}

Expected source filename:
{TARGETS[digest]}

Reference comment:
{COMMENT}

Instructions for removing unencrypted copies:

1. Confirm that this encrypted archive decrypts successfully.

2. Confirm that the restored source file has this MD5 checksum:

   {digest}

3. Remove unencrypted copies from the computer, mounted USB drives,
   synchronized directories, Trash, backup directories, and remote
   computers that you own or administer.

4. Search for the file by MD5 checksum. Do not depend only on the
   filename because another copy may have been renamed.

5. Run the scan command again:

   /home/we6jbo/moms-book-guard.py scan

6. Ordinary deletion does not guarantee physical erasure from SSDs,
   filesystem snapshots, cloud storage, previously created backups,
   email systems, or devices that are not currently connected.

7. Do not remove the encryption password unless you are certain that
   the encrypted archive will never need to be opened again.
"""


def unique_output_path(
    source: Path,
    digest: str,
) -> Path:
    """Create a unique encrypted-archive path."""

    ENCRYPTED_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
        mode=0o700,
    )

    try:
        inode = source.stat().st_ino
    except OSError:
        inode = 0

    expected_name = TARGETS[digest]

    base_name = (
        f"{expected_name}."
        f"{digest[:12]}."
        f"{inode}."
        "tar.gz.enc"
    )

    candidate = ENCRYPTED_DIRECTORY / base_name
    counter = 1

    while candidate.exists():
        candidate = ENCRYPTED_DIRECTORY / (
            f"{base_name}.{counter}"
        )
        counter += 1

    return candidate


def safely_read_archive(
    archive_path: Path,
    destination: Path,
) -> None:
    """
    Extract only the expected files from a verification archive.

    This avoids unrestricted archive extraction.
    """

    allowed_names = {
        "README.txt",
        *TARGETS.values(),
    }

    with tarfile.open(archive_path, "r:gz") as archive:
        for member in archive.getmembers():
            member_name = Path(member.name).name

            if member_name not in allowed_names:
                raise RuntimeError(
                    f"Unexpected archive member: {member.name}"
                )

            if not member.isfile():
                raise RuntimeError(
                    f"Unexpected non-file archive member: {member.name}"
                )

            extracted_file = archive.extractfile(member)

            if extracted_file is None:
                raise RuntimeError(
                    f"Could not read archive member: {member.name}"
                )

            destination_path = destination / member_name

            with destination_path.open("wb") as output:
                shutil.copyfileobj(extracted_file, output)


def encrypt_and_verify(
    source: Path,
    digest: str,
) -> Path:
    """
    Copy a source file into an archive, encrypt it, and verify it.

    The source is not removed by this function.
    """

    ensure_key_file()

    output = unique_output_path(source, digest)

    with tempfile.TemporaryDirectory(
        prefix="moms-book-guard-"
    ) as temporary_directory_name:
        temporary_directory = Path(
            temporary_directory_name
        )

        payload_directory = temporary_directory / "payload"
        payload_directory.mkdir(mode=0o700)

        stored_file = payload_directory / TARGETS[digest]
        shutil.copy2(source, stored_file)

        copied_digest = md5_file(stored_file)

        if copied_digest != digest:
            raise RuntimeError(
                "The temporary source copy failed MD5 verification.\n"
                f"Expected: {digest}\n"
                f"Received: {copied_digest}"
            )

        note_file = payload_directory / "README.txt"

        note_file.write_text(
            make_note(source, digest),
            encoding="utf-8",
        )

        archive_path = temporary_directory / "archive.tar.gz"

        with tarfile.open(
            archive_path,
            "w:gz",
        ) as archive:
            archive.add(
                stored_file,
                arcname=stored_file.name,
                recursive=False,
            )

            archive.add(
                note_file,
                arcname=note_file.name,
                recursive=False,
            )

        try:
            subprocess.run(
                [
                    "openssl",
                    "enc",
                    "-aes-256-cbc",
                    "-salt",
                    "-pbkdf2",
                    "-iter",
                    "250000",
                    "-in",
                    str(archive_path),
                    "-out",
                    str(output),
                    "-pass",
                    f"file:{KEY_FILE}",
                ],
                check=True,
            )
        except subprocess.CalledProcessError as error:
            output.unlink(missing_ok=True)

            raise RuntimeError(
                f"OpenSSL encryption failed for {source}"
            ) from error

        verification_archive = (
            temporary_directory / "verification.tar.gz"
        )

        try:
            subprocess.run(
                [
                    "openssl",
                    "enc",
                    "-d",
                    "-aes-256-cbc",
                    "-pbkdf2",
                    "-iter",
                    "250000",
                    "-in",
                    str(output),
                    "-out",
                    str(verification_archive),
                    "-pass",
                    f"file:{KEY_FILE}",
                ],
                check=True,
            )
        except subprocess.CalledProcessError as error:
            output.unlink(missing_ok=True)

            raise RuntimeError(
                f"Encrypted archive verification failed for {source}"
            ) from error

        verification_directory = (
            temporary_directory / "verification"
        )

        verification_directory.mkdir(mode=0o700)

        safely_read_archive(
            verification_archive,
            verification_directory,
        )

        restored_file = (
            verification_directory / TARGETS[digest]
        )

        restored_digest = md5_file(restored_file)

        if restored_digest != digest:
            output.unlink(missing_ok=True)

            raise RuntimeError(
                "The decrypted source failed MD5 verification.\n"
                f"Source: {source}\n"
                f"Expected: {digest}\n"
                f"Received: {restored_digest}"
            )

        restored_note = (
            verification_directory / "README.txt"
        )

        if not restored_note.exists():
            output.unlink(missing_ok=True)

            raise RuntimeError(
                "The encrypted archive did not contain README.txt."
            )

        note_text = restored_note.read_text(
            encoding="utf-8",
            errors="replace",
        )

        if COMMENT not in note_text:
            output.unlink(missing_ok=True)

            raise RuntimeError(
                "The encrypted archive note did not contain "
                f"the required comment: {COMMENT}"
            )

    try:
        output.chmod(0o600)
    except OSError:
        pass

    return output


def remove_original(path: Path) -> None:
    """
    Remove the unencrypted file.

    This removes the filesystem directory entry. It does not guarantee
    physical erasure from SSD media, snapshots, backups, or remote storage.
    """

    if path.is_symlink():
        raise RuntimeError(
            f"Refusing to remove symbolic link: {path}"
        )

    if not path.is_file():
        raise RuntimeError(
            f"Source is no longer a regular file: {path}"
        )

    path.unlink()


def finalize(roots: list[Path]) -> None:
    """Run the checklist, encrypt matching files, and remove originals."""

    if not checklist_complete():
        return

    matches = find_matches(roots)

    print()
    print("Files currently matching the protected MD5 checksums:")
    print_matches(matches)

    files: list[tuple[str, Path]] = [
        (digest, path)
        for digest, paths in matches.items()
        for path in paths
    ]

    if not files:
        print("No matching unencrypted source files were found.")
        return

    print()
    print(
        "Each listed source file will be copied into an encrypted archive."
    )
    print(
        "Each archive will be decrypted and MD5-verified before its "
        "unencrypted source is removed."
    )
    print()
    print(
        "This does not remove copies from offline drives, snapshots, "
        "cloud services, email attachments, or computers that are not "
        "currently mounted and included in SEARCH_ROOTS."
    )

    if not ask_yes_no(
        "Proceed with encryption, verification, and removal?"
    ):
        print("Cancelled. No source files were changed.")
        return

    failures: list[str] = []

    for digest, path in files:
        print()
        print(f"Processing: {path}")

        try:
            current_digest = md5_file(path)

            if current_digest != digest:
                raise RuntimeError(
                    "The source file changed after the initial scan."
                )

            encrypted_path = encrypt_and_verify(
                path,
                digest,
            )

            remove_original(path)

            print(f"Encrypted archive: {encrypted_path}")
            print(f"Removed source:    {path}")

        except Exception as error:
            failure = f"{path}: {error}"
            failures.append(failure)

            print(
                f"FAILED: {failure}",
                file=sys.stderr,
            )

    print()
    print("Running post-operation MD5 scan...")

    remaining = find_matches(roots)

    print_matches(remaining)

    if failures:
        print()
        print("Some operations failed:")

        for failure in failures:
            print(f"  {failure}")

        sys.exit(1)

    if any(remaining.values()):
        print()
        print(
            "Warning: At least one matching unencrypted file still exists "
            "in the configured search directories."
        )

        sys.exit(2)

    print()
    print(
        "No matching unencrypted files remain in the configured "
        "search directories."
    )

    print(
        f"Encrypted archives are stored in: {ENCRYPTED_DIRECTORY}"
    )


def copy_to_usb(
    destination: Path,
    roots: list[Path],
) -> None:
    """Explicitly copy matching files to a mounted USB destination."""

    try:
        destination = destination.resolve()
    except OSError as error:
        raise RuntimeError(
            f"Could not resolve USB destination: {destination}"
        ) from error

    if not destination.exists():
        raise RuntimeError(
            f"USB destination does not exist: {destination}"
        )

    if not destination.is_dir():
        raise RuntimeError(
            f"USB destination is not a directory: {destination}"
        )

    if not os.access(destination, os.W_OK):
        raise RuntimeError(
            f"USB destination is not writable: {destination}"
        )

    matches = find_matches(roots)

    print_matches(matches)

    files = [
        (digest, path)
        for digest, paths in matches.items()
        for path in paths
    ]

    if not files:
        print("No matching files were found.")
        return

    if not ask_yes_no(
        f"Copy these matching files to {destination}?"
    ):
        print("Cancelled.")
        return

    destination_directory = (
        destination / "n-Birthday-Book-Sources"
    )

    destination_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    manifest_lines = [
        "n O'n Birthday Book Source Files",
        "",
        f"Reference comment: {COMMENT}",
        "",
    ]

    for digest, source in files:
        counter = 1

        while True:
            output_name = (
                f"{digest}-{counter}-{TARGETS[digest]}"
            )

            output_path = (
                destination_directory / output_name
            )

            if not output_path.exists():
                break

            counter += 1

        shutil.copy2(
            source,
            output_path,
        )

        copied_digest = md5_file(output_path)

        if copied_digest != digest:
            output_path.unlink(missing_ok=True)

            raise RuntimeError(
                f"USB copy failed MD5 verification: {source}"
            )

        manifest_lines.append(
            f"{digest}  {output_name}"
        )

        print(f"Copied: {source}")
        print(f"To:     {output_path}")

    manifest_path = (
        destination_directory / "MD5SUMS.txt"
    )

    manifest_path.write_text(
        "\n".join(manifest_lines) + "\n",
        encoding="utf-8",
    )

    print()
    print(f"Manifest written to: {manifest_path}")


def copy_to_ssh(
    remote: str,
    roots: list[Path],
) -> None:
    """Explicitly copy matching files to an SSH/SCP destination."""

    if shutil.which("scp") is None:
        raise RuntimeError(
            "scp is not installed.\n"
            "Install it with:\n"
            "sudo apt install openssh-client"
        )

    if not remote.strip():
        raise RuntimeError(
            "The SSH destination cannot be empty."
        )

    matches = find_matches(roots)

    print_matches(matches)

    paths = [
        path
        for path_list in matches.values()
        for path in path_list
    ]

    if not paths:
        print("No matching files were found.")
        return

    print()
    print(f"Remote SCP destination: {remote}")

    if not ask_yes_no(
        "Copy the matching files to this destination?"
    ):
        print("Cancelled.")
        return

    command = [
        "scp",
        "--",
        *[str(path) for path in paths],
        remote,
    ]

    subprocess.run(
        command,
        check=True,
    )

    print()
    print("SCP copy completed.")


def show_email_text() -> None:
    """Display the optional text that can be pasted into an email."""

    print(
        """n O'n Birthday Book source-file identifiers:

77e1f203a1b6854bc317a60e7ce659fc
061273aa663036439e4e4c6b93af5b20
0d999b21d48b7a6ffa83a233232c603d

Reference comment: AP16NDDfsmD6
"""
    )


def build_argument_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""

    parser = argparse.ArgumentParser(
        description=(
            "Find, copy, encrypt, and remove n O'n "
            "birthday-book source files by MD5 checksum."
        )
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    subparsers.add_parser(
        "scan",
        help="Search for matching files without changing them.",
    )

    subparsers.add_parser(
        "finalize",
        help=(
            "Run the dated checklist, encrypt matching files, "
            "verify them, and remove unencrypted originals."
        ),
    )

    usb_parser = subparsers.add_parser(
        "usb",
        help="Explicitly copy matching files to a mounted USB drive.",
    )

    usb_parser.add_argument(
        "destination",
        type=Path,
        help=(
            "Mounted USB directory, such as "
            "/media/we6jbo/MYUSB"
        ),
    )

    ssh_parser = subparsers.add_parser(
        "ssh",
        help="Explicitly copy matching files using SCP.",
    )

    ssh_parser.add_argument(
        "remote",
        help=(
            "SCP destination, such as "
            "user@computer:/home/user/archive/"
        ),
    )

    subparsers.add_parser(
        "email-text",
        help="Display the MD5 text that can be pasted into an email.",
    )

    return parser


def main() -> None:
    """Program entry point."""

    ensure_required_programs()

    parser = build_argument_parser()
    arguments = parser.parse_args()

    if arguments.command == "scan":
        matches = find_matches(SEARCH_ROOTS)
        print_matches(matches)

    elif arguments.command == "finalize":
        finalize(SEARCH_ROOTS)

    elif arguments.command == "usb":
        copy_to_usb(
            arguments.destination,
            SEARCH_ROOTS,
        )

    elif arguments.command == "ssh":
        copy_to_ssh(
            arguments.remote,
            SEARCH_ROOTS,
        )

    elif arguments.command == "email-text":
        show_email_text()


if __name__ == "__main__":
    try:
        main()

    except KeyboardInterrupt:
        print()
        print(
            "Cancelled by user.",
            file=sys.stderr,
        )
        sys.exit(130)

    except subprocess.CalledProcessError as error:
        print(
            f"External command failed with status "
            f"{error.returncode}.",
            file=sys.stderr,
        )
        sys.exit(error.returncode or 1)

    except Exception as error:
        print(
            f"Error: {error}",
            file=sys.stderr,
        )
        sys.exit(1)
