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
    // -- 繁简体 --
    /*
     $('.timepicker').datetimepicker({
     dateFormat: "yy-mm-dd",
     timeFormat: "HH:mm:ss",
     timeInput: true,
     showSecond: true,
     stepHour: 1,
     stepMinute: 1,
     stepSecond: 1,
     changeMonth: true,
     changeYear: true,
     firstDay: 1,
     monthNamesShort: [ "一月", "二月", "三月", "四月", "五月", "六月", "七月", "八月", "九月", "十月", "十一月", "十二月" ],
     dayNamesMin: [ "日","一","二","三","四","五","六"]
     });
     */

    $(".back-to-top").click(function (event) {
        $('html,body').animate({scrollTop: 0}, 100);
        return false;
    });
});
