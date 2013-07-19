$(document).ready(function(){
    // global variables
    window.story_id = window.location.pathname.slice(1);
    window.$my_vocab_tbody = $('#my_vocab #my_vocab_table tbody');

    
    // What to show if not logged in. isLoggedIn is defined in base.js
    if (!window.isLoggedIn) {
        $('div#vocab_area_container').html('<p>Log in to create your own personal vocabulary' + 
                                            ' list for this story ' +
                                            'and browse lists created by other students.</p>');
        $('div#right_tool_bar').hide();
        return false;
    }
    
    
    initVocabArea();
});


function initVocabArea(){
    var vocab_area = $('div#vocab_area_container').get(0);
    
    // keeps vocab_area scrolled down
    vocab_area.scrollTop = vocab_area.scrollHeight;
    
    initMyVocab(vocab_area);
    initUserVocab();
    initQandA();
    initComments();
    
    initRightToolBar(vocab_area);
}

function initMyVocab(vocab_area){
    var $add_vocab_form = $('#my_vocab form#add_vocab');
    var $error_msg = $('div#error_msg');
    var $input_new_word = $('input#new_word');
    var $input_new_def = $('input#new_def');
    
    buildVocabTools($add_vocab_form);
    buildVocabToolMenu($add_vocab_form);
    
    // normal mode
    function show_error(msg){
        $error_msg.html('<i class="icon-exclamation-sign"></i> ' + msg);
        $input_new_word.focus();
    }
    $add_vocab_form.submit(function(e){
        var active_tool = VocabTools.active_tool;
        
        if ($input_new_word.val().trim().length === 0 ||
            $input_new_def.val().trim().length === 0) {
            show_error('Both fields are required.');
        } 
        else if (active_tool && (active_tool.mode === 'edit') && !active_tool.chosen.length){
            // this would be better placed in edit_tool.bind_events somehow
            show_error('Please select something to edit or exit edit mode.');
        }
        else if (active_tool && (active_tool.mode !== 'edit')){
            alert('Somehow youre still in ' + active_tool.mode + ' mode.');
        }
        else {
            addVocab($add_vocab_form, active_tool); 
            $error_msg.html('');
        }
        
        e.preventDefault();
    });
    
    // keep it scrolled down after submitting or focusing to new_word
    $input_new_word.focus(function(){vocab_area.scrollTop = vocab_area.scrollHeight;});
}

function initUserVocab(){
    var $import_button = $('div#user_vocab button.import_chosen');
    var $user_vocab = $('div#user_vocab');
    var $pick_student = $user_vocab.children('div#pick_student');
    var $student_links = $pick_student.find('a');
    var $show_vocab = $user_vocab.children('div#show_vocab');
    var $back_to_students = $show_vocab.children('a#back_to_students');
    var $user_vocab_rows = $show_vocab.find('table.vocab_list').find('tr');
    var $user_vocab_select_all = $('div#show_vocab > div > a.select_all');
    var $success_msg = $show_vocab.find('span.success_message');
    
    $show_vocab.hide();
    
    // show the vocab of a student when picked
    $student_links.on('click', function(e){
        $pick_student.toggle();
        $show_vocab.toggle(); 
    });
    
    // go back to pick which student
    $back_to_students.on('click', function(e){
        if ($user_vocab_rows.hasClass('import_chosen')){
            var folytat = confirm("All selected words will be lost." + 
                                    "  Are you sure you want to continue?");
            if (!folytat){
                return false;
            }
        }
        $show_vocab.toggle();
        $pick_student.toggle();
        $user_vocab_rows.removeClass('import_chosen');
        
        e.preventDefault();
    });
    
    $user_vocab_rows.on({
        'mouseenter mouseleave': function(e){
            $(this).not('.import_chosen').toggleClass('import_highlight');
        },
        click: function(e){
            $(this).toggleClass('import_chosen').toggleClass('import_highlight');
        }
    });
    
    $import_button.on('click', function(e){
        var $chosen = $user_vocab_rows.filter('.import_chosen');
        if (!$chosen.length){
            alert('Please select some rows to import');
        } else {
            importVocab($chosen); // ajax
        }
        e.preventDefault();
    });
    
    $user_vocab_select_all.on('click', function(e){
        var $active_student = $($student_links.filter('.active').attr('href'));
        var $active_vocab = $active_student.find($user_vocab_rows);
        if ($(this).html() === 'select all'){
            $active_vocab.addClass('import_chosen');
            $(this).html('deselect all');
        } else if ($(this).html() === 'deselect all') {
            $active_vocab.removeClass('import_chosen');
            $(this).html('select all');
        }
        
        e.preventDefault();
    });
    
}

function initQandA(){
    var $questions = $('#QandA #questions');
    var $ask_question_form = $('#QandA form#ask_question');
    var $question = $ask_question_form.find('#question');
    
    // submit a new question
    $ask_question_form.submit(function(e){
        if ($question.val().trim().length === 0){ return false; }
        else {
            askQuestion($ask_question_form, $question);
        }
        e.preventDefault();
    });
    
    // show the answer form when clicking on "answer it!"
    $questions.on('click','a.answer_it', function(e){
        $(this).closest('.meta_Q').siblings('form.answer_question').toggle()
                .find('textarea.answer').focus();

        if ($(this).html() === 'answer it!' ){ $(this).html("don't answer it");}
        else {$(this).html('answer it!');}

        e.preventDefault();
    });
    
    // submit an answer to a question
    $questions.on('submit', 'form.answer_question', function(e){
        e.preventDefault();
        var $answer = $(this).children('.answer');
        if ($answer.val().length === 0){ return false; }
        else{
            var q_key_e = $(this).parents('.QA_container').attr('id');
            //ajax
            answerQuestion($(this), $answer, q_key_e);
        }
    });
    
    $questions.on('click', '.A_container a.thanks', function(e){
        
        // make sure they don't thank twice
        if ($(this).hasClass('clicked')){ return false; }
        
        //ajax
        incrementThanks($(this));
        
        e.preventDefault(); 
    });
    
    $questions.on('click', 'a.delete_question', function(e){
       var proceed = confirm('Are you sure you want to delete your question?');
       if (!proceed){ return false;}
       else{
           var $QA_container = $(this).closest('.QA_container');
           deleteQuestion($QA_container);
       }
       e.preventDefault(); 
    });
    
    $questions.on('click', 'a.delete_answer', function(e){
        var proceed = confirm('Are you sure you want to delete your answer?');
        if (!proceed){ return false;}
        else{
            var $A_container = $(this).closest('.A_container');
            deleteAnswer($A_container);
        }
        e.preventDefault();
    });
}

function initComments(){
    // what do i need here
    $('#comments form').submit(function(e){
        saveComments($(this));
        e.preventDefault();
    });
}

function initRightToolBar(vocab_area){
    var $tabs = $('#right_tool_bar ul a');
    var $hide_vocab = $('#right_tool_bar a#hide_vocab');
    
    $hide_vocab.click(function(e){
        $(vocab_area).toggle();
        if ($(this).html() === "Hide") {
            $(this).html("Show");
        } else {
            $(this).html("Hide");
        }
        e.preventDefault();
    });
    
    // turn off the active tool when navigating away
    $tabs.not('#my_vocab_link').click(function(e){
        var active = VocabTools.active_tool;
        if (active){ active.turn_off(); }
    });
}

function buildVocabTools($add_vocab_form){
    // creates global object VocabTools
     window.VocabTools = { active_tool: null};

    function VocabTool(name){
        this.mode = name;
        this.chosen = $();
        this.menu_link = $('#my_vocab_tools #tool_menu a#' + name + '_tool'); // maybe superfluous
        this.on_switch = this.menu_link.find('.on_switch');
        this.instructions = $('#instructions_container').children('div#' + name + '_instructions');
    
        this.hover_highlight = name + '_highlight';
        this.chosen_class = name + '_chosen';
        var self = this;

        this.add_to_VocabTools = function(){
            // once we've finished building each tool add it to window
            VocabTools[name + '_tool'] = this;
        };    
        this.at_turn_off = function(){ return true; };
        this.at_turn_on = function(){ return true; };
        this.at_bind_events = function(){ return true; };
        this.at_unbind_events = function(){ return true; };
        this.turn_off = function(){
            this.unbind_events();
            this.at_turn_off();
            
            this.deselect_all();
            this.on_switch.hide();
            this.instructions.hide();
            
            VocabTools.active_tool = null;
        };
        this.turn_on = function(){
            this.on_switch.show();
            this.instructions.show();
            this.at_turn_on(); // this is before bind_events for reorder to work
            this.bind_events();
            VocabTools.active_tool = this;
        };
        this.select_row = function($row){
            $row.addClass(self.chosen_class).removeClass(self.hover_highlight);
            this.chosen = this.chosen.add($row);
            return this;
        };
        this.select_all = function(){
            this.chosen = $my_vocab_tbody.children('tr').addClass(self.chosen_class);
        }
        this.deselect_row = function($row){
            $row.removeClass(self.chosen_class).addClass(self.hover_highlight);
            this.chosen = this.chosen.not($row);
            return this;
        };
        this.deselect_all = function(){
            this.chosen.removeClass(self.chosen_class);
            this.chosen = $();
            return this;
        };
        this.get_chosen_indices = function(){
            var indices = [];
            $my_vocab_tbody.children('tr').each(function(i){
                if ($(this).hasClass(self.chosen_class)){ indices.push(i); }
            });
            return indices;
        };
        this.bind_events = function(){
            $my_vocab_tbody.on('mouseenter mouseleave', 'tr', function(){
                $(this).not('.' + self.chosen_class).toggleClass(self.hover_highlight);
            });
            this.at_bind_events();
        };
        this.unbind_events = function(){
            $my_vocab_tbody.off('mouseenter mouseleave', 'tr');
            this.at_unbind_events();
        };

    };

    var edit_tool = new VocabTool('edit');
    var delete_tool = new VocabTool('delete');
    var reorder_tool = new VocabTool('reorder');
    
    edit_tool.submit_icon = $("#my_vocab #add_vocab button#submit_word i");
    edit_tool.at_turn_on = function(){this.submit_icon.removeClass("icon-plus").addClass("icon-edit");};
    edit_tool.at_turn_off = function(){this.submit_icon.removeClass("icon-edit").addClass("icon-plus");};
    edit_tool.at_bind_events = function(){
        var self = this;
        $my_vocab_tbody.on('click', 'tr', function(e){
            var hungarian = $(this).children().first().html();
            var meaning = $(this).children().first().next().html();
            self.deselect_all().select_row($(this));
            $add_vocab_form.children().first().val(hungarian).trigger('focus')
                                      .next().val(meaning);
        });

    };
    edit_tool.at_unbind_events = function(){
        $my_vocab_tbody.off('click', 'tr');
    };
    
    delete_tool.at_turn_on = function(){$add_vocab_form.hide();};
    delete_tool.at_turn_off = function(){$add_vocab_form.show();};
    delete_tool.at_bind_events = function(){
        var self = this;
        $my_vocab_tbody.on('click', 'tr', function(){
            var is_selected = $(this).hasClass(self.chosen_class);
            if (is_selected){ self.deselect_row($(this)); }
            else { self.select_row($(this)); }
        });
        self.instructions.children('a.select_all').on('click', function(e){
            if ($(this).html() == "select all") {
                self.select_all();
                $(this).html('deselect all');
            } 
            else if ($(this).html() == "deselect all"){
                self.deselect_all();
                $(this).html('select all');
            }
            e.preventDefault();
        });
        self.instructions.children('button#delete_selected').on('click', function(e){
            vl_indices = self.get_chosen_indices();
            if (!vl_indices.length){ 
                alert('Please select something to delete.');
                return false;
            } else {
                var proceed = confirm('Are you sure you want to delete these words?');
                if (proceed == true){ deleteVocab(vl_indices); } // ajax
            }
            e.preventDefault();
        });
    };
    delete_tool.at_unbind_events = function(){
        $my_vocab_tbody.off('click', 'tr');
        this.instructions.children('a.select_all').off('click');
        this.instructions.children('button#delete_selected').off('click');
    };
    
    reorder_tool.has_changes = false;
    reorder_tool.at_turn_on = function(){
        $add_vocab_form.hide();
        $my_vocab_tbody.sortable({disabled: false});
        $my_vocab_tbody.addClass('moveable');
    };
    reorder_tool.at_turn_off = function(){
        if (this.has_changes){ $my_vocab_tbody.sortable('cancel'); }
        $my_vocab_tbody.sortable('disable');
        $my_vocab_tbody.removeClass('moveable');
        this.has_changes = false;
        $add_vocab_form.show();
    };
    reorder_tool.at_bind_events = function(){
        var self = this;
        $my_vocab_tbody.on('sortupdate', function(e, ui){ self.has_changes = true; });
        self.instructions.children('button#reorder').on('click', function(e){
            if (!self.has_changes) { return false; }
            
            var keys_ordered = [];
            $my_vocab_tbody.children('tr').each(function(i){
                keys_ordered.push(this.id);
            });
            
            reorderVocab(keys_ordered); // ajax
            e.preventDefault();
        });
    };
    reorder_tool.at_unbind_events = function(){
        this.instructions.children('button#reorder').off('click');
        $my_vocab_tbody.off('sort_update');
    }
    
    // add each tool to VocabTools
    var tools = [edit_tool, delete_tool, reorder_tool];
    $.each(tools,function(i, tool){ tool.add_to_VocabTools(); });
}

function buildVocabToolMenu($add_vocab_form){
    // sets styling and basic functionality of the vocab tool menu
    
    var $my_vocab_tools = $("#my_vocab_tools");
    var $normal_instructions = $('div#normal_instructions');
    var $tools_button = $my_vocab_tools.find('button#tools_button');
    var $tool_menu = $my_vocab_tools.find("ul#tool_menu");
    
    function tools_button_and_instructions(){
        // $my_vocab_tools.hide();
        if ($my_vocab_tbody.children('tr').length) {
            $normal_instructions.hide();
            // $my_vocab_tools.show();
        } else {
            $add_vocab_form.one("submit", function(e){
                $normal_instructions.hide();
                // $my_vocab_tools.show();
            });
            $('#user_vocab #show_vocab button.import_chosen').one("click", function(e){
                $normal_instructions.hide();
                // $my_vocab_tools.show();
            });
        } 
        // when to show the tools button
        // $tools_button.hide();
        // $('div#vocab_area_container').on({
        //     mouseenter: function(e){$tools_button.show();},
        //     mouseleave: function(e){$tools_button.hide();},
        // });
        // when to show the tool_menu
        $tools_button.click(function(e){$tool_menu.show(); e.preventDefault();});
        // when to hide the tool_menu
        $my_vocab_tools.on({
            mouseenter: function(){$tools_button.css("color", "#28a875");},
            mouseleave: function(){$tool_menu.hide(); $tools_button.css("color", "lightgrey");}
        });
    }
    tools_button_and_instructions();
    
    // Switching modes via clicking
    var $menu_links = $tool_menu.find('a');
    $menu_links.on('click', function(e){
        var clicked = VocabTools[this.id];
        var active = VocabTools.active_tool;
        
        if (!active){ clicked.turn_on(); }
        else if (active.mode === clicked.mode){ clicked.turn_off(); }
        else { active.turn_off(); clicked.turn_on(); }
        
        e.preventDefault();
    });
}





// =================
// = Ajax Requests =
// =================

function addVocab($add_vocab_form, edit_tool){
    // REFACTORED and TESTED :)
    var vl_index = -1;
    var mode = 'normal';
    if (edit_tool){
        vl_index = edit_tool.chosen.index(); //number of rows before it
        mode = 'edit';
    }
    $.ajax({
        url: "/addvocab",
        type: "POST",
        data: $add_vocab_form.serialize() + '&story_id=' + story_id 
                    + '&mode=' + mode + '&vl_index=' + vl_index,
        dataType : "html",
        success: function( new_row ) {
            if (!edit_tool){
                $my_vocab_tbody.append(new_row);
            } else {
                edit_tool.chosen.replaceWith(new_row);
                edit_tool.chosen = $();
            }
            $add_vocab_form.children('input').val('');
        },
        error: function( xhr, status ) {alert( "Sorry, there was a problem!");},
        complete: function( xhr, status ) {$add_vocab_form.children('#new_word').focus();}
    });
}
    
function deleteVocab(vl_indices){
    // REFACTORED  :)
    $.ajax({
        url: "/deletevocab",
        type: "POST",
        data: $.param({'vl_indices': vl_indices, 'story_id': story_id }),
        success: function() {
            VocabTools.delete_tool.chosen.remove();
            VocabTools.delete_tool.chosen = $(); // maybe superfluous
        },
        error: function( xhr, status ) {alert( "Sorry, there was a problem!");}
    });
}

function reorderVocab(keys_ordered){
    // REFACTORED :)
    $.ajax({
        url: "/reordervocab",
        type: "POST",
        data: $.param({'keys': keys_ordered, 'story_id': story_id}),
        dataType: "html",
        success: function() {
            $('#reorder_instructions span.success_message').slideDown(200).delay(1000).fadeOut(400);
        },
        error: function( xhr, status) {alert( "Sorry, there was a problem!");},
        complete: function( xhr, status) {
            VocabTools.reorder_tool.has_changes = false;
        }
    });
}

function importVocab($chosen){
    
    var keys_to_add = []; // list of vocab keys encrypted
    $chosen.each(function(){
        keys_to_add.push(this.id);
    });
    // appends the keys to the students vocab list and adds the rows in the html
    $.ajax({
        url: "/importvocab",
        type: "POST",
        // the data to send (if object, will be converted to a query string)
        data: $.param({'keys': keys_to_add, 'story_id': story_id }),
        // the type of data we expect back
        dataType : "html",
        // the response is passed to the function
        success: function() {
            $chosen.removeClass('import_chosen')
                   .clone()
                   .appendTo($my_vocab_tbody);
            $('#user_vocab #show_vocab span.success_message').slideDown(200)
                                                         .delay(1000).fadeOut(200);
            $chosen = $();
        },
        error: function( xhr, status ) {alert( "Sorry, there was a problem!");},
        complete: function( xhr, status ) {}
    });
}

function askQuestion($ask_question_form, $question){
    $.ajax({
        url: "/askquestion",
        type: "POST",
        data: $ask_question_form.serialize() + '&story_id=' + story_id,
        success: function(new_question) {
            //prepend the new question to the list of questions
            $('#QandA div#questions').prepend(new_question);
            $question.val('');
        },
        error: function( xhr, status ) {alert( "Sorry, there was a problem!");}
    });
}

function deleteQuestion($QA_container){
    var q_key_e = $QA_container.attr('id');
    $.ajax({
        url: 'deletequestion',
        type: 'POST',
        data: $.param({ 'q_key_e': q_key_e, 'story_id': story_id }),
        success: function(){
            $QA_container.remove();
        },
        error: function(){
            alert( "Sorry, there was a problem!");
        },
    });
}

function answerQuestion($answer_form, $answer, q_key_e){
    // LESSON LEARNED: $.param is necessary when working with q_key_e. The encrypted key still
    // needs to be URL safe when sent back to the server.
    $.ajax({
        url: "/answerquestion",
        type: "POST",
        data: $.param({'answer': $answer.val(), 'story_id': story_id, 'q_key_e': q_key_e}),
        success: function(new_answer) {
            //append the new_answer to the other answers
            $answer.val('');
            $answer_form.siblings('.meta_Q').find('a.answer_it').trigger('click');
            $answer_form.closest('.QA_container').append(new_answer);
        },
        error: function( xhr, status ) {alert( "Sorry, there was a problem!");}
    });
}

function deleteAnswer($A_container){
    var a_key_e = $A_container.attr('id');
    $.ajax({
        url: 'deleteanswer',
        type: 'POST',
        data: $.param({ 'a_key_e': a_key_e, 'story_id': story_id }),
        success: function(){
            $A_container.remove();
        },
        error: function(){
            alert( "Sorry, there was a problem!");
        },
    });    
}

function incrementThanks($thanks_link){
    var a_key_e = $thanks_link.closest('.A_container').attr('id');
    $.ajax({
        url: '/incrementthanks',
        type: 'POST',
        data: $.param({'a_key_e': a_key_e, 'story_id': story_id}),
        success: function(){
            //increment the actual counter and disable the link
            $thanks_link.siblings('.thanks_counter').html(function(i,t){
                return (parseInt(t) + 1).toString();
            });
            $thanks_link.addClass('clicked');
        },
        error: function( xhr, status ) {alert( "Sorry, there was a problem!");}
    });
}

function saveComments($comments_form){
    $.ajax({
        url: "/savecomments",
        type: "POST",
        data: $comments_form.serialize() + "&story_id=" + story_id,
        success: function(){
            $comments_form.find('.success_message').slideDown(200).delay(1000).fadeOut(400);
        },
        error: function(xhr, status){alert( "Sorry, there was a problem!");},
    });
}




