#!/usr/bin/env python3
import os
import sys

import CloudFlare
import urllib.request
import functools
import logging
import yaml


class ConfigNotFound(Exception):
    pass


def load_config():
    blank_config = [
        {
            "auth": {"email": None, "token": None},
            "zone": "my_zone_id",
            "names": ["my.domain.name"],
        }
    ]
    config_dir = os.path.expandvars("$HOME/.config/cfddns")
    config_filename = "config.yaml"
    config_path = os.path.join(config_dir, config_filename)

    if not os.path.exists(config_path):
        print(f"Creating a basic config at {config_path}, please fill it out")
        os.makedirs(config_dir, exist_ok=True)

        with open(config_path, "w") as f:
            f.write(yaml.dump(blank_config))

        raise ConfigNotFound()

    with open(config_path, "r") as f:
        return yaml.safe_load(f.read())


@functools.lru_cache()
def get_public_ip():
    return urllib.request.urlopen("https://api.ipify.org/").read().decode().strip()


def handle_ddns(auth: dict, zone_id: str, names: [str]):
    cf = CloudFlare.CloudFlare(**auth)
    dns_records = cf.zones.dns_records.get(zone_id)

    if not dns_records:
        print(f"ERROR: NO DNS RECORDS FOUND FOR {zone_id}")
        return False

    public_ip = get_public_ip()

    for name in names:
        for dns_record in dns_records:
            if dns_record["name"] != name:
                continue

            print(f"Found {dns_record['type']} for {name}")
            if dns_record["type"] != "A":
                continue

            current_ip = dns_record["content"]

            if public_ip == current_ip:
                print("Record {} is already current".format(dns_record["name"]))
                break

            print(
                "Record {} is out of date (Currently {}, should be {})...".format(
                    dns_record["name"], dns_record["content"], public_ip
                )
            )
            try:
                cf.zones.dns_records.put(
                    zone_id,
                    dns_record["id"],
                    data={
                        "type": dns_record["type"],
                        "name": dns_record["name"],
                        "content": public_ip,
                    },
                )

            except Exception as e:
                logging.exception("Failed to update record")
                print(dns_record)

            else:
                print("  Updated!")

            break

    return True

def main():
    try:
        config = load_config()
    except ConfigNotFound as e:
        print(e)
        sys.exit(1)

    for zone_config in config:
        auth = zone_config["auth"]
        zone_id = zone_config["zone"]
        names = zone_config["names"]

        if not handle_ddns(auth, zone_id, names):
            print(f"Failed to update {', '.join(names)}")


if __name__ == "__main__":
    main()