$(document).ready(function(){
    $("div.query_result").hover(function(){
        $(this).toggleClass("highlighted");
    });
    
    $('a.disabled').attr('title', 'Feature not available yet.').on({
        click: function(e){e.preventDefault();},
    });
    
});