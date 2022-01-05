import logging
import pickle
import time
from datetime import date
from os.path import abspath, dirname, exists, join

import numpy as np
import pandas as pd
from bokeh.embed import components
from bokeh.layouts import column, row
from bokeh.models import (
    ColumnDataSource,
    CustomJS,
    DateRangeSlider,
    Div,
    MultiSelect,
    RangeSlider,
    TapTool,
    TextInput,
)
from bokeh.models.widgets import Panel, Tabs
from bokeh.plotting import figure
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from sklearn import neighbors, svm

import sworm.bokeh_callbacks as cb
from sworm.bokeh_data import country_list, df, journal_list, topic_list

from .bokeh_helpers import map_create_color_mapper, map_create_hover_tool
from .forms import CustomUserCreationForm
from .models import Article, Author, Country, CustomUser, Journal

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

data_dir = join(abspath(join(dirname(__file__), "..")), "data")
django_nn_tfidf_file = join(data_dir, "nn-tfidf.pkl")
django_theta_file = join(data_dir, "django-theta.pkl")
django_tfidf_file = join(data_dir, "django-articles-tfidf.pkl")

nearest_neighbors_cache = pickle.load(open(django_nn_tfidf_file, "rb"))


class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy("login")
    template_name = "registration/signup.html"


def helper_load_thetas():
    df_theta = pd.read_pickle(django_theta_file)
    df_theta.reset_index(inplace=True)
    df_theta["index"] = df_theta["index"].apply(lambda x: int(x.replace("SCOPUS_ID:", "")))
    df_theta.set_index("index", inplace=True)
    return df_theta


def helper_load_tfidf():
    return pickle.load(open(django_tfidf_file, "rb"))


def view_author(request, id: int):
    author = Author.objects.get(id=id)

    return render(request, "author.html", {"author": author})


def view_articles(request, id: int):
    article = Article.objects.get(id=id)
    authors = article.authors.all()

    authors = [a.name for a in authors]

    similar_articles = []

    try:
        for i in nearest_neighbors_cache[id][1:]:
            sim = Article.objects.filter(id=int(i)).get()
            similar_articles.append(sim)
    except Exception as e:
        log.exception(e)

    return render(
        request,
        "article.html",
        {
            "article": article,
            "authors": authors,
            "similar_articles": similar_articles,
            "active": "library",
        },
    )


def view_journal(request, issn):
    journal = Journal.objects.get(issn=issn)
    n_articles = Article.objects.filter(journal=journal).count()

    articles = Article.objects.order_by("-citations")[:20]

    return render(
        request,
        "journal.html",
        {"journal": journal, "n_articles": n_articles, "articles": articles},
    )


@login_required
def endpoint_fit_recommender(request):
    """
    Fitting SVM recommender for single user
    """
    df_theta = helper_load_thetas()
    helper_fit_recommender(df_theta, request.user)
    return redirect(view_library)


@login_required
def endpoint_fir_all_recommender(request):
    if not request.user.is_superuser:
        log.error("Illegal Access")
        return redirect(view_library)

    users = CustomUser.objects.order_by("id")
    log.info(f"Training for {len(users)} users")

    df_theta = helper_load_thetas()

    for user in users:
        helper_fit_recommender(df_theta, user)

    return redirect(view_library)


def helper_fit_recommender(df_theta, user):
    """
    Fit SVM for a specific user, pass all articles though it and store the results

    Inspired by
    https://github.com/karpathy/arxiv-sanity-preserver/blob/master/buildsvm.py
    """
    t0 = time.time()
    ids = [article.id for article in user.articles.order_by("id")]
    log.info(f"Saved Articles for {user}: {ids}")
    if len(ids) == 0:
        log.info("Can not fit without articles.")
        return

    saved = df_theta.index.isin(ids)
    log.info(saved.sum())
    y = np.array(saved).astype(np.uint8)
    X = helper_load_tfidf()
    log.info(X.shape)
    log.info(y.shape)
    clf = svm.LinearSVC(class_weight="balanced", verbose=False, max_iter=10000, tol=1e-6, C=0.1)
    clf.fit(X, y)

    scores = clf.decision_function(X)
    helper_dump_recommends(user, scores)
    t1 = time.time()
    log.info(f"Fitting took {t1 - t0} s")


def helper_dump_recommends(user, scores):
    path = join(data_dir, "svm", f"{user.id}-scores.pkl")
    with open(path, "wb") as f:
        log.info(f"Writing recommender scores for {user} to {path}")
        pickle.dump(scores, f)


def view_impress(request):
    return render(request, "imprint.html", {"active": "imprint"})


def view_map(request):
    """
    Create the bokeh map and return required elements
    """
    log.info("Loading data...")
    t1 = time.perf_counter()

    d = df.copy()
    d.index.rename("index", inplace=True)
    d.index = d.reset_index()["index"].apply(lambda x: x.replace("SCOPUS_ID:", ""))

    source = ColumnDataSource(d)
    log.info(f"Loading took: {time.perf_counter() - t1} s")
    t2 = time.perf_counter()

    color_mapper = map_create_color_mapper(topic_list)
    hover = map_create_hover_tool()

    plot = figure(
        plot_width=1800,
        plot_height=1000,
        tools=[hover, "pan", "wheel_zoom", "box_zoom", "reset", "save", "tap"],
        title=None,
        toolbar_location="above",
    )

    renderer = plot.scatter(
        source=source,
        x="x1",
        y="x2",
        size=5,
        fill_color=color_mapper,
        line_alpha=0.3,
        line_color="gray",
        legend_field="cluster",
    )

    log.info(renderer)

    div_info = Div(text="Click on an article for details.", height=150)
    callback_selected = CustomJS(
        args=dict(source=source, current_selection=div_info), code=cb.selected_code()
    )
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
        value=(date(1959, 1, 1), date(2021, 9, 1)),
        start=date(1959, 1, 1),
        end=date(2021, 9, 1),
        step=1,
    )

    date_range_slider.js_on_change("value", input_callback)

    citation_count_slider = RangeSlider(
        title="Citation Count",
        value=(0, df["citations"].max()),
        start=0,
        end=df["citations"].max(),
        step=1,
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
    plot.add_layout(plot.legend[0], "right")
    plot.toolbar.logo = None

    # layout
    info_column = column([selection_title, div_info])

    journal_pane = Panel(child=journal_choice, title="Journals")
    topic_pane = Panel(child=topic_choice, title="Topics")
    country_pane = Panel(child=country_choice, title="Countries")
    tab = Tabs(tabs=[journal_pane, topic_pane, country_pane])

    filter_column = column(
        [
            filter_title,
            row([text_cout_label, text_count]),
            text_search,
            date_range_slider,
            citation_count_slider,
            tab,
        ]
    )

    content = row([filter_column, plot, info_column])
    layout = column([content], name="main")
    layout.sizing_mode = "scale_both"

    log.info(f"Creating document took {time.perf_counter() - t2} s")
    t3 = time.perf_counter()

    log.info(f"Finished:  {time.perf_counter() - t3} s")

    script, div = components(layout)

    return render(request, "map.html", {"script": script, "div": div, "active": "map"})


@login_required
def view_library(request):
    articles = request.user.articles.order_by("id")

    recommended_articles = helper_get_recommends(request.user)

    template_params = {
        "articles": articles,
        "active": "library",
        "recommended": recommended_articles,
    }
    return render(request, "library.html", template_params)


def helper_get_recommends(user, n=10):
    """
    Load article scores from file, select top n results, find their scopus ids and return
    matching entries from the database
    """
    data_dir = join(abspath(join(dirname(__file__), "..")), "data")

    path = join(data_dir, "svm", f"{user.id}-scores.pkl")
    # newly registered users will not have recommendations
    if not exists(path):
        return []

    with open(path, "rb") as f:
        log.info(f"Loading scores from {path}")
        scores = pickle.load(f)

    # FIXME: this will lead to too few results in some cases
    top_indexes = np.argsort(scores)[::-1][:100]
    log.info(f"Top indices: {top_indexes}")
    log.info(f"Top scores: {scores[top_indexes]}")

    # read thetas from disk, get ids of top x articles
    path = join(data_dir, "django-theta.pkl")
    df_theta = pd.read_pickle(path)
    df_theta.reset_index(inplace=True)
    # TODO: we should not have to do this each time
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
def endpoint_save_article(request, id):
    try:
        art = Article.objects.get(id=id)
        request.user.articles.add(art)
    except Article.DoesNotExist:
        log.error(f"Article with id '{id}' does not exist")

    return redirect(view_library)


@login_required
def endpoint_unsave_article(request, id):
    try:
        art = Article.objects.get(id=id)
        request.user.articles.remove(art)
    except Article.DoesNotExist:
        log.error(f"Article with id '{id}' does not exist")

    return redirect(view_library)


@login_required
def endpoint_populate_db(request):
    """
    Populate database with data from Pandas Dataframe
    """

    if not request.user.is_superuser:
        log.error("import_articles(): Illegal Access")
        return render(request, "library.html")

    path = join(data_dir, "django-data.pkl")
    log.info(f"Loading data from {path}")
    local_df = pd.read_pickle(path)
    log.info(df.columns)

    # add all authors
    idx = ~(df["author"].isna() | df["author-id"].isna())
    author_name_map = {}
    for _, (author_names, author_ids) in df[idx][["author", "author-id"]].iterrows():
        # TODO: change export formaty
        # convert
        author_names = author_names.split(",")
        author_names = [name.strip() for name in author_names]

        log.info(author_ids)
        author_ids = [int(ident) for ident in author_ids]

        for author_name, author_id in zip(author_names, author_ids):
            if author_id in author_name_map:
                actual_name = author_name_map[author_id]
                if actual_name != author_name:
                    log.warning(
                        f"Wrong author name mapping: {author_id} -> '{author_name}' but is '{actual_name}'"
                    )
            else:
                author_name_map[author_id] = author_name
                log.info(f"Author Name {author_id} -> {author_name}")
                author = Author.objects.create(id=author_id, name=author_name)
                author.save()

    # add all journals
    issns = local_df["journal-issn"].unique()
    log.info(f"Found {len(issns)} issns")
    for issn in issns:
        if type(issn) is not str:
            log.error(f"Found broken issn {issn}")
            return redirect(view_library)

        names = local_df[local_df["journal-issn"] == issn]["journal"].unique()
        log.info(f"Journal Name {issn} -> {names}")
        assert len(names == 1)
        Journal.objects.create(issn=issn, name=names[0])

    # create countries
    countries = local_df["country"].unique()
    for country in countries:
        Country.objects.create(name=country)

    # add all articles
    for n, (index, article) in enumerate(local_df.iterrows()):
        log.info(f"Entry {index}: {n/len(local_df):.2%}")

        # date = datetime.datetime.strptime(article["date"], '%d.%m.%Y')
        ident = index.replace("SCOPUS_ID:", "")

        try:
            journal = Journal.objects.get(issn=article["journal-issn"])
            country = Country.objects.get(name=article["country"])

            entry = Article.objects.create(
                id=ident,
                title=article["title"],
                abstract=article["abstract"],
                publish_on=article["date"],
                lda_topics=article["topics"],
                journal=journal,
                citations=article["citations"],
                country=country,
                doi=article["doi"],
                x1=article["x1"],
                x2=article["x2"],
            )

            entry.save()

            authors = article["author-id"]
            if type(authors) is list:
                authors = [int(ident) for ident in authors]
                for ident in authors:
                    author = Author.objects.get(id=ident)
                    log.info(f"Adding author: {author}")
                    entry.authors.add(author)
            entry.save()

        except Journal.DoesNotExist:
            log.error(f"Missing Journal with issn: {article['journal-issn']}")

    log.warning("Import finished.")
    return redirect(view_library)
