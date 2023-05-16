"""Test functionality around linking instances"""
from pathlib import Path

import pytest

from .. import place
from . import utils

GLOBAL_SHULKER = (
    "global",
    """; global
[minecraft]
*

[link-folders]
screenshots
backups
crash-reports
logs
""",
)


class TestGlobalPlace:
    """Test the simplest case of linking--where the files in the shulker should
    go into every instance"""

    @pytest.fixture(autouse=True)
    def setup_teardown(self, minecraft_root):
        """Setup / teardown for this test class"""
        chest_folder = minecraft_root / "EnderChest"
        utils.pre_populate_enderchest(chest_folder, GLOBAL_SHULKER)

        do_not_touch = {
            (chest_folder / "global" / "resourcepacks" / "stuff.zip"): "dfgwhgsadfhsd",
            (chest_folder / "global" / "logs" / "bumpona.log"): (
                "Like a bump on a bump on a log, baby.\n"
                "Like I'm in a fist fight with a fog, baby.\n"
                "Step-ball-change and a pirouette.\n"
                "And I regret, I regret.\n"
            ),
        }

        for path, contents in do_not_touch.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(contents)

        yield

        # check on teardown that all those "do_not_touch" files are untouched
        for path, contents in do_not_touch.items():
            assert path.read_text() == contents

    @pytest.mark.parametrize(
        "instance_name, instance_spec", utils.TESTING_INSTANCES[:2]
    )
    def test_place_is_willing_to_replace_empty_folders_by_default(
        self, minecraft_root, instance_name, instance_spec
    ):
        place.place_enderchest(minecraft_root)

        assert (
            instance_spec.root / "logs"
        ).resolve() == minecraft_root / "EnderChest" / "global" / "logs"

        # also, just to be explicit
        assert (instance_spec.root / "logs" / "bumpona.log").exists()

    @pytest.mark.parametrize(
        "instance_name, instance_spec", utils.TESTING_INSTANCES[:2]
    )
    def place_is_able_to_place_individual_files(
        self, minecraft_root, instance_name, instance_spec
    ):
        place.place_enderchest(minecraft_root)

        assert not (instance_spec.root / "resourcepacks").is_symlink()

        assert (instance_spec.root / "resourcepacks" / "stuff.zip").resolve() == (
            minecraft_root / "EnderChest" / "global" / "resourcepacks" / "stuff.zip"
        )

    @pytest.mark.parametrize(
        "instance_name, instance_spec", utils.TESTING_INSTANCES[:2]
    )
    def place_cleans_up_broken_symlinks_by_default(
        self, minecraft_root, instance_name, instance_spec
    ):
        broken_link = instance_spec.root / "shaderpacks" / "Seuss CitH.zip.txt"
        broken_link.symlink_to(minecraft_root / "i-do-not-exist.txt")

        place.place_enderchest(minecraft_root)

        assert not broken_link.exists()

    @pytest.mark.parametrize(
        "instance_name, instance_spec", utils.TESTING_INSTANCES[:2]
    )
    def place_will_not_overwrite_a_non_empty_folder(
        self, minecraft_root, instance_name, instance_spec
    ):
        existing_file = instance_spec.root / "screenshots" / "thumbs.db"
        existing_file.write_text("opposable")

        with pytest.raises(
            RuntimeError, match=rf"{instance_name}(.*)screenshots(.*)is not empty"
        ):
            place.place_enderchest(minecraft_root)

        # make sure the file is still there afterwards
        assert existing_file.exists()
        assert existing_file.resolve() == existing_file
        assert existing_file.read_text() == "opposable"

    @pytest.mark.parametrize(
        "instance_name, instance_spec", utils.TESTING_INSTANCES[:2]
    )
    def place_will_not_overwrite_a_file(
        self, minecraft_root, instance_name, instance_spec
    ):
        existing_file = instance_spec.root / "resourcepacks" / "stuff.zip"
        existing_file.write_text("other_stuff")

        with pytest.raises(
            RuntimeError, match=rf"{instance_name}(.*)stuff.zip(.*)exists"
        ):
            place.place_enderchest(minecraft_root)

        # make sure the file is still there afterwards
        assert existing_file.exists()
        assert existing_file.resolve() == existing_file
        assert existing_file.read_text() == "other_stuff"

    @pytest.mark.parametrize(
        "instance_name, instance_spec", utils.TESTING_INSTANCES[:2]
    )
    def place_will_overwrite_an_existing_symlink(
        self, minecraft_root, instance_name, instance_spec
    ):
        (minecraft_root / "workspace" / "other_stuff.zip").write_text("working stuff")
        existing_symlink = instance_spec.root / "resourcepacks" / "stuff.zip"
        existing_symlink.symlink_to(minecraft_root / "workspace" / "other_stuff.zip")

        place.place_enderchest(minecraft_root)

        assert (
            existing_symlink.resolve()
            == minecraft_root / "EnderChest" / "global" / "resourcepacks" / "stuff.zip"
        )
        assert existing_symlink.read_text() == "dfgwhgsadfhsd"
