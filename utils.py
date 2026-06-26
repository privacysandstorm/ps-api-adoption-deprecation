import matplotlib.pyplot as plt
import matplotlib
import os
import seaborn as sns
import numpy as np


def saveFig(path, size=[4, 3]):
    plt.rcParams["figure.autolayout"] = True
    # Sane default fig size for papers
    matplotlib.rcParams["figure.figsize"] = size

    # Uses Opentype-compatible fonts
    # conferences often require this for camera ready, so if you don't do it pre-submission you'll have a nightmare at camera-ready time.
    matplotlib.rcParams["pdf.fonttype"] = 42
    matplotlib.rcParams["ps.fonttype"] = 42
    # Automatically make the directory hierarchy so I can just save figures with path names
    os.makedirs(os.path.dirname(path), exist_ok=True)
    # Makes background transparent so plots can go in slides and look good
    plt.gcf().patch.set_alpha(0)
    # Default fig size
    plt.gcf().set_size_inches(*size)
    # Make figure fill whole PDF (otherwise figs have huge margins in LaTeX
    plt.tight_layout(
        pad=0,
    )
    plt.savefig(path, bbox_inches="tight")
    plt.clf()
    # Sets seaborn whitegrid on every plot for consistency (darkgrid is nice for slides)
    sns.set_style("whitegrid")


def addVerticalDates(minDate, maxDate):
    offsetDatesStart = 0
    offsetDatesEnd = 10
    datesBis = [
        np.datetime64("2022-04-01"),
        np.datetime64("2022-07-01"),
        np.datetime64("2022-10-01"),
        np.datetime64("2023-04-01"),
        np.datetime64("2023-07-01"),
        np.datetime64("2024-01-01"),
        np.datetime64("2024-04-01"),
        np.datetime64("2024-07-01"),
        np.datetime64("2025-10-01"),
        np.datetime64("2026-01-01"),
    ]
    for date in datesBis:
        if minDate > date:
            offsetDatesStart += 1
        if maxDate < date:
            offsetDatesEnd -= 1

    dates = [
        "2022Q2",
        "2022Q3",
        "2022Q4",
        "2023Q2",
        "2023Q3",
        "2024Q1",
        "2024Q2",
        "2024Q3",
        "2025Q4",
        "2026Q1",
    ]
    labels = ["❶", "❷", "❸", "❹", "❺", "❻", "❼", "❽", "❾", "❿"]

    dates = dates[offsetDatesStart:offsetDatesEnd]
    labels = labels[offsetDatesStart:offsetDatesEnd]

    for i in range(len(dates)):
        plt.axvline(dates[i], linestyle="-", linewidth=0.6, color="black")  # type: ignore
        # get converters and transform between graph unit to display unit
        xaxis = plt.gca().xaxis
        converter = xaxis.get_converter()
        unit_data = xaxis.get_units()
        xdisplay = converter.convert(dates[i], unit_data, xaxis)  # type: ignore

        plt.text(
            x=xdisplay,  # - 0.25,
            y=0.98,  # -0.033,
            s=labels[i],
            fontsize=12,
            transform=plt.gca().get_xaxis_transform(),
        )


def normalizeAPINames(apiName):
    return apiName.replace(" ", "-").lower()


def convertTicklabelsQuarters(labels):
    newLabels = []
    newLabels = [
        (
            f"{label.get_text()[-2:]}\n{label.get_text()[0:-2]}"
            if label.get_text()[-2:] == "Q1"
            else f"{label.get_text()[-2:]}"
        )
        for label in labels
    ]
    return newLabels
