import base64
from io import BytesIO

from matplotlib import pyplot as plt


def plot_to_markdown(fig: plt.Figure) -> str:
    """
    Convert a matplotlib plot to a markdown string.
    """
    buffer = BytesIO()
    fig.savefig(buffer, format="png")
    image_data = base64.b64encode(buffer.getvalue())

    return f"![img](data:image/png;base64,{image_data.decode()})"
