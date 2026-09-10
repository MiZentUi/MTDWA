import base64
import os
import tempfile
from decimal import Decimal
from io import BytesIO


def collect_property_type_stats(deals):
    type_stats = {}
    for deal in deals:
        key = deal.property.property_type.name
        type_stats.setdefault(key, {"count": 0, "total": Decimal("0.00")})
        type_stats[key]["count"] += 1
        type_stats[key]["total"] += deal.amount
    return sorted(type_stats.items(), key=lambda item: item[1]["count"], reverse=True)


def render_property_type_chart(stats):
    if not stats:
        return ""

    os.environ.setdefault("MPLCONFIGDIR", os.path.join(tempfile.gettempdir(), "matplotlib"))

    import matplotlib

    matplotlib.use("Agg")
    from matplotlib import pyplot as plt

    labels = [name for name, _payload in stats]
    counts = [payload["count"] for _name, payload in stats]
    totals = [payload["total"] for _name, payload in stats]
    colors = ["#285943", "#8d3c2f", "#3f6f8f", "#a66a2c", "#5d5a8f", "#6f655c"]
    bar_colors = [colors[index % len(colors)] for index in range(len(labels))]

    figure_height = max(3.2, min(8.0, 1.4 + len(labels) * 0.55))
    figure, axis = plt.subplots(figsize=(8.5, figure_height))
    bars = axis.barh(labels, counts, color=bar_colors)
    axis.invert_yaxis()
    axis.set_title("Сделки по видам недвижимости", pad=12)
    axis.set_xlabel("Количество сделок")
    axis.grid(axis="x", linestyle="--", alpha=0.25)
    axis.set_axisbelow(True)
    axis.spines["top"].set_visible(False)
    axis.spines["right"].set_visible(False)

    value_labels = [
        f"{count} шт. / {total.quantize(Decimal('1'))} BYN"
        for count, total in zip(counts, totals)
    ]
    axis.bar_label(bars, labels=value_labels, padding=6, fontsize=9)
    axis.margins(x=0.22)
    figure.tight_layout()

    buffer = BytesIO()
    figure.savefig(buffer, format="png", dpi=160, bbox_inches="tight")
    plt.close(figure)
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"
