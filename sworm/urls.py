from django.urls import path
from .views import (SignUpView, library_view, import_articles, map_view, add_article_to_library,
                    remove_article_from_library,
                    impress_view, articles_view, journal_view, fit_recommender_all_users,
                    fit_recommender_user)

urlpatterns = [
    path('signup/', SignUpView.as_view(), name='signup'),
    path('map/', map_view, name="map"),
    path('article/<int:id>', articles_view, name="article"),
    path('journal/<str:issn>', journal_view, name="journal"),
    path('library/', library_view, name="library"),
    path('impress/', impress_view, name="impress"),

    # services
    path('add/<str:id>', add_article_to_library, name="add_to_library"),
    path('remove/<str:id>', remove_article_from_library, name="remove_from_library"),

    # helpers for administration
    path('import/', import_articles, name="import"),
    path('refit-all/', fit_recommender_all_users, name="refit_all"),
    path('refit/', fit_recommender_user, name="refit"),
]
