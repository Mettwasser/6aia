import datetime
import nextcord


"""<t:1624385691:t>
<t:1624385691:T>
<t:1624385691:d>
<t:1624385691:D>
<t:1624385691:f>
<t:1624385691:F>
<t:1624385691:R>
    8:14 PM
    8:14:51 PM
    06/22/2021
    June 22, 2021
    June 22, 2021 8:14 PM
    Tuesday, June 22, 2021 8:14 PM
    a year ago"""


def to_timestamp(time: datetime.datetime, format: str = "t"):
    """
    Converts a datetime to a discord timestamp.
    """

    # Check if the date is diffrent. If so, force a time format
    if nextcord.utils.utcnow().date() != time.date():
        format = "f"

    # return a string that represents a discord timestamp
    return f"<t:{int(time.timestamp())}:{format}>"


def disable_buttons(view: nextcord.ui.View):
    # Sets the `disabled` value of all the Buttons to True
    for child in view.children:
        if isinstance(child, nextcord.ui.Button):
            child.disabled = True


def align(names: list, values: list, set_column: bool = True, custom_width=None):
    text = ""
    width = custom_width or len(max(names, key=len)) + 2

    for name, value in zip(names, values):
        text += str(name).ljust(width) + \
            (":".ljust(width // 4) if set_column else "") + str(value) + "\n"

    return text
