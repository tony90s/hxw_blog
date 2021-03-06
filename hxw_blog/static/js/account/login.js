/**
 * Created by tony on 17-11-12.
 */
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

        var reg_email = /^[\w-]+(\.[\w-]+)*@[\w-]+(\.[\w-]+)+$/;
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

        $.ajax({
            type: 'POST',
            url: login_api_url,
            data: {
                "account": account,
                "password": password,
                "redirect_url": redirect_url,
                "remember": remember
            },
            dataType: 'json',
            success: function (data) {
                if (data.code == 200) {
                    location.href = data.redirect_url;
                }
                else {
                    show_msg(warning_div, data.msg);
                    return false
                }
            },
            error: function (XMLHttpRequest, textStatus, errorThrown) {
                var response_json = XMLHttpRequest.responseJSON;
                show_msg(warning_div, response_json.msg);
                return false
            }
        });
    });

    $("#btn_register").click(function (e) {
        var redirect_url = this.dataset.next;
        window.location.href = register_url + '?next=' + redirect_url;
    });

    $(".social-login .weibo").click(function (e) {
        var redirect_url = this.dataset.next;
        window.location.href = weibo_login_url + '?redirect_url=' + redirect_url;
    });

    $(".social-login .qq").click(function (e) {
        var redirect_url = this.dataset.next;
        window.location.href = qq_login_url + '?redirect_url=' + redirect_url;
    });

    $(".social-login .alipay").click(function (e) {
        var redirect_url = this.dataset.next;
        window.location.href = alipay_login_url + '?redirect_url=' + redirect_url;
    })
});