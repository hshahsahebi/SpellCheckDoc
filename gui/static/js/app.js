var fuse;
var BreakException = {};
var corrections = {};
var ignored = [];
var error_codes = {
    'non_word': 2,
    'real_word': 3,
    'rw_ignored': 4,
    'case': 5
}

$(document).ready(function () {
    calculate_size();
    load_dictionary();
    $(window).resize(function() {
        calculate_size();
    });
    
    $('[data-toggle="tooltip"]').tooltip({placement: 'left'});
});

$(document).on('click', '.text-input', text_focus);
$(document).on('blur', '.text-input', text_blur);
$(document).on('input', '#dic_search', update_dictionary_list);
$(document).on('click', '.spellcheck-btn', spellcheck);

$('.text-input').on('input', function () {
    var text = this.textContent,
        count = text.trim().replace(/\s+/g, ' ').split(' ').length;
    
    if(text.trim().length > 0){
        $('.status-bar-text').text('Word Count: ' + count);
    }
    else{
        $('.status-bar-text').text('Status bar...');
    }
});

$(document).on('click', '.suggest, .highlight', function(){
    var index = $(this).data('index');

    $('.replacements').remove();
    $('highlight.active, suggest.active').removeClass('active');

    if($('.suggest.active').length > 0){
        $('.suggest.active').removeClass('active');
    }
    if($('.highlight.active').length > 0){
        $('.highlight.active').removeClass('active');
    }

    $('[data-index="' + index + '"]').addClass('active');
    show_suggestion_dropdown(index);
    if(document.querySelector('.text-input [data-index="' + index + '"]')){
        document.querySelector('.text-input [data-index="' + index + '"]').scrollIntoView({
            behavior: "smooth",
            block: "center"
        });
    }
});

document.querySelector('.text-input').addEventListener('keydown', function(event) {
    $('.replacements').remove();
    $('highlight.active, suggest.active').removeClass('active');

    if (event.which == 8) {
        s = window.getSelection();
        r = s.getRangeAt(0)
        el = r.startContainer.parentElement
        if (el.classList.contains('highlight')) {
            if (r.startOffset == r.endOffset && r.endOffset == el.textContent.length) {
                event.preventDefault();
                el.remove();
                return;
            }
        }
    }
});

$(document).on('click', '.replace-instance', function(){
    var index = $(this).parents('.highlight').data('index');
    var word = $(this).children('.replace-word').text();

    var pattern = '<span\\sdata\-index\\=\\"' + index + '.+?<\\/span>';
    var re = new RegExp(pattern, "gi");
    text = $('.text-input').html();
    
    if(findings = text.match(re)){
        findings.forEach(instance => {
            text = text.replace(instance, word);
        });

        $('[data-index="' + index + '"]').remove();
        $('.text-input').html(text);
    }
});

$(document).on('click', '.add-to-dictionary', function(){
    var index = $(this).parents('.suggest.active').data('index');

    if(typeof corrections[index] != "undefined"){
        $.ajax({
            url: '/add_to_dic',
            type: 'POST',
            data: {
                word: corrections[index].word, 
                word_pos: corrections[index].pos, 
                prev_word: corrections[index].prev_word,
                prev_word_pos: corrections[index].prev_pos,
                next_word: corrections[index].next_word,
                next_word_pos: corrections[index].next_pos,
            },
            beforeSend: function(){
                $('.status-bar-suggestion').html('Adding <b>' + corrections[index].word + '</b> to dictionary');
            },
            error: function(){
                $('.status-bar-suggestion').html('Failed to add the word!');
            },
            success: function(resp){
                if(resp == 'success'){
                    var pattern = '<span\\sdata\-index\\=\\"' + index + '.+?<\\/span>';
                    var re = new RegExp(pattern, "gi");
                    text = $('.text-input').html();
                    if(findings = text.match(re)){
                        findings.forEach(instance => {
                            text = text.replace(instance, corrections[index].word);
                        });
                
                        $('[data-index="' + index + '"]').remove();
                        $('.text-input').html(text);
                        $('.status-bar-suggestion').html('<b>' + corrections[index].word + '</b> added successfully.');
                    }
                }
                else{
                    $('.status-bar-suggestion').html('Failed to add the word!');
                }
            }
        });
    }
    else{
        $('.status-bar-suggestion').html('Failed to add the word!');
    }
});

$(document).on('click', '.ignore-suggestion', function(){
    var index = $(this).parents('.suggest.active').data('index');

    if(typeof corrections[index] != "undefined"){
        var pattern = '<span\\sdata\-index\\=\\"' + index + '.+?<\\/span>';
        var re = new RegExp(pattern, "gi");
        text = $('.text-input').html();
        if(findings = text.match(re)){
            findings.forEach(instance => {
                text = text.replace(instance, corrections[index].word);
            });
    
            $('[data-index="' + index + '"]').remove();
            $('.text-input').html(text);
            ignored.push(index);
        }
    }
    else{
        $('.status-bar-suggestion').html('Failed!');
    }
});

function text_focus(){
    var default_text = 'start typing...';
    var actual_text = $('.text-input').text().trim();

    if(default_text == actual_text.toLowerCase()){
        $('.text-input').text('');
        $('.text-input').css('font-size', '20px');
        $('.text-input').css('color', '#444');
    }
}

function text_blur(){
    var actual_text = $('.text-input').text().trim();

    if(actual_text.length == 0){
        $('.text-input').text('Start typing...');
        $('.text-input').css('font-size', '24px');
        $('.text-input').css('color', '#999');
    }
}

function calculate_size(){
    var footer_size = $('footer').innerHeight();
    var status_size = $('.status-bar').innerHeight();
    var window_size = window.innerHeight;

    boxes_size = window_size - footer_size - status_size - 5;

    $('.text-input, .suggestions, .dictionary').css('height', boxes_size + 'px')
    $('.text-input, .suggestions, .dictionary').css('overflow-y', 'auto')
}

function load_dictionary(){
    $.ajax({
        url: '/dictionary',
        dataType: 'JSON',
        beforeSend: function(){
            $('.dictionary-word-list').html('<div class="mt-2 loading"><i class="fas fa-spinner fa-spin"></i> Words are loading...</div>');
            $('.status-bar-dictionary').text('Loading...');
        },
        error: function(){
            $('.dictionary-word-list').text('');
            var reload = '<a href="javascript:;" onclick="load_dictionary()"><i class="fas fa-redo-alt"></i> Reload</a>';
            $('.status-bar-dictionary').html('Failed to load! ' + reload);
        },
        success: function(result){
            $('.status-bar-dictionary').html('<i class="fas fa-check text-success"></i> ' + result.dictionary.length + ' Words loaded!');
            fuse = new Fuse(result.dictionary, {
                shouldSort: true,
                threshold: 0.15,
                location: 0,
                distance: 5,
                keys: ["word"]
            });

            update_dictionary_list(result.common_words);
        }
    });
}

function update_dictionary_list(word){
    if(Array.isArray(word)){
        words = word;
    }
    else if(typeof word != "string"){
        words = fuse.search($('#dic_search').val());
    }
    else{
        words = fuse.search(word);
    }

    counter = 1;
    $('.dictionary-word-list').html('');

    try{
        words.forEach(elem => {
            $('.dictionary-word-list').append('<div>' + elem.word + '</div>');
            if(counter++ == 11) throw BreakException;
        });
    } catch(e){
        if (e !== BreakException) throw e;
    }
}

function spellcheck(){
    text = $('.text-input').html();
    var tmp = document.createElement("DIV");
    tmp.innerHTML = text.replace(/<br>/gi, " ");
    text = tmp.textContent || tmp.innerText || "";
    $('.replacements').remove();

    if(text.trim().length == 0){
        $('.suggest-list').text('');
        $('.status-bar-suggestion').text('There is nothing to check!');
    }
    else{
        $.ajax({
            url: '/spellcheck',
            type: 'POST',
            dataType: 'JSON',
            data: {text: text},
            beforeSend: function(){
                $('.suggest-list').html('<div class="mt-2 loading"><i class="fas fa-spinner fa-spin"></i> Checking the text...</div>');
                $('.status-bar-suggestion').html('<i class="fas fa-search"></i> Processing the text...');
                $('.process-duration').remove();
                $('.processed-words').remove();
            },
            error: function(){
                $('.suggest-list').text('');
                var retry = '<a href="javascript:;" onclick="spellcheck()"><i class="fas fa-redo-alt"></i> Retry</a>';
                $('.status-bar-suggestion').html('Failed to check! ' + retry);
            },
            success: function(resp){
                $('.suggest-list').text('');
                
                $('.status-bar-text').append('<span class="processed-words"> (processed: ' + resp.processed_words + ')</span>');
                $('.status-bar-text').append('<span class="process-duration float-right"><i class=""></i> ~' + resp.duration + ' seconds</span>');

                prepare_suggestions(resp.corrections);
                show_suggestions();
            }
        })
    }
}

function prepare_suggestions(records){
    corrections = {};
    all_suggestions = 0;
    ignored_numbers = 0;

    records.forEach(function(record, rec_index){
        word = record.word[0];
        prev_word = record.prev_word[0];
        end_sent_err = false;
        start_sent_err = false;

        if(word.toLowerCase() == '|endsent|'){
            word = record.prev_word[0];
            end_sent_err = true;
        }
        if(prev_word.toLowerCase() == '|startsent|'){
            start_sent_err = true;
        }

        pattern_word = word.replace(/[\+\*\{\}\[\]]/gi, '');
        pattern_prev_word = typeof prev_word == 'string' ? prev_word.replace(/[\+\*\{\}\[\]]/gi, '') : null;
        stopwords_pattern = '[\\s\\,\\.\\?\\!]+';
        highlight_pattern = '(<\/span>)?';

        if(pattern_prev_word && !end_sent_err && !start_sent_err){
            pattern = pattern_prev_word + highlight_pattern + stopwords_pattern + pattern_word;
        }
        else if(end_sent_err && start_sent_err){
            pattern = highlight_pattern + '(' + stopwords_pattern + '|^)' + pattern_word + '(' + stopwords_pattern + '|$)';
        }
        else if(end_sent_err){
            pattern = pattern_word + '(' + stopwords_pattern + '|$)';
        }
        else if(start_sent_err){
            pattern = '(' + stopwords_pattern + '|^)' + pattern_word;
        }

        active_error = null;
        message = null;
        title = null;
        
        switch(record.status){
            case error_codes['non_word']:
                active_error = 'non_word';
                title = '<b>' + word + '</b> - check the spelling';
                message = 'The word <b>' + word + '</b> is not in our dictionary. ' + 
                    'If the spelling is correct, you can add it to the dictionary.';
                break;

            case error_codes['real_word']:
                active_error = 'real_word';
                title = '<b>' + word + '</b> - check the position';
                if(start_sent_err){
                    message = 'The word <b>' + word + 
                        '</b> does not seem a proper candidate for starting the sentence.';
                }
                else if(end_sent_err){
                    message = 'The word <b>' + word + 
                        '</b> does not seem a proper candidate to end the sentence.';
                }
                else{
                    message = 'The word <b>' + word + 
                        '</b> seems inappropriate in the correct place.';
                }
                break;

            case error_codes['rw_ignored']:
                active_error = 'rw_ignored';
                title = '<b>' + word + '</b> - double check the position';
                message = 'Although the word <b>' + word + 
                    '</b> seems in a right position based on its type, you may want to revise it.';
                break;

            case error_codes['case']:
                active_error = 'case';
                title = '<b>' + word + '</b> - check the case';
                message = 'The word <b>' + word + '</b> may have a case error. Consider reviewing the word';
        }

        if(active_error != null){
            index = word.toLowerCase() + '_' + record.prev_word[0].toLowerCase();

            if(ignored.indexOf(index) < 0 && (typeof corrections[index] == "undefined" || 
                corrections[index].error_code > record.status)){

                next_elem = (typeof records[rec_index + 1] != "undefined") ? records[rec_index + 1] : null;
                next_word = (next_elem) ? next_elem.word[0] : '|ENDSENT|';
                next_pos = (next_elem) ? next_elem.word[1] : '|ENDSENT|';
                    
                corrections[index] = {
                    'word': word,
                    'prev_word': record.prev_word[0],
                    'next_word': next_word,
                    'pos': record.word[1],
                    'prev_pos': record.prev_word[1],
                    'next_pos': next_pos,
                    'error_code': record.status,
                    'error': active_error,
                    'title': title,
                    'message': message,
                    'pattern': pattern,
                    'is_start': start_sent_err,
                    'is_end': end_sent_err,
                    'suggestions': record.suggestions
                }

                all_suggestions++;
            }
            else if(ignored.indexOf(index) >= 0){
                ignored_numbers++;
            }
        }
    });
    
    notif = (all_suggestions == 0) ? 'No issues found' : 
        ('<span class="badge badge-info suggestions-count">' + all_suggestions + '</span> suggestion(s)');
    $('.status-bar-suggestion').html('<i class="fas fa-check text-success"></i> ' + notif);

    if(ignored_numbers > 0){
        $('.status-bar-suggestion').append(' | <span class="badge badge-warning">' + 
            ignored_numbers + '</span> Ignored');
    }
}

function show_suggestions(){
    passage = trim_highlight_tags($('.text-input').html());
    suggest_elements = '';
    highlighted_text = '';
    available_suggestions = 0;

    for(correction in corrections){
        data = corrections[correction];
        add_it = false;

        highlight_element = 
            '<span data-index="' + correction + '" class="highlight error_' + data.error + '">' +
                data.word + '</span>';

        re = new RegExp(data.pattern, "gi");
        findings = passage.match(re);

        if(findings){
            findings.forEach(finding => {
                if(typeof finding == 'string'){
                    new_phrase = finding.replace(data.word, highlight_element);
                    prev_passage = passage;
                    passage = passage.replace(finding, new_phrase);

                    if(passage != prev_passage){
                        add_it = true;
                    }
                }
            });

            if(add_it){
                suggest_elements += 
                    '<div class="suggest error_' + data.error + '" data-index="' + correction + '">' + 
                        '<i class="ignore-suggestion far fa-bell-slash" data-toggle="tooltip" title="Ignore"></i>' + 
                        '<i class="add-to-dictionary fas fa-folder-plus" data-toggle="tooltip" title="Add to Dictionary"></i>' + 
                        '<h3 class="suggest_title">' + data.title + '</h3>' +
                        '<p class="suggest-message">' + data.message + '</p>' + 
                    '</div>';
                available_suggestions++;
            }
        }
    }

    $('.suggest-list').html(suggest_elements);
    $('.text-input').html(passage);
    $('.suggestions-count').text(available_suggestions);
}

function trim_highlight_tags(text){
    markups = text.match(/<span.*?class\=.+?highlight.+?<\/span>/gi);

    if(markups){
        markups.forEach(markup => {
            word = markup.match(/\>.+\</gi);
            word = word[0].substring(1, word[0].length - 1);
            text = text.replace(markup, word);
        });
    }

    return text;
}

function show_suggestion_dropdown(index){
    elem = '<div class="replacements" contenteditable="false">';

    if(typeof corrections[index] == "undefined" || !Array.isArray(corrections[index].suggestions) || 
        corrections[index].suggestions.length == 0){
        elem += 
            '<div class="no-instance">' + 
            '<i class="far fa-sad-tear"></i> No suggestion available' +
            '</div>';
    }
    else{
        corrections[index].suggestions.forEach(suggest => {
            for(replace in suggest){
                elem += 
                '<div class="replace-instance">' + 
                '<label class="replace-distance">' + suggest[replace] + '</label>' + 
                '<label class="replace-word">' + replace + '</label>' + 
                '</div>';
            }
        });
    }

    elem += '</div>';

    $('.highlight[data-index="' + index + '"]').append(elem);
}