from PySide6.QtWidgets import QWidget


class BaseSettingsPage(QWidget):
    """
    Abstract base class for modular settings pages.

    This defines the 'contract' that all specific settings pages (Network,
    Discord, etc.) must follow. The main SettingsDialog will interact
    with these methods rather than touching widgets directly.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        # Subclasses should call self.setup_ui() in their __init__

    def setup_ui(self):
        """
        Create the layout and widgets for this page.
        Must be implemented by subclass.
        """
        raise NotImplementedError("Settings pages must implement setup_ui()")

    def load_data(self, data: dict):
        """
        Populate the UI widgets with values from the config dictionary.

        Args:
            data (dict): The specific section of the config relevant to this page.
                         (e.g., only the 'targets' dictionary for NetworkPage)
        """
        raise NotImplementedError("Settings pages must implement load_data()")

    def get_data(self) -> dict:
        """
        Scrape the current values from the UI widgets and return them as a dict.

        Returns:
            dict: The updated configuration dictionary for this section.
        """
        raise NotImplementedError("Settings pages must implement get_data()")

    def validate(self) -> tuple[bool, str]:
        """
        Check if the user's input is valid.

        Returns:
            tuple: (is_valid, error_message)
            - is_valid (bool): True if data is safe to save.
            - error_message (str): User-friendly error if valid is False.
        """
        # Default to True. Subclasses should override this if they have
        # specific validation rules (e.g., checking valid IP formats).
        return True, ""
