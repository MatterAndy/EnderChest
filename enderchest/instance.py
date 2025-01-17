"""Specification of a Minecraft instance"""
import re
from configparser import SectionProxy
from pathlib import Path
from typing import NamedTuple


class InstanceSpec(NamedTuple):
    """Specification of a Minecraft instance

    Parameters
    ----------
    name : str
        The "display name" for the instance
    root : Path
        The path to its ".minecraft" folder
    minecraft_versions : list-like of str
        The minecraft versions of this instance. This is typically a 1-tuple,
        but some loaders (such as the official one) will just comingle all
        your assets together across all profiles
    modloader : str or None
        The (display) name of the modloader, or None if this is a vanilla
        instance
    tags : list-like of str
        The tags assigned to this instance
    """

    name: str
    root: Path
    minecraft_versions: tuple[str, ...]
    modloader: str | None
    tags: tuple[str, ...]

    @classmethod
    def from_cfg(cls, section: SectionProxy) -> "InstanceSpec":
        """Parse an instance spec as read in from the enderchest config file

        Parameters
        ----------
        section : dict-like of str to str
            The section in the enderchest config as parsed by a ConfigParser

        Returns
        -------
        InstanceSpec
            The resulting InstanceSpec

        Raises
        ------
        KeyError
            If a required key is absent
        ValueError
            If a required entry cannot be parsed
        """
        return cls(
            section.name,
            Path(section["root"]),
            tuple(
                _parse_version(version.strip())
                for version in section["minecraft_version"].strip().split()
            ),
            section.get("modloader", None),
            tuple(
                tag.strip()
                for tag in section.get("tags", "")
                .replace(",", "\n")
                .strip()
                .split("\n")
            ),
        )


def equals(
    minecraft_root: Path, instance: InstanceSpec, other_instance: InstanceSpec
) -> bool:
    """Determine whether two instances point to the same location

    Parameters
    ----------
    minecraft_root : Path
        The starting location (the parent of where your EnderChest folder lives)
    instance : InstanceSpec
        the first instance
    other_instance : InstanceSpec
        the instance to compare it against

    Returns
    -------
    bool
        True if and only if the two instances have the same root, with regards
        to the provided `minecraft_root`
    """
    path = minecraft_root / instance.root.expanduser()
    other_path = minecraft_root / other_instance.root.expanduser()
    return path.expanduser().resolve() == other_path.expanduser().resolve()


def _parse_version(version_string: str) -> str:
    """The first release of each major Minecraft version doesn't follow strict
    major.minor.patch semver. This method appends the ".0" so that our version
    matcher doesn't mess up

    Parameters
    ----------
    version_string : str
        The version read in from the Minecraft instance's config

    Returns
    -------
    str
        Either the original version string or the original version string with
        ".0" tacked onto the end of it

    Notes
    -----
    Regex adapted straight from https://semver.org
    """
    if re.match(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)$", version_string):
        return version_string + ".0"
    return version_string
