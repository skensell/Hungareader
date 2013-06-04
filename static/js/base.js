$(document).ready(function(){
    makeTabs();
    makeInfoMessages();
});

function makeTabs(){
    // makes tabs with a fading transition
    $('ul.tabs.fade').each(function(){
      // For each set of tabs, we want to keep track of
      // which tab is active and it's associated content
      var $active, $content, $links = $(this).find('a');

      // If the location.hash matches one of the links, use that as the active tab.
      // If no match is found, use the first link as the initial active tab.
      $active = $($links.filter('[href="'+location.hash+'"]')[0] || $links[0]);
      $active.addClass('active');
      $content = $($active.attr('href'));

      // Hide the remaining content
      $links.not($active).each(function () {
        $($(this).attr('href')).hide();
      });

      // Bind the click event handler
      $(this).on('click', 'a', function(e){
        // If the clicked tab is active, do nothing
        if ($(this).hasClass('active')) {
            return false;
        } else {
        
            var $clicked = $(this);
            var fade_in_new_active = function(){
                // Update the variables with the new link and content
                $active = $clicked;
                $content = $($clicked.attr('href'));
                $active.addClass('active');
                $content.fadeIn('fast');
            }
        
            //Remove active class from old tab
            $active.removeClass('active');
            $content.fadeOut('fast', fade_in_new_active);

            // Prevent the anchor's default click action
            e.preventDefault();
        }
      });
    });
    
    // makes tabs which have a normal transition
    $('ul.tabs.classic').each(function(){
      // For each set of tabs, we want to keep track of
      // which tab is active and it's associated content
      var $active, $content, $links = $(this).find('a');

      // If the location.hash matches one of the links, use that as the active tab.
      // If no match is found, use the first link as the initial active tab.
      $active = $($links.filter('[href="'+location.hash+'"]')[0] || $links[0]);
      $active.addClass('active');
      $content = $($active.attr('href'));

      // Hide the remaining content
      $links.not($active).each(function () {
        $($(this).attr('href')).hide();
      });

      // Bind the click event handler
      $(this).on('click', 'a', function(e){
        // If the clicked tab is active, do nothing
        if ($(this).hasClass('active')) {
            return false;
        } else {
            $active.removeClass('active');
            $content.hide();
            
            $active = $(this);
            $content = $($active.attr('href'));
            
            $active.addClass('active');
            $content.show();

            // Prevent the anchor's default click action
            e.preventDefault();
        }
      });
    });
}

function makeInfoMessages(){
    var $info_msgs = $('div.info_message');
    
    $info_msgs.children('i.close_this').on({
       'mouseenter mouseleave': function(){$(this).toggleClass('highlighted');},
       'click': function(){
           $(this).closest('div.info_message').remove();
       }, 
    });
}

// window.readCookie
(function(){
    // returns undefined if no student
    var cookies;

    function readCookie(name,c,C,i){
        if(cookies){ return cookies[name]; }

        c = document.cookie.split('; ');
        cookies = {};

        for(i=c.length-1; i>=0; i--){
           C = c[i].split('=');
           cookies[C[0]] = C[1];
        }

        return cookies[name];
    }

    window.readCookie = readCookie;
})();

// window.isLoggedIn
window.isLoggedIn = (window.readCookie('student_id') !== undefined);

// window.getQueryParam
(function(){
    // Doesn't URL-decode, but that could be done
    var query_params;
    
    function getQueryParam(name){
        if (query_params){return query_params[name];}
        
        query_params = {};
        var q_string = window.location.search.slice(1);
        var each_param = q_string.split('&');
        
        for (var i = 0; i < each_param.length; i++){
            var P = each_param[i].split('=');
            query_params[P[0]] = P[1];       
        }
        
        return query_params[name]
    }
    
    window.getQueryParam = getQueryParam;
    
})();