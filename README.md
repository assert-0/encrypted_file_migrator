# Encrypted file migrator

This script is a wrapper around tools like `tar`, `zstd` and `openssl`
to compress and encrypt files.

Its main purpose is to compress and encrypt system backups directly to a
removable drive before restoring them on a new system.

## Requirements

- `Python 3.6+`
- `tar`
- `zstd`
- `openssl`
- `pv` (progress bar)

## Usage

To list the available options, run:
```bash
encrypted_file_migrator -h
```

Example backup usage:
```bash
encrypted_file_migrator backup \
    --manifest-path "./manifest" \
    --exclude-manifest-path "./exclude_manifest" \
    --destination-path "/mnt/removable/out.tar.zst.crypt"
``` 
When prompted, enter the password to encrypt the file.

Example restore usage:
```bash
encrypted_file_migrator restore \
--source-backup-path "/mnt/removable/out.tar.zst.crypt"
```

Like before, when prompted, enter the password to decrypt the file.

Examples for the manifest and exclude manifest files can be found in the
`test_files` directory. They are fed directly to the `tar` command.

## Installation

To install the script, run:
```bash
pip install .
```
