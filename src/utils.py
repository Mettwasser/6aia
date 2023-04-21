import datetime
import nextcord

"""
<t:1624385691:t>
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
    a year ago
"""


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

class Align:

    @staticmethod
    def align(names: list[str], values: list[int], set_column: bool = True, custom_width=None) -> str:
        # set the initial text
        text = ""

        # custom width or the longest name out of `names` + 2
        width = custom_width or len(max(names, key=len)) + 2

        # loop over kvp
        for name, value in zip(names, values):
            # append string with the correct alignment
            text += str(name).ljust(width) + \
                (":".ljust(width // 3) if set_column else "") + str(value) + "\n"


        return text

    @staticmethod
    def alignmany(connectors: list[str], *lists: list[object], amount_newlines = 1, spacing_char = " ") -> str:
        '''
        A function that aligns multiple items from `lists`.
        Note:
            connectors must be the length of the rest of your values -1
            Example:
                vals, names = [1,2], [True, False]
                connectors can only contain 1 item (which is placed between 1 and True / 2 and False)
        '''
        # set the initial text
        text = ""

        connectors += [""]

        # custom width or the longest (str) item out of `lists`
        widths = [max(len(str(item)) + 2 for item in column) for column in zip(*lists)]

        # loop over kvp
        for list in lists:
            for c, (item, connector) in enumerate(zip(list, connectors)):
                text += str(item).ljust(widths[c], spacing_char) + (connector.ljust(widths[c]//3, spacing_char) if isinstance(connector, str) else "")
            text += "\n" * amount_newlines
        
        return text