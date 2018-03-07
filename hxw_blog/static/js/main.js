function show_msg(selector, msg) {
    selector.removeClass("fade");
    selector.html(msg);
}

function hide_msg(selector) {
    selector.addClass("fade");
    selector.html('');
}

function bind_auto_submit(form_input, btn) {
    form_input.bind('keydown', function (e) {
        var theEvent = e || window.event;
        var code = theEvent.keyCode || theEvent.which || theEvent.charCode;
        if (code == 13) {
            btn.click();
            return false
        }
    });
}

function bind_dismiss_msg_container(container) {
    $(":input").bind('input propertychange', function () {
        hide_msg(container);
        return false
    });
}

$(document).ready(function () {

    $(".back-to-top").click(function (event) {
        $('html,body').animate({scrollTop: 0}, 100);
        return false;
    });

    var back_to_top_link = $(".fixed-btn .back-to-top");

    $(window).scroll(function () {
        var targetPercentage = 10;
        var scrollTo = $(window).scrollTop(),
        docHeight = $(document).height(),
        windowHeight = $(window).height();
        var scrollPercent = (scrollTo / (docHeight-windowHeight)) * 100;
        scrollPercent = scrollPercent.toFixed(1);
        if (scrollPercent >= targetPercentage) {
            back_to_top_link.css('display','block');
        }
        else {
            back_to_top_link.css('display','none');
        }
    });

    $("#register_link").click(function (e) {
        var register_url =  this.dataset.register_url;
        var next = window.location.href;
        window.location.href = register_url + '?next=' + next;
    });

    $("#login_link").click(function (e) {
        var login_url =  this.dataset.login_url;
        var next = window.location.href;
        window.location.href = login_url + '?next=' + next;
    })
});
