from datetime import datetime
import json
from pathlib import Path
from xml.etree.ElementTree import Element, ElementTree, SubElement


COMPONENTS_REPO_PATH = Path(r"C:\Users\matthew\Desktop\components-main")
RETRODECK_VERSION = "v0.10.6b"
COMPONENTS_VERSION = "20260301-0950"
DAT_VERSION_NUMBER = f"{RETRODECK_VERSION} ({COMPONENTS_VERSION})"
KNOWN_BIOS_KEYS = ("filename", "md5", "sha256", "system", "description", "required", "paths")


def create_starter_xml_tree():
    root = Element("datafile")
    header = SubElement(root, "header")

    name = SubElement(header, "name")
    name.text = "RetroDECK BIOS"
    description = SubElement(header, "description")
    description.text = "Custom DAT with MD5 hashes of files in RetroDECK BIOS Checker"
    version = SubElement(header, "version")
    version.text = DAT_VERSION_NUMBER
    date = SubElement(header, "date")
    date.text = datetime.strptime(COMPONENTS_VERSION, "%Y%m%d-%H%M").strftime("%Y-%m-%d %H:%M:%S")
    author = SubElement(header, "author")
    author.text = "Darrow"
    homepage = SubElement(header, "homepage")
    homepage.text = "https://github.com/RetroDECK/RetroDECK"
    url = SubElement(header, "url")
    url.text = "https://github.com/RetroDECK/Components"
    romvault = SubElement(header, "romvault")
    romvault.set("forcepacking", "fileonly")

    return root


def recurse_for_bios(d, f, *a):
    bios = []
    if isinstance(d, list):
        for i in d:
            bios.extend(recurse_for_bios(i, f, *a))
    elif isinstance(d, dict):
        for k, v in d.items():
            if k == "bios":
                if isinstance(v, dict):
                    bios.append(v)
                else:
                    bios.extend(v)
            else:
                bios.extend(recurse_for_bios(v, f, *a, k))
    return bios


def main():
    sub_elements_component_system_dict: dict[str, list[Element]] = {}
    root = create_starter_xml_tree()

    for i in COMPONENTS_REPO_PATH.iterdir():
        if i.is_dir():
            for j in i.iterdir():
                if j.is_file() and j.name == "component_manifest.json":
                    with open(j, "r") as f:
                        data = json.load(f)

                    bios = recurse_for_bios(data, i.name)
                    for b in bios:
                        system = b["system"]
                        if not isinstance(system, list):
                            system = [system]
                        for s in system:
                            md5 = b.get("md5")
                            multiple_md5s = True
                            if not md5:
                                md5 = [None]
                            elif not isinstance(md5, list):
                                multiple_md5s = False
                                md5 = [md5]

                            for m in md5:
                                emulator_system_key = f"{i.name} - {s}"
                                name = b["filename"]
                                if m is None:
                                    emulator_system_key += " (no hashes)"
                                elif multiple_md5s:
                                    emulator_system_key += f' ({"".join(x for x in name if x.isalnum())} - {m})'

                                game = sub_elements_component_system_dict.get(emulator_system_key)
                                if game is None:
                                    game = SubElement(root, "game")
                                    game.set("name", emulator_system_key)
                                    sub_elements_component_system_dict[emulator_system_key] = game

                                for k in b.keys():
                                    if k not in KNOWN_BIOS_KEYS:
                                        raise Exception(f"Unknown BIOS key encountered: '{k}' in component {i.name}")
                                rom = SubElement(game, "rom")
                                rom.set("name", name)
                                if m is not None:
                                    rom.set("md5", m)
                                rom.set("description", b["description"])
                                if "required" in b:
                                    rom.set("required", b["required"])
                                if "sha256" in b:
                                    rom.set("sha256", b["sha256"])
                                paths = b.get("paths", [])
                                if isinstance(paths, str):
                                    paths = [paths]
                                for p in paths:
                                    path = SubElement(rom, "path")
                                    path.text = p

    with open(f"Retrodeck BIOS {DAT_VERSION_NUMBER}.dat", "wb") as f:
        f.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write(b'<!DOCTYPE datafile PUBLIC "-//Logiqx//DTD ROM Management Datafile//EN" "http://www.logiqx.com/Dats/datafile.dtd">\n')
        ElementTree(root).write(f, "utf-8")


if __name__ == "__main__":
    main()
