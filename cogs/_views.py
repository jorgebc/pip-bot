"""Reusable Discord UI views shared across cogs."""

import discord

_REBOOT_CONFIRM_TIMEOUT = 30  # seconds


class RebootConfirmView(discord.ui.View):
    """Ephemeral confirmation view for the /reboot command.

    Sets ``confirmed`` to ``True`` when the user presses Confirm, ``False``
    when they press Cancel, and leaves it ``None`` on timeout.
    """

    def __init__(self) -> None:
        """Initialise the view with a 30-second timeout."""
        super().__init__(timeout=_REBOOT_CONFIRM_TIMEOUT)
        self.confirmed: bool | None = None

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.danger)
    async def confirm_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        """Handle the Confirm button press.

        Args:
            interaction: Discord interaction from the button click.
            button: The button that was pressed.
        """
        self.confirmed = True
        await interaction.response.defer()
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        """Handle the Cancel button press.

        Args:
            interaction: Discord interaction from the button click.
            button: The button that was pressed.
        """
        self.confirmed = False
        await interaction.response.defer()
        self.stop()
