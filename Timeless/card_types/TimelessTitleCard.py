from pathlib import Path
from collections import namedtuple
from typing import Literal, Optional, TYPE_CHECKING

from pydantic import root_validator

from app.schemas.card_type import BaseCardTypeCustomFontAllText

from modules.BaseCardType import (
    BaseCardType,
    ImageMagickCommands,
    Extra,
    CardDescription
)
from modules.Debug import log
from modules.EpisodeInfo2 import EpisodeInfo
from modules.Title import SplitCharacteristics

if TYPE_CHECKING:
    from app.models.preferences import Preferences
    from modules.Font import Font


BoxCoordinates = namedtuple('BoxCoordinates', ('x0', 'y0', 'x1', 'y1'))


class TimelessTitleCard(BaseCardType):
    """
    CardType that produces title cards for "Timeless" television series.
    """

    API_DETAILS = CardDescription(
        name='Timeless (2016)',
        identifier='Timeless',
        example='https://raw.githubusercontent.com/Supremicus/tcm-images/main/LocalCardTypePreviews/TimelessTitleCard.preview.jpg',
        creators=[
            'Supremicus'
        ],
        source='local',
        supports_custom_fonts=False,
        supports_custom_seasons=True,
        supported_extras=[
        ],
        description=[
            'Title card intended for the "Timeless" television '
            'series with matching custom font to create the shows text '
            'just like the shows logo.'
        ]
    )

    class CardModel(BaseCardTypeCustomFontAllText):
        title_text: str
        season_text: str
        episode_text: str
        font_color: str
        font_size: float = 1.0
        font_interline_spacing: int = 0
        font_vertical_shift: int = 0

    """Directory where all reference files used by this card are stored"""
    REF_DIRECTORY = Path(__file__).parent / 'ref'

    """Characteristics for title splitting by this class"""
    TITLE_CHARACTERISTICS: SplitCharacteristics = {
        'max_line_width': 24,
        'max_line_count': 4,
        'style': 'even',
    }

    """How to name archive directories for this type of card"""
    ARCHIVE_NAME = 'Timeless'

    """Characteristics of the title text"""
    TITLE_FONT = str((REF_DIRECTORY / 'fonts/Timeless-Main.otf').resolve())
    TITLE_FONT_INFILL = REF_DIRECTORY / 'fonts/Timeless-Infill.otf'
    TITLE_FONT_GEARS = REF_DIRECTORY / 'fonts/Timeless-Gears.otf'
    DEFAULT_FONT_CASE = 'source'
    TITLE_COLOR = '#FFFFFF'
    TITLE_COLOR_INFILL = '#000000'
    TITLE_COLOR_GEARS = '#000000'

    """Characteristics of episode text"""
    EPISODE_TEXT_FONT = REF_DIRECTORY / 'fonts/Timeless-Main.otf'
    EPISODE_TEXT_FONT_INFILL = REF_DIRECTORY / 'fonts/Timeless-Infill.otf'
    EPISODE_TEXT_FONT_GEARS = REF_DIRECTORY / 'fonts/Timeless-Gears.otf'
    EPISODE_TEXT_FORMAT = 'EPISODE {episode_number}'
    EPISODE_TEXT_COLOR = '#FFFFFF'
    EPISODE_TEXT_COLOR_INFILL = '#000000'
    EPISODE_TEXT_COLOR_GEARS = '#000000'

    """Standard font replacements for the title font"""
    FONT_REPLACEMENTS = {
    }

    """Whether this CardType uses season titles for archival purposes"""
    USES_SEASON_TITLE = True

    """Source path for the gradient image"""
    __GRADIENT_IMAGE = REF_DIRECTORY / 'overlays/gradient.png'

    __slots__ = (
        'source_file',
        'output_file',
        'title_text',
        'season_text',
        'episode_text',
        'hide_season_text',
        'hide_episode_text',
        'line_count',
        'font_file',
        'font_color',
        'font_size',
        'font_interline_spacing',
        'font_vertical_shift',
        'episode_text_color',
        'title_text_size',
        'index_text_size',
        'y',
        '_title_text_dimensions',
        '_index_text_dimensions',
        '_title_coordinates',
        '_index_coordinates',
    )

    def __init__(self, *,
            source_file: Path,
            card_file: Path,
            title_text: str,
            season_text: str,
            episode_text: str,
            hide_season_text: bool = False,
            hide_episode_text: bool = False,
            font_file: str = TITLE_FONT,
            font_color: str = TITLE_COLOR,
            font_size: float = 1.0,
            font_interline_spacing: int = 0,
            font_vertical_shift: int = 0,
            episode_text_color: str = EPISODE_TEXT_COLOR,
            blur: bool = False,
            grayscale: bool = False,
            preferences: Optional['Preferences'] = None,
            **unused,
        ) -> None:
        """Construct a new instance of this Card."""

        # Initialize the parent class - this sets up an ImageMagickInterface
        super().__init__(blur, grayscale, preferences=preferences)

        self.source_file = source_file
        self.output_file = card_file

        # Ensure characters that need to be escaped are
        self.title_text = self.image_magick.escape_chars(title_text)
        self.season_text = self.image_magick.escape_chars(season_text)
        self.episode_text = self.image_magick.escape_chars(episode_text)
        self.hide_season_text = hide_season_text
        self.hide_episode_text = hide_episode_text
        self.line_count = len(title_text.split('\n'))

        # Font customizations
        self.font_file = font_file
        self.font_color = font_color
        self.font_size = font_size
        self.font_interline_spacing = -50 + font_interline_spacing
        self.font_vertical_shift = font_vertical_shift

        # Optional extras
        self.episode_text_color = episode_text_color

        # Custom sizes and offsets
        self.title_text_size = 256 * self.font_size
        self.index_text_size = 60
        self.y = 47 + self.font_vertical_shift

        # Put coordinates into memory
        self._title_coordinates = None
        self._index_coordinates = None
        self._title_text_dimensions = None
        self._index_text_dimensions = None


    def get_title_dimensions(self):
        """
        Get the dimensions of the title text.

        Returns:
            Tuple[float, float]: Width and height of the title text.
        """
        if self._title_text_dimensions is None:
            self._title_text_dimensions = self.image_magick.get_text_dimensions(
                self.title_text_commands,
                interline_spacing=self.font_interline_spacing,
                line_count=len(self.title_text.splitlines()),
            )
        return self._title_text_dimensions


    @property
    def title_text_commands(self) -> ImageMagickCommands:
        """Subcommands required to add the title text."""

        return [
            # Add title text
            f'-font "{self.font_file}"',
            f'-gravity south',
            f'-pointsize {self.title_text_size}',
            f'-kerning 0',
            f'-interline-spacing {self.font_interline_spacing}',
            f'-background transparent',
            f'-fill "{self.font_color}"',
            f'-annotate +0{self.y:+} "{self.title_text}"',
        ]


    @property
    def title_text_infill_commands(self) -> ImageMagickCommands:
        """Subcommands required to add the title text."""

        return [
            # Add title text
            f'-font "{self.TITLE_FONT_INFILL}"',
            f'-gravity south',
            f'-pointsize {self.title_text_size}',
            f'-kerning 0',
            f'-interline-spacing {self.font_interline_spacing}',
            f'-background transparent',
            f'-fill "{self.TITLE_COLOR_INFILL}"',
            f'-annotate +0{self.y:+} "{self.title_text}"',
        ]


    @property
    def title_text_gears_commands(self) -> ImageMagickCommands:
        """Subcommands required to add the title text."""

        return [
            # Add title text
            f'-font "{self.TITLE_FONT_GEARS}"',
            f'-gravity south',
            f'-pointsize {self.title_text_size}',
            f'-kerning 0',
            f'-interline-spacing {self.font_interline_spacing}',
            f'-background transparent',
            f'-fill "{self.TITLE_COLOR_GEARS}"',
            f'-annotate +0{self.y:+} "{self.title_text}"',
        ]


    @property
    def index_text_commands(self) -> ImageMagickCommands:
        """Subcommands required to add the index text."""

        # All text hidden, return empty commands
        if self.hide_season_text and self.hide_episode_text:
            return []

        # Set index text based on which text is hidden/not
        if self.hide_season_text:
            index_text = self.episode_text
        elif self.hide_episode_text:
            index_text = self.season_text
        else:
            index_text = f'{self.season_text} • {self.episode_text}'

        title_width, title_height = self.get_title_dimensions()

        # Text offsets
        index_offset = self.y + title_height - 10

        return [
            f'-font "{self.EPISODE_TEXT_FONT}"',
            f'-gravity south',
            f'-pointsize {self.index_text_size}',
            f'-kerning 0',
            f'-fill "{self.episode_text_color}"',
            f'-annotate +0{index_offset:+} "{index_text}"',
        ]


    @property
    def index_text_infill_commands(self) -> ImageMagickCommands:
        """Subcommands required to add the index text."""

        # All text hidden, return empty commands
        if self.hide_season_text and self.hide_episode_text:
            return []

        # Set index text based on which text is hidden/not
        if self.hide_season_text:
            index_text = self.episode_text
        elif self.hide_episode_text:
            index_text = self.season_text
        else:
            index_text = f'{self.season_text} • {self.episode_text}'

        title_width, title_height = self.get_title_dimensions()

        # Text offsets
        index_offset = self.y + title_height - 10

        return [
            f'-font "{self.EPISODE_TEXT_FONT_INFILL}"',
            f'-gravity south',
            f'-pointsize {self.index_text_size}',
            f'-kerning 0',
            f'-fill "{self.EPISODE_TEXT_COLOR_INFILL}"',
            f'-annotate +0{index_offset:+} "{index_text}"',
        ]


    @property
    def index_text_gears_commands(self) -> ImageMagickCommands:
        """Subcommands required to add the index text."""

        # All text hidden, return empty commands
        if self.hide_season_text and self.hide_episode_text:
            return []

        # Set index text based on which text is hidden/not
        if self.hide_season_text:
            index_text = self.episode_text
        elif self.hide_episode_text:
            index_text = self.season_text
        else:
            index_text = f'{self.season_text} • {self.episode_text}'

        title_width, title_height = self.get_title_dimensions()

        # Text offsets
        index_offset = self.y + title_height - 10

        return [
            f'-font "{self.EPISODE_TEXT_FONT_GEARS}"',
            f'-gravity south',
            f'-pointsize {self.index_text_size}',
            f'-kerning 0',
            f'-fill "{self.EPISODE_TEXT_COLOR_GEARS}"',
            f'-annotate +0{index_offset:+} "{index_text}"',
        ]


    @property
    def gradient_commands(self) -> ImageMagickCommands:
        """
        Subcommand to overlay the gradient to this image. This rotates
        and repositions the gradient overlay based on the text position.
        """

        return [
            f'"{self.__GRADIENT_IMAGE.resolve()}"',
            f'-composite',
        ]


    @staticmethod
    def is_custom_font(font: 'Font', extras: dict) -> bool:
        """
        Determine whether the given font characteristics constitute a
        default or custom font.

        Args:
            font: The Font being evaluated.
            extras: Dictionary of extras for evaluation.

        Returns:
            True if a custom font is indicated, False otherwise.
        """

        return FontPreviewTitleCard._is_custom_font(font)


    @staticmethod
    def is_custom_season_titles(
            custom_episode_map: bool,
            episode_text_format: str,
        ) -> bool:
        """
        Determine whether the given attributes constitute custom or
        generic season titles.

        Args:
            custom_episode_map: Whether the EpisodeMap was customized.
            episode_text_format: The episode text format in use.

        Returns:
            True if custom season titles are indicated, False otherwise.
        """

        return (
            custom_episode_map
            or episode_text_format != TimelessTitleCard.EPISODE_TEXT_FORMAT
        )


    @staticmethod
    def SEASON_TEXT_FORMATTER(episode_info: EpisodeInfo) -> str:
        """
        Fallback season title formatter.

        Args:
            episode_info: Info of the Episode whose season text is being
                determined.

        Returns:
            'Specials' if the season number is 0; otherwise just
            'SEASON {x}'.
        """

        if episode_info.season_number == 0:
            return 'SPECIALS'

        return 'SEASON {season_number}'


    def create(self) -> None:
        """
        Make the necessary ImageMagick and system calls to create this
        object's defined title card.
        """

        self.image_magick.run([
            f'convert',
            f'"{self.source_file.resolve()}"',
            # Resize and apply styles to source image
            *self.resize_and_style,
            *self.gradient_commands,
            # Add index text
            *self.index_text_commands,
            *self.index_text_infill_commands,
            *self.index_text_gears_commands,
            # Add title text
            *self.title_text_commands,
            *self.title_text_infill_commands,
            *self.title_text_gears_commands,
            # Attempt to overlay mask
            *self.add_overlay_mask(self.source_file),
            # Create card
            *self.resize_output,
            f'"{self.output_file.resolve()}"',
        ])