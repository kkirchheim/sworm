from bokeh.models import CustomJS


def input_callback(source):
    """
    slider call back for date selection, keyword search and cluster selection
    """

    callback = CustomJS(
        args=dict(source=source),
        code="""
        var data = source.data;
        var x1 = data['x1'];
        var x2 = data['x2'];
        var x1_backup = data['x1_backup'];
        var x2_backup = data['x2_backup'];
        var timestamp = data['timestamp'];

        var abstract = data['abstract'];
        var title = data['title'];
        var author = data['author'];
        var journal = data['journal'];
        var label = data['journal'];
        var topic = data['cluster'];
        var citations = data['citations'];
        var country = data['country'];

        var lower_date = date_range_slider.value[0];
        var upper_date = date_range_slider.value[1];
        var key = text_search.value;
        var journal_select = journal_choice.value;
        var topic_select = topic_choice.value;
        var country_select = country_choice.value;

        var lower_citation = citation_count_slider.value[0];
        var upper_citation = citation_count_slider.value[1];

        var found = 0;

        for (var i = 0; i < x1.length; i++) {
            var select_text = true;

            if(key != "") {
                select_text = abstract[i].toLowerCase().includes(key.toLowerCase())
                    || title[i].toLowerCase().includes(key.toLowerCase())
                    || author[i].toLowerCase().includes(key.toLowerCase())
                    || journal[i].toLowerCase().includes(key.toLowerCase());
            }

            var select_journal = journal_select.includes(journal[i]);
            var select_topic = topic_select.includes(topic[i]);
            var select_country = country_select.includes(country[i]);
            var select_date = timestamp[i] >= lower_date && timestamp[i] <= upper_date;
            var select_citations = citations[i]  >= lower_citation && citations[i] <= upper_citation;

            if(select_date && select_text && select_journal && select_topic && select_citations && select_country) {
                x1[i] = x1_backup[i];
                x2[i] = x2_backup[i];
                found++;
            } else {
                x1[i] = undefined;
                x2[i] = undefined;
            }
        }
        text_count.text = String(found);
        source.change.emit();

    """,
    )
    return callback


def selected_code():
    """
    handle the currently selected article
    """

    code = """
            var titles = [];
            var authors = [];
            var journals = [];
            var links = [];
            var dates = [];
            var abstracts = [];
            var citations = [];
            var countries = [];
            var topics = [];
            var ids = [];

            cb_data.source.selected.indices.forEach(index => titles.push(source.data['title'][index]));
            cb_data.source.selected.indices.forEach(index => authors.push(source.data['author'][index]));
            cb_data.source.selected.indices.forEach(index => journals.push(source.data['journal'][index]));
            cb_data.source.selected.indices.forEach(index => links.push(source.data['doi'][index]));
            cb_data.source.selected.indices.forEach(index => countries.push(source.data['country'][index]));
            cb_data.source.selected.indices.forEach(index => dates.push(source.data['date'][index]));
            cb_data.source.selected.indices.forEach(index => abstracts.push(source.data['abstract'][index]));
            cb_data.source.selected.indices.forEach(index => citations.push(source.data['citations'][index]));
            cb_data.source.selected.indices.forEach(index => topics.push(source.data['topics'][index]));
            cb_data.source.selected.indices.forEach(index => ids.push(source.data['index'][index]));

            titles = "<b><a href='/article/" + ids[0].toString() + "'>" + titles[0].toString().replace(/<br>/g, ' ') + "</a></b><br>";
            authors = "<b>Authors:</b> " + authors[0].toString() + "<br>";
            var save_option = '<a class="btn btn-primary" href="/add/' + ids[0] + '">Add to Library</a><br>';
            dates = "<b>Published:</b> " + dates[0].toString() + "<br>";
            journals = "<b>Journal:</b> " + journals[0].toString() + "<br>";
            citations = "<b>Citations:</b> " + citations[0].toString() + "<br>";
            countries = "<b>Country:</b> " + countries[0].toString() + "<br>";
            topics = "<b>LDA Topic(s):</b> " + topics[0].toString() + "<br>";
            links = "<b>Link:</b> <a href='" + "https://doi.org/" + links[0].toString() + "'>" + "https://doi.org/"
                + links[0].toString() + "</a><br>";
            abstracts = "<p><b>Abstract: </b>" +  abstracts[0].toString() + "</p>";

            current_selection.text = titles  + dates + authors + topics + journals + citations + countries + links + abstracts + save_option;
            current_selection.change.emit();
    """
    return code
