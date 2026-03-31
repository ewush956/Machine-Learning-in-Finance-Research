# ########################################################
# #                      Imports                         #
# ########################################################
from matplotlib import rcParams

import matplotlib.pyplot as plt


# ##########################################################
# #                      Constants                         #
# ##########################################################
FIGURE_DPI = 90


# #####################################################################################
# #                      Dark/Light Mode Matplot Graph Themes                         #
# #####################################################################################
def apply_matplotlib_theme(color_mode: str) -> None:
    if color_mode == "dark":
        plt.style.use("dark_background")
        rcParams.update(
            {
                "figure.facecolor": "#2A2D31",
                "axes.facecolor": "#2A2D31",
                "axes.edgecolor": "#d0d0d0",
                "axes.labelcolor": "#e8e8e8",
                "text.color": "#e8e8e8",
                "xtick.color": "#d0d0d0",
                "ytick.color": "#d0d0d0",
                "grid.color": "#3a3a3a",
                "grid.alpha": 0.45,
                "axes.grid": True,
                "axes.spines.top": False,
                "axes.spines.right": False,
                "legend.frameon": False,
                "figure.dpi": FIGURE_DPI,
                "savefig.bbox": "tight",
            }
        )
    else:
        plt.style.use("default")
        rcParams.update(
            {
                "figure.facecolor": "white",
                "axes.facecolor": "white",
                "axes.edgecolor": "#222222",
                "axes.labelcolor": "#111111",
                "text.color": "#111111",
                "xtick.color": "#222222",
                "ytick.color": "#222222",
                "grid.color": "#d9d9d9",
                "grid.alpha": 0.7,
                "axes.grid": True,
                "axes.spines.top": False,
                "axes.spines.right": False,
                "legend.frameon": False,
                "figure.dpi": FIGURE_DPI,
                "savefig.bbox": "tight",
            }
        )
