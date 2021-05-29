from bokeh.palettes import Turbo256, linear_palette
from bokeh.transform import factor_cmap
from bokeh.models import HoverTool


def map_create_color_mapper(topics):
    color_mapper = factor_cmap(
        field_name="cluster",
        palette=linear_palette(Turbo256, len(topics)),
        factors=topics,
    )
    return color_mapper


def map_create_hover_tool():
    hover = HoverTool(tooltips=[
        ("Title", '<div style="width:400px;">@title{safe}</div>'),
        ("Index", '@index{safe}'),
        ("Date", "@date{safe}"),
        ("Author(s)", "@author{safe}"),
        ("LDA Topics(s)", "@topics{safe}"),
        ("Journal", "@journal{safe}"),
        ("Citations", "@citations"),
        ("Country", "@country"),
        ("Abstract", '<div style="width:400px;">@abstract{safe}</div>'),  # wrap abstracts
        ("DOI", "@doi"),
    ], point_policy="follow_mouse")
    return hover
