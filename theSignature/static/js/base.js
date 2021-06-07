function showBtns() {
    if($("#btns").css("display") == "none"){
        $("#btns").show();
    } else {
        $("#btns").hide();
    }
}



$(document).ready(function(){
	$('.cross').click(function(){
		$(this).toggleClass('open');
	});
});

function goTop(){
	$('html').scrollTop(0);
}