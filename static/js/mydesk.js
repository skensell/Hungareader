$(document).ready(function(){
    
    $('#defs').click(function(e){
        var $defs = $('table.vocab_list td:nth-child(2)');
        if ($defs.css('visibility') == 'visible') {
            $defs.css('visibility', 'hidden');
        } else {
            $defs.css('visibility', 'visible');
        }
        e.preventDefault();
    });
    
});