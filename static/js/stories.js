$(document).ready(function(){
    $("div.query_result").hover(function(){
        $(this).toggleClass("highlighted");
    });


    var difficulty = getQueryParam('difficulty');
    var type_filter = getQueryParam('type_filter');
    
    if (difficulty){
        $('a.left_nav').removeClass('chosen').filter('#' + difficulty).addClass('chosen');
    }
    if (type_filter){
        $('a.top_nav').removeClass('chosen').filter('#' + type_filter).addClass('chosen');
    }
    
//ends document ready    
});

