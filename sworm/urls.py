from django.urls import path
from .views import (SignUpView, view_library, endpoint_populate_db, view_map, endpoint_save_article,
                    endpoint_unsave_article,
                    view_impress, view_articles, view_journal, endpoint_fir_all_recommender,
                    endpoint_fit_recommender, view_author)

urlpatterns = [
    path('signup/', SignUpView.as_view(), name='signup'),
    path('map/', view_map, name="map"),
    path('article/<int:id>', view_articles, name="article"),
    path('author/<int:id>', view_author, name="author"),
    path('journal/<str:issn>', view_journal, name="journal"),
    path('library/', view_library, name="library"),
    path('impress/', view_impress, name="impress"),

    # services
    path('add/<str:id>', endpoint_save_article, name="add_to_library"),
    path('remove/<str:id>', endpoint_unsave_article, name="remove_from_library"),

    # helpers for administration
    path('import/', endpoint_populate_db, name="import"),
    path('refit-all/', endpoint_fir_all_recommender, name="refit_all"),
    path('refit/', endpoint_fit_recommender, name="refit"),
]
