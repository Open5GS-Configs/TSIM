from pathlib import Path
import re

CONFIG_DIR = Path("/root/open5gs/install/etc/open5gs")

NEW_LOG_DIR = "/root/open5gs/install/var/log/open5gs"
NEW_FREE_DIAMETER_DIR = "/root/open5gs/install/etc/freeDiameter"
NEW_TLS_DIR = "/root/open5gs/install/etc/open5gs/tls"
NEW_HNET_DIR = "/root/open5gs/install/etc/open5gs/hnet"

for yaml_file in CONFIG_DIR.glob("*.yaml"):
    try:
        content = yaml_file.read_text()

        updated_content = re.sub(
            r'(^\s*path:\s*).*/([^/\s]+)$',
            rf'\1{NEW_LOG_DIR}/\2',
            content,
            flags=re.MULTILINE,
        )

        updated_content = re.sub(
            r'(^\s*freeDiameter:\s*).*/([^/\s]+)$',
            rf'\1{NEW_FREE_DIAMETER_DIR}/\2',
            updated_content,
            flags=re.MULTILINE,
        )

        updated_content = re.sub(
            r'(^\s*private_key:\s*).*/([^/\s]+)$',
            rf'\1{NEW_TLS_DIR}/\2',
            updated_content,
            flags=re.MULTILINE,
        )
        
        updated_content = re.sub(
            r'(^\s*cert:\s*).*/([^/\s]+)$',
            rf'\1{NEW_TLS_DIR}/\2',
            updated_content,
            flags=re.MULTILINE,
        )

        updated_content = re.sub(
            r'(^\s*verify_client_cacert:\s*).*/([^/\s]+)$',
            rf'\1{NEW_TLS_DIR}/\2',
            updated_content,
            flags=re.MULTILINE,
        )

        updated_content = re.sub(
            r'(^\s*cacert:\s*).*/([^/\s]+)$',
            rf'\1{NEW_TLS_DIR}/\2',
            updated_content,
            flags=re.MULTILINE,
        )

        updated_content = re.sub(
            r'(^\s*client_private_key:\s*).*/([^/\s]+)$',
            rf'\1{NEW_TLS_DIR}/\2',
            updated_content,
            flags=re.MULTILINE,
        )

        updated_content = re.sub(
            r'(^\s*client_cert:\s*).*/([^/\s]+)$',
            rf'\1{NEW_TLS_DIR}/\2',
            updated_content,
            flags=re.MULTILINE,
        )

        updated_content = re.sub(
            r'(^\s*key:\s*).*/([^/\s]+)$',
            rf'\1{NEW_HNET_DIR}/\2',
            updated_content,
            flags=re.MULTILINE,
        )

        if updated_content != content:
            yaml_file.write_text(updated_content)
            print(f"Updated: {yaml_file.name}")
        else:
            print(f"No changes: {yaml_file.name}")

    except Exception as e:
        print(f"Error processing {yaml_file.name}: {e}")

print("\nDone!")