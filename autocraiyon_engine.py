import random
import time
from pathlib import Path
from shutil import copyfile
from string import punctuation
from base64 import b64decode

from seleniumuser import User

root = Path(__file__).parent


class Autocraiyon:
    def __init__(
        self,
        word_list: list[str],
        word_list_title: str = None,
        num_generations: int = None,
        num_words_range: tuple[int, int] = (2, 10),
        browser: str = "firefox",
        webdriverpath: Path | str = None,
        save_individual_images: bool = False,
    ):
        """:param word_list: List of words to choose from.

        :param word_list_title: Title of the folder generations using this word list will be saved into.

        :param num_generations: Number of images to generate. If None, generations will continue indefinitely.

        :param num_words_range: Each prompt will contain a random number of words between num_words_range[0] and num_words_range[1].

        :param browser: Can be 'firefox' or 'chrome'.

        :param webdriverpath: Path to the appropriate web driver executable for browser and system.
        Can be None if the web driver is in you PATH.

        :param save_inidividual_images: If True, each of the 9 images from a generation will be saved
        to a folder named after the prompt in addition to the screenshot image."""
        self.word_list = word_list
        self.num_generations = num_generations
        self.num_words_range = num_words_range
        self._set_save_location(word_list_title)
        self.temp_dir = root / "images" / "temp"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.user = User(
            browser_type=browser,
            download_dir=self.temp_dir,
            driver_path=webdriverpath,
            page_load_timeout=120,
        )
        self.should_save_individual_images = save_individual_images

    def _set_save_location(self, word_list_title: str = None):
        self.image_dir = (
            root / "images" / word_list_title if word_list_title else root / "images"
        )
        self.image_dir.mkdir(parents=True, exist_ok=True)

    def get_prompt(self) -> str:
        num_words = random.randint(self.num_words_range[0], self.num_words_range[1])
        return " ".join(random.choice(self.word_list) for _ in range(num_words))

    def use_word_list(self, word_list: list[str], word_list_title: str = None):
        self.word_list = word_list
        self._set_save_location(word_list_title)

    def go_to_generator(self):
        url = "https://www.craiyon.com/"
        self.user.get(url)
        # remove ad banners
        for ad in [
            '//div[@id="craiyon_left_rail"]',
            '//div[@id="craiyon_right_rail"]',
            '//div[@id="fs-sticky-footer"]',
            '//div[@id="videoplayer"]',
        ]:
            try:
                self.user.remove(ad)
            except Exception as e:
                pass

    def submit_prompt(self):
        self.user.send_keys('//div[@id="prompt"]', self.prompt, clear_first=True)
        self.user.click('//button[@id="generateButton"]')

    def monitor_for_results(self) -> bool:
        """Monitors for generation results to appear.

        Returns True if they have appeared within 'max_wait',
        returns False if they haven't."""
        try:
            self.user.wait_until(
                lambda: self.user.find(
                    '//div[@class="grid grid-cols-3 gap-1 sm:gap-2"]'
                ),
                max_wait=60 * 3,
                polling_interval=1,
            )
            return True
        except KeyboardInterrupt:
            pass
        except TimeoutError:
            return False

    def download_results(self):
        # For some reason the first click on the screenshot button always fails and throws an exception.
        try:
            self.user.click('//button[@aria-label="Screenshot"]')
        except Exception as e:
            time.sleep(1)
            self.user.click('//button[@aria-label="Screenshot"]')
        img_path = self.monitor_file_download()
        if self.should_save_individual_images and img_path:
            self.save_individual_images(img_path)

    def save_individual_images(self, img_path: Path):
        """Each image element contains the base64 encoded data for the image in its src tag.

        A subfolder named after imgPath in self.image_dir will be created and the individual images will be save there."""
        base_name = img_path.stem
        save_dir = self.image_dir / base_name
        save_dir.mkdir(parents=True, exist_ok=True)
        soup = self.user.get_soup()
        for i, img in enumerate(
            soup.find("div", class_="grid grid-cols-3 gap-1 sm:gap-2").find_all("img")
        ):
            data = img.get("src")
            data = data[data.find(",") + 1 :].replace("\n", "")
            dst = save_dir / f"{base_name}-{i}.jpg"
            dst.write_bytes(b64decode(data))

    def monitor_file_download(self) -> Path | None:
        """Downloading results is done through the craiyon interface,
        so the save directory is scanned for a file with the matching prompt/prompt fragment
        to confirm download is complete.

        The file is then moved to a directory named after the word_list, if a name was provided.

        Otherwise the file is moved to the 'image' directory.

        A temp folder is used so that the seleniumuser object doesn't
        have to be deleted and recreated to change save directories when a new word list is used.

        Returns a Path object for the downloaded image."""
        # format prompt according to how craiyon formats file download names
        name = "_".join(self.prompt.split(" ")[:5])
        for ch in " " + punctuation:
            name = name.replace(ch, "_")
        # monitor for file
        img_path = None
        try:
            self.user.wait_until(
                lambda: any(name in str(f) for f in self.temp_dir.glob("*.*")),
                max_wait=60 * 5,
                polling_interval=1,
            )
            print("File downloaded successfully.")
            img_path = self._move_file(name)
        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(e)
            print(
                f"Could not locate image file with prompt fragment {name} in the title."
            )
        return img_path

    def _move_file(self, name: str) -> Path | None:
        """Move downloaded file from temp into the directory pointed at by self.image_dir.

        Returns a Path object for the downloaded file."""
        for file in self.temp_dir.glob("*.*"):
            if name in str(file):
                print(f"Moving file from temp to {self.image_dir.stem}...")
                copyfile(str(file), str(self.image_dir / file.name))
                print("Move complete.")
                # delete file from temp directory
                file.unlink()
                return self.image_dir / file.name
        return None

    def automate(self):
        """Automates generation and download process."""
        i = 1
        continue_condition = (
            lambda: i <= self.num_generations if self.num_generations else lambda: True
        )
        self.go_to_generator()
        while continue_condition():
            try:
                self.prompt = self.get_prompt()
                print(
                    f'Generating prompt {i}/{self.num_generations if self.num_generations else "inf"}: {self.prompt}'
                )
                self.submit_prompt()
                print("Waiting for results...")
                result = self.monitor_for_results()
                if result:
                    print("Downloading results...")
                    self.download_results()
            except KeyboardInterrupt:
                break
            except Exception as e:
                input(str(e))
            i += 1
        print("goodbye")
        self.user.close_browser()
