/**
 * Created by tony on 17-11-12.
 */
function loginByWeibo(obj) {
    var redirect_url = obj.dataset.next;
    window.location.href = weibo_login_url + '?redirect_url=' + redirect_url;
}

$(function () {

    var btn_login = $("#btn_login");
    var login_form_input = $("#form_login :input");
    bind_auto_submit(login_form_input, btn_login);
    bind_dismiss_msg_container($("#warning_msg"));

    $("[data-toggle='tooltip']").tooltip();

    btn_login.click(function (e) {
        var form = $(this).parent('form');
        var account = form.find('[name="account"]').val();
        var password = form.find('[name="password"]').val();
        var remember = form.find('[name="remember"]').prop("checked");
        var redirect_url = this.dataset.next;

        var reg_email = /^([\.a-zA-Z0-9_-])+@([a-zA-Z0-9_-])+(\.[a-zA-Z0-9_-])+/;
        var reg_password = /^[\.\w@_-]{6,30}$/;

        var warning_div = $("#warning_msg");
        if ((account == '') || (password == '')) {
            var msg = '请输入账户和密码';
            show_msg(warning_div, msg);
            return false
        }
        else if (!reg_email.test(account)) {
            var msg = '账号格式有误，请重新输入';
            show_msg(warning_div, msg);
            return false
        }
        else {
            if (!reg_password.test(password)) {
                var msg = '密码格式有误，请重新输入';
                show_msg(warning_div, msg);
                return false
            }
        }

        $.post(
            login_url,
            {
                "account": account,
                "password": password,
                "redirect_url": redirect_url,
                "remember": remember
            },
            function (data) {
                if (data.code == 200) {
                    location.href = data.redirect_url;
                }
                else {
                    show_msg(warning_div, data.msg);
                    return false
                }
            }
        );
    });

});