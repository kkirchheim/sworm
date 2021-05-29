from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from .forms import CustomUserCreationForm
from .models import Article, Journal, CustomUser
from django.contrib.auth.decorators import login_required
from bokeh.plotting import figure
from datetime import date
from bokeh.models import ColumnDataSource
from bokeh.models import TextInput, DateRangeSlider, Div, CustomJS, TapTool, RangeSlider, MultiSelect
from bokeh.layouts import column, row
from bokeh.models.widgets import Tabs, Panel
from bokeh.embed import components
from .bokeh_helpers import map_create_hover_tool, map_create_color_mapper
import time
from sworm.bokeh_data import df, topic_list, journal_list, country_list
import sworm.bokeh_callbacks as cb
from sklearn import svm
from sklearn import neighbors
from os.path import join, abspath, dirname, exists
import pickle
import pandas as pd

import numpy as np
import logging

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

data_dir = join(abspath(join(dirname(__file__), "..")), "data")


class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'registration/signup.html'


def create_kdtree():
    path = join(data_dir, "django-theta.pkl")
    df_theta = pd.read_pickle(path)
    X = np.array(df_theta.values)

    df_theta.reset_index(inplace=True)
    df_theta["index"] = df_theta["index"].apply(lambda x: int(x.replace("SCOPUS_ID:", "")))
    df_theta.set_index("index", inplace=True)

    log.info(df_theta.index)
    tree = neighbors.KDTree(X)
    return tree


tree = create_kdtree()


def articles_view(request, id):
    article = Article.objects.get(id=id)

    path = join(data_dir, "django-theta.pkl")
    df_theta = pd.read_pickle(path)
    df_theta.reset_index(inplace=True)
    df_theta["index"] = df_theta["index"].apply(lambda x: int(x.replace("SCOPUS_ID:", "")))
    df_theta.set_index("index", inplace=True)

    query_x = df_theta.loc[int(id)]
    dist, ind = tree.query([query_x], k=6)

    similar_articles = []

    for i in df_theta.iloc[ind[0][1:]].index:
        log.info(f"Found {i}")
        sim = Article.objects.filter(id=i).get()
        similar_articles.append(sim)

    return render(
        request, 'article.html', {'article': article, "similar_articles": similar_articles, "active": "library"})


def journal_view(request, issn):
    journal = Journal.objects.get(issn=issn)
    n_articles = Article.objects.filter(journal=journal).count()

    articles = Article.objects.order_by("id")[:10]

    return render(
        request, 'journal.html', {'journal': journal, 'n_articles': n_articles, "articles": articles})


@login_required
def fit_recommender_user(request):
    """
    Fitting SVM recommender for single user
    """
    path = join(data_dir, "django-theta.pkl")
    df_theta = pd.read_pickle(path)
    X = np.array(df_theta.values)

    df_theta.reset_index(inplace=True)
    df_theta["index"] = df_theta["index"].apply(lambda x: x.replace("SCOPUS_ID:", ""))
    df_theta.set_index("index", inplace=True)

    fit_recommender(X, data_dir, df_theta, request.user)

    return redirect(library_view)


@login_required
def fit_recommender_all_users(request):
    if not request.user.is_superuser:
        log.error(f"Illegal Access")

    users = CustomUser.objects.order_by("id")
    log.info(f"Training for {len(users)} users")

    data_dir = join(abspath(join(dirname(__file__), "..")), "data")
    path = join(data_dir, "django-theta.pkl")
    df_theta = pd.read_pickle(path)
    X = np.array(df_theta.values)

    df_theta.reset_index(inplace=True)
    df_theta["index"] = df_theta["index"].apply(lambda x: x.replace("SCOPUS_ID:", ""))
    df_theta.set_index("index", inplace=True)

    for user in users:
        fit_recommender(X, data_dir, df_theta, user)

    return redirect(library_view)


def fit_recommender(X, data_dir, df_theta, user):
    """
    https://github.com/karpathy/arxiv-sanity-preserver/blob/master/buildsvm.py
    """
    t0 = time.time()
    ids = [str(article.id) for article in user.articles.order_by("id")]
    log.info(f"Identifiers: {ids}")
    log.info(df_theta.index)
    saved = df_theta.index.isin(ids)
    y = np.array(saved).astype(np.uint8)
    log.info(np.unique(y))
    clf = svm.SVC(class_weight='balanced', verbose=False, max_iter=100000, tol=1e-6, C=0.1)
    clf.fit(X, y)
    scores = clf.decision_function(X)
    path = join(data_dir, "svm", f"{user.id}-scores.pkl")
    with open(path, "wb") as f:
        log.info(f"Writing to {path}")
        pickle.dump(scores, f)
    t1 = time.time()
    log.info(f"Fitting took {t1 - t0} s")


def impress_view(request):
    return render(request, 'impress.html', {"active": "impress"})


def map_view(request):
    log.info(f"Loading data...")
    t1 = time.perf_counter()

    d = df.copy()
    d.index.rename("index", inplace=True)
    d.index = d.reset_index()["index"].apply(lambda x: x.replace("SCOPUS_ID:", ""))

    source = ColumnDataSource(d)
    log.info(f"Loading took: {time.perf_counter() - t1} s")
    t2 = time.perf_counter()

    color_mapper = map_create_color_mapper(topic_list)
    hover = map_create_hover_tool()

    plot = figure(plot_width=1800, plot_height=1000,
                  tools=[hover, 'pan', 'wheel_zoom', 'box_zoom', 'reset', 'save', 'tap'],
                  title=None, toolbar_location="above")

    renderer = plot.scatter(source=source, x="x1", y="x2", size=5, fill_color=color_mapper, line_alpha=0.3,
                            line_color="gray", legend_field="cluster")

    log.info(renderer)

    div_info = Div(text="Click on an article for details.", height=150)
    callback_selected = CustomJS(args=dict(source=source, current_selection=div_info), code=cb.selected_code())
    taptool = plot.select(type=TapTool)
    taptool.callback = callback_selected

    # other interactive components

    input_callback = cb.input_callback(source)

    text_search = TextInput(title="Search:")
    text_search.js_on_change("value", input_callback)

    text_cout_label = Div(text="Displayed Documents:", height=25)
    text_count = Div(text=f"{len(df)}", height=25)

    date_range_slider = DateRangeSlider(
        title="Publication Date",
        value=(date(1960, 1, 1), date.today()),
        start=date(1960, 1, 1),
        end=date.today(),
        step=1)

    date_range_slider.js_on_change("value", input_callback)

    citation_count_slider = RangeSlider(
        title="Citation Count",
        value=(0, df["citations"].max()),
        start=0,
        end=df["citations"].max(),
        step=1
    )
    citation_count_slider.js_on_change("value", input_callback)

    journal_choice = MultiSelect(value=journal_list, options=journal_list, size=25)
    journal_choice.js_on_change("value", input_callback)

    topic_choice = MultiSelect(value=topic_list, options=topic_list, size=25)
    topic_choice.js_on_change("value", input_callback)

    country_choice = MultiSelect(value=country_list, options=country_list, size=25)
    country_choice.js_on_change("value", input_callback)

    # pass call back arguments
    input_callback.args["text_search"] = text_search
    input_callback.args["date_range_slider"] = date_range_slider
    input_callback.args["journal_choice"] = journal_choice
    input_callback.args["text_count"] = text_count
    input_callback.args["topic_choice"] = topic_choice
    input_callback.args["citation_count_slider"] = citation_count_slider
    input_callback.args["country_choice"] = country_choice

    # non interactive components
    # title = Div(text="<h1>SWORM - Social Work Research Map</h1>")
    filter_title = Div(text="<h2>Filter</h2>")
    selection_title = Div(text="<h2>Selection</h2>")

    # styling
    plot.sizing_mode = "scale_both"
    plot.margin = 5
    plot.legend.visible = True
    plot.legend.spacing = -7
    plot.legend.label_text_font_size = "10px"
    # plot.legend.orientation = "horizontal"
    # plot.legend.location = "top_center"

    plot.toolbar.autohide = True
    # plot.legend.click_policy="hide"
    plot.add_layout(plot.legend[0], 'right')
    plot.toolbar.logo = None

    # layout
    info_column = column([
        selection_title,
        div_info
    ])

    journal_pane = Panel(child=journal_choice, title="Journals")
    topic_pane = Panel(child=topic_choice, title="Topics")
    country_pane = Panel(child=country_choice, title="Countries")
    tab = Tabs(tabs=[journal_pane, topic_pane, country_pane])

    filter_column = column([
        filter_title,
        row([text_cout_label, text_count]),
        text_search,
        date_range_slider,
        citation_count_slider,
        tab
    ])

    content = row([filter_column, plot, info_column])
    layout = column([content], name="main")
    layout.sizing_mode = "scale_both"

    log.info(f"Creating document took {time.perf_counter() - t2} s")
    t3 = time.perf_counter()

    log.info(f"Finished:  {time.perf_counter() - t3} s")

    script, div = components(layout)

    return render(
        request, 'map.html', {'script': script, 'div': div, "active": "map"})


@login_required
def library_view(request):
    articles = request.user.articles.order_by('id')

    recommended_articles = get_recommended_articles(request.user)

    template_params = {'articles': articles, "active": "library", "recommended": recommended_articles}
    return render(request, 'library.html', template_params)


def get_recommended_articles(user, n=10):
    data_dir = join(abspath(join(dirname(__file__), "..")), "data")

    path = join(data_dir, "svm", f"{user.id}-scores.pkl")
    # newly registered users will not have a svm
    if not exists(path):
        return []

    with open(path, "rb") as f:
        log.info(f"Loading scores from {path}")
        scores = pickle.load(f)

    path = join(data_dir, "django-theta.pkl")
    df_theta = pd.read_pickle(path)

    # FIXME: this will lead to too few results in some cases
    top_indexes = np.argsort(scores)[::-1][:100]
    log.info(top_indexes)
    log.info(scores[top_indexes])

    df_theta.reset_index(inplace=True)

    index = df_theta["index"].apply(lambda x: x.replace("SCOPUS_ID:", ""))
    top_ids = index[top_indexes]

    recommended_articles = []
    saved_articles = user.articles.order_by("id")

    for id in top_ids:
        recommendation = Article.objects.get(id=id)
        if recommendation in saved_articles:
            continue

        recommended_articles.append(recommendation)
        if len(recommended_articles) == n:
            break

    return recommended_articles


@login_required
def add_article_to_library(request, id):
    try:
        art = Article.objects.get(id=id)
        request.user.articles.add(art)
    except Article.DoesNotExist:
        log.error(f"Article with id '{id}' does not exist")

    return redirect(library_view)


@login_required
def remove_article_from_library(request, id):
    try:
        art = Article.objects.get(id=id)
        request.user.articles.remove(art)
    except Article.DoesNotExist:
        log.error(f"Article with id '{id}' does not exist")

    return redirect(library_view)


@login_required
def import_articles(request):
    """
    Populate database with data from Pandas Dataframe
    """

    if not request.user.is_superuser:
        log.error(f"import_articles(): Illegal Access")
        return render(request, 'library.html')

    path = join(data_dir, "django-data.pkl")
    log.info(f"Loading data from {path}")
    local_df = pd.read_pickle(path)

    # add all journals
    issns = local_df["journal-issn"].unique()
    log.info(f"Found {len(issns)} issns")
    for issn in issns:

        if type(issn) is not str:
            log.error(f"Found broken issn {issn}")
            return redirect(library_view)

        names = local_df[local_df["journal-issn"] == issn]["journal"].unique()
        log.info(f"Name {issn} -> {names}")
        assert len(names == 1)
        Journal.objects.create(
            issn=issn,
            name=names[0]
        )

    # add all articles
    for n, (index, article) in enumerate(local_df.iterrows()):
        log.info(f"Entry {index}: {n/len(local_df):.2%}")

        # date = datetime.datetime.strptime(article["date"], '%d.%m.%Y')
        ident = index.replace("SCOPUS_ID:", "")

        try:
            journal = Journal.objects.get(issn=article["journal-issn"])

            Article.objects.create(
                id=ident,
                title=article["title"],
                abstract=article["abstract"],
                publish_on=article["date"],
                authors=article["author"],
                lda_topics=article["topics"],
                journal=journal,
                citations=article["citations"],
                country=article["country"],
                doi=article["doi"],
                x1=article["x1"],
                x2=article["x2"],
            )
        except Journal.DoesNotExist:
            log.error(f"Missing Journal with issn: {article['journal-issn']}")

    log.warning(f"Import finished.")
    return redirect(library_view)


