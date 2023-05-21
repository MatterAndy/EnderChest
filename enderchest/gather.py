"""Functionality for finding, resolving and parsing local installations and instances"""
import logging
from pathlib import Path
from urllib.parse import ParseResult

from . import filesystem as fs
from . import instance, loggers
from .enderchest import EnderChest
from .instance import InstanceSpec
from .shulker_box import ShulkerBox


def load_ender_chest(minecraft_root: Path) -> EnderChest:
    """Load the configuration from the enderchest.cfg file in the EnderChest
    folder.

    Parameters
    ----------
    minecraft_root : Path
        The root directory that your minecraft stuff (or, at least, the one
        that's the parent of your EnderChest folder)

    Returns
    -------
    EnderChest
        The EnderChest configuration

    Raises
    ------
    FileNotFoundError
        If no EnderChest folder exists in the given minecraft root or if no
        enderchest.cfg file exists within that EnderChest folder
    """
    config_path = fs.ender_chest_config(minecraft_root)
    loggers.GATHER_LOGGER.debug(f"Loading {config_path}")
    ender_chest = EnderChest.from_cfg(config_path)
    loggers.GATHER_LOGGER.debug(f"Parsed EnderChest installation from {minecraft_root}")
    return ender_chest


def load_ender_chest_instances(minecraft_root: Path) -> list[InstanceSpec]:
    """Get the list of instances registered with the EnderChest located in the
    minecraft root

    Parameters
    ----------
    minecraft_root : Path
        The root directory that your minecraft stuff (or, at least, the one
        that's the parent of your EnderChest folder)

    Returns
    -------
    list of InstanceSpec
        The instances registered with the EnderChest

    Notes
    -----
    If no EnderChest is installed in the given location, then this will return
    an empty list rather than failing outright.
    """
    try:
        ender_chest = load_ender_chest(minecraft_root)
        instances: list[InstanceSpec] = ender_chest.instances
    except (FileNotFoundError, ValueError) as bad_chest:
        loggers.GATHER_LOGGER.error(
            f"Could not load EnderChest from {minecraft_root}:\n  {bad_chest}"
        )
        instances = []
    if len(instances) == 0:
        loggers.GATHER_LOGGER.info(
            f"There are no instances registered to the {minecraft_root} EnderChest"
        )
    else:
        loggers.GATHER_LOGGER.info(
            "These are the instances that are currently registered"
            f" to the {minecraft_root} EnderChest:\n"
            + "\n".join(
                [
                    f"  {i + 1}. {_render_instance(instance)})"
                    for i, instance in enumerate(instances)
                ]
            )
        )
    return instances


def _render_instance(instance: InstanceSpec) -> str:
    """Render an instance spec to a descriptive string

    Parameters
    ----------
    instance : InstanceSpec
        The instance spec to render

    Returns
    -------
    str
        {instance.name} ({instance.root})
    """
    return f"{instance.name} ({instance.root})"


def load_shulker_boxes(minecraft_root: Path) -> list[ShulkerBox]:
    """Load all shulker boxes in the EnderChest folder and return them in the
    order in which they should be linked.

    Parameters
    ----------
    minecraft_root : Path
        The root directory that your minecraft stuff (or, at least, the one
        that's the parent of your EnderChest folder)

    Returns
    -------
    list of ShulkerBoxes
        The shulker boxes found in the EnderChest folder, ordered in terms of
        the sequence in which they should be linked

    Notes
    -----
    If no EnderChest is installed in the given location, then this will return
    an empty list rather than failing outright.
    """
    shulker_boxes: list[ShulkerBox] = []
    try:
        for shulker_config in fs.shulker_box_configs(minecraft_root):
            shulker_box = _load_shulker_box(shulker_config)
            if shulker_box is not None:
                shulker_boxes.append(shulker_box)
    except FileNotFoundError:
        loggers.GATHER_LOGGER.error(
            f"There is no EnderChest installed within {minecraft_root}"
        )
        return []

    shulker_boxes = sorted(shulker_boxes)

    if len(shulker_boxes) == 0:
        loggers.GATHER_LOGGER.info(
            f"There are no shulker boxes within the {minecraft_root} EnderChest"
        )
    else:
        loggers.GATHER_LOGGER.info(
            f"These are the shulker boxes within the {minecraft_root} EnderChest,"
            "\nlisted in the order in which they are linked:\n"
            + "\n".join(
                f"  {_render_shulker_box(shulker_box)}" for shulker_box in shulker_boxes
            )
        )
    return shulker_boxes


def _load_shulker_box(config_file: Path) -> ShulkerBox | None:
    """Attempt to load a shulker box from a config file, and if you can't,
    at least log why the loading failed.

    Parameters
    ----------
    config_file : Path
        Path to the config file

    Returns
    -------
    ShulkerBox | None
        The parsed shulker box or None, if the shulker box couldn't be parsed
    """
    try:
        loggers.GATHER_LOGGER.debug(f"Attempting to parse {config_file}")
        shulker_box = ShulkerBox.from_cfg(config_file)
        loggers.GATHER_LOGGER.debug(
            f"Successfully parsed {_render_shulker_box(shulker_box)}"
        )
        return shulker_box
    except (FileNotFoundError, ValueError) as bad_box:
        loggers.GATHER_LOGGER.warning(
            f"Could not load shulker box from {config_file}:\n  {bad_box}"
        )
    return None


def _render_shulker_box(shulker_box: ShulkerBox) -> str:
    """Render a shulker box to a descriptive string

    Parameters
    ----------
    shulker_box : ShulkerBox
        The shulker box spec to render

    Returns
    -------
    str
        {priority}. {folder_name} [({name})]
            (if different from folder name)
    """
    stringified = f"{shulker_box.priority}. {shulker_box.root.name}"
    if shulker_box.root.name != shulker_box.name:
        # note: this is not a thing
        stringified += f" ({shulker_box.name})"
    return stringified


def load_ender_chest_remotes(minecraft_root: Path) -> list[tuple[ParseResult, str]]:
    """Load all remote EnderChest installations registered with this one

    Parameters
    ----------
    minecraft_root : Path
        The root directory that your minecraft stuff (or, at least, the one
        that's the parent of your EnderChest folder)

    Returns
    -------
    list of (URI, str) tuples
        The URIs of the remote EnderChests, paired with their aliases

    Notes
    -----
    If no EnderChest is installed in the given location, then this will return
    an empty list rather than failing outright.
    """
    try:
        ender_chest = load_ender_chest(minecraft_root)
        remotes: dict[str, ParseResult] = ender_chest.remotes
    except (FileNotFoundError, ValueError) as bad_chest:
        loggers.GATHER_LOGGER.error(
            f"Could not load EnderChest from {minecraft_root}:\n  {bad_chest}"
        )
        remotes = {}

    if len(remotes) == 0:
        loggers.GATHER_LOGGER.info(
            f"There are no remotes registered to the {minecraft_root} EnderChest"
        )
        return []

    report = (
        "These are the remote EnderChest installations registered"
        f" to the one installed at {minecraft_root}"
    )
    remote_list: list[tuple[ParseResult, str]] = []
    for alias, remote in remotes.items():
        report += f"\n  - {_render_remote(alias, remote)}"
        remote_list.append((remote, alias))
    loggers.GATHER_LOGGER.info(report)
    return remote_list


def _render_remote(alias: str, uri: ParseResult) -> str:
    """Render a remote to a descriptive string

    Parameters
    ----------
    alias : str
        The name of the remote
    uri : ParseResult
        The parsed URI for the remote

    Returns
    -------
    str
        {uri_string} [({alias})]}
            (if different from the URI hostname)
    """
    uri_string = uri.geturl()

    if uri.hostname != alias:
        uri_string += f" ({alias})"
    return uri_string


def load_shulker_box_matches(
    minecraft_root: Path, shulker_box_name: str
) -> list[InstanceSpec]:
    """Get the list of registered instances that link to the specified shulker box

    Parameters
    ----------
    minecraft_root : Path
        The root directory that your minecraft stuff (or, at least, the one
        that's the parent of your EnderChest folder)
    shulker_box_name : str
        The name of the shulker box you're asking about

    Returns
    -------
    list of InstanceSpec
        The instances that are / should be linked to the specified shulker box
    """
    instances = load_ender_chest_instances(minecraft_root)
    if not instances:
        return instances

    config_file = fs.shulker_box_config(minecraft_root, shulker_box_name)
    shulker_box = _load_shulker_box(config_file)
    if shulker_box is None:
        return []
    matches = [instance for instance in instances if shulker_box.matches(instance)]

    if len(matches) == 0:
        report = "does not link to by any registered instances"
    else:
        report = "is linked to by the following instancs:\n" + "\n".join(
            f"  - {_render_instance(instance)}" for instance in matches
        )

    loggers.GATHER_LOGGER.info(
        f"The shulker box {_render_shulker_box(shulker_box)} {report}"
    )

    return matches


def gather_minecraft_instances(
    minecraft_root: Path, search_path: Path, official: bool | None
) -> list[InstanceSpec]:
    """Search the specified directory for Minecraft installations

    Parameters
    ----------
    minecraft_root : Path
        The root directory that your minecraft stuff (or, at least, the one
        that's the parent of your EnderChest folder). This will be used to
        construct relative paths.

    search_path : Path
        The path to search

    official : bool or None
        Whether we expect that the instances found in this location will be:
          - from the official launcher (official=True)
          - from a MultiMC-style launcher (official=False)
          - a mix / unsure (official=None)

    Returns
    -------
    list of InstanceSpec
        A list of parsed instances
    """
    instances: list[InstanceSpec] = []
    for folder in fs.minecraft_folders(search_path):
        folder_path = folder.absolute()
        loggers.GATHER_LOGGER.info(f"Found {folder}")
        if official is not False:
            try:
                instances.append(
                    instance.gather_metadata_for_official_instance(folder_path)
                )
                continue
            except ValueError as not_official:
                loggers.GATHER_LOGGER.log(
                    logging.INFO if official is None else logging.WARNING,
                    (f"{folder} is not an official instance:" f"\n{not_official}",),
                )
        if official is not True:
            try:
                instances.append(instance.gather_metadata_for_mmc_instance(folder_path))
                continue
            except ValueError as not_mmc:
                loggers.GATHER_LOGGER.log(
                    logging.INFO if official is None else logging.WARNING,
                    f"{folder} is not an MMC-like instance:\n{not_mmc}",
                )
        loggers.GATHER_LOGGER.warn(
            f"{folder_path} does not appear to be a valid Minecraft instance"
        )
    official_count = 0
    for i, mc_instance in enumerate(instances):
        if mc_instance.name == "official":
            if official_count > 0:
                instances[i] = mc_instance._replace(name=f"official.{official_count}")
            official_count += 1
        try:
            instances[i] = mc_instance._replace(
                root=mc_instance.root.relative_to(minecraft_root)
            )
        except ValueError:
            # TODO: if not Windows, try making relative to "~"
            pass  # instance isn't inside the minecraft root
    return instances