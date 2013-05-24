$(document).ready(function(){
    $("#story").htmlarea({
        css: "/static/plugins/richtextarea/style/jHtmlArea.Editor.css",
        
        toolbar: [
                "bold", "italic", "underline",
                "|",
                "justifyleft", "justifycenter", "justifyright",
                ]
        });

    $("div.jHtmlArea div.ToolBar ul li a").attr("tabindex", -1);
});