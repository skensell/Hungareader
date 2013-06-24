$(document).ready(function(){
    
    initVocabControls();
    
});

function initVocabControls(){
    
    $('#defs').click(function(e){
        var $defs = $('table.vocab_list td:nth-child(2)');
        if ($defs.css('visibility') == 'visible') {
            $defs.css('visibility', 'hidden');
        } else {
            $defs.css('visibility', 'visible');
        }
        e.preventDefault();
    });
    
    $(window).scroll(function(){
        var $v_controls = $('#vocab_controls_container');
        var $v_controls_fake = $('#vocab_controls_fake');
        if  ($(this).scrollTop() >= 247){
             $v_controls.css({position:'fixed',top:0, width:'50em'});
             $v_controls_fake.show();
        } else {
             $v_controls.css({position:'relative'});
             $v_controls_fake.hide();
            }
    });
}

